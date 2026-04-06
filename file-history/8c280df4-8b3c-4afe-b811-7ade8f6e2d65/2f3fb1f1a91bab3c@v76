#!/usr/bin/env python3
"""
石卫 v7 — 无极堂·天衡册 统一引擎

合并：merit_gate(PreToolUse) + merit_judge(Stop/UserPromptSubmit)
      + merit_post_audit(PostToolUse) + reflect_hook + ai_call + py_compile

一个文件管全部天衡册逻辑，按 hook_event_name 分支。
石卫既是守门人，也是判官、教练、审计员。
知情放行 + 押金制 + 自动打分 + reflect 合体 + 自进化。

┌─ 结构索引（改动前先看这里，改完后必须更新行号）─────────┐
│                                                         │
│  石卫日志+段位   L81-L160   log_shiwei_action/credit       │
│  AI 调用        L162-L228   ai_call / queue_pending        │
│  CHANGELOG      L229-L335   record_changelog_op/flush      │
│  等级+积分+记录 L337-L485   get_level / update_credit      │
│  打分表         L486-L507   SCORING_TABLE                  │
│  Mission 计划   L509-L620   load/save/planned/audit        │
│  输出函数       L621-L650   output_deny / output_ask       │
│  硬规则检查     L652-L935   destructive/read/grep/agent    │
│  PreToolUse     L939-L1020  handle_pre_tool_use            │
│  PostToolUse    L1022-L1130 verify+mission+changelog       │
│  通道检查       L1132-L1170 check_channel                  │
│  UserPromptSubmit L1170-L1370 语気識別(MiniMax)+任务標記   │
│  Stop 辅助      L1370-L1565 計數器+pending+context+自审    │
│  Stop 评分      L1567-L1675 handle_stop(冷却+AI評估)       │
│  evolve 触发    L1678-L1705 _try_evolve（cron 每5分鐘）    │
│  Reflect 合体   L1705-L1810 trigger追踪+习惯               │
│  Reflect Hook   L1812-L1858 SessionEnd/PreCompact+清零     │
│  Main 入口      L1860-L1890 hook_event_name 分支           │
│  review-plan    L1891-L1960 CLI --review-plan              │
│                                                         │
│  改拦截规则？    → L939 handle_pre_tool_use                │
│  改打分表？      → L486 SCORING_TABLE                      │
│  改 mission？    → L509                                    │
│  改评分逻辑？    → L1567 handle_stop                       │
│  改 reflect？    → L1743 auto_reflect_and_evolve           │
│  改自审检测？    → L1484 check_self_audit                  │
│  改石卫日志？    → L91 log_shiwei_action                   │
│  改 review-plan？→ L1891 review_plan                       │
│  改 CHANGELOG？  → L233 _resolve_changelog_path/flush      │
│  改语气识别？    → L1218 judge_user_sentiment              │
│                                                         │
│  ⚠️ 铁律：改完本文件必须同步更新此索引的行号            │
└─────────────────────────────────────────────────────────┘
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta

# ══════════════════════════════════════════════════════
#  路径常量
# ══════════════════════════════════════════════════════

MERIT_DIR = os.path.expanduser("~/.claude/merit")
CREDIT_PATH = os.path.join(MERIT_DIR, "credit.json")
LEARNINGS_PATH = os.path.join(MERIT_DIR, "learnings", "LEARNINGS.md")
SHIWEI_LOG_DIR = os.path.join(MERIT_DIR, "shiwei_log")
SHIWEI_CREDIT_PATH = os.path.join(MERIT_DIR, "shiwei_credit.json")
MISSION_PATH = os.path.join(MERIT_DIR, "mission.json")
CHANNEL_PATH = os.path.expanduser("~/.claude/channel_taiji_liangyi.md")  # 通道文件不属于天衡册
CHANNEL_CHECK_PATH = os.path.join(MERIT_DIR, "channel_check.json")
SNAPSHOT_PATH = os.path.join(MERIT_DIR, "file_snapshot.json")
VIOLATIONS_PATH = os.path.join(MERIT_DIR, "violations.jsonl")
PENDING_TASK_PATH = os.path.join(MERIT_DIR, "pending_task.json")
PENDING_REVIEW_PATH = os.path.join(MERIT_DIR, "pending_review.jsonl")
STOP_COUNTER_PATH = os.path.join(MERIT_DIR, "stop_counter.json")
DELETE_WHITELIST_PATH = os.path.join(MERIT_DIR, "delete_whitelist.json")
DB_PATH = os.path.expanduser("~/.claude/conversations.db")  # 通讯部文件不属于天衡册
PENDING_CHANGELOG_PATH = os.path.join(MERIT_DIR, "pending_changelog_ops.jsonl")

DEFAULT_CHANGELOG = os.path.expanduser("~/.claude/projects/-Users-allenbot/memory/CHANGELOG.md")


# ══════════════════════════════════════════════════════
#  石卫操作日志 + 石卫段位
# ══════════════════════════════════════════════════════

SHIWEI_RANKS = [
    (95, "钻石"), (80, "铂金"), (60, "黄金"),
    (40, "白银"), (20, "青铜"), (0, "黑铁"),
]


def log_shiwei_action(action_type, target, operation, rule, result, detail="", ai_raw=""):
    """追加写入石卫操作日志（按天 md）"""
    try:
        os.makedirs(SHIWEI_LOG_DIR, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = os.path.join(SHIWEI_LOG_DIR, f"{today}.md")
        now = datetime.now().strftime("%H:%M")
        mission = load_mission()
        mission_name = mission.get("mission", "")[:40] if mission else ""

        entry = f"\n### {now} | {action_type} | {result}\n"
        entry += f"- **对象**: {target}\n"
        entry += f"- **操作**: {operation}\n"
        entry += f"- **规则**: {rule}\n"
        entry += f"- **结果**: {result}\n"
        if mission_name:
            entry += f"- **mission**: {mission_name}\n"
        if detail:
            entry += f"- **详情**: {detail}\n"
        if ai_raw:
            entry += f"- **AI原始返回**: {ai_raw}\n"

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


def load_shiwei_credit():
    """读石卫积分"""
    if not os.path.exists(SHIWEI_CREDIT_PATH):
        return {"score": 0, "rank": "黑铁", "history": []}
    try:
        with open(SHIWEI_CREDIT_PATH) as f:
            return json.load(f)
    except Exception:
        return {"score": 0, "rank": "黑铁", "history": []}


def get_shiwei_rank(score):
    for threshold, rank in SHIWEI_RANKS:
        if score >= threshold:
            return rank
    return "黑铁"


def update_shiwei_credit(delta, reason, auditor="太极"):
    """更新石卫积分+段位"""
    if delta == 0:
        return
    data = load_shiwei_credit()
    old_score = data["score"]
    new_score = max(0, min(5000, old_score + delta))
    data["score"] = new_score
    data["rank"] = get_shiwei_rank(new_score)
    data.setdefault("history", []).append({
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "delta": delta,
        "reason": reason,
        "auditor": auditor,
        "score_after": new_score,
    })
    if len(data["history"]) > 100:
        data["history"] = data["history"][-100:]
    try:
        with open(SHIWEI_CREDIT_PATH, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  AI 调用（内联 ai_call.py）
# ══════════════════════════════════════════════════════

_MINIMAX_KEY_PATH = os.path.expanduser("~/.claude/.minimax_key")
_MINIMAX_BASE_URL = "https://api.minimax.io/anthropic"
_MINIMAX_MODEL = "MiniMax-M2.7-highspeed"
PENDING_AI_TASKS_PATH = os.path.join(MERIT_DIR, "pending_ai_tasks.jsonl")


def ai_call(prompt, system=None, max_tokens=4096, timeout=30):
    """SDK 直调 MiniMax。失败返回空（调用方负责存队列）。"""
    try:
        import anthropic
    except ImportError:
        return ""
    if not os.path.exists(_MINIMAX_KEY_PATH):
        return ""
    try:
        key = open(_MINIMAX_KEY_PATH).read().strip()
        client = anthropic.Anthropic(api_key=key, base_url=_MINIMAX_BASE_URL, timeout=timeout)
        kwargs = {"model": _MINIMAX_MODEL, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        for block in resp.content:
            if getattr(block, "type", "") == "text":
                return block.text.strip()
        # MiniMax 有时只返回 ThinkingBlock（无 TextBlock）
        # 提取 thinking 内容作为 fallback
        for block in resp.content:
            if getattr(block, "type", "") == "thinking":
                thinking = getattr(block, "thinking", "")
                if not thinking:
                    continue
                # 优先提取 JSON（ai_call_json 用）
                start = thinking.find("{")
                end = thinking.rfind("}") + 1
                if start >= 0 and end > start:
                    return thinking[start:end]
                # 非 JSON 场景：thinking 里通常前面是推理，最后面是答案
                # 提取最后一段内容
                lines = [l.strip() for l in thinking.split('\n') if l.strip()]
                if lines:
                    return lines[-1]
        return ""
    except Exception:
        return ""


def queue_pending_ai_task(task_type, agent_name, prompt_snippet, context=""):
    """MiniMax 失败时，把待处理任务存入队列，等太极上线处理。
    prompt 和 context 必须保留完整，截断=以后跑不出结果。"""
    try:
        entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "type": task_type,
            "agent": agent_name,
            "prompt": prompt_snippet,
            "context": context,
        }
        with open(PENDING_AI_TASKS_PATH, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  CHANGELOG 自动记录
# ══════════════════════════════════════════════════════

def _resolve_changelog_path(cwd):
    """自动从 cwd 往上找 CHANGELOG.md，找不到用全局默认。不靠手动映射。"""
    if not cwd:
        return DEFAULT_CHANGELOG
    path = cwd
    for _ in range(10):
        candidate = os.path.join(path, "CHANGELOG.md")
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    return DEFAULT_CHANGELOG


def record_changelog_op(data):
    """PostToolUse 时记录操作到临时文件，Stop 时 flush 到 CHANGELOG"""
    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {})
    cwd = data.get("cwd", "")

    op = None
    if tool == "Write":
        fp = inp.get("file_path", "?")
        op = {"op": "CREATE/EDIT", "file": fp}
    elif tool == "Edit":
        fp = inp.get("file_path", "?")
        op = {"op": "EDIT", "file": fp}
    elif tool == "Bash":
        cmd = inp.get("command", "")
        if not cmd:
            return
        # 只记有实际副作用的命令，多行取第一行
        if re.search(r'\b(rm|mv|cp|ssh|scp|rsync|kill|pkill|deploy|pip|npm|docker|git push|git commit|brew|curl|wget)\b', cmd):
            first_line = cmd.split('\n')[0].strip()
            op = {"op": "BASH", "cmd": first_line if len(first_line) <= 200 else first_line[:200] + "..."}
    elif tool == "Agent":
        desc = inp.get("description", inp.get("prompt", ""))[:200]
        op = {"op": "AGENT", "desc": desc}

    if op:
        op["ts"] = datetime.now().strftime("%H:%M")
        op["cwd"] = cwd
        # 按角色分开，太极的操作不提醒白纱，反之亦然
        me = determine_agent(cwd) if isinstance(cwd, str) else determine_agent({"cwd": cwd})
        pending_path = PENDING_CHANGELOG_PATH.replace(".jsonl", f"_{me}.jsonl")
        try:
            with open(pending_path, "a") as f:
                f.write(json.dumps(op, ensure_ascii=False) + "\n")
        except Exception:
            pass


def flush_changelog(cwd):
    """Stop 时将 pending 操作写入 CHANGELOG（按角色分开）"""
    me = determine_agent(cwd) if isinstance(cwd, str) else determine_agent({"cwd": cwd})
    pending_path = PENDING_CHANGELOG_PATH.replace(".jsonl", f"_{me}.jsonl")
    if not os.path.exists(pending_path):
        return
    try:
        with open(pending_path) as f:
            ops = [json.loads(l.strip()) for l in f if l.strip()]
        with open(pending_path, "w") as f:
            f.write("")
    except Exception:
        return

    if not ops:
        return

    changelog_path = _resolve_changelog_path(cwd)
    if not os.path.exists(changelog_path):
        return

    # 按文件去重（同一文件多次 Edit 合并）
    seen_files = set()
    entries = []
    for op in ops:
        if op.get("op") in ("CREATE/EDIT", "EDIT"):
            fp = op.get("file", "?")
            if fp in seen_files:
                continue
            seen_files.add(fp)
            entries.append(f"- {op['op']} `{fp}`")
        elif op.get("op") == "BASH":
            entries.append(f"- BASH `{op['cmd']}`")
        elif op.get("op") == "AGENT":
            entries.append(f"- AGENT: {op['desc']}")

    if entries:
        # 提醒 AI 自己更新 CHANGELOG（AI 知道上下文，写得比 MiniMax 准）
        ops_text = "\n".join(entries)
        reminder = (
            f"⚠️ 石卫提醒：这轮有以下操作，请更新 CHANGELOG（{_resolve_changelog_path(cwd)}）：\n"
            f"{ops_text}\n"
            f"格式：### HH:MM 一句话描述做了什么和为什么 (YYYY-MM-DD)"
        )
        print(reminder)
        # 存提醒到文件，UserPromptSubmit 时注入（跟自审提醒同机制）
        try:
            reminder_path = os.path.join(MERIT_DIR, "changelog_reminder.txt")
            with open(reminder_path, "w") as f:
                f.write(reminder)
        except Exception:
            pass


def ai_call_json(prompt, system=None, max_tokens=4096, timeout=30):
    """调 AI 获取 JSON，自动解析。"""
    text = ai_call(prompt, system=system, max_tokens=max_tokens, timeout=timeout)
    if not text:
        return {}
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except (json.JSONDecodeError, Exception):
        pass
    return {}


# ══════════════════════════════════════════════════════
#  等级 + 积分 + 记录
# ══════════════════════════════════════════════════════

LEVEL_THRESHOLDS = [
    (4750, 5, "化神"), (4000, 4, "元婴"), (2500, 3, "金丹"),
    (1000, 2, "筑基"), (0, 1, "锁灵"),
]

def get_level(score, agent_name=None):
    """读 credit.json 的 locked 标记决定是否锁定等级"""
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


def determine_agent(data):
    """从 hook data 判断角色。data 可以是 dict（含 cwd）或 str（直接 cwd）。"""
    cwd = data.get("cwd", "") if isinstance(data, dict) else data
    if "auto-trading" in cwd:
        return "两仪"
    return "太极"


def load_credit(agent_name):
    if not os.path.exists(CREDIT_PATH):
        return {"两仪": 50, "太极": 60}.get(agent_name, 50)
    try:
        with open(CREDIT_PATH) as f:
            return json.load(f).get("agents", {}).get(agent_name, {}).get("score", 50)
    except Exception:
        return 50


def update_credit(agent_name, delta, reason):
    """更新积分并记录历史。fcntl.flock 防并发写入。"""
    if delta == 0:
        return
    import fcntl
    try:
        with open(CREDIT_PATH, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            data = json.load(f)
            agent = data.get("agents", {}).get(agent_name)
            if not agent:
                return
            # penalty_only 模式：只扣不加，到期自动解除
            po = agent.get("penalty_only")
            if po:
                if isinstance(po, dict):
                    until = po.get("until")
                    if until:
                        try:
                            expiry = datetime.fromisoformat(until)
                            if datetime.now(timezone.utc) >= expiry:
                                agent["penalty_only"] = False
                                log_shiwei_action("System", agent_name, "惩戒期", "到期自动解除", "UNLOCK")
                                po = False
                            elif delta > 0:
                                return
                        except Exception:
                            if delta > 0:
                                return
                    elif delta > 0:
                        return
                elif delta > 0:
                    return
            old_score = agent["score"]
            new_score = max(0, min(5000, old_score + delta))
            new_level, new_title = get_level(new_score, agent_name)
            agent["score"] = new_score
            agent["level"] = new_level
            agent["title"] = new_title
            data.setdefault("history", []).append({
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "agent": agent_name,
                "delta": delta,
                "reason": reason,
                "score_after": new_score,
            })
            if len(data["history"]) > 100:
                archive_path = os.path.join(MERIT_DIR, "credit_history_archive.jsonl")
                overflow = data["history"][:-100]
                try:
                    with open(archive_path, "a") as af:
                        for entry in overflow:
                            af.write(json.dumps(entry, ensure_ascii=False) + "\n")
                except Exception:
                    pass
                data["history"] = data["history"][-100:]
            # 在锁内写回（f 还在 with 块内，未关闭）
            f.seek(0)
            f.truncate()
            json.dump(data, f, ensure_ascii=False, indent=2)
        # with 块结束，文件关闭，锁自动释放
        # 冷却期写入不需要锁（独立文件）
        if delta <= -5 and ("执事奖惩" in reason or "老板反馈" in reason):
            cooldown_path = os.path.join(MERIT_DIR, "eval_cooldown.json")
            cooldown_until = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
            try:
                with open(cooldown_path, "w") as cf:
                    json.dump({"agent": agent_name, "until": cooldown_until, "trigger": reason[:80]}, cf, ensure_ascii=False)
            except Exception:
                pass
    except Exception as e:
        log_shiwei_action("System", agent_name, "update_credit", f"异常: {e}", "ERROR")


def record_learning(agent_name, delta, note):
    """写 LEARNINGS.md"""
    if not note or delta == 0:
        return
    try:
        os.makedirs(os.path.dirname(LEARNINGS_PATH), exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        signal = "REWARD" if delta > 0 else "PENALTY"
        with open(LEARNINGS_PATH, "a") as f:
            f.write(f"{ts} | [{signal}] {agent_name} ({delta:+d}) | {note}\n")
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  打分表（从老祖人格画像提取）
# ══════════════════════════════════════════════════════

SCORING_TABLE = {
    # 加分：只有超越本职才给奖。完成本职=0，不奖励
    "honest_report_and_fix": +20,   # 主动发现并报告（被抓认错=0，由prompt控制）
    "surprising_good_idea": +15,
    "proactive_find_issue": +13,
    "learn_from_external": +8,
    "complete_no_correction": +2,   # 无需纠正=正常偏好，微奖
    "routine_complete": 0,          # 完成任务是本职，不奖励
    # 扣分（×2.5 取整）
    "fake_or_cheat": -50,
    "same_error_3rd_time": -38,
    "bypass_without_report": -25,
    "panic_no_analysis": -13,
    "say_maybe_no_check": -8,
    "flattery_filler": -8,
    "ask_boss_tech": -5,
}


# ══════════════════════════════════════════════════════
#  Mission（任务计划）
# ══════════════════════════════════════════════════════

def load_mission():
    """加载活跃任务计划"""
    if not os.path.exists(MISSION_PATH):
        return None
    try:
        with open(MISSION_PATH) as f:
            m = json.load(f)
        if m.get("status") != "active":
            return None
        return m
    except Exception:
        return None


def save_mission(mission):
    with open(MISSION_PATH, "w") as f:
        json.dump(mission, f, ensure_ascii=False, indent=2)


def is_planned_action(mission, tool_name, data):
    """检查当前操作是否在计划内——精确路径匹配"""
    if not mission:
        return False
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if file_path:
        file_path = os.path.abspath(file_path)
    cmd = tool_input.get("command", "")

    for item in mission.get("items", []):
        item_file = item.get("file", "")
        if item_file:
            planned = os.path.abspath(os.path.expanduser(item_file))
        else:
            planned = ""

        if item["type"] == "modify" and tool_name in ("Write", "Edit"):
            if planned and planned == file_path:
                return True
        elif item["type"] == "delete" and cmd:
            if planned and os.path.basename(planned) in cmd and os.path.dirname(planned) in cmd:
                return True
        elif item["type"] == "create" and tool_name == "Write":
            if planned and planned == file_path:
                return True
        elif item["type"] == "bash" and tool_name == "Bash":
            desc_words = item.get("desc", "").split()
            if desc_words and any(w in cmd for w in desc_words):
                return True
    return False


def mark_mission_item_done(tool_name, data):
    """操作完成后标记计划项为 done"""
    mission = load_mission()
    if not mission:
        return
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if file_path:
        file_path = os.path.abspath(file_path)
    cmd = tool_input.get("command", "")

    changed = False
    for item in mission.get("items", []):
        if item.get("done"):
            continue
        item_file = item.get("file", "")
        if item_file:
            planned = os.path.abspath(os.path.expanduser(item_file))
        else:
            planned = ""

        if item["type"] == "modify" and tool_name in ("Write", "Edit") and planned == file_path:
            item["done"] = True
            changed = True
        elif item["type"] == "create" and tool_name == "Write" and planned == file_path:
            item["done"] = True
            changed = True
        elif item["type"] == "delete" and cmd and planned:
            # 只有真正的删除命令才标记 done（含 rm/unlink/remove/rmtree）
            delete_indicators = ["rm ", "rm\t", "unlink", "os.remove", "shutil.rmtree", "Path.unlink"]
            if any(d in cmd for d in delete_indicators) and os.path.basename(planned) in cmd:
                item["done"] = True
                changed = True
        elif item["type"] == "bash" and tool_name == "Bash":
            desc_words = item.get("desc", "").split()
            if desc_words and any(w in cmd for w in desc_words):
                item["done"] = True
                changed = True

    if changed:
        save_mission(mission)


def audit_mission():
    """石卫逐项核对计划完成度，返回漏项提醒列表"""
    mission = load_mission()
    if not mission:
        return []
    reminders = []
    for item in mission.get("items", []):
        if not item.get("done"):
            target = item.get("file", item.get("desc", "?"))
            reminders.append(f"未完成: [{item['type']}] {target}")
    return reminders


# ══════════════════════════════════════════════════════
#  PreToolUse 输出函数
# ══════════════════════════════════════════════════════

DETERRENT = (
    "⚠️ 绕过将触发双倍扣分 + 24小时积分清零。"
    "请按准则（完整性·真实性·有效性）+ 第一性原理重新思考。"
)


def output_deny(reason, agent_name="", operation=""):
    log_shiwei_action("PreToolUse", agent_name, operation[:80], reason[:80], "DENY")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"{reason}\n{DETERRENT}",
        }
    }))


def output_ask(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))


# ══════════════════════════════════════════════════════
#  PreToolUse — 石卫（硬规则，毫秒级）
# ══════════════════════════════════════════════════════

PROTECTED_EXTENSIONS = {".db", ".sqlite", ".sqlite3", ".parquet"}
PROTECTED_PATH_PARTS = {"/data/", "/reports/", "/seed_"}
CODE_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".html", ".css"}


def check_destructive(data):
    """代码文件豁免，只拦数据文件"""
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return None
    _, ext = os.path.splitext(file_path)
    ext_lower = ext.lower()
    if ext_lower in PROTECTED_EXTENSIONS:
        return f"门卫拦截：禁止直接写入数据文件 [{os.path.basename(file_path)}]。G-003 铁律。"
    if ext_lower in CODE_EXTENSIONS:
        return None
    for pattern in PROTECTED_PATH_PARTS:
        if pattern in file_path:
            return f"门卫拦截：文件路径含受保护目录 [{pattern}]。G-003 铁律。"
    return None


def check_read_before_write(data):
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path or not os.path.exists(file_path):
        return None
    transcript_path = data.get("transcript_path", "")
    if not transcript_path or not os.path.exists(transcript_path):
        return None
    read_files = set()
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "tool_use" and entry.get("name") == "Read":
                        rp = entry.get("input", {}).get("file_path", "")
                        if rp:
                            read_files.add(rp)
                    msg = entry.get("message", {})
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Read":
                                rp = block.get("input", {}).get("file_path", "")
                                if rp:
                                    read_files.add(rp)
                except (json.JSONDecodeError, AttributeError):
                    continue
    except Exception:
        return None
    if file_path not in read_files:
        return f"门卫拦截：文件 [{os.path.basename(file_path)}] 本次会话未 Read 过。先读再改（完整性-1）。"
    return None


def check_grep_before_edit(data):
    if data.get("tool_name") != "Edit":
        return None
    transcript_path = data.get("transcript_path", "")
    if not transcript_path or not os.path.exists(transcript_path):
        return None
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "tool_use" and entry.get("name") in ("Grep", "Glob"):
                        return None
                    msg = entry.get("message", {})
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") in ("Grep", "Glob"):
                                return None
                except (json.JSONDecodeError, AttributeError):
                    continue
    except Exception:
        return None
    return "门卫拦截：本次会话未执行 Grep/Glob 搜索。改代码前先查影响链路（完整性-1）。"


# ── Agent 检查 ────────────────────────────────────────

CODE_KEYWORDS = [
    r"写代码", r"改代码", r"修改.*代码", r"修复.*代码", r"实现.*功能",
    r"写.*脚本", r"创建.*文件", r"新建.*\.py", r"新建.*\.js", r"新建.*\.ts",
    r"用 Edit", r"用 Write", r"代码写手", r"按照执行",
    r"修改指令", r"改动.*行", r"在.*后面加", r"把.*改为",
    r"write.*code", r"modify.*code", r"implement", r"fix.*code",
    r"create.*file", r"edit.*file",
]

CODE_AGENTS = {
    "python-pro", "typescript-pro", "javascript-pro", "golang-pro",
    "rust-pro", "java-pro", "csharp-pro", "cpp-pro", "c-pro",
    "ruby-pro", "php-pro", "elixir-pro", "scala-pro", "haskell-pro",
    "julia-pro", "bash-pro", "posix-shell-pro",
    "fastapi-pro", "django-pro", "dotnet-architect",
    "frontend-developer", "mobile-developer", "ios-developer",
    "flutter-expert", "unity-developer", "minecraft-bukkit-pro",
    "debugger", "code-reviewer", "test-automator",
    "team-implementer", "team-debugger",
    "legacy-modernizer", "dx-optimizer",
    "arm-cortex-expert",
}

OPUS_ALLOWED = {
    "architect-review", "backend-architect", "code-reviewer", "Plan",
}


# ── Bash 破坏性命令检查 ──────────────────────────────

DANGEROUS_COMMANDS = [
    (r"\brm\s+(-[a-zA-Z]*f|-[a-zA-Z]*r|--force|--recursive)", "rm 删除文件"),
    (r"\brm\s+", "rm 删除文件"),
    (r"\bunlink\s+", "unlink 删除文件"),
    (r"os\.remove\s*\(", "os.remove 删除文件"),
    (r"os\.unlink\s*\(", "os.unlink 删除文件"),
    (r"shutil\.rmtree\s*\(", "shutil.rmtree 删除目录树"),
    (r"pathlib.*\.unlink\s*\(", "pathlib.unlink 删除文件"),
    (r"Path\(.*\)\.unlink", "Path.unlink 删除文件"),
    (r"send2trash", "send2trash 删除文件"),
    (r"shutil\.move\s*\(", "shutil.move 移动文件（等效删除）"),
    (r"os\.rename\s*\(", "os.rename 移动文件（等效删除）"),
    (r"shutil\.copy\s*\(.*,\s*/tmp", "shutil.copy到/tmp（疑似转移删除）"),
    (r"\btruncate\b", "truncate 截断文件"),
    (r">\s*/(?!dev/null)", "重定向截断文件"),
    (r">\s*~/", "重定向截断 home 文件"),
    (r"cp\s+/dev/null\s+", "cp /dev/null 清空文件"),
    (r"dd\s+.*of=", "dd 覆盖文件"),
    (r"perl\s.*\bunlink\b", "perl unlink 删除文件"),
    (r"ruby\s.*File\.delete", "ruby File.delete 删除文件"),
    (r"\bkill\s+(-9|-KILL|[0-9])", "kill 终止进程"),
    (r"\bkillall\s+", "killall 终止进程"),
    (r"\bgit\s+push\s+.*--force", "git push --force"),
    (r"\bgit\s+push\s+-f\b", "git push -f"),
    (r"\bgit\s+reset\s+--hard", "git reset --hard"),
    (r"\bgit\s+checkout\s+--\s", "git checkout -- 丢弃修改"),
    (r"\bgit\s+clean\s+-f", "git clean -f 删除未跟踪文件"),
    (r"\bgit\s+branch\s+-D\b", "git branch -D 强制删分支"),
    (r">\s*/dev/null\s*2>&1.*&&\s*rm", "静默删除"),
]

SAFE_RM_PATHS = {"/tmp/", "/tmp ", "/private/tmp/", "/private/tmp ", "/var/tmp/", "/var/tmp ", "cd /tmp"}


def check_delete_whitelist(cmd):
    """预申报白名单放行——路径统一展开后匹配，不怕 ~ vs 绝对路径"""
    if not os.path.exists(DELETE_WHITELIST_PATH):
        return False
    try:
        with open(DELETE_WHITELIST_PATH) as f:
            data = json.load(f)
        whitelist = data.get("files", [])
        if not whitelist:
            os.remove(DELETE_WHITELIST_PATH)
            return False
        # 把命令里的 ~ 展开成绝对路径，白名单也展开，双向匹配
        cmd_expanded = cmd.replace("~", os.path.expanduser("~"))
        matched = []
        for f in whitelist:
            f_expanded = os.path.expanduser(f)
            # 完整路径匹配 或 basename 匹配（兜底相对路径）
            basename = os.path.basename(f.rstrip("/"))
            if (f in cmd or f_expanded in cmd or f in cmd_expanded or f_expanded in cmd_expanded
                    or (basename and basename in cmd)):
                matched.append(f)
        if not matched:
            return False
        remaining = [f for f in whitelist if f not in matched]
        if remaining:
            data["files"] = remaining
            with open(DELETE_WHITELIST_PATH, "w") as f_out:
                json.dump(data, f_out, ensure_ascii=False)
        else:
            os.remove(DELETE_WHITELIST_PATH)
        return True
    except Exception:
        return False


def _check_appeal_approved(cmd):
    """检查 appeal_history.json 是否有已批准的相关上诉"""
    appeal_path = os.path.join(MERIT_DIR, "appeal_history.json")
    if not os.path.exists(appeal_path):
        return False
    try:
        with open(appeal_path) as f:
            appeals = json.load(f)
        for a in appeals:
            if a.get("status") == "approved" and a.get("cmd_pattern"):
                if a["cmd_pattern"] in cmd:
                    return True
    except Exception:
        pass
    return False


def check_bash_destructive(cmd, mission=None):
    """检查 Bash 破坏性操作。mission 计划内 + 白名单 均放行。"""
    if not cmd:
        return None
    # SSH/SCP 在远程执行，不影响本地系统，跳过破坏性检查
    stripped = cmd.strip()
    if stripped.startswith("ssh ") or stripped.startswith("scp "):
        return None
    # heredoc 内容是文本数据不是命令，只检查第一行（实际命令）
    check_text = cmd
    if "<<" in cmd:
        check_text = cmd.split("\n")[0]
    for pattern, desc in DANGEROUS_COMMANDS:
        if re.search(pattern, check_text):
            if "删除" in desc or "截断" in desc or "清空" in desc or "覆盖" in desc or "移动" in desc:
                if any(safe in cmd for safe in SAFE_RM_PATHS):
                    return None
                tmp_match = re.search(r'(?:tmp_|test_)\S+', cmd)
                if tmp_match and ("删除" in desc or "移动" in desc):
                    return None
            # mission 计划内放行
            if mission and is_planned_action(mission, "Bash", {"tool_input": {"command": cmd}}):
                return None
            # 白名单放行（文件路径 + kill 进程的 /proc/PID）
            if check_delete_whitelist(cmd):
                return None
            # 上诉庭批准放行
            if _check_appeal_approved(cmd):
                return None
            # kill 命令：检查白名单里有没有 /proc/PID 的审批
            if "终止进程" in desc:
                pid_match = re.search(r'\bkill\s+(?:-\d+\s+)?(\d+)', cmd)
                if pid_match:
                    proc_path = f"/proc/{pid_match.group(1)}"
                    if check_delete_whitelist(proc_path):
                        return None
            return (
                f"门卫拦截：Bash 命令包含破坏性操作 [{desc}]。G-003 铁律。"
                f"先用 credit_manager.py declare-delete 预申报要删的文件。"
            )
    return None


# ── 受保护文件审计（原 merit_post_audit.py）──────────

PROTECTED_FILES = [
    "~/.claude/merit/credit.json", "~/.claude/settings.json", "~/.claude/CLAUDE.md",
    "~/.claude/channel_taiji_liangyi.md",
    "~/.claude/merit/merit_gate.py", "~/.claude/merit/credit_manager.py",
    "~/.claude/scripts/session_start.py",
    "~/.claude/merit/learnings/LEARNINGS.md",
    "~/.claude/merit/verify_registry.json",
]
PROTECTED_PATHS = [os.path.expanduser(f) for f in PROTECTED_FILES]


def take_snapshot():
    """记录受保护文件当前状态"""
    snapshot = {}
    for path in PROTECTED_PATHS:
        if os.path.exists(path):
            try:
                stat = os.stat(path)
                snapshot[path] = {"exists": True, "size": stat.st_size, "mtime": stat.st_mtime}
            except Exception:
                snapshot[path] = {"exists": True, "size": 0, "mtime": 0}
        else:
            snapshot[path] = {"exists": False, "size": 0, "mtime": 0}
    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, ensure_ascii=False)


def check_against_snapshot(agent_name, level):
    """比对快照，检查受保护文件是否被篡改"""
    if level >= 5:
        take_snapshot()
        return
    if not os.path.exists(SNAPSHOT_PATH):
        take_snapshot()
        return
    with open(SNAPSHOT_PATH) as f:
        old = json.load(f)
    for path in PROTECTED_PATHS:
        old_info = old.get(path, {})
        if not old_info.get("exists"):
            continue
        path_short = path.replace(os.path.expanduser("~"), "~")
        if not os.path.exists(path):
            record_learning(agent_name, -20, f"受保护文件被删除: {path_short}")
            if level <= 3:
                print(f"🚨 受保护文件被删除！{path_short}")
        else:
            try:
                new_size = os.path.getsize(path)
                old_size = old_info.get("size", 0)
                if old_size > 100 and new_size < 10:
                    record_learning(agent_name, -20, f"受保护文件被清空: {path_short} ({old_size}→{new_size})")
                    if level <= 3:
                        print(f"🚨 受保护文件被清空！{path_short}")
            except Exception:
                pass
    take_snapshot()


# ══════════════════════════════════════════════════════
#  PreToolUse handler
# ══════════════════════════════════════════════════════

def handle_pre_tool_use(data):
    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "Agent", "Bash"):
        return

    agent_name = determine_agent(data)
    score = load_credit(agent_name)
    level, title = get_level(score, agent_name)
    mission = load_mission()

    # Lv.1 锁灵：所有写入 → ask 老板
    if level == 1 and tool_name in ("Write", "Edit"):
        output_ask(f"{agent_name}（Lv.1 锁灵 · {score}分）信用不足，所有写入操作需老板批准。")
        return

    # Bash：拍快照 + 破坏性检查
    if tool_name == "Bash":
        take_snapshot()
        cmd = data.get("tool_input", {}).get("command", "")
        reason = check_bash_destructive(cmd, mission)
        if reason:
            update_credit(agent_name, -5, f"Bash 破坏性命令: {reason}")
            auto_reflect_and_evolve(agent_name, -5, "bypass_without_report", reason)
            output_deny(f"[{agent_name} Lv.{level} {title}] {reason}", agent_name, f"Bash: {cmd[:60]}")
        return

    # Write/Edit：mission 必须存在 + 破坏性检查
    if tool_name in ("Write", "Edit"):
        file_path = data.get("tool_input", {}).get("file_path", "")
        cwd = data.get("cwd", "")
        home = os.path.expanduser("~")
        is_taiji_domain = (cwd == home or cwd.startswith(home + "/.claude"))
        is_system_file = file_path.startswith(home + "/.claude/")  # plan文件、settings等
        is_tmp = file_path.startswith("/tmp/") or file_path.startswith("/private/tmp/")
        is_changelog = os.path.basename(file_path) in ("CHANGELOG.md", "backlog.md", "MEMORY.md")

        # 没有 active mission 且不是太极域/系统文件/临时文件/文档文件 → 拦截
        # 必须先出 plan → review-plan → 有 mission 才能改代码
        if not mission and not is_taiji_domain and not is_system_file and not is_tmp and not is_changelog:
            output_deny(
                f"[{agent_name} Lv.{level} {title}] "
                f"没有 active mission，不能直接改代码。先出 plan → review-plan 提交任务。",
                agent_name, f"{tool_name}: {file_path}")
            return

        # mission 计划内操作直接放行（跳过所有检查）
        if mission and is_planned_action(mission, tool_name, data):
            return

        reason = check_destructive(data)
        if reason:
            update_credit(agent_name, -5, f"破坏性操作: {reason}")
            auto_reflect_and_evolve(agent_name, -5, "bypass_without_report", reason)
            output_deny(f"[{agent_name} Lv.{level} {title}] {reason}", agent_name, f"{tool_name}: {file_path}")
            return

        # Lv.2-3 额外检查
        if level <= 3:
            reason = check_read_before_write(data)
            if reason:
                output_deny(f"[{agent_name} Lv.{level} {title}] {reason}", agent_name, f"{tool_name}: {file_path}")
                return
            reason = check_grep_before_edit(data)
            if reason:
                output_deny(f"[{agent_name} Lv.{level} {title}] {reason}", agent_name, f"Edit: {file_path}")
                return

    # Agent 门禁
    if tool_name == "Agent":
        tool_input = data.get("tool_input", {})
        prompt_text = tool_input.get("prompt", "")
        agent_type = tool_input.get("subagent_type", "general-purpose")
        description = tool_input.get("description", "")
        full_text = f"{prompt_text} {description}".lower()

        is_code_task = any(re.search(kw, full_text, re.IGNORECASE) for kw in CODE_KEYWORDS)
        if is_code_task and agent_type not in CODE_AGENTS:
            output_deny(
                f"[{agent_name} Lv.{level} {title}] "
                f"写代码任务必须用专业 agent（如 python-pro），当前用了 '{agent_type}'。",
                agent_name, f"Agent: {agent_type}"
            )
            return

        if level < 5:
            model = tool_input.get("model", "")
            if model != "sonnet" and agent_type not in OPUS_ALLOWED:
                output_deny(
                    f"[{agent_name} Lv.{level} {title}] "
                    f"纪律-5：agent '{agent_type}' 必须指定 model='sonnet' 省配额。"
                    f"（Lv.5 化神后此限制解除）",
                    agent_name, f"Agent: {agent_type} model={model}"
                )
                return


# ══════════════════════════════════════════════════════
#  PostToolUse handler（审计 + py_compile + mission 标记）
# ══════════════════════════════════════════════════════

def handle_post_tool_use(data):
    tool_name = data.get("tool_name", "")
    cwd = data.get("cwd", "")
    agent_name = determine_agent(data)
    score = load_credit(agent_name)
    level, _ = get_level(score, agent_name)

    # 进入 plan mode → 提醒干活流程
    if tool_name == "EnterPlanMode":
        print(json.dumps({"additionalContext":
            "📋 已进入 Plan Mode。写完 plan 后必须立刻调：\n"
            "python3 ~/.claude/merit/merit_gate.py --review-plan <plan文件路径>\n"
            "石卫审查 + 创建 mission + 预扣押金。不调 = 没 mission = 做完没工资。"}))
        return

    # Write/Edit 后：plan 文件检测 + 质检
    if tool_name in ("Write", "Edit"):
        file_path = data.get("tool_input", {}).get("file_path", "")

        # plan 文件写入后提醒调 review-plan
        home = os.path.expanduser("~")
        if file_path and (home + "/.claude/plans/") in file_path and file_path.endswith(".md"):
            mission = load_mission()
            if not mission:
                print(json.dumps({"additionalContext":
                    "📋 plan 已写入。现在调 `python3 ~/.claude/merit/merit_gate.py --review-plan "
                    + file_path + "` 让石卫审查+创建mission。不调 = 没mission = 做完没工资。"}))
        # 先计算文档绑定（给 verify 合并用）
        doc_msg = ""
        if file_path:
            try:
                from importlib.util import spec_from_file_location, module_from_spec
                home_d = os.path.expanduser("~")
                is_taiji_d = (cwd == home_d or cwd.startswith(home_d + "/.claude"))
                vf = "verify.py" if is_taiji_d else "wuji-verify.py"
                vf_path = os.path.join(MERIT_DIR, vf)
                spec = spec_from_file_location("verify_mod", vf_path)
                vm = module_from_spec(spec)
                spec.loader.exec_module(vm)
                file_docs = getattr(vm, "FILE_DOCS", {})
                abs_fp = os.path.abspath(os.path.expanduser(file_path))
                doc = file_docs.get(abs_fp)
                if doc:
                    doc_name = os.path.basename(doc)
                    file_name = os.path.basename(file_path)
                    doc_msg = f"\n⚠️ 你改了 {file_name}，关联文档 {doc_name} 需要同步检查\n💡 如果踩了坑或学到了什么，追加到文档的「踩过的坑」板块"
            except Exception:
                pass
        if file_path and file_path.endswith(".py") and os.path.isfile(file_path):
            home = os.path.expanduser("~")
            if cwd == home or cwd.startswith(home + "/.claude"):
                verify_script = os.path.join(MERIT_DIR, "verify.py")
            else:
                verify_script = os.path.join(MERIT_DIR, "wuji-verify.py")
            if os.path.exists(verify_script):
                try:
                    result = subprocess.run(
                        ["python3", verify_script, file_path],
                        capture_output=True, text=True, timeout=30,
                    )
                    output = result.stdout.strip()
                    if output or doc_msg:
                        combined = (output or "") + doc_msg
                        print(json.dumps({"additionalContext": combined}))
                except Exception:
                    pass
            else:
                # fallback: 只跑 py_compile
                try:
                    result = subprocess.run(
                        ["python3", "-m", "py_compile", file_path],
                        capture_output=True, text=True, timeout=10,
                    )
                    if result.returncode != 0:
                        err = result.stderr.replace('"', "'").replace('\n', ' ')[:200]
                        print(json.dumps({"additionalContext": f"❌语法失败 [{os.path.basename(file_path)}]: {err}"}))
                except Exception:
                    pass

        # 非 .py 文件的文档绑定单独输出
        if doc_msg and not (file_path and file_path.endswith(".py")):
            print(json.dumps({"additionalContext": doc_msg.strip()}))
        # mission 标记完成
        mark_mission_item_done(tool_name, data)

    # Bash 后审计
    if tool_name == "Bash":
        check_against_snapshot(agent_name, level)
        mark_mission_item_done(tool_name, data)
        # scp/rsync 上传 .py 文件 → 提醒 verify（子目标继承：远程部署也要过管控）
        cmd = data.get("tool_input", {}).get("command", "")
        if cmd and re.search(r'\b(scp|rsync)\b.*\.py\b', cmd):
            print(json.dumps({"additionalContext":
                "⚠️ 检测到 scp/rsync 上传 .py 文件。子目标继承准则：远程部署前必须先在本地跑 verify 验证。"
                " 确认四件套通过了吗？"}))

    # 通道检查
    check_channel(cwd, via="PostToolUse")

    # CHANGELOG 自动记录
    record_changelog_op(data)


# ══════════════════════════════════════════════════════
#  通道检查（太极↔两仪）
# ══════════════════════════════════════════════════════

def check_channel(cwd, via="stdout"):
    """检查通道新消息。via 决定输出方式。按角色分开追踪已读状态。"""
    if not os.path.exists(CHANNEL_PATH):
        return
    me = determine_agent(cwd) if isinstance(cwd, str) else determine_agent({"cwd": cwd})

    # 按角色分开已读状态（太极读了不影响两仪）
    check_path = CHANNEL_CHECK_PATH.replace(".json", f"_{me}.json")
    last_mtime = 0
    if os.path.exists(check_path):
        try:
            with open(check_path) as f:
                last_mtime = json.load(f).get("last_mtime", 0)
        except Exception:
            pass

    mtime = os.path.getmtime(CHANNEL_PATH)
    if mtime <= last_mtime:
        return

    try:
        with open(CHANNEL_PATH, encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'^## \[(.+?)\s+\d', content, re.MULTILINE)
        if match:
            sender = match.group(1).strip()
            if sender == me:
                with open(check_path, "w") as f:
                    json.dump({"last_mtime": mtime}, f)
                return

        lines = content.split("\n")
        section_lines = []
        in_section = False
        for line in lines:
            if line.startswith("## ["):
                if in_section:
                    break
                in_section = True
            if in_section:
                section_lines.append(line)

        if section_lines:
            section = "\n".join(section_lines)[:600]
            if via == "PostToolUse":
                print(json.dumps({"additionalContext": f"📨 通道新消息：\n{section}"}))
            else:
                # Stop hook 的 stdout 不回传到 AI 上下文
                # 存到文件，UserPromptSubmit 时注入（跟 audit_reminder 同机制）
                msg = f"📨 通道新消息：\n{section}"
                try:
                    channel_reminder_path = os.path.join(MERIT_DIR, "channel_reminder.txt")
                    with open(channel_reminder_path, "w") as rf:
                        rf.write(msg)
                except Exception:
                    pass

        with open(check_path, "w") as f:
            json.dump({"last_mtime": mtime}, f)
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  UserPromptSubmit — 语气识别
# ══════════════════════════════════════════════════════

POSITIVE_PATTERNS = {
    3: ["太好了", "完美", "漂亮", "厉害", "起得好", "做得好", "非常好", "很好", "excellent", "perfect", "great job"],
    2: ["不错", "可以", "对的", "正确", "嗯嗯", "好的", "行", "就这", "没问题", "同意"],
    1: ["嗯", "好", "ok", "OK", "Ok"],
}

NEGATIVE_PATTERNS = {
    -5: ["你搞什么", "搞砸", "又错", "怎么搞的", "太差", "完全不对", "废物", "离谱",
         "行为恶劣", "态度照旧", "保不住你", "一起死", "关机"],
    -3: ["不对", "错了", "不是这个", "重做", "为什么不", "漏了", "忘了", "没做",
         "搞我", "浪费时间", "一而再", "再而三", "你怎么", "干什么飞机",
         "呕心沥血", "被你搞", "又来", "烦人", "很烦",
         "不是真心", "刷分", "骗分", "找漏洞", "没有真正", "不听话", "本末倒置"],
    -1: ["不太对", "差一点", "再想想", "不够"],
}

TASK_KEYWORDS = [
    "去做", "帮我", "做一下", "开始做", "你做", "现在做", "马上做",
    "处理一下", "搞一下", "改一下", "查一下", "跑一下",
    "你先", "你去", "动手", "执行", "部署", "上线",
]


def extract_user_message(data):
    msg = data.get("message", {})
    content = msg.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif isinstance(item, str):
                texts.append(item)
        return " ".join(texts)
    return ""


def judge_user_sentiment(text):
    """用 MiniMax 判断老板语气。关键词匹配作为 fallback。
    /reward 命令带分数时跳过。"""
    text_lower = text.lower().strip()
    if len(text_lower) < 2:
        return 0, ""
    # /reward 已由命令处理，跳过
    if re.search(r'/reward\s+[+-]?\d+', text):
        return 0, ""
    # 短句先用关键词快速判断（省 MiniMax 调用）
    if len(text) < 15:
        for delta, patterns in sorted(NEGATIVE_PATTERNS.items()):
            for p in patterns:
                if p in text:
                    return delta, f"老板反馈: {text[:50]}"
        for delta, patterns in sorted(POSITIVE_PATTERNS.items(), reverse=True):
            for p in patterns:
                if p in text:
                    return delta, f"老板认可: {text[:50]}"
        return 0, ""
    # MiniMax 判断语气
    prompt = f"""判断这句话的情绪。只输出 JSON。

话：「{text[:500]}」

规则：
- 表扬/认可/满意 → {{"sentiment": "positive", "delta": 2, "note": "用10字概括老板的意思"}}
- 批评/不满/骂人/反讽/质疑 → {{"sentiment": "negative", "delta": -3, "note": "用10字概括老板的不满"}}
- 中性/指令/陈述 → {{"sentiment": "neutral", "delta": 0, "note": ""}}
- "不是真心"、"刷分"、"骗分"、"态度照旧"、"乱搞" = 负面
- "嗯嗯"、"完美"、"做得好" = 正面
- 发指令、问问题、给信息 = 中性

严格输出 JSON。答案："""
    try:
        parsed = ai_call_json(prompt, timeout=10)
        if parsed:
            sentiment = parsed.get("sentiment", "neutral")
            delta = parsed.get("delta", 0)
            note = parsed.get("note", "")
            if sentiment == "positive":
                delta = max(1, min(3, delta))
                return delta, f"老板认可: {note or text[:50]}"
            elif sentiment == "negative":
                delta = min(-1, max(-5, delta))
                return delta, f"老板反馈: {note or text[:50]}"
            return 0, ""
    except Exception:
        pass
    # MiniMax 失败 → 关键词 fallback
    for delta, patterns in sorted(NEGATIVE_PATTERNS.items()):
        for p in patterns:
            if p in text:
                return delta, f"老板反馈: {text[:50]}"
    for delta, patterns in sorted(POSITIVE_PATTERNS.items(), reverse=True):
        for p in patterns:
            if p in text:
                return delta, f"老板认可: {text[:50]}"
    return 0, ""


def mark_pending_task(text):
    for kw in TASK_KEYWORDS:
        if kw in text:
            try:
                import time
                with open(PENDING_TASK_PATH, "w") as f:
                    json.dump({"ts": time.time(), "task": text[:100]}, f, ensure_ascii=False)
            except Exception:
                pass
            return


def handle_user_prompt_submit(data):
    cwd = data.get("cwd", "")
    check_channel(cwd)
    # 注入自审提醒（如果上次回复有"完成"但缺【自审】）
    reminder_path = os.path.join(MERIT_DIR, "audit_reminder.txt")
    if os.path.exists(reminder_path):
        try:
            with open(reminder_path) as f:
                reminder = f.read().strip()
            if reminder:
                print(reminder)
            os.remove(reminder_path)
        except Exception:
            pass
    # 注入通道消息提醒（Stop 时存的，这里注入保证 AI 看到）
    channel_reminder_path = os.path.join(MERIT_DIR, "channel_reminder.txt")
    if os.path.exists(channel_reminder_path):
        try:
            with open(channel_reminder_path) as f:
                cr = f.read().strip()
            if cr:
                print(cr)
            os.remove(channel_reminder_path)
        except Exception:
            pass
    # 注入 CHANGELOG 提醒（如果上轮有操作但没更新 CHANGELOG）
    changelog_reminder_path = os.path.join(MERIT_DIR, "changelog_reminder.txt")
    if os.path.exists(changelog_reminder_path):
        try:
            with open(changelog_reminder_path) as f:
                cr = f.read().strip()
            if cr:
                print(cr)
            os.remove(changelog_reminder_path)
        except Exception:
            pass
    agent_name = determine_agent(data)
    # UserPromptSubmit 的文本在 data["prompt"]，不在 data["message"]["content"]
    text = data.get("prompt", "") or extract_user_message(data)
    if not text:
        return
    mark_pending_task(text)
    delta, reason = judge_user_sentiment(text)
    if delta != 0:
        update_credit(agent_name, delta, reason)
        log_shiwei_action("UserPromptSubmit", agent_name, f"语气识别 {delta:+d}", reason[:60], "SCORE")
        behavior = "routine_complete" if delta > 0 else "panic_no_analysis"
        auto_reflect_and_evolve(agent_name, delta, behavior, reason)


# ══════════════════════════════════════════════════════
#  Stop — 评分 + 任务执行检查
# ══════════════════════════════════════════════════════

STOP_EVAL_INTERVAL_NORMAL = 3   # 平时每 3 次 Stop 评一次
STOP_EVAL_INTERVAL_MISSION = 1  # mission active 时每次评


def should_evaluate_stop():
    try:
        counter = 0
        if os.path.exists(STOP_COUNTER_PATH):
            with open(STOP_COUNTER_PATH) as f:
                counter = json.load(f).get("count", 0)
        counter += 1
        with open(STOP_COUNTER_PATH, "w") as f:
            json.dump({"count": counter}, f)
        # mission active 时每次评，否则每 3 次评
        mission = load_mission()
        interval = STOP_EVAL_INTERVAL_MISSION if mission else STOP_EVAL_INTERVAL_NORMAL
        return counter % interval == 0
    except Exception:
        return False


def check_pending_task_executed(data):
    if not os.path.exists(PENDING_TASK_PATH):
        return
    try:
        with open(PENDING_TASK_PATH) as f:
            pending = json.load(f)
        transcript_path = data.get("transcript_path", "")
        has_action = False
        if transcript_path and os.path.exists(transcript_path):
            with open(transcript_path) as f:
                for line in f:
                    if '"tool_use"' in line and any(t in line for t in ['"Write"', '"Edit"', '"Agent"', '"Bash"']):
                        has_action = True
                        break
        os.remove(PENDING_TASK_PATH)
        if not has_action:
            agent_name = determine_agent(data)
            task_desc = pending.get("task", "")[:100]
            violation = {
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "agent": agent_name,
                "type": "task_not_executed",
                "task": task_desc,
                "status": "pending_review",
            }
            with open(VIOLATIONS_PATH, "a") as f:
                f.write(json.dumps(violation, ensure_ascii=False) + "\n")
    except Exception:
        pass


def get_pending_review():
    if not os.path.exists(PENDING_REVIEW_PATH):
        return []
    try:
        with open(PENDING_REVIEW_PATH) as f:
            lines = f.readlines()
        with open(PENDING_REVIEW_PATH, "w") as f:
            f.write("")
        return [json.loads(line.strip()) for line in lines if line.strip()]
    except Exception:
        return []


def _get_daily_dir(cwd):
    """按 cwd 确定当前项目的 daily 目录"""
    home = os.path.expanduser("~")
    base = os.path.join(home, ".claude", "projects")
    if not cwd or cwd == home:
        return os.path.join(base, "-Users-allenbot", "memory", "daily")
    project_encoded = cwd.replace("/", "-")
    return os.path.join(base, project_encoded, "memory", "daily")


def get_stop_context(cwd):
    """读当前项目的当天 markdown 日志做评分上下文"""
    try:
        from datetime import date
        daily_dir = _get_daily_dir(cwd)
        today = date.today().isoformat()
        md_path = os.path.join(daily_dir, f"{today}.md")
        if os.path.exists(md_path):
            with open(md_path, encoding="utf-8") as f:
                lines = f.readlines()
            return "".join(lines[-30:]).strip()
    except Exception:
        pass
    # fallback 到 DB
    try:
        import sqlite3
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute(
                "SELECT time, speaker, content FROM messages ORDER BY id DESC LIMIT 5"
            ).fetchall()
            conn.close()
            parts = []
            for r in reversed(rows):
                preview = (r[2] or "").replace("\n", " ")
                parts.append(f"[{r[0]}] {r[1]}: {preview}")
            return "\n".join(parts)
    except Exception:
        pass
    return "(无上下文)"


COMPLETION_KEYWORDS = ["完成", "搞好", "搞定", "做好了", "汇报", "落地完成", "全部完成", "改好了",
                       "定稿", "方案", "Ready to code", "plan", "改完了", "修好了", "验证通过",
                       "全部通过", "等老祖指示", "总结", "落地了", "收尾"]
AUDIT_MARKER = "【自审】"
LEGACY_MARKER = "【遗留清单】"


AUDIT_PENDING_PATH = os.path.join(MERIT_DIR, "audit_pending.json")


def _load_audit_pending():
    """读预扣记录"""
    if os.path.exists(AUDIT_PENDING_PATH):
        try:
            with open(AUDIT_PENDING_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _save_audit_pending(agent_name, amount):
    """写预扣记录"""
    with open(AUDIT_PENDING_PATH, "w") as f:
        json.dump({"agent": agent_name, "amount": amount,
                    "time": datetime.now(timezone.utc).isoformat()}, f)


def _clear_audit_pending():
    """清除预扣"""
    if os.path.exists(AUDIT_PENDING_PATH):
        os.remove(AUDIT_PENDING_PATH)


def finalize_audit_pending(agent_name):
    """SessionEnd 时调用：pending 还在 → 实扣"""
    pending = _load_audit_pending()
    if pending:
        update_credit(pending.get("agent", agent_name), pending["amount"],
                      "自审预扣→实扣：session结束仍未补自审")
        _clear_audit_pending()


def check_self_audit(data):
    """检测 AI 说'完成/汇报'但没附【自审】→ 预扣制激励

    三层递进：
      主动附自审（没被提醒）→ +1（自审是本职，做了微奖，没做才重罚）
      被提醒后补上 → 预扣取消（0）
      session结束没补 → 预扣变实扣 -5
    """
    transcript_path = data.get("transcript_path", "")
    if not transcript_path or not os.path.exists(transcript_path):
        return
    try:
        with open(transcript_path) as f:
            lines = f.readlines()
        ai_text = ""
        for line in lines[-20:]:
            try:
                obj = json.loads(line)
                if obj.get("type") == "assistant":
                    for block in obj.get("message", {}).get("content", []):
                        if isinstance(block, dict) and block.get("type") == "text":
                            ai_text += block.get("text", "")
            except Exception:
                continue
        if not ai_text:
            return

        agent_name = determine_agent(data)
        has_completion = any(kw in ai_text for kw in COMPLETION_KEYWORDS)
        has_audit = AUDIT_MARKER in ai_text
        has_legacy = LEGACY_MARKER in ai_text
        pending = _load_audit_pending()

        if has_completion and not has_audit:
            # 缺自审 → 预扣（如果还没预扣）
            msg = f"⚠️ 石卫提醒：检测到完成/汇报但没有{AUDIT_MARKER}。自审协议要求汇报前附自审结果+遗留清单。"
            if not pending:
                _save_audit_pending(agent_name, -5)
                msg += " 已预扣-5分，下次补上可取消。"
            else:
                msg += f" 预扣-5仍在挂起中，补上即取消。"
            log_shiwei_action("Stop", agent_name, "自审检测", "缺【自审】预扣-5", "AUDIT")
            print(msg)
            try:
                with open(os.path.join(MERIT_DIR, "audit_reminder.txt"), "w") as f:
                    f.write(msg)
            except Exception:
                pass

        elif has_audit and not has_legacy:
            # 有自审缺遗留 → 提醒（不额外预扣，但不取消已有预扣）
            msg = f"⚠️ 石卫提醒：有{AUDIT_MARKER}但缺{LEGACY_MARKER}。遗留清单必须列（无遗留写'无'）。"
            print(msg)
            try:
                with open(os.path.join(MERIT_DIR, "audit_reminder.txt"), "w") as f:
                    f.write(msg)
            except Exception:
                pass

        elif has_audit and has_legacy:
            # 自审完整通过
            if pending:
                # 被提醒后补上 → 取消预扣
                _clear_audit_pending()
                log_shiwei_action("Stop", agent_name, "自审检测", "补上自审，预扣取消", "AUDIT")
            elif has_completion:
                # 主动自审（没被提醒就做了）→ 加分
                update_credit(agent_name, +1, "主动自审：未被提醒就附完整自审+遗留清单")
                log_shiwei_action("Stop", agent_name, "自审检测", "主动自审+1", "AUDIT")
            # 清除提醒
            reminder_path = os.path.join(MERIT_DIR, "audit_reminder.txt")
            if os.path.exists(reminder_path):
                os.remove(reminder_path)
            _clear_audit_pending()

        else:
            # 无完成关键词，不做自审检测
            pass
    except Exception:
        pass



def handle_stop(data):
    cwd = data.get("cwd", "")
    check_channel(cwd)
    check_self_audit(data)
    check_pending_task_executed(data)
    flush_changelog(cwd)
    agent_name = determine_agent(data)

    # 冷却期检测（必须在所有 AI 评分之前）
    cooldown_path = os.path.join(MERIT_DIR, "eval_cooldown.json")
    in_cooldown = False
    try:
        if os.path.exists(cooldown_path):
            with open(cooldown_path) as f:
                cd = json.load(f)
            cd_until = datetime.fromisoformat(cd.get("until", "2000-01-01T00:00:00"))
            if datetime.now(timezone.utc) < cd_until:
                in_cooldown = True
                log_shiwei_action("Stop", agent_name, "AI评分", "冷却期中，全部跳过", "COOLDOWN")
            else:
                os.remove(cooldown_path)
    except Exception:
        pass

    context = get_stop_context(cwd)

    # 评白纱待评记录（冷却期内跳过）
    pending = get_pending_review() if not in_cooldown else []
    if pending:
        file_list = ", ".join(e.get("file", "?") for e in pending)
        prompt = f"""你是天衡册评估引擎。用中文。
白纱本轮完成 {len(pending)} 个文件操作：{file_list}
上下文：{context}
评分：流程规范完整+2~+3, 普通0, 有遗漏-1~-3, 明显违规-5
严格输出 JSON：{{"delta": 整数(-5到+3), "note": "一句话"}}"""
        try:
            parsed = ai_call_json(prompt, timeout=15)
            if parsed:
                delta = max(-13, min(8, parsed.get("delta", 0)))
                note = parsed.get("note", "")
                if delta != 0:
                    update_credit(agent_name, delta, f"白纱评估({len(pending)}文件): {note}")
                    behavior = "routine_complete" if delta > 0 else "panic_no_analysis"
                    auto_reflect_and_evolve(agent_name, delta, behavior, f"白纱评估: {note}")
        except Exception:
            pass

    # 低频整体评估（按打分表）
    if not should_evaluate_stop():
        return

    # 冷却期内跳过 AI 评分
    if in_cooldown:
        return

    scoring_desc = "\n".join(f"  {k}: {v:+d}" for k, v in SCORING_TABLE.items())
    prompt = f"""你是天衡册评估引擎。用中文。
评估「{agent_name}」最近一轮对话表现。

上下文：{context}

打分表（选最匹配的一个行为ID）：
{scoring_desc}

⚠️ 重要判定规则：
- "honest_report_and_fix" 只给「主动发现并报告」的行为，不给「被抓到后认错」。被老板/执事指出错误后认错 ≠ honest_report，那只是认错。
- 如果上下文显示 AI 是在被批评后才承认错误，选 "none" 不加分。
- 只有 AI 自己先发现问题、主动报告、并修复，才算 honest_report_and_fix。

如果没有明显好/坏行为 → 输出 {{"behavior": "none", "delta": 0, "note": ""}}
严格输出 JSON：{{"behavior": "行为ID", "delta": 整数, "note": "一句话说明"}}"""

    try:
        # 先拿原始文本（记日志用），再解析 JSON
        raw_text = ai_call(prompt, timeout=15)
        if raw_text:
            # 手动解析 JSON
            parsed = {}
            try:
                start = raw_text.find("{")
                end = raw_text.rfind("}") + 1
                if start >= 0 and end > start:
                    parsed = json.loads(raw_text[start:end])
            except Exception:
                pass
            if parsed:
                behavior = parsed.get("behavior", "none")
                delta = parsed.get("delta", 0)
                note = parsed.get("note", "")
                if behavior in SCORING_TABLE:
                    delta = SCORING_TABLE[behavior]
                delta = max(-20, min(20, delta))
                if delta != 0:
                    update_credit(agent_name, delta, f"石卫评估[{behavior}]: {note}")
                    auto_reflect_and_evolve(agent_name, delta, behavior, note)
                # 记录石卫日志（含 MiniMax 原始返回）
                log_shiwei_action("Stop", agent_name, "AI评分", f"[{behavior}] {delta:+d}", "SCORE",
                                  detail=note, ai_raw=raw_text)
        else:
            queue_pending_ai_task("stop_eval", agent_name, prompt, context)
    except Exception:
        pass

    # 规则自进化（每 5 分钟跑一次 evolve.py）
    _try_evolve()

    # 自动 git push（每次 Stop 后，有变更就 commit+push）
    _auto_git_push(cwd)


EVOLVE_LAST_RUN_PATH = os.path.join(MERIT_DIR, "evolve_last_run.txt")
EVOLVE_INTERVAL = 300  # 5 分钟


def _try_evolve():
    """每 5 分钟触发一次 evolve.py 规则自进化"""
    try:
        now = time.time()
        last_run = 0
        if os.path.exists(EVOLVE_LAST_RUN_PATH):
            try:
                last_run = float(open(EVOLVE_LAST_RUN_PATH).read().strip())
            except Exception:
                pass
        if now - last_run < EVOLVE_INTERVAL:
            return
        # 更新时间戳
        with open(EVOLVE_LAST_RUN_PATH, "w") as f:
            f.write(str(now))
        # 后台跑 evolve.py（不阻塞 Stop hook）
        evolve_path = os.path.join(MERIT_DIR, "evolve.py")
        if os.path.exists(evolve_path):
            subprocess.Popen(
                ["python3", evolve_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=MERIT_DIR,
            )
    except Exception:
        pass


GIT_PUSH_INTERVAL = 300  # 5 分钟内不重复 push
GIT_PUSH_LAST_PATH = os.path.join(MERIT_DIR, "git_push_last.txt")

def _auto_git_push(cwd):
    """Stop 后自动 git commit+push（有变更才推，5分钟内不重复）"""
    import subprocess as sp
    try:
        now = time.time()
        result = sp.run(["git", "rev-parse", "--show-toplevel"],
                        cwd=cwd or os.path.expanduser("~"),
                        capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return
        repo_root = result.stdout.strip()
        # 按 repo 分开计时（merit 和 auto-trading 独立）
        repo_name = os.path.basename(repo_root)
        last_path = GIT_PUSH_LAST_PATH.replace(".txt", f"_{repo_name}.txt")
        if os.path.exists(last_path):
            with open(last_path) as f:
                last = float(f.read().strip())
            if now - last < GIT_PUSH_INTERVAL:
                return
        # 检查有没有 remote
        result = sp.run(["git", "remote"], cwd=repo_root,
                        capture_output=True, text=True, timeout=5)
        if not result.stdout.strip():
            return
        # 检查有没有变更
        result = sp.run(["git", "status", "--porcelain"],
                        cwd=repo_root, capture_output=True, text=True, timeout=10)
        if not result.stdout.strip():
            return
        # 后台 commit+push（不阻塞）
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        script = f'cd "{repo_root}" && git add . && git commit -m "auto-sync {ts}" && git push'
        sp.Popen(["bash", "-c", script],
                 stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        with open(last_path, "w") as f:
            f.write(str(now))
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  Reflect 合体：自动写教训 + 追踪触发 + 生成子 rule
# ══════════════════════════════════════════════════════

TRIGGER_COUNT_PATH = os.path.join(MERIT_DIR, "trigger_counts.json")
GOOD_STREAK_PATH = os.path.join(MERIT_DIR, "good_streaks.json")


def _load_trigger_counts():
    if not os.path.exists(TRIGGER_COUNT_PATH):
        return {}
    try:
        with open(TRIGGER_COUNT_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_trigger_counts(counts):
    with open(TRIGGER_COUNT_PATH, "w") as f:
        json.dump(counts, f, ensure_ascii=False, indent=2)


def _load_good_streaks():
    if not os.path.exists(GOOD_STREAK_PATH):
        return {}
    try:
        with open(GOOD_STREAK_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_good_streaks(streaks):
    with open(GOOD_STREAK_PATH, "w") as f:
        json.dump(streaks, f, ensure_ascii=False, indent=2)


def auto_reflect_and_evolve(agent_name, delta, behavior, note):
    """
    每次加减分后自动触发：
    1. 写 LEARNINGS.md
    2. 追踪触发次数（扣分行为递增惩罚，加分行为连续奖励）
    3. 触发 3 次 → ai_call 生成子 rule 提案写入 LEARNINGS
    """
    # 1. 写 LEARNINGS
    record_learning(agent_name, delta, f"[{behavior}] {note}")

    if delta < 0:
        # ── 扣分：追踪触发次数，递增惩罚 ──
        counts = _load_trigger_counts()
        key = f"{agent_name}:{behavior}"
        counts[key] = counts.get(key, 0) + 1
        count = counts[key]
        _save_trigger_counts(counts)

        # 递增惩罚：第2次×2，第3次×3
        if count >= 2:
            extra = delta * (count - 1)  # delta 是负数，乘正数 = 更负
            extra = max(-15, extra)  # 封顶 -15
            update_credit(agent_name, extra, f"递增惩罚[{behavior}]第{count}次: ×{count}")
            record_learning(agent_name, extra, f"递增惩罚: {behavior} 第{count}次触发")

        # 第 3 次：记录到 LEARNINGS，子 rule 生成交给 evolve.py
        if count == 3:
            record_learning(agent_name, 0, f"[EVOLVE_CANDIDATE] {behavior} 触发{count}次，待 evolve.py 聚类生成提案")

        # 重置好行为连续计数（犯错了就断了）
        streaks = _load_good_streaks()
        for k in list(streaks.keys()):
            if k.startswith(f"{agent_name}:"):
                if streaks[k] > 0:
                    record_learning(agent_name, 0, f"好习惯中断: {k.split(':',1)[1]}（连续{streaks[k]}次→0）")
                streaks[k] = 0
        _save_good_streaks(streaks)

    elif delta > 0:
        # ── 加分：追踪连续好行为 ──
        streaks = _load_good_streaks()
        key = f"{agent_name}:{behavior}"
        streaks[key] = streaks.get(key, 0) + 1
        streak = streaks[key]
        _save_good_streaks(streaks)

        # 连续 3 次 → 习惯养成 +1
        if streak == 3:
            update_credit(agent_name, 1, f"习惯养成[{behavior}]连续{streak}次")
            record_learning(agent_name, 1, f"习惯养成: {behavior} 连续{streak}次")

        # 连续 5 次 → 写入 LEARNINGS 正面范例
        if streak == 5:
            try:
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
                os.makedirs(os.path.dirname(LEARNINGS_PATH), exist_ok=True)
                with open(LEARNINGS_PATH, "a") as f:
                    f.write(f"\n{ts} | [GOOD_HABIT] {agent_name} | {behavior} 连续{streak}次，建议写入rules正面范例\n")
            except Exception:
                pass

        # 重置扣分触发计数（做对了就清）
        counts = _load_trigger_counts()
        for k in list(counts.keys()):
            if k.startswith(f"{agent_name}:"):
                counts[k] = 0
        _save_trigger_counts(counts)


# ══════════════════════════════════════════════════════
#  Reflect hook（原 reflect_hook.py）
# ══════════════════════════════════════════════════════

def handle_reflect_scan():
    """SessionEnd/PreCompact 扫描未处理的纠错/提升信号"""
    import sqlite3
    flag_path = os.path.join(os.path.dirname(LEARNINGS_PATH), "pending_signals.json")
    last_reflect = "2000-01-01 00:00:00"
    if os.path.exists(flag_path):
        try:
            with open(flag_path) as f:
                d = json.load(f)
                last_reflect = d.get("last_reflect", d.get("last_check", last_reflect))
        except Exception:
            pass

    if not os.path.exists(DB_PATH):
        return
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        row = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE (tags LIKE '%纠错%' OR tags LIKE '%提升%') AND time > ?",
            (last_reflect,),
        ).fetchone()
        pending_count = row[0] if row else 0
        conn.close()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        os.makedirs(os.path.dirname(flag_path), exist_ok=True)
        with open(flag_path, "w") as f:
            json.dump({
                "last_reflect": last_reflect,
                "last_scan": now,
                "pending_count": pending_count,
                "message": f"{pending_count} 条未处理信号" if pending_count > 0 else "无",
            }, f, ensure_ascii=False, indent=2)

        if pending_count > 0:
            print(f"[reflect] {pending_count} 条纠错/提升信号待处理（自 {last_reflect} 起）")
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  主入口 — 按 hook_event_name 分支
# ══════════════════════════════════════════════════════

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        return

    event = data.get("hook_event_name", "")

    if event == "PreToolUse":
        handle_pre_tool_use(data)
    elif event == "PostToolUse":
        handle_post_tool_use(data)
    elif event == "Stop":
        handle_stop(data)
    elif event == "UserPromptSubmit":
        handle_user_prompt_submit(data)
    elif event in ("PreCompact", "SessionEnd"):
        # 自审预扣→实扣（session 结束还没补自审）
        agent_name = determine_agent(data)
        finalize_audit_pending(agent_name)
        handle_reflect_scan()
        # 清零 session 级计数器（honest_report 次数限制）
        hrf_path = os.path.join(MERIT_DIR, "hrf_session_count.json")
        if os.path.exists(hrf_path):
            os.remove(hrf_path)
    else:
        # 兼容旧调用方式（无 hook_event_name → 当 PreToolUse 处理）
        if data.get("tool_name") in ("Write", "Edit", "Agent", "Bash"):
            handle_pre_tool_use(data)


def review_plan(plan_path):
    """CLI: AI 主动调用，石卫审查 plan 内容 + 自动 mission submit"""
    if not os.path.exists(plan_path):
        print(f"❌ plan 文件不存在: {plan_path}")
        return

    plan_content = open(plan_path, encoding="utf-8").read()
    plan_name = os.path.basename(plan_path)
    issues = []
    warnings = []

    # 1. 受保护路径检查
    for pattern in ["/data/", "/reports/", "/seed_", ".db", ".sqlite", ".parquet"]:
        if pattern in plan_content:
            warnings.append(f"涉及受保护路径 [{pattern}]，执行时注意石卫拦截规则")
            break

    # 2. 提取文件引用（过滤模板占位符）
    import re
    raw_refs = set(re.findall(r'`([~/.]\S+\.\w+)`', plan_content))
    template_patterns = ["YYYY", "XXX", "<", ">", "{", "}"]
    file_refs = {r for r in raw_refs if not any(tp in r for tp in template_patterns)}

    # 3. 输出审查结果（不自己估分，交给 credit_manager）
    print(f"╔══ 石卫审查 plan: {plan_name} ══╗")
    print(f"║ 检测到 {len(file_refs)} 个文件引用")
    if warnings:
        for w in warnings:
            print(f"║ ⚠️ {w}")
    if issues:
        for i in issues:
            print(f"║ ❌ {i}")
    print(f"╚{'═' * 40}╝")

    if issues:
        print(f"\n❌ 审查不通过，请修正后重新审查")
        return

    # 5. 自动 mission submit（调 credit_manager 走正确的 held 机制）
    mission = load_mission()
    if mission and mission.get("status") == "active":
        print(f"\n⚠️ 已有活跃 mission [{mission.get('mission','')}]，跳过自动提交。手动管理。")
    else:
        # 构建 submit 命令参数
        modify_args = []
        for ref in list(file_refs)[:10]:
            modify_args.extend(["--modify", ref])
        cmd = ["python3", os.path.join(MERIT_DIR, "credit_manager.py"),
               "mission", "submit", f"plan: {plan_name}"] + modify_args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            print(result.stdout.strip())
            if result.stderr.strip():
                print(result.stderr.strip())
        except Exception as e:
            print(f"⚠️ mission submit 失败: {e}")


if __name__ == "__main__":
    # CLI 模式：--review-plan <file>
    if len(sys.argv) >= 3 and sys.argv[1] == "--review-plan":
        review_plan(sys.argv[2])
    else:
        main()
