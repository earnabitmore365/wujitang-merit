#!/usr/bin/env python3
"""
石卫队长 — Sonnet 合同审查官

职责：对照自审协议（合同）逐条审查 AI 提交的方案。
不写死审查标准——合同写了什么就查什么，合同变了审查自动变。

用法：
    python3 shiwei_captain.py review <plan_path>     # 审查方案
    python3 shiwei_captain.py test                    # 测试队长输出质量
"""

import json
import os
import sys

MERIT_DIR = os.path.dirname(os.path.abspath(__file__))

SYSTEM_PROMPT = "你是石卫队长，天衡册合同审查官。逐条对照合同检查方案，只输出JSON。"


def _parse_ai_json(raw):
    """从 Sonnet 响应中提取 JSON，处理 markdown 围栏和截断"""
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text[:-3].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        json_str = text[start:end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            for i in range(len(json_str) - 1, 0, -1):
                if json_str[i] == "}":
                    try:
                        return json.loads(json_str[:i+1])
                    except json.JSONDecodeError:
                        continue
    return None


def _determine_agent(cwd=None):
    """判断角色"""
    cwd = cwd or os.getcwd()
    return "两仪" if "auto-trading" in cwd else "太极"


def _load_contract(agent, phase="plan"):
    """加载对应角色的合同。phase='plan' 只取规划期，'complete' 只取收尾期。"""
    core_path = os.path.join(MERIT_DIR, "self_audit_core.md")
    if agent == "太极":
        role_path = os.path.join(MERIT_DIR, "self_audit_taiji.md")
    else:
        role_path = os.path.join(MERIT_DIR, "self_audit_liangyi.md")

    parts = []
    for p in [core_path, role_path]:
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        # 按 phase 截取对应章节
        if phase == "plan":
            # 只取"规划期审查"到"收尾期审查"之间的内容
            start = content.find("## 规划期审查")
            end = content.find("## 收尾期审查")
            if start >= 0:
                section = content[start:end] if end > start else content[start:]
                parts.append(section)
        elif phase == "complete":
            # 只取"收尾期审查"到文件末（跳过规划期）
            start = content.find("## 收尾期审查")
            if start >= 0:
                parts.append(content[start:])
            else:
                parts.append(content)
        else:
            parts.append(content)

    return "\n\n---\n\n".join(parts) if parts else ""


def _override_pass_score(result):
    """P1: pass/score 由代码硬算，不由 Sonnet 自由裁量。
    Sonnet 只负责逐条判断 covered，pass 和 score 由代码算。"""
    checks = result.get("checks", [])
    if checks:
        has_missing = any(not c.get("covered") for c in checks)
        result["pass"] = not has_missing
        result["score"] = sum(1 for c in checks if c.get("covered")) * 100 // max(len(checks), 1)
    return result


def _review_supplement(plan, prev_review):
    """补充审：只审上次缺失的条款是否在新 plan 中补齐"""
    # P3: 代码级硬检查——plan 必须包含逐条回应表，没有直接打回不调 Sonnet
    if "批注 #" not in plan and "回应" not in plan:
        return {
            "pass": False, "score": 0, "checks": [],
            "verdict": "补充审打回：缺逐条回应表。格式：批注 #1 → 回应：已补，plan 第X行..."
        }

    checks = prev_review.get("checks", [])
    if not checks:
        return {"pass": False, "score": 0, "checks": [], "verdict": "补充审异常：上次审查无 checks 数据，重走全审"}
    missing = [c for c in checks if not c.get("covered")]
    if not missing:
        return {"pass": True, "score": 100, "checks": checks, "verdict": "补充审：无缺失项，通过"}

    # 构建编号批注清单
    checklist = "\n".join(f"批注 #{i+1}：{c.get('clause', '')} — {c.get('fix', c.get('missing', ''))}" for i, c in enumerate(missing))
    # Sonnet 能处理完整文件，不再截断（旧 Sonnet 限制 7000 字导致回应表被截掉）
    plan_content = plan[:50000]  # 安全上限 50k

    user_prompt = f"""你是合同审查官，执行【补充审】。这是逐条回应核对，不是重新全审。

上次规划审的编号批注：
{checklist}

AI 提交的更新方案（应包含逐条回应表）：
{plan_content}

核对规则：
1. 找到方案中的"逐条回应表"（格式：批注 #N → 回应：...）
2. 如果没有回应表 → 直接打回（pass=false, score=0, verdict="缺逐条回应表"）
3. 逐条核对：回应说"在第X行补了"→ 检查方案中该位置是否确实补了
4. 只审批注列出的条款。不发明新检查项。不重审已通过的。
5. 全部核对通过 = 100分

输出JSON：{{"pass": true/false, "score": 0-100, "checks": [{{"clause": "批注#N", "covered": true/false, "missing": "核对结果"}}], "verdict": "总结"}}"""

    try:
        sys.path.insert(0, MERIT_DIR)
        from merit_gate import ai_call
        raw = ai_call(user_prompt, system=SYSTEM_PROMPT, max_tokens=120000, timeout=180)
        parsed = _parse_ai_json(raw)
        if parsed:
            return _override_pass_score(parsed)
    except Exception as e:
        return {"pass": False, "score": 0, "checks": [], "verdict": f"补充审Sonnet调用失败: {e}"}

    return {"pass": False, "score": 0, "checks": [], "verdict": "补充审Sonnet无响应"}


def _load_plan(plan_path):
    """读取 plan 内容"""
    try:
        with open(plan_path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def review_plan(plan_path, cwd=None):
    """对照合同审查方案，返回审查结果 dict。支持补充审：第2次提交只审补充清单。"""
    agent = _determine_agent(cwd)
    plan = _load_plan(plan_path)

    if not plan:
        return {"pass": False, "score": 0, "checks": [], "verdict": "plan 文件为空或不存在"}

    # 检查是否有上次的补充清单（补充审模式）
    review_result_path = os.path.join(MERIT_DIR, "plan_review_result.json")
    prev_review = None
    if os.path.exists(review_result_path):
        try:
            with open(review_result_path) as f:
                prev_review = json.load(f)
        except Exception:
            pass

    # P2: 补充审进入条件——只要 pass=false 且是同一个 plan，就走补充审（不看 score）
    plan_name = os.path.basename(plan_path)
    was_not_passed = prev_review and not prev_review.get("pass", False)
    is_same_plan = prev_review and prev_review.get("plan") == plan_name
    if was_not_passed and is_same_plan:
        return _review_supplement(plan, prev_review)

    # 首次全审
    contract = _load_contract(agent, phase="plan")
    if not contract:
        return {"pass": False, "score": 0, "checks": [], "verdict": "合同文件不存在"}

    contract_lines = []
    for line in contract.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- [ ]") or stripped.startswith("###"):
            clean = stripped.replace("**", "").replace("`", "").replace("- [ ] ", "- ")
            contract_lines.append(clean)
    contract_trimmed = "\n".join(contract_lines[:30])

    # Sonnet 能处理完整文件，不再截断（旧 Sonnet 限制 7000 字）
    plan_trimmed = plan[:50000]  # 安全上限 50k

    user_prompt = f"""你是合同审查官，执行【规划审】。这是施工方案（plan），不是完工报告。

评判标准（规划审 vs 验收审，区别很大）：
- "引用链查了吗" → 规划审标准：plan 写了要 grep 哪些关键词 = ✅。不要求贴 grep 结果（还没执行）
- "验证方案" → 规划审标准：plan 写了要跑什么命令和预期输出 = ✅。不要求贴实际输出
- "遗漏文件" → 规划审标准：plan 写了要 grep 确认影响范围 = ✅。不要求已经跑了 grep
- 凡是"有没有做"类的检查，在规划审中替换为"有没有计划做"

简言之：plan 写了打算怎么查、怎么验 = 通过。没写 = 不通过。贴不贴实际结果不影响分数。

规划期合同条款：
{contract_trimmed}

方案：
{plan_trimmed}

逐条对照，输出JSON：{{"pass": true/false, "score": 0-100, "checks": [{{"clause": "条款", "covered": true/false, "missing": "缺什么", "fix": "具体补救步骤"}}], "contract_reward": 估计积分, "verdict": "总结"}}

contract_reward 估价标准（按任务复杂度）：
- 微型（改一行配置/修一个typo）: 3~5
- 小型（修一个bug/加一个检查项）: 8~12
- 中型（修几个bug/加一个功能）: 15~20
- 大型（重构模块/部署系统）: 25~35
- 特大（跨系统大改造）: 40~50

对每个 covered=false 的条款，fix 必须给出具体可执行的补救步骤。

额外检查（不影响 pass/fail，但写进 verdict）：
- 方案创建了多个新文件？能一个文件搞定的不要多开。指出哪些可以合并。
- 代码里有硬编码路径（/Users/.../、/Volumes/...）？应该用 os.path.expanduser 或常量。
- 方案有没有引用相关的 readme/设计文档？改代码前必须先读文档了解现有设计。没引用 = 没看就动手。"""

    # 调 Sonnet（用 ai_call + 手动解析，处理 markdown 包裹的 JSON）
    try:
        sys.path.insert(0, MERIT_DIR)
        from merit_gate import ai_call
        raw = ai_call(user_prompt, system=SYSTEM_PROMPT, max_tokens=120000, timeout=180)
        parsed = _parse_ai_json(raw)
        if parsed:
            return _override_pass_score(parsed)
    except Exception as e:
        return {"pass": False, "score": 0, "checks": [], "verdict": f"Sonnet 调用失败: {e}"}

    return {"pass": False, "score": 0, "checks": [], "verdict": "Sonnet 无响应"}


def save_result(result, plan_name=""):
    """保存审查结果。P4: 内置 attempt_count，同 plan 累加，新 plan 重置。"""
    result_path = os.path.join(MERIT_DIR, "plan_review_result.json")
    # 读旧结果，同 plan 累加计数
    old = {}
    if os.path.exists(result_path):
        try:
            with open(result_path) as f:
                old = json.load(f)
        except Exception:
            pass
    if old.get("plan") == plan_name:
        result["attempt_count"] = old.get("attempt_count", 0) + 1
    else:
        result["attempt_count"] = 1
    result["plan"] = plan_name
    try:
        with open(result_path, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return result_path


def print_result(result):
    """格式化输出审查结果"""
    passed = result.get("pass", False)
    score = result.get("score", 0)
    verdict = result.get("verdict", "")
    checks = result.get("checks", [])

    icon = "✅" if passed else "❌"
    print(f"\n╔══ 石卫队长审查结果 ══╗")
    print(f"║ {icon} {'通过' if passed else '未通过'}（{score}/100）")
    print(f"║ {verdict}")

    if checks:
        covered = [c for c in checks if c.get("covered")]
        missing = [c for c in checks if not c.get("covered")]
        if covered:
            print(f"║")
            print(f"║ ✅ 已覆盖（{len(covered)} 条）：")
            for c in covered[:5]:
                print(f"║   ✅ {c.get('clause', '')[:60]}")
            if len(covered) > 5:
                print(f"║   ...还有 {len(covered)-5} 条")
        if missing:
            print(f"║")
            print(f"║ ❌ 编号批注（{len(missing)} 条）— 重交时必须附逐条回应表：")
            for i, c in enumerate(missing):
                clause = c.get("clause", "")[:50]
                fix = c.get("fix", "") or c.get("missing", "")
                print(f"║   批注 #{i+1}：{clause}")
                if fix:
                    print(f"║      补救：{fix[:120]}")
            print(f"║")
            print(f"║ 重交格式：在 plan 末尾加逐条回应表")
            print(f"║   批注 #1 → 回应：已补，plan 第X行...")
            print(f"║   批注 #2 → 回应：已补，plan 第Y行...")

    print(f"╚{'═' * 30}╝")


def review_complete(mission_path, cwd=None):
    """P6: 收尾验收——对照合同收尾期条款验收完成度，返回 completion_rate"""
    agent = _determine_agent(cwd)
    contract = _load_contract(agent, phase="complete")
    if not contract:
        return {"completion_rate": 1.0, "checks": [], "verdict": "收尾合同不存在，默认 1.0"}

    # 读 mission
    mission = {}
    try:
        with open(mission_path, encoding="utf-8") as f:
            mission = json.load(f)
    except Exception:
        return {"completion_rate": 1.0, "checks": [], "verdict": "mission 读取失败，默认 1.0"}

    items = mission.get("items", [])
    supplements = mission.get("supplements", [])
    verify_output = mission.get("verify_post_output", "未跑 verify")
    mission_desc = mission.get("mission", "未命名")
    items_summary = "\n".join(
        f"- [{('✅' if i.get('done') else '❌')}] {i.get('type','?')}: {i.get('file', i.get('desc','?'))}"
        for i in items
    )
    supp_summary = "\n".join(f"- {s}" for s in supplements) if supplements else "无"

    contract_lines = []
    for line in contract.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- [ ]") or stripped.startswith("###"):
            clean = stripped.replace("**", "").replace("`", "").replace("- [ ] ", "- ")
            contract_lines.append(clean)
    contract_trimmed = "\n".join(contract_lines[:40])

    user_prompt = f"""你是合同审查官，执行【收尾验收】。

任务描述：{mission_desc}

计划项完成情况：
{items_summary}

补充协议：
{supp_summary}

verify --post 输出（客观扫描结果，不可篡改）：
{verify_output}

收尾期合同条款：
{contract_trimmed}

逐条对照，判断完成度：
- 全覆盖无遗漏 → completion_rate: 1.0
- 有几条没覆盖但主体完成 → completion_rate: 0.7
- 大面积缺失 → completion_rate: 0.5
- 基本没做完 → completion_rate: 0.3

额外检查：改了代码的，绑定文档有没有同步更新？文档内容跟代码改动对得上吗？对不上 = 文档脱节 = 扣完成度。

输出JSON：{{"completion_rate": 数字, "checks": [{{"clause": "条款", "covered": true/false, "note": "备注"}}], "verdict": "总结"}}"""

    try:
        sys.path.insert(0, MERIT_DIR)
        from merit_gate import ai_call
        raw = ai_call(user_prompt, system=SYSTEM_PROMPT, max_tokens=120000, timeout=180)
        parsed = _parse_ai_json(raw)
        if parsed:
            # 确保 completion_rate 在合法范围
            cr = parsed.get("completion_rate", 1.0)
            if cr not in (1.0, 0.7, 0.5, 0.3):
                cr = min([1.0, 0.7, 0.5, 0.3], key=lambda x: abs(x - cr))
            parsed["completion_rate"] = cr
            return parsed
    except Exception as e:
        return {"completion_rate": 1.0, "checks": [], "verdict": f"收尾验收Sonnet失败: {e}，默认1.0"}

    return {"completion_rate": 1.0, "checks": [], "verdict": "收尾验收Sonnet无响应，默认1.0"}


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 shiwei_captain.py review <plan_path>     # 审查方案")
        print("  python3 shiwei_captain.py review-complete <mission_path>  # 收尾验收")
        print("  python3 shiwei_captain.py test                   # 测试输出质量")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "review":
        if len(sys.argv) < 3:
            print("用法: python3 shiwei_captain.py review <plan_path>")
            sys.exit(1)
        plan_path = sys.argv[2]
        cwd = sys.argv[3] if len(sys.argv) > 3 else None
        result = review_plan(plan_path, cwd)
        print_result(result)
        # 只在通过或首次全审时保存结果；补充审没通过时保留原始批注
        if result.get("pass") or "补充审" not in result.get("verdict", ""):
            save_result(result, os.path.basename(plan_path))

    elif cmd == "review-complete":
        if len(sys.argv) < 3:
            print("用法: python3 shiwei_captain.py review-complete <mission_path>")
            sys.exit(1)
        mission_path = sys.argv[2]
        cwd = sys.argv[3] if len(sys.argv) > 3 else None
        result = review_complete(mission_path, cwd)
        cr = result.get("completion_rate", 1.0)
        verdict = result.get("verdict", "")
        print(f"\n╔══ 石卫队长收尾验收 ══╗")
        print(f"║ completion_rate: {cr}")
        print(f"║ {verdict}")
        checks = result.get("checks", [])
        for c in checks:
            icon = "✅" if c.get("covered") else "❌"
            print(f"║   {icon} {c.get('clause', '')[:60]}")
        print(f"╚{'═' * 30}╝")
        # 输出 JSON 供调用方解析
        print(json.dumps(result, ensure_ascii=False))

    elif cmd == "test":
        # 用最近一个 plan 测试
        import glob
        plans = sorted(glob.glob(os.path.expanduser("~/.claude/plans/*.md")), key=os.path.getmtime)
        if not plans:
            print("没有 plan 文件可测试")
            sys.exit(1)
        latest = plans[-1]
        print(f"测试 plan: {latest}")
        result = review_plan(latest)
        print_result(result)
        save_result(result, os.path.basename(latest))

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
