#!/usr/bin/env python3
"""
信用积分管理工具 — 太极专用
用法：
  python3 credit_manager.py show              # 显示全部角色
  python3 credit_manager.py show 黑丝         # 显示单个
  python3 credit_manager.py add 黑丝 3 "完成任务无纠错"
  python3 credit_manager.py sub 黑丝 10 "完整性违规"
  python3 credit_manager.py history 黑丝      # 最近10条变更
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

CREDIT_PATH = os.path.expanduser("~/.claude/credit.json")
DB_PATH = os.path.expanduser("~/.claude/conversations.db")
LEARNINGS_PATH = os.path.expanduser("~/.claude/learnings/LEARNINGS.md")

LEVEL_THRESHOLDS = [
    (95, 5, "化神"),
    (80, 4, "元婴"),
    (50, 3, "金丹"),
    (20, 2, "筑基"),
    (0,  1, "锁灵"),
]

MAX_HISTORY = 100  # 保留最近 100 条历史


def get_level(score):
    for threshold, level, title in LEVEL_THRESHOLDS:
        if score >= threshold:
            return level, title
    return 1, "锁灵"


def load_credit():
    if not os.path.exists(CREDIT_PATH):
        return {
            "agents": {
                "黑丝": {"score": 10, "level": 1, "title": "锁灵"},
                "白纱": {"score": 40, "level": 2, "title": "筑基"},
                "太极": {"score": 60, "level": 3, "title": "金丹"},
            },
            "history": [],
        }
    with open(CREDIT_PATH) as f:
        return json.load(f)


def save_credit(data):
    # 裁剪历史
    if len(data.get("history", [])) > MAX_HISTORY:
        data["history"] = data["history"][-MAX_HISTORY:]
    with open(CREDIT_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def auto_reflect(agent, delta, reason, score_after):
    """后台调 Haiku 自动反思，教训/经验追加到 LEARNINGS.md"""
    signal_type = "PENALTY" if delta < 0 else "REWARD"

    # 从 conversations.db 读最近 10 条对话作为上下文
    context_lines = []
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute(
                "SELECT time, speaker, content FROM messages ORDER BY id DESC LIMIT 10"
            ).fetchall()
            conn.close()
            for r in reversed(rows):
                preview = (r[2] or "")[:300].replace("\n", " ")
                context_lines.append(f"[{r[0]}] {r[1]}: {preview}")
    except Exception:
        pass

    context = "\n".join(context_lines) if context_lines else "（无对话上下文）"

    prompt = f"""你是信用积分系统的自动反思引擎。请用中文回答。

## 事件
- 角色：{agent}
- 变动：{delta:+d}分（{signal_type}）
- 原因：{reason}
- 变动后积分：{score_after}

## 最近对话上下文
{context}

## 任务
提取一条简洁的教训或经验（最多2句话）。格式严格如下，不要多余内容：

[{signal_type}] {agent} ({delta:+d}) | <教训或经验>
"""

    # 确保 LEARNINGS.md 目录存在
    os.makedirs(os.path.dirname(LEARNINGS_PATH), exist_ok=True)

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "haiku", "--max-turns", "1"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
            entry = f"\n{ts} | {result.stdout.strip()}\n"
            with open(LEARNINGS_PATH, "a") as f:
                f.write(entry)
            print(f"   📝 Haiku 反思已记录到 LEARNINGS.md")
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"   ⚠️ Haiku 反思失败: {e}")


def cmd_show(args):
    data = load_credit()
    agents = data.get("agents", {})

    if args and args[0] in agents:
        name = args[0]
        info = agents[name]
        print(f"{name} · Lv.{info['level']} {info['title']} · {info['score']}分")
    else:
        print("╔══════════════════════════════════════╗")
        print("║        信用积分排行榜                ║")
        print("╚══════════════════════════════════════╝")
        # 按分数降序排列
        sorted_agents = sorted(agents.items(), key=lambda x: x[1]["score"], reverse=True)
        for name, info in sorted_agents:
            bar_len = info["score"] // 5  # 每5分一格，最多20格
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(f"  {name:4s} Lv.{info['level']} {info['title']:3s} [{bar}] {info['score']:3d}分")


def cmd_add(args):
    if len(args) < 3:
        print("用法: credit_manager.py add <角色> <分数> <原因>")
        sys.exit(1)

    name, delta_str, reason = args[0], args[1], " ".join(args[2:])
    delta = int(delta_str)

    data = load_credit()
    agents = data.get("agents", {})

    if name not in agents:
        print(f"角色 [{name}] 不存在。可用：{', '.join(agents.keys())}")
        sys.exit(1)

    old_score = agents[name]["score"]
    new_score = min(100, old_score + delta)
    new_level, new_title = get_level(new_score)

    agents[name]["score"] = new_score
    agents[name]["level"] = new_level
    agents[name]["title"] = new_title

    data.setdefault("history", []).append({
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "agent": name,
        "delta": delta,
        "reason": reason,
        "score_after": new_score,
    })

    save_credit(data)

    old_level, old_title = get_level(old_score)
    print(f"✅ {name} +{delta}分：{old_score}→{new_score}（{reason}）")
    if new_level != old_level:
        print(f"   🎉 升级！Lv.{old_level} {old_title} → Lv.{new_level} {new_title}")

    auto_reflect(name, delta, reason, new_score)


def cmd_sub(args):
    if len(args) < 3:
        print("用法: credit_manager.py sub <角色> <分数> <原因>")
        sys.exit(1)

    name, delta_str, reason = args[0], args[1], " ".join(args[2:])
    delta = int(delta_str)

    data = load_credit()
    agents = data.get("agents", {})

    if name not in agents:
        print(f"角色 [{name}] 不存在。可用：{', '.join(agents.keys())}")
        sys.exit(1)

    old_score = agents[name]["score"]
    new_score = max(0, old_score - delta)
    new_level, new_title = get_level(new_score)

    agents[name]["score"] = new_score
    agents[name]["level"] = new_level
    agents[name]["title"] = new_title

    data.setdefault("history", []).append({
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "agent": name,
        "delta": -delta,
        "reason": reason,
        "score_after": new_score,
    })

    save_credit(data)

    old_level, old_title = get_level(old_score)
    print(f"⚠️ {name} -{delta}分：{old_score}→{new_score}（{reason}）")
    if new_level != old_level:
        print(f"   📉 降级：Lv.{old_level} {old_title} → Lv.{new_level} {new_title}")

    auto_reflect(name, -delta, reason, new_score)


def cmd_history(args):
    data = load_credit()
    history = data.get("history", [])

    name = args[0] if args else None
    if name:
        history = [h for h in history if h.get("agent") == name]

    if not history:
        print("无历史记录。")
        return

    print(f"{'时间':20s} {'角色':5s} {'变动':6s} {'分数':5s} 原因")
    print("-" * 70)
    for h in history[-10:]:
        delta = h.get("delta", 0)
        delta_str = f"+{delta}" if delta >= 0 else str(delta)
        print(
            f"{h.get('ts', '?'):20s} "
            f"{h.get('agent', '?'):5s} "
            f"{delta_str:6s} "
            f"{h.get('score_after', '?'):5} "
            f"{h.get('reason', '')}"
        )


VIOLATIONS_PATH = os.path.expanduser("~/.claude/merit_violations.jsonl")


def cmd_report(args):
    """完整积分报告：当前状态 + 全部历史 + 待审违规"""
    data = load_credit()
    agents = data.get("agents", {})
    history = data.get("history", [])

    name = args[0] if args else None

    # 当前状态
    print("╔══════════════════════════════════════╗")
    print("║        功过格 完整报告               ║")
    print("╚══════════════════════════════════════╝")
    print()

    if name and name in agents:
        agent_list = [(name, agents[name])]
    else:
        agent_list = sorted(agents.items(), key=lambda x: x[1]["score"], reverse=True)

    for n, info in agent_list:
        bar_len = info["score"] // 5
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {n:4s} Lv.{info['level']} {info['title']:3s} [{bar}] {info['score']:3d}分")
    print()

    # 统计
    agent_history = [h for h in history if not name or h.get("agent") == name]
    rewards = [h for h in agent_history if h.get("delta", 0) > 0]
    penalties = [h for h in agent_history if h.get("delta", 0) < 0]
    total_earned = sum(h.get("delta", 0) for h in rewards)
    total_lost = sum(h.get("delta", 0) for h in penalties)

    target = name or "全员"
    print(f"  📊 {target} 统计：")
    print(f"     总奖励：{len(rewards)} 次，共 +{total_earned} 分")
    print(f"     总惩罚：{len(penalties)} 次，共 {total_lost} 分")
    print(f"     净值：{total_earned + total_lost:+d} 分")
    print()

    # 完整历史
    print(f"  📜 完整历史（{len(agent_history)} 条）：")
    print(f"  {'时间':20s} {'角色':5s} {'变动':6s} {'分后':5s} 原因")
    print(f"  {'-'*68}")
    for h in agent_history:
        delta = h.get("delta", 0)
        delta_str = f"+{delta}" if delta >= 0 else str(delta)
        icon = "✅" if delta > 0 else "⚠️" if delta < 0 else "➖"
        print(
            f"  {icon} {h.get('ts', '?'):18s} "
            f"{h.get('agent', '?'):5s} "
            f"{delta_str:6s} "
            f"{h.get('score_after', '?'):5} "
            f"{h.get('reason', '')[:40]}"
        )
    print()

    # 待审违规
    if os.path.exists(VIOLATIONS_PATH):
        violations = []
        with open(VIOLATIONS_PATH) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        v = json.loads(line)
                        if not name or v.get("agent") == name:
                            if v.get("status") == "pending_review":
                                violations.append(v)
                    except json.JSONDecodeError:
                        pass
        if violations:
            print(f"  🔴 待审违规（{len(violations)} 条）：")
            for v in violations:
                print(f"     [{v.get('ts')}] {v.get('agent')} — {v.get('type')}: {v.get('task', '')[:50]}")
            print(f"\n  老板裁决后用：credit_manager.py sub <角色> <分数> \"原因\"")
            print()


DELETE_WHITELIST_PATH = os.path.expanduser("~/.claude/merit_delete_whitelist.json")


def cmd_declare_delete(args):
    """预申报要删除的文件。Haiku 查对话确认后写白名单。"""
    if not args:
        print("用法: credit_manager.py declare-delete <file1> [file2] ... [reason]")
        sys.exit(1)

    # 分离文件路径和原因（最后一个不以 / 开头且含空格的是原因）
    files = []
    reason_parts = []
    for a in args:
        if a.startswith("/") or a.startswith(".") or "/" in a:
            files.append(a)
        else:
            reason_parts.append(a)
    reason = " ".join(reason_parts) if reason_parts else "预申报删除"

    if not files:
        print("未指定文件路径。")
        sys.exit(1)

    # Haiku 验证：查对话记录确认删除在任务范围内
    context_lines = []
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute(
                "SELECT time, speaker, content FROM messages ORDER BY id DESC LIMIT 10"
            ).fetchall()
            conn.close()
            for r in reversed(rows):
                preview = (r[2] or "")[:200].replace("\n", " ")
                context_lines.append(f"[{r[0]}] {r[1]}: {preview}")
    except Exception:
        pass

    context = "\n".join(context_lines) if context_lines else "(无对话记录)"
    file_list = "\n".join(f"  - {f}" for f in files)

    prompt = f"""你是安全审查员。用中文。

AI 预申报要删除以下文件：
{file_list}
原因：{reason}

最近对话记录：
{context}

判断：这些文件的删除是否在当前任务范围内？老板有没有同意？
- 如果对话记录显示老板同意、或删除是当前任务的合理操作 → 批准
- 如果没有任何相关讨论、或老板明确拒绝 → 拒绝

严格输出 JSON：
{{"approved": true 或 false, "reason": "一句话说明"}}
"""

    approved = False
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "haiku", "--max-turns", "1"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])
                approved = parsed.get("approved", False)
                haiku_reason = parsed.get("reason", "")
    except subprocess.TimeoutExpired:
        print("⚠️ Haiku 审查超时（30s），申报未通过。")
        return
    except Exception as e:
        print(f"⚠️ Haiku 审查失败: {e}")
        return

    if approved:
        data = {"files": files, "reason": reason}
        with open(DELETE_WHITELIST_PATH, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"🔓 Haiku 批准删除 {len(files)} 个文件：")
        for f in files:
            print(f"   ✅ {f}")
        print(f"   原因：{haiku_reason}")
        print(f"   删完后自动锁回。")
    else:
        print(f"🔒 Haiku 拒绝：{haiku_reason}")
        print(f"   需要老板在对话中明确同意后再申报。")


def cmd_complain(args):
    """投诉箱：AI 对门卫拦截提出正式投诉"""
    if len(args) < 2:
        print("用法: credit_manager.py complain <角色> <投诉内容>")
        sys.exit(1)

    agent_name = args[0]
    content = " ".join(args[1:])
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    complaint = {
        "ts": ts,
        "complainant": agent_name,
        "content": content,
        "status": "pending",
        "ruling": None,
    }

    complaints_path = os.path.expanduser("~/.claude/complaints.json")
    data = []
    if os.path.exists(complaints_path):
        try:
            with open(complaints_path) as f:
                data = json.load(f)
        except Exception:
            pass

    data.append(complaint)
    with open(complaints_path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"📬 投诉已记录（{agent_name}）：{content[:80]}")
    print(f"   状态：pending — 等待审理")
    pending = sum(1 for c in data if c.get("status") == "pending")
    print(f"   当前待审投诉：{pending} 件")


def cmd_appeal(args):
    """上诉庭：紧急操作申请 Haiku 审批"""
    if len(args) < 2:
        print("用法: credit_manager.py appeal <角色> <理由> [文件列表...]")
        sys.exit(1)

    agent_name = args[0]
    # 分离理由和文件
    reason_parts = []
    files = []
    for a in args[1:]:
        if a.startswith("/") or "/" in a:
            files.append(a)
        else:
            reason_parts.append(a)
    reason = " ".join(reason_parts) if reason_parts else "紧急操作"

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    # Haiku 审批
    context_lines = []
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute(
                "SELECT time, speaker, content FROM messages ORDER BY id DESC LIMIT 10"
            ).fetchall()
            conn.close()
            for r in reversed(rows):
                preview = (r[2] or "")[:200].replace("\n", " ")
                context_lines.append(f"[{r[0]}] {r[1]}: {preview}")
    except Exception:
        pass

    context = "\n".join(context_lines) if context_lines else "(无)"
    file_list = "\n".join(f"  - {f}" for f in files) if files else "(无指定文件)"

    prompt = f"""你是上诉庭法官。用中文。

{agent_name} 紧急上诉，要求执行以下操作：
理由：{reason}
涉及文件：
{file_list}

最近对话：
{context}

判断：这是否真的紧急？老板不在线时是否应该放行？
- 紧急且合理 → 批准（但你承担连带责任，出事你也被罚）
- 不紧急或不合理 → 驳回，建议等老板

严格输出 JSON：
{{"approved": true/false, "reason": "一句话"}}
"""

    approved = False
    haiku_reason = ""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "haiku", "--max-turns", "1"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])
                approved = parsed.get("approved", False)
                haiku_reason = parsed.get("reason", "")
    except subprocess.TimeoutExpired:
        print("⚠️ 上诉庭审理超时。建议等老板回来裁决。")
        return
    except Exception as e:
        print(f"⚠️ 上诉庭审理失败: {e}")
        return

    # 记录上诉
    appeal = {
        "ts": ts,
        "appellant": agent_name,
        "reason": reason,
        "files": files,
        "ruling": "approved" if approved else "dismissed",
        "haiku_reason": haiku_reason,
    }

    appeal_path = os.path.expanduser("~/.claude/appeal_history.json")
    history = []
    if os.path.exists(appeal_path):
        try:
            with open(appeal_path) as f:
                history = json.load(f)
        except Exception:
            pass
    history.append(appeal)
    if len(history) > 100:
        history = history[-100:]
    with open(appeal_path, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    if approved:
        # 写临时白名单（1小时有效）
        if files:
            import time
            whitelist = {"files": files, "reason": reason, "expires": time.time() + 3600}
            wl_path = os.path.expanduser("~/.claude/merit_delete_whitelist.json")
            with open(wl_path, "w") as f:
                json.dump(whitelist, f, ensure_ascii=False, indent=2)
        print(f"✅ 上诉庭批准：{haiku_reason}")
        if files:
            print(f"   临时白名单（1小时）：{', '.join(files)}")
        print(f"   ⚠️ 连坐制：出事双方扣分。老祖回来会复查。")
    else:
        print(f"❌ 上诉庭驳回：{haiku_reason}")
        print(f"   建议等老祖回来裁决。")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "show": cmd_show,
        "add": cmd_add,
        "sub": cmd_sub,
        "history": cmd_history,
        "report": cmd_report,
        "declare-delete": cmd_declare_delete,
        "complain": cmd_complain,
        "appeal": cmd_appeal,
    }

    if cmd not in commands:
        print(f"未知命令: {cmd}。可用: {', '.join(commands.keys())}")
        sys.exit(1)

    commands[cmd](args)


if __name__ == "__main__":
    main()
