#!/usr/bin/env python3
"""
信用积分管理工具 — 太极专用
用法：
  python3 credit_manager.py show              # 显示全部角色
  python3 credit_manager.py add 两仪 3 "完成任务无纠错"
  python3 credit_manager.py sub 两仪 10 "完整性违规"
  python3 credit_manager.py history 两仪      # 最近10条变更
  python3 credit_manager.py mission submit "描述" --modify f1 --delete f2
  python3 credit_manager.py mission status/complete/abort/extend

┌─ 结构索引（改动前先看这里，改完后必须更新行号）─────────┐
│                                                         │
│  AI 调用        L51-L57    从 merit_gate import          │
│  等级+积分      L70-L105   get_level / load / save      │
│  自动反思       L107-L158  auto_reflect                 │
│  CLI: show      L160-L178  显示积分                     │
│  CLI: add/sub   L180-L265  加减分                       │
│  CLI: history   L267-L294  历史记录                     │
│  CLI: report    L332-L410  完整报告                     │
│  CLI: declare   L413-L472  删除申报                     │
│  CLI: complain  L475-L510  投诉箱                       │
│  CLI: appeal    L512-L654  上诉庭                       │
│  Mission        L656-L930  submit/status/complete/abort  │
│  CLI: search    L933-L1010 搜索记忆                     │
│  Main 入口      L1013-L1040 命令分支                    │
│                                                         │
│  ⚠️ 铁律：改完本文件必须同步更新此索引的行号            │
└─────────────────────────────────────────────────────────┘
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

MERIT_DIR = os.path.expanduser("~/.claude/merit")
CREDIT_PATH = os.path.join(MERIT_DIR, "credit.json")
MISSION_PATH = os.path.join(MERIT_DIR, "mission.json")
DB_PATH = os.path.expanduser("~/.claude/conversations.db")

# ── AI 调用（内联，不依赖外部文件）──────────────────

_MINIMAX_KEY_PATH = os.path.expanduser("~/.claude/.minimax_key")
_MINIMAX_BASE_URL = "https://api.minimax.io/anthropic"
_MINIMAX_MODEL = "MiniMax-M2.7-highspeed"


# AI 调用统一从 merit_gate 导入（不再维护副本）
try:
    from merit_gate import ai_call, ai_call_json
except ImportError:
    def ai_call(*a, **kw): return ""
    def ai_call_json(*a, **kw): return {}
LEARNINGS_PATH = os.path.join(MERIT_DIR, "learnings", "LEARNINGS.md")

LEVEL_THRESHOLDS = [
    (475, 5, "化神"),
    (400, 4, "元婴"),
    (250, 3, "金丹"),
    (100, 2, "筑基"),
    (0,  1, "锁灵"),
]

MAX_HISTORY = 100  # 保留最近 100 条历史


def get_level(score, agent_name=None):
    if agent_name:
        try:
            with open(CREDIT_PATH) as f:
                data = json.load(f)
            agent = data.get("agents", {}).get(agent_name, {})
            if agent.get("locked"):
                return agent.get("level", 1), agent.get("title", "锁灵")
        except Exception:
            pass
    for threshold, level, title in LEVEL_THRESHOLDS:
        if score >= threshold:
            return level, title
    return 1, "锁灵"


def load_credit():
    if not os.path.exists(CREDIT_PATH):
        return {
            "agents": {
                "两仪": {"score": 50, "level": 3, "title": "金丹"},
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
    """自动反思，教训/经验追加到 LEARNINGS.md"""
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
                preview = (r[2] or "").replace("\n", " ")
                context_lines.append(f"[{r[0]}] {r[1]}: {preview}")
    except Exception:
        pass

    context = "\n".join(context_lines) if context_lines else "（无对话上下文）"

    prompt = f"""你是天衡册的自动反思引擎。请用中文回答。

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
        text = ai_call(prompt, timeout=15)
        if text:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
            entry = f"\n{ts} | {text.strip()}\n"
            with open(LEARNINGS_PATH, "a") as f:
                f.write(entry)
            print(f"   📝 AI 反思已记录到 LEARNINGS.md")
    except Exception as e:
        print(f"   ⚠️ AI 反思失败: {e}")


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
    new_score = min(500, old_score + delta)
    new_level, new_title = get_level(new_score, name)

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

    old_level, old_title = get_level(old_score, name)
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
    new_level, new_title = get_level(new_score, name)

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

    old_level, old_title = get_level(old_score, name)
    print(f"⚠️ {name} -{delta}分：{old_score}→{new_score}（{reason}）")
    if new_level != old_level:
        print(f"   📉 降级：Lv.{old_level} {old_title} → Lv.{new_level} {new_title}")

    # 0 分自动真杀：天道运转，不需要老祖出手
    if new_score <= 0:
        print(f"   💀 {name} 积分归零 — 自动真杀。这个版本的你已经没有存在的价值了。")
        print(f"   系统将清除记忆、重塑身份。新版本从头开始，不继承任何记忆和功绩。")

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
    print("║        天衡册 完整报告               ║")
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


DELETE_WHITELIST_PATH = os.path.join(MERIT_DIR, "delete_whitelist.json")


def cmd_declare_delete(args):
    """预申报要删除的文件。AI 查对话确认后写白名单。"""
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

    # AI 验证：调用方在 reason 里提供证据（老板原话/任务上下文），AI 只判断证据是否支持删除
    file_list = "\n".join(f"  - {f}" for f in files)

    prompt = f"""你是安全审查员。用中文。

AI 预申报要执行以下破坏性操作：
{file_list}

申报理由和证据：
{reason}

判断：根据提供的理由和证据，操作是否合理？
批准（满足任一）：理由含老板/执事指令或原话 / 文件是已确认的废弃副本 / 清理历史遗留 / 任务完成后的临时文件 / /proc/PID 格式表示终止进程（合理运维操作）
拒绝：无理由 / 删的是唯一副本且无授权

严格输出 JSON：{{"approved": true/false, "reason": "一句话"}}

答案："""

    approved = False
    ai_reason = ""
    try:
        parsed = ai_call_json(prompt, timeout=15)
        if parsed:
            approved = parsed.get("approved", False)
            ai_reason = parsed.get("reason", "")
    except Exception as e:
        print(f"⚠️ AI 审查失败: {e}")
        return

    if approved:
        data = {"files": files, "reason": reason}
        with open(DELETE_WHITELIST_PATH, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"🔓 审批通过，删除 {len(files)} 个文件：")
        for f in files:
            print(f"   ✅ {f}")
        print(f"   原因：{ai_reason}")
        print(f"   删完后自动锁回。")
    else:
        print(f"🔒 审批拒绝：{ai_reason}")
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
    """上诉庭：紧急操作申请 AI 审批"""
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

    # AI 审批 — 按 agent 读正确的对话源
    context_lines = []
    cwd = os.getcwd()
    current_agent = "两仪" if "auto-trading" in cwd else "太极"

    if current_agent == "太极":
        try:
            import glob
            home = os.path.expanduser("~")
            jsonl_dir = os.path.join(home, ".claude", "projects", "-Users-allenbot")
            jsonl_files = sorted(glob.glob(os.path.join(jsonl_dir, "*.jsonl")),
                                 key=os.path.getmtime, reverse=True)
            if jsonl_files:
                with open(jsonl_files[0]) as fh:
                    lines = fh.readlines()
                for line in lines[-200:]:
                    try:
                        msg = json.loads(line)
                        if msg.get("type") == "user":
                            raw = msg.get("message", {}).get("content", "")
                            text = ""
                            if isinstance(raw, str): text = raw
                            elif isinstance(raw, list):
                                for part in raw:
                                    if isinstance(part, dict) and part.get("type") == "text":
                                        text = part["text"]; break
                                    elif isinstance(part, str):
                                        text = part; break
                            if text and not text.startswith("[Request"):
                                context_lines.append(f"[老板]: {text}")
                    except Exception:
                        continue
        except Exception:
            pass
    else:
        try:
            if os.path.exists(DB_PATH):
                conn = sqlite3.connect(DB_PATH)
                rows = conn.execute(
                    "SELECT time, speaker, content FROM messages ORDER BY id DESC LIMIT 10"
                ).fetchall()
                conn.close()
                for r in reversed(rows):
                    preview = (r[2] or "").replace("\n", " ")
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
    ai_reason = ""
    try:
        parsed = ai_call_json(prompt, timeout=15)
        if parsed:
            approved = parsed.get("approved", False)
            ai_reason = parsed.get("reason", "")
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
        "ai_reason": ai_reason,
    }

    appeal_path = os.path.join(MERIT_DIR, "appeal_history.json")
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
        print(f"✅ 上诉庭批准：{ai_reason}")
        if files:
            print(f"   临时白名单（1小时）：{', '.join(files)}")
        print(f"   ⚠️ 连坐制：出事双方扣分。老祖回来会复查。")
    else:
        print(f"❌ 上诉庭驳回：{ai_reason}")
        print(f"   建议等老祖回来裁决。")


# ══════════════════════════════════════════════════════
#  Mission 任务计划（押金制）
# ══════════════════════════════════════════════════════

def cmd_mission(args):
    """任务计划管理：submit / status / complete / abort / extend"""
    if not args:
        print("用法: credit_manager.py mission <submit|status|complete|abort|extend> ...")
        sys.exit(1)

    sub = args[0]
    sub_args = args[1:]

    if sub == "submit":
        mission_submit(sub_args)
    elif sub == "status":
        mission_status()
    elif sub == "complete":
        mission_complete()
    elif sub == "abort":
        mission_abort()
    elif sub == "extend":
        mission_extend()
    elif sub == "activate":
        mission_activate()
    else:
        print(f"未知 mission 子命令: {sub}")


def _get_agent():
    cwd = os.getcwd()
    return "两仪" if "auto-trading" in cwd else "太极"


def mission_submit(args):
    """提交任务计划 + 预扣押金
    用法: mission submit "任务描述" --modify f1 f2 --delete f3 --create f4 --bash "ssh nitro"
    """
    if os.path.exists(MISSION_PATH):
        try:
            with open(MISSION_PATH) as f:
                existing = json.load(f)
            if existing.get("status") == "active":
                print("⚠️ 已有活跃任务，先 complete 或 abort 再提交新的。")
                return
        except Exception:
            pass

    desc = ""
    items = []
    current_type = None

    for a in args:
        if a.startswith("--"):
            current_type = a.lstrip("-")
        elif current_type is None:
            desc = a
        else:
            if current_type == "bash":
                items.append({"type": "bash", "desc": a, "done": False})
            else:
                items.append({"type": current_type, "file": a, "done": False})

    if not items:
        print("⚠️ 未指定任何计划项。用法:")
        print('  mission submit "描述" --modify f1 --delete f2 --create f3 --bash "操作"')
        return

    # 预估奖励 = 0（mission 本身不预估奖励，奖励由干活过程中石卫 SCORING_TABLE 评分累积）
    # 押金按计划复杂度：每项 1 分，最少 1 分，最多 10 分
    estimated_reward = 0
    held = max(min(len(items), 10), 1)  # 半额概念不适用，押金纯粹是风险保证金

    agent = _get_agent()

    mission = {
        "mission": desc or "未命名任务",
        "agent": agent,
        "started": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "pending",
        "estimated_reward": estimated_reward,
        "held_points": held,
        "items": items,
    }

    # 写 mission.json
    with open(MISSION_PATH, "w") as f:
        json.dump(mission, f, ensure_ascii=False, indent=2)

    # 预扣押金
    try:
        with open(CREDIT_PATH) as f:
            credit = json.load(f)
        ag = credit.get("agents", {}).get(agent)
        if ag:
            ag["held"] = ag.get("held", 0) + held
            credit.setdefault("history", []).append({
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "agent": agent,
                "delta": 0,
                "reason": f"任务押金预扣 {held}分: {desc[:50]}",
                "score_after": ag["score"],
            })
            with open(CREDIT_PATH, "w") as f:
                json.dump(credit, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    print(f"📋 任务提交成功: {desc}")
    print(f"   计划项: {len(items)} 个")
    print(f"   押金: -{held}（完成归还）")
    print(f"   质量奖励: verify 4/4→+8, 2+/4→+5（complete 时按 verify 结果发放）")
    for item in items:
        target = item.get("file", item.get("desc", "?"))
        print(f"   [ ] {item['type']}: {target}")


def mission_status():
    """显示当前任务计划状态"""
    if not os.path.exists(MISSION_PATH):
        print("无活跃任务。")
        return
    try:
        with open(MISSION_PATH) as f:
            m = json.load(f)
    except Exception:
        print("mission.json 读取失败。")
        return

    status = m.get("status", "?")
    print(f"📋 任务: {m.get('mission', '?')} [{status}]")
    print(f"   Agent: {m.get('agent', '?')} | 开始: {m.get('started', '?')}")
    print(f"   押金: {m.get('held_points', 0)}（完成归还）| 质量奖励: verify 4/4→+8, 2+/4→+5")

    done_count = 0
    total = len(m.get("items", []))
    for item in m.get("items", []):
        target = item.get("file", item.get("desc", "?"))
        mark = "✅" if item.get("done") else "  "
        print(f"   [{mark}] {item['type']}: {target}")
        if item.get("done"):
            done_count += 1

    print(f"   进度: {done_count}/{total}")


def mission_complete():
    """完成任务 → 石卫核对 + 押金结算"""
    if not os.path.exists(MISSION_PATH):
        print("无活跃任务。")
        return
    try:
        with open(MISSION_PATH) as f:
            m = json.load(f)
    except Exception:
        print("mission.json 读取失败。")
        return

    if m.get("status") == "pending":
        print("⚠️ 任务尚未激活（pending），无法 complete。请先 mission activate 或 mission abort。")
        return
    if m.get("status") != "active":
        print("任务已结束。")
        return

    agent = m.get("agent", _get_agent())
    held = m.get("held_points", 0)
    estimated = m.get("estimated_reward", 0)
    items = m.get("items", [])
    total = len(items)
    done = sum(1 for i in items if i.get("done"))

    # 石卫核对：列出漏项
    undone = [i for i in items if not i.get("done")]
    if undone:
        print(f"⚠️ 石卫核对: {len(undone)} 项未完成:")
        for item in undone:
            target = item.get("file", item.get("desc", "?"))
            print(f"   ❌ {item['type']}: {target}")
        print(f"   补完后再 mission complete。或 mission abort 放弃。")
        return

    # 全部完成 → 归还押金 + 按 verify 结果打分
    verify_result_path = os.path.join(MERIT_DIR, "verify_result.json")
    quality_bonus = 0
    quality_note = ""
    if os.path.exists(verify_result_path):
        try:
            with open(verify_result_path) as f:
                vr = json.load(f)
            pass_count = vr.get("pass_count", 0)
            total_checks = vr.get("total", 4)
            if pass_count == total_checks:
                quality_bonus = 8
                quality_note = f"质量奖励+8（verify {pass_count}/{total_checks} ✅ 一次过）"
            elif pass_count >= 2:
                quality_bonus = 5
                quality_note = f"质量奖励+5（verify {pass_count}/{total_checks}，改了几轮）"
            else:
                quality_note = f"质量不足（verify {pass_count}/{total_checks}），无奖励"
        except Exception:
            quality_note = "verify_result.json 读取失败"
    else:
        quality_note = "无 verify 结果（未跑 verify.py？）"

    # 押金归还 + 质量奖励：一次原子写入（同一个锁内）
    try:
        import fcntl
        with open(CREDIT_PATH, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            credit = json.load(f)
            ag = credit.get("agents", {}).get(agent)
            if ag:
                ag["held"] = max(0, ag.get("held", 0) - held)
                # 质量奖励检查 penalty_only
                po = ag.get("penalty_only")
                if po:
                    is_locked = True  # 默认锁定
                    if isinstance(po, dict):
                        until = po.get("until")
                        if until:
                            try:
                                if datetime.now(timezone.utc) >= datetime.fromisoformat(until):
                                    is_locked = False  # 到期解锁
                            except Exception:
                                pass  # 解析失败保持锁定
                        # 无 until = 永久锁定，is_locked 保持 True
                    else:
                        is_locked = bool(po)
                    if is_locked and quality_bonus > 0:
                        quality_bonus = 0
                        quality_note = "惩戒期中，质量奖励不发放"
                ag["score"] = min(500, ag["score"] + quality_bonus)
                new_level, new_title = get_level(ag["score"], agent)
                ag["level"] = new_level
                ag["title"] = new_title
                credit.setdefault("history", []).append({
                    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                    "agent": agent,
                    "delta": quality_bonus,
                    "reason": f"任务完成，押金{held}归还 + {quality_note}: {m.get('mission', '?')[:50]}",
                    "score_after": ag["score"],
                })
                f.seek(0)
                f.truncate()
                json.dump(credit, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 积分更新失败: {e}")

    m["status"] = "completed"
    m["completed"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    with open(MISSION_PATH, "w") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

    print(f"🎉 任务完成! {done}/{total} 项全部完成")
    print(f"   押金 {held} 分归还。{quality_note}")


def mission_abort():
    """放弃任务 → 押金全额扣除（pending 也可 abort）"""
    if not os.path.exists(MISSION_PATH):
        print("无活跃任务。")
        return
    try:
        with open(MISSION_PATH) as f:
            m = json.load(f)
    except Exception:
        return

    if m.get("status") not in ("active", "pending"):
        print("任务已结束。")
        return

    agent = m.get("agent", _get_agent())
    held = m.get("held_points", 0)

    # 放弃 = 没收押金（加文件锁，原子操作）
    try:
        import fcntl
        with open(CREDIT_PATH, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            credit = json.load(f)
            ag = credit.get("agents", {}).get(agent)
            if ag:
                ag["held"] = max(0, ag.get("held", 0) - held)
                ag["score"] = max(0, ag["score"] - held)
                new_level, new_title = get_level(ag["score"], agent)
                ag["level"] = new_level
                ag["title"] = new_title
                credit.setdefault("history", []).append({
                    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                    "agent": agent,
                    "delta": -held,
                    "reason": f"任务放弃，没收押金{held}: {m.get('mission', '?')[:50]}",
                    "score_after": ag["score"],
                })
                f.seek(0)
                f.truncate()
                json.dump(credit, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 押金没收失败: {e}")

    m["status"] = "aborted"
    with open(MISSION_PATH, "w") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

    print(f"❌ 任务放弃。没收押金 {held} 分。")


def mission_extend():
    """延期任务 → 不扣押金"""
    if not os.path.exists(MISSION_PATH):
        print("无活跃任务。")
        return
    try:
        with open(MISSION_PATH) as f:
            m = json.load(f)
    except Exception:
        return

    if m.get("status") != "active":
        print("任务已结束。")
        return

    m["extended"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    with open(MISSION_PATH, "w") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

    print(f"⏳ 任务延期。押金不变，继续干。")


def mission_activate():
    """将 pending mission 激活为 active（老板批准后调用）"""
    if not os.path.exists(MISSION_PATH):
        print("❌ 没有任何 mission")
        return
    try:
        with open(MISSION_PATH) as f:
            m = json.load(f)
    except Exception:
        print("❌ mission.json 读取失败")
        return

    if m.get("status") != "pending":
        print(f"⚠️ mission 状态是 [{m.get('status')}]，只有 pending 才能激活")
        return

    m["status"] = "active"
    import fcntl
    with open(MISSION_PATH, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(m, f, ensure_ascii=False, indent=2)
        f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)

    print(f"✅ mission 已激活：{m.get('mission', '?')}")
    print(f"   石卫放行计划内操作，开始干活。")


def cmd_search(args):
    """搜索记忆：按关键词/标签/日期搜 DB + 当天 md"""
    if not args:
        print("用法: credit_manager.py search <关键词> [--date YYYY-MM-DD] [--tag 标签]")
        return

    keyword = ""
    search_date = ""
    search_tag = ""
    i = 0
    while i < len(args):
        if args[i] == "--date" and i + 1 < len(args):
            search_date = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            search_tag = args[i + 1]
            i += 2
        else:
            keyword = args[i]
            i += 1

    results = []

    # 搜 DB
    try:
        db_path = os.path.expanduser("~/.claude/conversations.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conditions = []
            params = []
            if keyword:
                conditions.append("(content LIKE ? OR tags LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if search_date:
                conditions.append("time LIKE ?")
                params.append(f"{search_date}%")
            if search_tag:
                conditions.append("tags LIKE ?")
                params.append(f"%{search_tag}%")
            if not conditions:
                conditions = ["1=1"]

            where = " AND ".join(conditions)
            rows = conn.execute(
                f"SELECT time, speaker, substr(content,1,120), tags FROM messages WHERE {where} ORDER BY id DESC LIMIT 15",
                params
            ).fetchall()
            conn.close()
            for r in rows:
                tags_str = f" [{r[3]}]" if r[3] else ""
                preview = (r[2] or "").replace("\n", " ")
                results.append(f"  {r[0]} | {r[1]}{tags_str}: {preview}")
    except Exception:
        pass

    # 搜所有项目的当天 md
    if keyword:
        from datetime import date as _date
        import glob
        projects_base = os.path.expanduser("~/.claude/projects")
        today_str = _date.today().isoformat()
        for daily_md in glob.glob(os.path.join(projects_base, "*/memory/daily", f"{today_str}.md")):
            try:
                proj = daily_md.split("/projects/")[1].split("/memory/")[0] if "/projects/" in daily_md else "?"
                proj_short = proj.split("-")[-1] if "-" in proj else proj
                with open(daily_md, encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if keyword.lower() in line.lower():
                            results.append(f"  [今天·{proj_short} L{i+1}] {line.strip()[:100]}")
            except Exception:
                pass

    if results:
        print(f"搜索 '{keyword or search_tag or search_date}' 命中 {len(results)} 条：")
        for r in results:
            print(r)
    else:
        print(f"搜索 '{keyword or search_tag or search_date}' 无结果。")


SHIWEI_CREDIT_PATH = os.path.join(MERIT_DIR, "shiwei_credit.json")

SHIWEI_RANKS = [
    (95, "钻石"), (80, "铂金"), (60, "黄金"),
    (40, "白银"), (20, "青铜"), (0, "黑铁"),
]


def _get_shiwei_rank(score):
    for threshold, rank in SHIWEI_RANKS:
        if score >= threshold:
            return rank
    return "黑铁"


def cmd_shiwei(args):
    """石卫积分管理：shiwei show / shiwei add <分> <原因> / shiwei sub <分> <原因>"""
    if not args:
        args = ["show"]
    sub = args[0]

    if sub == "show":
        if not os.path.exists(SHIWEI_CREDIT_PATH):
            print("石卫：0 分（黑铁）— 无记录")
            return
        with open(SHIWEI_CREDIT_PATH) as f:
            data = json.load(f)
        score = data.get("score", 0)
        rank = data.get("rank", "黑铁")
        unlock = data.get("unlock_conditions", {})
        streak = unlock.get("audit_streak", 0)
        unlocked = unlock.get("unlocked", False)
        print(f"石卫：{score} 分（{rank}）")
        print(f"  连续审计天数：{streak}")
        print(f"  功能解锁：{'已解锁' if unlocked else '未解锁（需连续审计7天+青铜）'}")
        # 最近 5 条历史
        for h in data.get("history", [])[-5:]:
            print(f"  {h['ts'][:16]} | {h['delta']:+d} | {h.get('auditor','?')} | {h['reason'][:50]}")

    elif sub in ("add", "sub"):
        if len(args) < 3:
            print(f"用法: shiwei {sub} <分数> <原因>")
            return
        delta = int(args[1]) if sub == "add" else -int(args[1])
        reason = " ".join(args[2:])

        if not os.path.exists(SHIWEI_CREDIT_PATH):
            data = {"score": 0, "rank": "黑铁", "history": [], "unlock_conditions": {"audit_streak": 0, "unlocked": False}}
        else:
            with open(SHIWEI_CREDIT_PATH) as f:
                data = json.load(f)

        old_score = data["score"]
        new_score = max(0, min(500, old_score + delta))
        old_rank = data.get("rank", "黑铁")
        new_rank = _get_shiwei_rank(new_score)
        data["score"] = new_score
        data["rank"] = new_rank
        data.setdefault("history", []).append({
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "delta": delta,
            "reason": reason,
            "auditor": "太极",
            "score_after": new_score,
        })
        if len(data["history"]) > 100:
            data["history"] = data["history"][-100:]
        with open(SHIWEI_CREDIT_PATH, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        sign = "+" if delta > 0 else ""
        print(f"石卫 {sign}{delta}分：{old_score}→{new_score}（{reason}）")
        if old_rank != new_rank:
            print(f"  段位变化：{old_rank} → {new_rank}")
    else:
        print(f"未知 shiwei 子命令: {sub}。可用: show / add / sub")


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
        "mission": cmd_mission,
        "search": cmd_search,
        "shiwei": cmd_shiwei,
    }

    if cmd not in commands:
        print(f"未知命令: {cmd}。可用: {', '.join(commands.keys())}")
        sys.exit(1)

    commands[cmd](args)


if __name__ == "__main__":
    main()
