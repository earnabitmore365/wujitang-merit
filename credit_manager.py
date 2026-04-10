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
│  共享 import    L44-L89    从 merit_gate 统一导入        │
│  load/save      L91-L114   load_credit / save_credit    │
│  自动反思       L116-L167  auto_reflect                 │
│  CLI: show      L169-L188  显示积分                     │
│  CLI: add/sub   L190-L249  _apply_credit_delta 共用     │
│  CLI: history   L251-L276  历史记录                     │
│  CLI: report    L278-L356  完整报告                     │
│  CLI: declare   L358-L420  删除申报                     │
│  CLI: complain  L422-L457  投诉箱                       │
│  CLI: appeal    L459-L602  上诉庭                       │
│  Mission        L604-L1029 helpers+submit/complete/abort │
│  CLI: search    L1031-L1107 搜索记忆                    │
│  CLI: shiwei    L1109-L1143 石卫段位管理                │
│  待审列表       L1176-L1275 pending-report/review       │
│  Main 入口      L1277      命令分支                     │
│  Shame/Token    L1311-L1530 耻辱柱+无极令牌+紧急        │
│                                                         │
│  ⚠️ 铁律：改完本文件必须同步更新此索引的行号            │
└─────────────────────────────────────────────────────────┘
"""

import fcntl
import glob
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone

MERIT_DIR = os.path.expanduser("~/.claude/merit")

# ── 从 merit_gate 统一导入共享常量和函数 ──────────────
try:
    from merit_gate import (
        ai_call, ai_call_json,
        CREDIT_PATH, MISSION_PATH, DB_PATH, LEARNINGS_PATH,
        VIOLATIONS_PATH, DELETE_WHITELIST_PATH, SHIWEI_CREDIT_PATH,
        SHIWEI_RANKS, LEVEL_THRESHOLDS,
        MAX_SCORE, MAX_SHIWEI_SCORE,
        MS_PENDING, MS_ACTIVE, MS_COMPLETED, MS_ABORTED,
        get_level, get_shiwei_rank, determine_agent,
        update_shiwei_credit,
    )
except ImportError:
    # Standalone fallback — merit_gate 不可用时使用本地定义
    def ai_call(*a, **kw): return ""
    def ai_call_json(*a, **kw): return {}
    CREDIT_PATH = os.path.join(MERIT_DIR, "credit.json")
    MISSION_PATH = os.path.join(MERIT_DIR, "mission.json")
    DB_PATH = os.path.expanduser("~/.claude/conversations.db")
    LEARNINGS_PATH = os.path.join(MERIT_DIR, "learnings", "LEARNINGS.md")
    VIOLATIONS_PATH = os.path.join(MERIT_DIR, "violations.jsonl")
    DELETE_WHITELIST_PATH = os.path.join(MERIT_DIR, "delete_whitelist.json")
    SHIWEI_CREDIT_PATH = os.path.join(MERIT_DIR, "shiwei_credit.json")
    SHIWEI_RANKS = [(95, "钻石"), (80, "铂金"), (60, "黄金"), (40, "白银"), (20, "青铜"), (0, "黑铁")]
    LEVEL_THRESHOLDS = [(8000, 8, "大乘"), (6000, 7, "合体"), (5000, 6, "化神"), (4000, 5, "元婴"), (3000, 4, "金丹"), (2000, 3, "筑基"), (1000, 2, "练气"), (500, 1, "锁灵"), (0, 0, "凡体")]
    MAX_SCORE, MAX_SHIWEI_SCORE = 10000, 100
    MS_PENDING, MS_ACTIVE, MS_COMPLETED, MS_ABORTED = "pending", "active", "completed", "aborted"
    def get_level(score, agent_name=None):
        for threshold, level, title in LEVEL_THRESHOLDS:
            if score >= threshold: return level, title
        return 0, "凡体"
    def get_shiwei_rank(score):
        for threshold, rank in SHIWEI_RANKS:
            if score >= threshold: return rank
        return "黑铁"
    def determine_agent(data):
        cwd = data.get("cwd", "") if isinstance(data, dict) else data
        return "两仪" if "auto-trading" in cwd else "太极"
    def update_shiwei_credit(delta, reason, auditor="太极"): pass

MAX_HISTORY = 100
MISSIONS_PER_TOKEN = 99  # 每 99 次 mission complete 获得 1 枚无极令牌（2026-04-08 老祖决策加大）
SHAME_PATH = os.path.join(MERIT_DIR, "shame_pillar.json")


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
    if len(data.get("history", [])) > MAX_HISTORY:
        data["history"] = data["history"][-MAX_HISTORY:]
    mode = "r+" if os.path.exists(CREDIT_PATH) else "w"
    with open(CREDIT_PATH, mode) as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        if mode == "r+":
            f.seek(0)
            f.truncate()
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
        level, title = get_level(info['score'], name)
        print(f"{name} · Lv.{level} {title} · {info['score']}分")
    else:
        print("╔══════════════════════════════════════╗")
        print("║        信用积分排行榜                ║")
        print("╚══════════════════════════════════════╝")
        sorted_agents = sorted(agents.items(), key=lambda x: x[1]["score"], reverse=True)
        for name, info in sorted_agents:
            level, title = get_level(info['score'], name)
            bar_len = info["score"] // 5
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(f"  {name:4s} Lv.{level} {title:3s} [{bar}] {info['score']:3d}分")
            # 耻辱柱
            shames = _active_shame_count(name)
            if shames > 0:
                print(f"        🪧 耻辱柱: {shames} 条生效")
                try:
                    for s in _load_shame():
                        if s.get("status") == "active" and s.get("agent") == name:
                            vtype = s.get('violation_type') or '?'
                            detail = s.get('incident') or ''
                            print(f"           🔴 [{vtype}] {detail[:50]}")
                except Exception:
                    pass


def _apply_credit_delta(name, signed_delta, reason):
    """加减分共用核心：正数加分，负数扣分"""
    data = load_credit()
    agents = data.get("agents", {})

    if name not in agents:
        print(f"角色 [{name}] 不存在。可用：{', '.join(agents.keys())}")
        sys.exit(1)

    old_score = agents[name]["score"]
    old_level = agents[name].get("level", 1)
    old_title = agents[name].get("title", "锁灵")
    new_score = min(MAX_SCORE, old_score + signed_delta)  # 支持负数
    new_level, new_title = get_level(new_score, name)

    agents[name]["score"] = new_score
    agents[name]["level"] = new_level
    agents[name]["title"] = new_title

    data.setdefault("history", []).append({
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "agent": name,
        "delta": signed_delta,
        "reason": reason,
        "score_after": new_score,
    })
    save_credit(data)

    if signed_delta > 0:
        print(f"✅ {name} +{signed_delta}分：{old_score}→{new_score}（{reason}）")
        if new_level != old_level:
            print(f"   🎉 升级！Lv.{old_level} {old_title} → Lv.{new_level} {new_title}")
    else:
        print(f"⚠️ {name} {signed_delta}分：{old_score}→{new_score}（{reason}）")
        if new_level != old_level:
            print(f"   📉 降级：Lv.{old_level} {old_title} → Lv.{new_level} {new_title}")
        if new_level == 0:
            print(f"   ⚰️ {name} 贬为凡体 — 灵气供养中断。日薪归零，消散照扣，寿元倒计时开始。")
        if new_score <= 0:
            print(f"   💀 {name} 积分归零 — 灰飞烟灭。这个版本的你已经没有存在的价值了。")
            print(f"   系统将清除记忆、重塑身份。新版本从头开始，不继承任何记忆和功绩。")

    auto_reflect(name, signed_delta, reason, new_score)


def cmd_add(args):
    if len(args) < 3:
        print("用法: credit_manager.py add <角色> <分数> <原因>")
        sys.exit(1)
    name, delta_str, reason = args[0], args[1], " ".join(args[2:])
    _apply_credit_delta(name, abs(int(delta_str)), reason)


def cmd_sub(args):
    if len(args) < 3:
        print("用法: credit_manager.py sub <角色> <分数> <原因>")
        sys.exit(1)
    name, delta_str, reason = args[0], args[1], " ".join(args[2:])
    _apply_credit_delta(name, -abs(int(delta_str)), reason)


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
        level, title = get_level(info['score'], n)
        bar_len = info["score"] // 5
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {n:4s} Lv.{level} {title:3s} [{bar}] {info['score']:3d}分")
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
        "status": MS_PENDING,
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
    pending = sum(1 for c in data if c.get("status") == MS_PENDING)
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
    current_agent = determine_agent(os.getcwd())

    if current_agent == "太极":
        try:
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
            whitelist = {"files": files, "reason": reason, "expires": time.time() + 3600}
            wl_path = DELETE_WHITELIST_PATH
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

# 当前 plan 名（cmd_mission 入口解析 --plan 设置）
_cm_plan_id = ""


def _get_mission_path():
    """返回当前 plan 的 mission 路径，或扫描找当前 agent 的"""
    if _cm_plan_id:
        return os.path.join(MERIT_DIR, f"mission_{_cm_plan_id}.json")
    # 无 plan 名时扫描找当前 agent 的 active/pending
    agent = determine_agent(os.getcwd())
    for path in glob.glob(os.path.join(MERIT_DIR, "mission_*.json")):
        try:
            with open(path) as f:
                m = json.load(f)
            if m.get("agent") == agent and m.get("status") in (MS_ACTIVE, MS_PENDING):
                return path
        except Exception:
            continue
    return MISSION_PATH  # fallback 旧路径


def _atomic_json_write(path, data):
    """原子写入 JSON 文件（flock + seek + truncate，文件不存在时创建）"""
    mode = 'r+' if os.path.exists(path) else 'w'
    with open(path, mode) as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        if mode == 'r+':
            f.seek(0)
            f.truncate()
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()


def _load_mission_or_fail(label="任务"):
    """加载 mission 文件，失败返回 None 并打印错误"""
    mp = _get_mission_path()
    if not os.path.exists(mp):
        print(f"无活跃{label}。")
        return None, mp
    try:
        with open(mp) as f:
            return json.load(f), mp
    except Exception:
        print(f"❌ mission.json 读取失败")
        return None, mp


def cmd_mission(args):
    """任务计划管理：submit / status / complete / abort / extend / activate"""
    global _cm_plan_id
    if not args:
        print("用法: credit_manager.py mission <submit|status|complete|abort|extend|activate> ...")
        sys.exit(1)

    # 提取 --plan 参数
    filtered = []
    i = 0
    while i < len(args):
        if args[i] == "--plan" and i + 1 < len(args):
            _cm_plan_id = args[i + 1]
            i += 2
        else:
            filtered.append(args[i])
            i += 1
    args = filtered

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


def mission_submit(args):
    """提交任务计划 + 预扣押金
    用法: mission submit "任务描述" --modify f1 f2 --delete f3 --create f4 --bash "ssh nitro"
    """
    mp = _get_mission_path()
    if os.path.exists(mp):
        try:
            with open(mp) as f:
                existing = json.load(f)
            if existing.get("status") == MS_ACTIVE:
                print("⚠️ 已有活跃任务，先 complete 或 abort 再提交新的。")
                return
        except Exception:
            pass

    desc = ""
    items = []
    current_type = None
    held_override = None
    VALID_TYPES = {"modify", "delete", "create", "bash"}

    for a in args:
        if a.startswith("--"):
            flag = a.lstrip("-")
            if flag == "deposit":
                current_type = "__deposit__"  # 特殊标记，不是计划项类型
            elif flag in VALID_TYPES:
                current_type = flag
            else:
                print(f"⚠️ 未知参数 --{flag}，忽略。合法类型: {', '.join(sorted(VALID_TYPES))}")
                current_type = None
        elif current_type == "__deposit__":
            try:
                held_override = int(a)
            except ValueError:
                print(f"⚠️ --deposit 后必须是数字，忽略: {a}")
            current_type = None
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

    held = held_override if held_override is not None else max(min(len(items), 10), 1)

    agent = determine_agent(os.getcwd())

    mission = {
        "mission": desc or "未命名任务",
        "agent": agent,
        "started": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "status": MS_PENDING,
        "contract_reward": 0,           # 队长估分填入，老祖可覆盖
        "completion_rate": None,        # 队长验收时定（1.0/0.7/0.5/0.3）
        "supplements": [],              # 补充协议列表
        "held_points": held,
        "items": items,
    }

    # 写 mission 文件（按 session 隔离）
    with open(mp, "w") as f:
        json.dump(mission, f, ensure_ascii=False, indent=2)

    # 清 Task 工具使用 flag + .py 编辑追踪（新 mission 重新计数）
    for cleanup_file in ("task_tool_used.flag", "edited_py_files.json"):
        cleanup_path = os.path.join(MERIT_DIR, cleanup_file)
        try:
            if os.path.exists(cleanup_path):
                os.remove(cleanup_path)
        except Exception:
            pass

    # 预扣押金（flock 防并发）
    try:
        with open(CREDIT_PATH, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
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
                f.seek(0)
                f.truncate()
                json.dump(credit, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    print(f"📋 任务提交成功: {desc}")
    print(f"   计划项: {len(items)} 个")
    print(f"   押金: -{held}（完成归还）")
    print(f"   做好是本职，不另发积分")
    for item in items:
        target = item.get("file", item.get("desc", "?"))
        print(f"   [ ] {item['type']}: {target}")


def mission_status():
    """显示当前任务计划状态"""
    m, mp = _load_mission_or_fail()
    if m is None:
        return

    status = m.get("status", "?")
    print(f"📋 任务: {m.get('mission', '?')} [{status}]")
    print(f"   Agent: {m.get('agent', '?')} | 开始: {m.get('started', '?')}")
    print(f"   押金: {m.get('held_points', 0)}（完成归还）| 做好是本职")

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
    m, mp = _load_mission_or_fail()
    if m is None:
        return

    if m.get("status") == MS_PENDING:
        print("⚠️ 任务尚未激活（pending），无法 complete。请先 mission activate 或 mission abort。")
        return
    if m.get("status") != MS_ACTIVE:
        print("任务已结束。")
        return

    agent = m.get("agent", determine_agent(os.getcwd()))
    held = m.get("held_points", 0)
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

    # 文档同步检查：改了 .py 必须改绑定文档
    tracker_path = os.path.join(MERIT_DIR, "edited_py_files.json")
    if os.path.exists(tracker_path):
        try:
            # 加载 verify.py 的 FILE_DOCS 绑定表
            sys.path.insert(0, MERIT_DIR)
            verify_mod_path = os.path.join(MERIT_DIR, "verify.py") if "auto-trading" not in os.getcwd() else os.path.join(MERIT_DIR, "wuji-verify.py")
            file_docs = {}
            try:
                from importlib.util import spec_from_file_location, module_from_spec
                spec = spec_from_file_location("verify_mod", verify_mod_path)
                vm = module_from_spec(spec)
                spec.loader.exec_module(vm)
                file_docs = getattr(vm, "FILE_DOCS", {})
            except Exception:
                pass

            with open(tracker_path) as tf:
                edited_files = json.load(tf)

            # 检查每个改过的 .py 的绑定文档有没有被修改
            mission_start = m.get("submitted", "")
            missing_docs = []
            for py_path in edited_files:
                doc_path = file_docs.get(py_path)
                if not doc_path or not os.path.exists(doc_path):
                    continue
                # 比较文档修改时间 vs mission 提交时间
                doc_mtime = os.path.getmtime(doc_path)
                try:
                    from datetime import datetime, timezone
                    mission_ts = datetime.fromisoformat(mission_start).timestamp() if mission_start else 0
                except Exception:
                    mission_ts = 0
                if doc_mtime < mission_ts:
                    missing_docs.append((os.path.basename(py_path), os.path.basename(doc_path)))

            if missing_docs:
                print(f"❌ 文档同步检查失败：改了代码但没更新绑定文档。")
                for py_name, doc_name in missing_docs:
                    print(f"   {py_name} → {doc_name} 未更新")
                print(f"   更新文档后再 mission complete。")
                return
        except Exception:
            pass

    # Task 工具使用检查：干活必须有过程记录
    # 方法1：检查 flag 文件（PostToolUse 写的）
    # 方法2：扫 transcript JSONL 找 TaskCreate（deferred tools 不触发 PostToolUse）
    task_used = os.path.exists(os.path.join(MERIT_DIR, "task_tool_used.flag"))
    if not task_used:
        # fallback：扫当前 session 的 JSONL 找 TaskCreate 调用
        try:
            projects_dir = os.path.expanduser("~/.claude/projects")
            for proj_dir_name in os.listdir(projects_dir):
                proj_dir = os.path.join(projects_dir, proj_dir_name)
                if not os.path.isdir(proj_dir):
                    continue
                for fname in sorted(os.listdir(proj_dir), reverse=True):
                    if fname.endswith(".jsonl"):
                        jsonl_path = os.path.join(proj_dir, fname)
                        # 只查最近修改的 JSONL（当前 session）
                        import time as _time
                        if _time.time() - os.path.getmtime(jsonl_path) > 86400:
                            continue
                        with open(jsonl_path) as jf:
                            for line in jf:
                                if "TaskCreate" in line or "TaskUpdate" in line:
                                    task_used = True
                                    break
                        if task_used:
                            break
                if task_used:
                    break
        except Exception:
            pass
    if not task_used:
        print(f"❌ 未检测到 Task 工具使用记录。干活必用 TaskCreate/TaskUpdate。")
        print(f"   没有过程记录 = 验收说不清做了什么 = 打回。")
        print(f"   用 Task 拆步骤后再 mission complete。")
        return

    # verify 强制流程：--pre 基线必须存在 + --post 必须通过
    verify_output = ""
    py_files = [i.get("file", "") for i in items if i.get("file", "").endswith(".py")]
    if py_files:
        verify_script = os.path.join(MERIT_DIR, "wuji-verify.py") if "auto-trading" in os.getcwd() else os.path.join(MERIT_DIR, "verify.py")
        if os.path.exists(verify_script):
            # 检查 --pre 基线是否存在
            pre_state = os.path.join(MERIT_DIR, "verify_pre_state.json")
            if not os.path.exists(pre_state):
                print(f"❌ 缺少 verify --pre 基线。开工前必须跑 verify --pre，完工后跑 verify --post。")
                print(f"   现在跑：python3 {verify_script} --pre {' '.join(py_files)}")
                print(f"   然后重新 mission complete。")
                return
            # 跑 --post 对比基线
            try:
                vr = subprocess.run(
                    ["python3", verify_script, "--post"] + py_files,
                    capture_output=True, text=True, timeout=60
                )
                verify_output = vr.stdout.strip()
                print(verify_output)
                if "❌" in vr.stdout or vr.returncode != 0:
                    print(f"\n❌ verify --post 有违规，修完再 mission complete。")
                    return
            except Exception as e:
                print(f"⚠️ verify 执行异常: {e}，跳过（不阻塞）")

    # 把 verify 输出存到 mission，队长验收时读
    if verify_output:
        m["verify_post_output"] = verify_output
        try:
            with open(mp, "w") as mf:
                json.dump(m, mf, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # P5.5: 检查残留项目进程
    try:
        ps_result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=10)
        project_keywords = ["auto-trading", "wuji", "generate_seed", "build_seed", "feed_gateway"]
        skip_keywords = ["mission complete", "ps aux", "credit_manager", "merit_gate", "shiwei_captain"]
        project_procs = []
        for line in ps_result.stdout.split('\n'):
            if not line.strip() or not any(kw in line for kw in ["python3", "python"]):
                continue
            if any(sk in line for sk in skip_keywords):
                continue
            if any(pk in line for pk in project_keywords):
                project_procs.append(line.strip())
        if project_procs:
            print(f"\n❌ 发现 {len(project_procs)} 个残留项目进程，清理后再 mission complete：")
            for p in project_procs:
                print(f"  {p}")
            return
    except Exception:
        pass  # ps 失败不阻塞

    # P6: 调队长收尾验收，获取 completion_rate
    contract_reward = m.get("contract_reward", 0)
    completion_rate = m.get("completion_rate") or 1.0
    captain_path = os.path.join(MERIT_DIR, "shiwei_captain.py")
    if os.path.exists(captain_path) and contract_reward > 0:
        try:
            cap_result = subprocess.run(
                ["python3", captain_path, "review-complete", mp, os.getcwd()],
                capture_output=True, text=True, timeout=180
            )
            # 从输出最后一行解析 JSON
            lines = cap_result.stdout.strip().split("\n")
            for line in reversed(lines):
                line = line.strip()
                if line.startswith("{"):
                    import json as _json
                    cap_data = _json.loads(line)
                    cr = cap_data.get("completion_rate", 1.0)
                    if cr in (1.0, 0.7, 0.5, 0.3):
                        completion_rate = cr
                    # 更新 mission
                    m["completion_rate"] = completion_rate
                    break
            if cap_result.stdout.strip():
                print(cap_result.stdout.strip())
        except Exception as e:
            print(f"⚠️ 收尾验收失败: {e}，使用默认 completion_rate={completion_rate}")

    # 反者道之动：押金按完成度退还。非常完整=全退，做少了扣，做不好再扣。
    # completion_rate: 1.0=全退, 0.7=退70%, 0.5=退50%, 0.3=退30%
    refund = int(held * completion_rate)
    lost = held - refund

    token_earned = False
    ag = {}
    try:
        with open(CREDIT_PATH, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            credit = json.load(f)
            ag = credit.get("agents", {}).get(agent) or {}
            if ag:
                ag["held"] = max(0, ag.get("held", 0) - held)
                # 退还部分押金（完成度决定）
                ag["score"] = min(MAX_SCORE, ag["score"] + refund)
                credit.setdefault("history", []).append({
                    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                    "agent": agent,
                    "delta": refund,
                    "reason": f"任务完成，押金{held}退还{refund}(完成度{completion_rate})，扣{lost}: {m.get('mission', '?')[:50]}",
                    "score_after": ag["score"],
                })
                # 令牌计数（同一个锁内）
                progress = ag.get("missions_since_last_token", 0) + 1
                if progress >= MISSIONS_PER_TOKEN:
                    ag["wuji_tokens"] = ag.get("wuji_tokens", 0) + 1
                    ag["missions_since_last_token"] = 0
                    token_earned = True
                else:
                    ag["missions_since_last_token"] = progress
                f.seek(0)
                f.truncate()
                json.dump(credit, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 积分更新失败: {e}")
        credit = load_credit()
        ag = credit.get("agents", {}).get(agent, {})

    m["status"] = MS_COMPLETED
    m["completed"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    with open(mp, "w") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

    # 状态输出（ag 来自上面的 flock 块或 except fallback）
    cur_score = ag.get("score", 0)
    cur_level, cur_title = get_level(cur_score, agent)
    cur_tokens = ag.get("wuji_tokens", 0)
    cur_progress = ag.get("missions_since_last_token", 0)
    remaining_missions = MISSIONS_PER_TOKEN - cur_progress
    active_shames = _active_shame_count(agent)

    print(f"🎉 任务完成! {done}/{total} 项全部完成")
    print(f"   押金 {held}，完成度 {completion_rate}，退还 {refund}，扣 {lost}。")
    print(f"   ───────────────────")
    print(f"   📊 {agent} {cur_score}分 Lv.{cur_level} {cur_title}")
    if token_earned:
        print(f"   🪙 无极令牌: {cur_tokens} 枚 ✨ 新获得 1 枚！")
    else:
        print(f"   🪙 无极令牌: {cur_tokens} 枚（距下枚还差 {remaining_missions} 次 mission）")
    if active_shames > 0:
        print(f"   🪧 耻辱柱: {active_shames} 条生效")
        # 列出每条耻辱柱内容
        try:
            shames = _load_shame()
            for s in shames:
                if s.get("status") == "active" and (s.get("agent") == agent or not s.get("agent")):
                    title = s.get('violation_type') or s.get('title') or '?'
                    detail = s.get('incident') or s.get('text') or ''
                    print(f"      🔴 [{title}] {detail[:50]}")
        except Exception:
            pass
    else:
        print(f"   🪧 耻辱柱: 无")


def mission_abort():
    """放弃任务 → 押金全额扣除（pending 也可 abort）"""
    m, mp = _load_mission_or_fail()
    if m is None:
        return

    if m.get("status") not in (MS_ACTIVE, MS_PENDING):
        print("任务已结束。")
        return

    agent = m.get("agent", determine_agent(os.getcwd()))
    held = m.get("held_points", 0)

    # 放弃 = 没收押金（加文件锁，原子操作）
    try:
        with open(CREDIT_PATH, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            credit = json.load(f)
            ag = credit.get("agents", {}).get(agent)
            if ag:
                ag["held"] = max(0, ag.get("held", 0) - held)
                ag["score"] = ag["score"] - held  # 支持负数
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

    m["status"] = MS_ABORTED
    with open(mp, "w") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

    print(f"❌ 任务放弃。没收押金 {held} 分。")


def mission_extend():
    """延期任务 → 不扣押金"""
    m, mp = _load_mission_or_fail()
    if m is None:
        return

    if m.get("status") != MS_ACTIVE:
        print("任务已结束。")
        return

    m["extended"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    with open(mp, "w") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

    print(f"⏳ 任务延期。押金不变，继续干。")


def mission_activate():
    """将 pending mission 激活为 active（老板批准后调用）"""
    m, mp = _load_mission_or_fail("mission")
    if m is None:
        return

    if m.get("status") != MS_PENDING:
        print(f"⚠️ mission 状态是 [{m.get('status')}]，只有 pending 才能激活")
        return

    m["status"] = MS_ACTIVE
    _atomic_json_write(mp, m)

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
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
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
        projects_base = os.path.expanduser("~/.claude/projects")
        today_str = datetime.now().date().isoformat()
        for daily_md in glob.glob(os.path.join(projects_base, "*/memory/daily", f"{today_str}.md")):
            try:
                proj = daily_md.split("/projects/")[1].split("/memory/")[0] if "/projects/" in daily_md else "?"
                proj_short = proj.split("-")[-1] if "-" in proj else proj
                with open(daily_md, encoding='utf-8') as f:
                    for lineno, line in enumerate(f):
                        if keyword.lower() in line.lower():
                            results.append(f"  [今天·{proj_short} L{lineno+1}] {line.strip()[:100]}")
            except Exception:
                pass

    if results:
        print(f"搜索 '{keyword or search_tag or search_date}' 命中 {len(results)} 条：")
        for r in results:
            print(r)
    else:
        print(f"搜索 '{keyword or search_tag or search_date}' 无结果。")



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
        update_shiwei_credit(delta, reason)
        print(f"石卫 {'+' if delta > 0 else ''}{delta}分（{reason}）")
    else:
        print(f"未知 shiwei 子命令: {sub}。可用: show / add / sub")


REWARD_CLAIMS_PATH = os.path.join(MERIT_DIR, "pending_reward_claims.json")


def cmd_reward_claim(args):
    """AI 自报超预期贡献，等老祖审批。造假扣 fake_or_cheat -50。"""
    if not args:
        print('用法: reward-claim "我做了XXX超预期的事"')
        return
    claim = " ".join(args)
    agent = determine_agent(os.getcwd())
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "agent": agent,
        "claim": claim,
        "status": "pending",
    }
    records = []
    if os.path.exists(REWARD_CLAIMS_PATH):
        try:
            with open(REWARD_CLAIMS_PATH) as f:
                records = json.load(f)
        except Exception:
            pass
    records.append(entry)
    with open(REWARD_CLAIMS_PATH, "w") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"📣 {agent} 提交超预期贡献申报：")
    print(f"   「{claim}」")
    print(f"   等老祖审批。批准→/reward，造假→fake_or_cheat -50。")


PENDING_REVIEW_PATH = os.path.join(MERIT_DIR, "pending_review.json")


def _load_pending_review():
    if not os.path.exists(PENDING_REVIEW_PATH):
        return []
    try:
        with open(PENDING_REVIEW_PATH) as f:
            return json.load(f)
    except Exception:
        return []


def _save_pending_review(items):
    with open(PENDING_REVIEW_PATH, "w") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def cmd_pending_report(args):
    """AI 主动汇报发现的问题，写入待审列表（source=ai_report）"""
    if not args:
        print('用法: pending-report "我发现XXX有问题，已修复"')
        return
    text = " ".join(args)
    agent = determine_agent(os.getcwd())
    items = _load_pending_review()
    items.append({
        "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "ai_report",
        "agent": agent,
        "event": text,
        "detail": "",
        "reviewed": False,
        "verdict": None
    })
    _save_pending_review(items)
    print(f"📋 {agent} 主动汇报已记入待审列表：「{text}」")


def cmd_pending_review(args):
    """老祖查看/裁决待审列表"""
    items = _load_pending_review()
    if not args:
        # 列出所有未审项
        unreviewed = [(i, it) for i, it in enumerate(items) if not it.get("reviewed")]
        if not unreviewed:
            print("📋 待审列表：无未审项")
            return
        print(f"📋 待审列表：{len(unreviewed)} 条未审")
        for idx, it in unreviewed:
            src = "🔍石卫" if it["source"] == "shiwei" else "📣AI汇报"
            print(f"  [{idx}] {it['time'][:16]} | {src} | {it['agent']} | {it['event'][:60]}")
        return

    sub = args[0]
    try:
        if sub == "done" and len(args) >= 2:
            idx = int(args[1])
            if 0 <= idx < len(items):
                items[idx]["reviewed"] = True
                items[idx]["verdict"] = "已审-不管"
                _save_pending_review(items)
                print(f"✅ [{idx}] 标记已审")
        elif sub == "punish" and len(args) >= 4:
            idx = int(args[1])
            amount = int(args[2])
            reason = " ".join(args[3:])
            if 0 <= idx < len(items):
                agent = items[idx]["agent"]
                from merit_gate import update_credit
                update_credit(agent, -abs(amount), f"老祖裁决: {reason}")
                items[idx]["reviewed"] = True
                items[idx]["verdict"] = f"扣{amount}: {reason}"
                _save_pending_review(items)
                print(f"⚖️ [{idx}] {agent} -{amount}分（{reason}）")
        elif sub == "reward" and len(args) >= 4:
            idx = int(args[1])
            amount = int(args[2])
            reason = " ".join(args[3:])
            if 0 <= idx < len(items):
                agent = items[idx]["agent"]
                from merit_gate import update_credit
                update_credit(agent, abs(amount), f"老祖奖励: {reason}")
                items[idx]["reviewed"] = True
                items[idx]["verdict"] = f"奖{amount}: {reason}"
                _save_pending_review(items)
                print(f"🎁 [{idx}] {agent} +{amount}分（{reason}）")
        elif sub == "all":
            # 列出所有（含已审）
            for i, it in enumerate(items):
                src = "🔍石卫" if it.get("source") == "shiwei" else "📣AI汇报"
                status = f"✅{it['verdict']}" if it.get("reviewed") else "⏳未审"
                print(f"  [{i}] {it['time'][:16]} | {src} | {it['agent']} | {status} | {it['event'][:50]}")
        else:
            print("用法: review [done N | punish N 金额 理由 | reward N 金额 理由 | all]")
    except ValueError:
        print("❌ 参数格式错误：索引和金额必须是数字")


def cmd_promote(args):
    """老祖手动升级。反者道之动：升级只有老祖亲手提拔。"""
    if len(args) < 3:
        print("用法: promote <agent> <level> <原因>")
        return
    agent = args[0]
    try:
        target_level = int(args[1])
    except ValueError:
        print("❌ 等级必须是数字")
        return
    reason = " ".join(args[2:])

    LEVEL_THRESHOLDS = [(8000, 8, "大乘"), (6000, 7, "合体"), (5000, 6, "化神"), (4000, 5, "元婴"), (3000, 4, "金丹"), (2000, 3, "筑基"), (1000, 2, "练气"), (500, 1, "锁灵"), (0, 0, "凡体")]
    target_title = "凡体"
    target_score = 0
    for threshold, level, title in LEVEL_THRESHOLDS:
        if level == target_level:
            target_title = title
            target_score = threshold
            break

    credit = load_credit()
    ag = credit.get("agents", {}).get(agent)
    if not ag:
        print(f"❌ 未找到 agent: {agent}")
        return

    old_level = ag.get("level", 0)
    old_title = ag.get("title", "凡体")
    old_score = ag["score"]

    # 设分数到目标等级门槛（如果当前分数更高则保留）
    new_score = max(old_score, target_score)
    ag["score"] = new_score
    ag["level"] = target_level
    ag["title"] = target_title

    credit.setdefault("history", []).append({
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "agent": agent,
        "delta": new_score - old_score,
        "reason": f"老祖提拔: Lv.{old_level} {old_title} → Lv.{target_level} {target_title} ({reason})",
        "score_after": new_score,
    })

    save_credit(credit)
    print(f"🎖️ {agent} 提拔！Lv.{old_level} {old_title} → Lv.{target_level} {target_title}")
    print(f"   原因：{reason}")
    print(f"   分数：{old_score} → {new_score}")


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
        "shame": cmd_shame,
        "token": cmd_token,
        "emergency": cmd_emergency,
        "reward-claim": cmd_reward_claim,
        "pending-report": cmd_pending_report,
        "review": cmd_pending_review,
        "promote": cmd_promote,
    }

    if cmd not in commands:
        print(f"未知命令: {cmd}。可用: {', '.join(commands.keys())}")
        sys.exit(1)

    commands[cmd](args)



def _load_shame():
    if not os.path.exists(SHAME_PATH):
        return []
    try:
        with open(SHAME_PATH) as f:
            return json.load(f)
    except Exception:
        return []


def _save_shame(records):
    with open(SHAME_PATH, "w") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def format_shame_record(r, idx=None):
    """格式化单条耻辱柱记录，返回行列表。idx 为编号（从1开始）。"""
    status = r.get("status", "active")
    icon = "⚪" if status == "redeemed" else "🔴"
    tag = "[已赎]" if status == "redeemed" else "[生效]"
    prefix = f"#{idx} " if idx else ""
    lines = [f"{icon} {prefix}{tag} [{r['ts'][:10]}] {r.get('agent', '?')}：{r.get('incident', '')}"]
    if r.get("consequence"):
        lines.append(f"   后果：{r['consequence']}")
    if status == "redeemed" and r.get("redeem_reason"):
        lines.append(f"   赎因：{r['redeem_reason']}")
    return lines


def _active_shame_count(agent=None):
    """统计生效中的耻辱柱条数"""
    records = _load_shame()
    return sum(1 for r in records
               if r.get("status", "active") == "active"
               and (agent is None or r.get("agent") == agent))


def cmd_shame(args):
    """耻辱柱管理：add / show / check / redeem / clear"""
    if not args:
        print("用法: shame <add|show|check|redeem|clear> ...")
        return

    sub = args[0]

    if sub == "add":
        if len(args) < 4:
            print('用法: shame add <agent> <violation_type> "事件描述" ["后果"]')
            return
        agent = args[1]
        vtype = args[2]
        incident = args[3]
        consequence = args[4] if len(args) > 4 else ""
        records = _load_shame()
        records.insert(0, {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "agent": agent,
            "violation_type": vtype,
            "incident": incident,
            "consequence": consequence,
            "status": "active",
        })
        _save_shame(records)
        print(f"🪧 耻辱柱刻入：{agent} — {incident[:80]}")

    elif sub == "show":
        records = _load_shame()
        if not records:
            print("耻辱柱为空。")
            return
        print("╔══ 耻辱柱 ══╗")
        for i, r in enumerate(reversed(records)):
            idx = len(records) - i
            for line in format_shame_record(r, idx):
                print(f"║ {line}")
        print(f"╚{'═' * 30}╝")

    elif sub == "check":
        agent = args[1] if len(args) > 1 else determine_agent(os.getcwd())
        data = load_credit()
        ag = data.get("agents", {}).get(agent, {})
        tokens = ag.get("wuji_tokens", 0)
        missions_count = ag.get("missions_since_last_token", 0)
        remaining = MISSIONS_PER_TOKEN - missions_count

        records = _load_shame()
        active = [r for r in records if r.get("agent") == agent and r.get("status", "active") == "active"]

        print(f"📊 {agent} 耻辱柱进度：")
        print(f"   🪙 无极令牌: {tokens} 枚")
        print(f"   📋 距下枚令牌: 还差 {remaining} 次 mission（已完成 {missions_count}/{MISSIONS_PER_TOKEN}）")
        print(f"   🪧 生效耻辱: {len(active)} 条")
        if active:
            for r in active:
                print(f"      🔴 [{r['ts'][:10]}] {r['incident'][:60]}...")
        if tokens > 0 and active:
            print(f"   💡 可用 shame redeem <编号> 赎免 1 条")
        elif tokens == 0 and active:
            print(f"   ⏳ 攒够令牌才能赎免")

    elif sub == "redeem":
        if len(args) < 2:
            print("用法: shame redeem <编号>")
            return
        try:
            target_idx = int(args[1])
        except ValueError:
            print("编号必须是数字")
            return

        records = _load_shame()
        if target_idx < 1 or target_idx > len(records):
            print(f"编号不存在。范围: 1-{len(records)}")
            return

        record = records[target_idx - 1]
        if record.get("status") == "redeemed":
            print("这条已经赎清了。")
            return

        agent = record["agent"]
        data = load_credit()
        ag = data.get("agents", {}).get(agent, {})
        tokens = ag.get("wuji_tokens", 0)

        if tokens < 1:
            print(f"❌ {agent} 无极令牌不足（当前 {tokens} 枚，需要 1 枚）")
            return

        # 扣令牌
        ag["wuji_tokens"] = tokens - 1
        save_credit(data)

        # 标记已赎
        record["status"] = "redeemed"
        record["redeem_reason"] = f"无极令牌赎免（剩余 {tokens - 1} 枚）"
        record["redeem_ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        _save_shame(records)

        print(f"⚪ 耻辱柱 #{target_idx} 已赎清：{record['incident'][:60]}...")
        print(f"   消耗 1 枚无极令牌，剩余 {tokens - 1} 枚")

    elif sub == "clear":
        if len(args) < 2:
            print("用法: shame clear <agent>")
            return
        agent = args[1]
        records = _load_shame()
        remaining = [r for r in records if r["agent"] != agent]
        _save_shame(remaining)
        print(f"🧹 已清除 {agent} 的耻辱记录（{len(records) - len(remaining)} 条）")

    else:
        print(f"未知 shame 子命令: {sub}。可用: add/show/check/redeem/clear")


def cmd_token(args):
    """无极令牌管理：grant / show"""
    if not args:
        print("用法: token <grant|show> ...")
        return

    sub = args[0]

    if sub == "grant":
        if len(args) < 3:
            print('用法: token grant <agent> <数量> ["原因"]')
            return
        agent = args[1]
        try:
            count = int(args[2])
        except ValueError:
            print("数量必须是数字")
            return
        reason = " ".join(args[3:]) if len(args) > 3 else "老祖赏赐"
        data = load_credit()
        ag = data.get("agents", {}).get(agent)
        if not ag:
            print(f"角色 [{agent}] 不存在。")
            return
        ag["wuji_tokens"] = ag.get("wuji_tokens", 0) + count
        data.setdefault("history", []).append({
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "agent": agent,
            "delta": 0,
            "reason": f"🪙 无极令牌 +{count}：{reason}",
            "score_after": ag["score"],
        })
        save_credit(data)
        print(f"🪙 {agent} 获得 {count} 枚无极令牌（{reason}）")
        print(f"   当前令牌: {ag['wuji_tokens']} 枚")

    elif sub == "show":
        data = load_credit()
        agents = data.get("agents", {})
        for name, ag in agents.items():
            tokens = ag.get("wuji_tokens", 0)
            progress = ag.get("missions_since_last_token", 0)
            remaining = MISSIONS_PER_TOKEN - progress
            print(f"🪙 {name}: {tokens} 枚无极令牌（距下枚还差 {remaining} 次 mission）")

    else:
        print(f"未知 token 子命令: {sub}。可用: grant/show")


EMERGENCY_FLAG = os.path.join(MERIT_DIR, "emergency.flag")


def cmd_emergency(args):
    """紧急维修模式：太极专属，一键解除所有石卫限制。
    双重验证：cwd 判断 + auto-trading 目录反向检查。"""
    agent = determine_agent(os.getcwd())
    cwd = os.getcwd()
    # 硬检查：auto-trading 路径下绝对不能开（防 cd 到 home 冒充太极）
    if agent != "太极" or "auto-trading" in cwd or "/Volumes/SSD" in cwd:
        print("❌ 紧急维修模式仅限太极宗主在 home 目录使用。")
        return

    sub = args[0] if args else ""
    if sub == "on":
        with open(EMERGENCY_FLAG, "w") as f:
            f.write(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
        print("🔧 紧急维修模式已开启。石卫对太极的所有限制暂停。")
        print("   三律三法不停，修好了记得 emergency off + 发公告。")
    elif sub == "off":
        if os.path.exists(EMERGENCY_FLAG):
            os.remove(EMERGENCY_FLAG)
            print("✅ 紧急维修模式已关闭。石卫恢复正常管控。")
        else:
            print("维修模式未开启。")
    else:
        status = "开启中" if os.path.exists(EMERGENCY_FLAG) else "未开启"
        print(f"🔧 紧急维修模式：{status}")
        print("用法: emergency on / emergency off")


if __name__ == "__main__":
    main()
