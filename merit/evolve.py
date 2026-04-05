#!/usr/bin/env python3
"""
石卫自进化引擎 — cron 每 5 分钟自动跑

cron: */5 * * * * python3 ~/.claude/merit/evolve.py
手动: python3 ~/.claude/merit/evolve.py
详细: EVOLVE_README.md

流程：
1. 读 LEARNINGS.md 全部教训（LRN格式 + PENALTY/REWARD格式）
2. 按 behavior 聚类，每一类都尝试生成子规则（不等累计）
3. MiniMax 生成 → MiniMax 二次审查 → 通过自动写入 rules.md 子类
4. 所有 approved 子类 → MiniMax 精炼父类 → 直接更新 INJECT 区
5. 30天未触发 → deprecated 归档
6. 子类只增不减，父类跟着子类进化，三重防丢保护
"""

import json
import os
import re
from datetime import datetime, timezone

MERIT_DIR = os.path.expanduser("~/.claude/merit")
LEARNINGS_PATH = os.path.join(MERIT_DIR, "learnings", "LEARNINGS.md")
PROPOSALS_PATH = os.path.join(MERIT_DIR, "rule_proposals.json")
DEPRECATED_PATH = os.path.join(MERIT_DIR, "rules_deprecated.md")
SHIWEI_LOG_DIR = os.path.join(MERIT_DIR, "shiwei_log")

# MiniMax AI 调用（复用 merit_gate 的）
import sys
sys.path.insert(0, MERIT_DIR)
try:
    from merit_gate import ai_call, queue_pending_ai_task
except ImportError:
    def ai_call(*a, **kw): return ""
    def queue_pending_ai_task(*a, **kw): pass


def parse_learnings():
    """读 LEARNINGS.md，提取教训并聚类。支持两种格式：
    1. 旧格式：[PENALTY/REWARD] agent [behavior_id] note
    2. LRN 格式：## LRN-XXXXXXXX + **类型**：纠错/提升 + **教训**：...
    """
    if not os.path.exists(LEARNINGS_PATH):
        return {}
    clusters = {}
    try:
        with open(LEARNINGS_PATH, encoding="utf-8") as f:
            content = f.read()

        # 格式1：旧格式 [PENALTY/REWARD] agent [behavior_id] note
        for match in re.finditer(r'\[(?:PENALTY|REWARD)\].*?\[(\w+)\]\s*(.*)', content):
            behavior = match.group(1)
            note = match.group(2).strip()
            if behavior not in clusters:
                clusters[behavior] = {"count": 0, "examples": [], "lessons": []}
            clusters[behavior]["count"] += 1
            if len(clusters[behavior]["examples"]) < 3:
                clusters[behavior]["examples"].append(note)

        # 格式2：LRN 条目（/reflect 写的）
        lrn_blocks = re.split(r'(?=## LRN-)', content)
        for block in lrn_blocks:
            if not block.startswith('## LRN-'):
                continue
            # 提取类型
            type_match = re.search(r'\*\*类型\*\*：(\S+)', block)
            lesson_match = re.search(r'\*\*教训\*\*：(.+?)(?:\n|$)', block)
            trigger_match = re.search(r'\*\*触发原话\*\*.*?：(.+?)(?:\n|$)', block)
            count_match = re.search(r'\*\*出现次数\*\*：(\d+)', block)

            if not type_match or not lesson_match:
                continue

            entry_type = type_match.group(1)  # 纠错/提升/最佳实践
            lesson = lesson_match.group(1).strip()
            trigger = trigger_match.group(1).strip() if trigger_match else ""
            count = int(count_match.group(1)) if count_match else 1

            # 用类型+教训前10字作为聚类key
            behavior = f"lrn_{entry_type}_{lesson[:20]}"

            if behavior not in clusters:
                clusters[behavior] = {"count": 0, "examples": [], "lessons": []}
            clusters[behavior]["count"] += count
            if len(clusters[behavior]["examples"]) < 3:
                clusters[behavior]["examples"].append(lesson)
            if trigger and len(clusters[behavior].get("lessons", [])) < 3:
                clusters[behavior].setdefault("lessons", []).append(trigger)

    except Exception:
        pass
    return clusters


def load_proposals():
    if not os.path.exists(PROPOSALS_PATH):
        return []
    try:
        with open(PROPOSALS_PATH) as f:
            return json.load(f)
    except Exception:
        return []


def save_proposals(proposals):
    try:
        with open(PROPOSALS_PATH, "w") as f:
            json.dump(proposals, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ❌ 保存提案失败: {e}")


def has_existing_proposal(proposals, behavior_id):
    """检查是否已有该 behavior 的提案（pending 或 approved）"""
    return any(
        p["behavior_id"] == behavior_id and p["status"] in ("pending", "approved")
        for p in proposals
    )


def validate_proposal(rule_text):
    """二次审查：MiniMax 验证提案质量，防止垃圾规则自动写入"""
    prompt = f"""你是规则审查员。用中文。

审查这条规则是否合理：
「{rule_text}」

判断标准：
1. 是否是明确的"做什么"或"不做什么"指令？（不是描述性的）
2. 是否会产生反效果？（如"禁止完成任务"、"禁止主动发现问题"这种荒谬规则）
3. 是否从根因出发？（不是表面症状）
4. AI 违反时是否能被检测到？

只输出 JSON：{{"pass": true/false, "reason": "一句话"}}

答案："""
    result = ai_call(prompt, max_tokens=4096, timeout=15)
    if not result:
        return False, "MiniMax审查失败"
    try:
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(result[start:end])
            return parsed.get("pass", False), parsed.get("reason", "")
    except Exception:
        pass
    return False, "解析失败"


def auto_approve_and_inject(proposal):
    """通过审查的提案自动写入 rules.md 子类区域"""
    rules_path = RULES_PATH
    if not os.path.exists(rules_path):
        return False

    rule_text = proposal["rule_text"]
    parent = classify_to_parent(rule_text)
    proposal["status"] = "approved"
    proposal["approved_by"] = "evolve_auto"
    proposal["approved_date"] = datetime.now().strftime("%Y-%m-%d")
    proposal["parent_category"] = parent

    # 写入 rules.md 子类区域（INJECT END 之后）
    try:
        with open(rules_path, encoding="utf-8") as f:
            content = f.read()

        # 在文件末尾追加子类
        entry = f"\n\n### {proposal['id']}｜{rule_text}\n"
        entry += f"- **来源**：evolve 自动生成（{proposal['behavior_id']} {proposal['source_count']}次）\n"
        entry += f"- **父类**：{parent}\n"
        entry += f"- **生效日期**：{proposal['approved_date']}\n"

        with open(rules_path, "a", encoding="utf-8") as f:
            f.write(entry)

        print(f"  ✅ 自动写入 rules.md：【{parent}】{rule_text[:50]}")
        return True
    except Exception as e:
        print(f"  ❌ 写入失败：{e}")
        return False


MAX_NEW_PER_RUN = 20  # 每轮最多处理 20 个新类（500 RPM 限制下绰绰有余）


def generate_proposals(clusters, proposals):
    """每类教训都尝试生成子规则 → 审查 → 自动写入。每轮最多 5 个新类。"""
    new_count = 0
    next_id = len(proposals) + 1

    for behavior, data in clusters.items():
        if new_count >= MAX_NEW_PER_RUN:
            break
        if has_existing_proposal(proposals, behavior):
            continue

        examples = "\n".join(f"  - {e}" for e in data["examples"])
        lessons = "\n".join(f"  - {l}" for l in data.get("lessons", []))
        prompt = f"""你是规则生成引擎。用中文。

「{behavior}」这类问题在 LEARNINGS 里出现了 {data['count']} 次。

教训：
{examples}

老板原话：
{lessons if lessons else '(无)'}

生成一条具体、可执行的行为规则，防止这类问题再发生。

要求：
1. 规则必须是"做什么"或"不做什么"的明确指令，不是描述性的
2. 从问题根因出发，不是表面症状
3. 必须对 AI 有约束力——如果 AI 违反了，应该能被检测到
4. 不要生成反向规则（如"禁止完成任务"这种荒谬的规则）

格式：一句话规则描述（不超过50字）
只输出规则本身，不要编号、不要标题前缀、不要解释。

答案："""

        rule_text = ai_call(prompt, max_tokens=16384, timeout=60)
        if rule_text:
            rule_text = rule_text.strip()
            # 二次审查
            passed, reason = validate_proposal(rule_text)
            if not passed:
                print(f"  ❌ 审查未通过 [{behavior}]: {reason}")
                continue

            proposal = {
                "id": f"SUB-{next_id:03d}",
                "status": "pending",
                "created": datetime.now().strftime("%Y-%m-%d"),
                "behavior_id": behavior,
                "rule_text": rule_text,
                "source_count": data["count"],
                "effective_triggers": 0,
                "last_trigger": None,
                "approved_by": None,
                "approved_date": None,
            }
            # 审查通过 → 自动批准并写入 rules.md
            if auto_approve_and_inject(proposal):
                proposals.append(proposal)
                next_id += 1
                new_count += 1
            else:
                # 写入失败，保持 pending
                proposals.append(proposal)
                next_id += 1
                print(f"  ⚠️ 写入失败，保持 pending")
        else:
            queue_pending_ai_task("rule_proposal", "evolve", prompt, f"{behavior} {data['count']}次")
            print(f"  ⚠️ MiniMax 失败，{behavior} 存入队列等太极处理")

    return new_count


def check_deprecation(proposals):
    """30 天未触发的 approved 子 rule → deprecated"""
    deprecated_count = 0
    today = datetime.now()

    for p in proposals:
        if p["status"] != "approved":
            continue
        last = p.get("last_trigger")
        if last:
            days_since = (today - datetime.fromisoformat(last)).days
        else:
            days_since = (today - datetime.fromisoformat(p.get("approved_date", p["created"]))).days

        if days_since >= 30:
            p["status"] = "deprecated"
            deprecated_count += 1
            # 写入废弃存档
            try:
                with open(DEPRECATED_PATH, "a", encoding="utf-8") as f:
                    f.write(f"\n## {p['id']}（废弃 {today.strftime('%Y-%m-%d')}）\n")
                    f.write(f"- 原规则：{p['rule_text']}\n")
                    f.write(f"- 原因：{days_since} 天未触发\n")
            except Exception:
                pass
            print(f"  🗑️ 废弃 {p['id']}：{days_since} 天未触发")

    return deprecated_count


RULES_PATH = os.path.expanduser("~/.claude/projects/-Users-allenbot/memory/rules.md")

# 父类关键词（用于把子规则归类到父类）
PARENT_KEYWORDS = {
    "完整性": ["完整", "链路", "同步", "遗留", "残留", "引用", "追踪", "全链路", "检查"],
    "真实性": ["验证", "查证", "确认", "实测", "真实", "造假", "数据", "核验"],
    "有效性": ["最简", "工具", "方案", "重复", "手搓", "现有"],
    "纪律": ["听完", "纠正", "压缩", "糊弄", "配额", "石卫", "报告", "报备"],
    "第一性原理": ["根因", "本质", "惯性", "模板"],
    "子目标继承": ["子目标", "子步骤", "管控", "绕过"],
    "渐进验证": ["小样本", "全量", "渐进"],
}


def classify_to_parent(rule_text):
    """根据规则内容归类到最匹配的父类"""
    scores = {}
    for parent, keywords in PARENT_KEYWORDS.items():
        scores[parent] = sum(1 for kw in keywords if kw in rule_text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "纪律"


def refresh_parent_summaries(proposals):
    """approved 子类新增后 → MiniMax 重新生成父类内容 → 直接写入 INJECT 区

    父类不是一句话总结——是该类别下所有规则的精炼列表。
    子类有新增，父类必须跟着进化，否则 hook 注入的是过时内容。
    """
    all_approved = [p for p in proposals if p["status"] == "approved"]
    # 有未更新的就处理；全部已更新时，每10轮强制精炼一次父类
    new_approved = [p for p in all_approved if not p.get("parent_updated")]
    if not new_approved:
        # 强制精炼：每10轮（约50分钟）重新精炼全部父类
        import random
        if random.randint(1, 10) != 1:
            return 0
        # 强制模式：把所有 approved 标记为未更新，重新精炼
        new_approved = all_approved
        for p in new_approved:
            p["parent_updated"] = False

    if not os.path.exists(RULES_PATH):
        return 0

    with open(RULES_PATH, encoding="utf-8") as f:
        content = f.read()

    # 按父类分组
    by_parent = {}
    for p in new_approved:
        parent = classify_to_parent(p["rule_text"])
        if parent not in by_parent:
            by_parent[parent] = []
        by_parent[parent].append(p["rule_text"])

    updated = 0
    for parent, new_rules in by_parent.items():
        # 提取 INJECT 区该父类的现有内容
        # 格式：【完整性】\n完整性-1｜...\n完整性-2｜...
        pattern = rf'(【{re.escape(parent)}】\n)((?:[^\n【]+\n)*)'
        match = re.search(pattern, content)
        if not match:
            continue

        header = match.group(1)  # 【完整性】\n
        existing_lines = match.group(2).strip()

        # 收集所有子规则（现有 + 新增，新增截取前200字防prompt过长）
        all_rules = existing_lines + "\n" + "\n".join(
            f"- 新增：{r[:200]}" for r in new_rules[:5]
        )

        # 计算下一个编号
        existing_nums = re.findall(rf'{re.escape(parent)}-(\d+)', existing_lines)
        next_num = max(int(n) for n in existing_nums) + 1 if existing_nums else 1

        new_rules_text = "\n".join(f"- {r[:200]}" for r in new_rules[:5])
        prompt = f"""你是规则追加引擎。用中文。

「{parent}」类别要追加以下新规则：
{new_rules_text}

现有规则（不可修改，原样保留）：
{existing_lines}

任务：只为新增规则生成条目，格式：{parent}-{next_num}｜规则描述
- 如果新规则跟现有规则完全重复，输出"无需追加"
- 如果新规则是全新的，输出新条目（从编号 {next_num} 开始）
- 每条最多3句话
- 只输出新条目或"无需追加"，不要输出现有规则

答案："""

        result = ai_call(prompt, max_tokens=4096, timeout=60)
        if result and len(result) < 2000:
            result = result.strip()
            if "无需追加" in result:
                print(f"  ⏭️ 【{parent}】新规则与现有重复，无需追加")
                for p in new_approved:
                    if classify_to_parent(p["rule_text"]) == parent:
                        p["parent_updated"] = True
                updated += 1
                continue

            # 提取新条目
            result_lines = [l.strip() for l in result.split("\n") if l.strip()]
            valid_lines = [l for l in result_lines if f"{parent}-" in l and "｜" in l]

            if valid_lines:
                # 追加到现有内容后面（不替换）
                old_section = match.group(0)
                new_section = old_section.rstrip("\n") + "\n" + "\n".join(valid_lines) + "\n"
                content = content.replace(old_section, new_section)

                with open(RULES_PATH, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"  ✅ 【{parent}】追加 {len(valid_lines)} 条新规则")
                updated += 1
                for p in new_approved:
                    if classify_to_parent(p["rule_text"]) == parent:
                        p["parent_updated"] = True
            else:
                print(f"  ❌ 【{parent}】格式不合格，跳过")
        else:
            print(f"  ⚠️ 【{parent}】MiniMax 失败或返回过长")

    return updated


def main():
    print("═══ 规则进化引擎 ═══")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 1. 读 LEARNINGS 聚类
    clusters = parse_learnings()
    print(f"\n📊 LEARNINGS 聚类：{len(clusters)} 类行为")
    for b, d in sorted(clusters.items(), key=lambda x: -x[1]["count"])[:5]:
        print(f"  {b}: {d['count']} 次")

    # 2. 加载现有提案
    proposals = load_proposals()
    pending = [p for p in proposals if p["status"] == "pending"]
    approved = [p for p in proposals if p["status"] == "approved"]
    print(f"\n📋 现有提案：{len(pending)} pending, {len(approved)} approved")

    # 3. LEARNINGS → 生成新子类提案
    print(f"\n🔄 检查新子类提案...")
    new_count = generate_proposals(clusters, proposals)
    print(f"  生成 {new_count} 条新提案")

    # 3.5 已有规则质量精炼（每轮随机抽 3 条 approved 用 MiniMax 审查改进）
    approved_list = [p for p in proposals if p["status"] == "approved" and p.get("rule_text")]
    if approved_list:
        import random
        sample = random.sample(approved_list, min(3, len(approved_list)))
        refined = 0
        for p in sample:
            prompt = f"""你是规则精炼引擎。用中文。

审查并改进这条规则的措辞：
「{p['rule_text']}」

要求：
1. 如果措辞已经很好（明确、可执行、从根因出发），原样输出
2. 如果可以更精准，输出改进版（不超过3句话）
3. 只输出规则本身，不要解释

答案："""
            result = ai_call(prompt, max_tokens=4096, timeout=30)
            if result and len(result) < 500 and result.strip() != p["rule_text"]:
                old = p["rule_text"]
                p["rule_text"] = result.strip()
                p["last_refined"] = datetime.now().strftime("%Y-%m-%d")
                refined += 1
                print(f"  🔧 精炼: {old[:40]}... → {result.strip()[:40]}...")
        if refined:
            print(f"  精炼 {refined} 条规则")

    # 4. approved 子类 → 精化父类总结
    print(f"\n🔄 检查父类更新...")
    parent_count = refresh_parent_summaries(proposals)
    print(f"  更新 {parent_count} 个父类建议")

    # 5. 检查废弃（30天未触发）
    print(f"\n🔍 检查废弃...")
    dep_count = check_deprecation(proposals)
    print(f"  废弃 {dep_count} 条")

    # 6. 保存
    save_proposals(proposals)

    # 7. 总结
    pending = [p for p in proposals if p["status"] == "pending"]
    approved = [p for p in proposals if p["status"] == "approved"]
    print(f"\n✅ 完成。pending={len(pending)} approved={len(approved)}")
    if pending:
        print(f"  待老板审批")
    if parent_count:
        print(f"  父类 INJECT 区已自动更新 {parent_count} 个类别")

    # 8. 自动 git push（每次 evolve 跑完同步 GitHub）
    auto_git_push()


def auto_git_push():
    """evolve 跑完自动 commit + push 到 GitHub"""
    import subprocess
    merit_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        # 检查有没有变更
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=merit_dir, capture_output=True, text=True, timeout=10
        )
        if not result.stdout.strip():
            return  # 没变更不推
        # add + commit + push
        subprocess.run(["git", "add", "."], cwd=merit_dir, capture_output=True, timeout=10)
        subprocess.run(
            ["git", "commit", "-m", f"evolve auto-sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            cwd=merit_dir, capture_output=True, timeout=10
        )
        result = subprocess.run(
            ["git", "push"],
            cwd=merit_dir, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"  📤 GitHub 已同步")
        else:
            print(f"  ⚠️ push 失败: {result.stderr[:100]}")
    except Exception as e:
        print(f"  ⚠️ git sync 失败: {e}")


if __name__ == "__main__":
    main()
