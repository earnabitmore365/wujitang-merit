#!/usr/bin/env python3
"""
功过格 Merit Ledger — UserPromptSubmit + Stop hook
老板说话 → 关键词匹配语气 → 自动加减分
AI 回复完 → 后台 Haiku 评估（低频）→ 自动加减分
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

CREDIT_PATH = os.path.expanduser("~/.claude/credit.json")
LEARNINGS_PATH = os.path.expanduser("~/.claude/learnings/LEARNINGS.md")
DB_PATH = os.path.expanduser("~/.claude/conversations.db")

# ── 等级 ──────────────────────────────────────────────

LEVEL_THRESHOLDS = [
    (95, 5, "化神"), (80, 4, "元婴"), (50, 3, "金丹"),
    (20, 2, "筑基"), (0, 1, "锁灵"),
]


def get_level(score):
    for threshold, level, title in LEVEL_THRESHOLDS:
        if score >= threshold:
            return level, title
    return 1, "锁灵"


def determine_agent(cwd):
    if "auto-trading" in cwd:
        return "黑丝"
    return "太极"


def update_credit(agent_name, delta, reason):
    if delta == 0:
        return
    try:
        if not os.path.exists(CREDIT_PATH):
            return
        with open(CREDIT_PATH) as f:
            data = json.load(f)
        agent = data.get("agents", {}).get(agent_name)
        if not agent:
            return
        old_score = agent["score"]
        new_score = max(0, min(100, old_score + delta))
        new_level, new_title = get_level(new_score)
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
            data["history"] = data["history"][-100:]
        with open(CREDIT_PATH, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def record_learning(agent_name, delta, note):
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
#  UserPromptSubmit — 关键词匹配老板语气
# ══════════════════════════════════════════════════════

# 正面词 → 加分（老板表扬/确认）
POSITIVE_PATTERNS = {
    3: ["太好了", "完美", "漂亮", "厉害", "起得好", "做得好", "非常好", "很好", "excellent", "perfect", "great job"],
    2: ["不错", "可以", "对的", "正确", "嗯嗯", "好的", "行", "就这", "没问题", "同意"],
    1: ["嗯", "好", "ok", "OK", "Ok", "继续"],
}

# 负面词 → 减分（老板批评/纠正）
NEGATIVE_PATTERNS = {
    -5: ["你搞什么", "搞砸", "又错", "怎么搞的", "太差", "完全不对", "废物", "离谱"],
    -3: ["不对", "错了", "不是这个", "重做", "为什么不", "漏了", "忘了", "没做"],
    -1: ["不太对", "差一点", "再想想", "不够"],
}


def extract_user_message(data):
    """从 UserPromptSubmit hook 数据提取老板消息"""
    # hook 数据结构：message.content 可能是字符串或数组
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
    """关键词匹配老板语气，返回 (delta, reason)"""
    text_lower = text.lower().strip()

    # 太短的消息不判断（可能是指令）
    if len(text_lower) < 2:
        return 0, ""

    # 先查负面（批评优先级高于表扬）
    for delta, patterns in sorted(NEGATIVE_PATTERNS.items()):
        for p in patterns:
            if p in text:
                return delta, f"老板反馈: {text[:50]}"

    # 再查正面
    for delta, patterns in sorted(POSITIVE_PATTERNS.items(), reverse=True):
        for p in patterns:
            if p in text:
                return delta, f"老板认可: {text[:50]}"

    return 0, ""


def handle_user_prompt_submit(data):
    """处理老板发言 → 语气判断 → 加减分"""
    cwd = data.get("cwd", "")
    agent_name = determine_agent(cwd)
    text = extract_user_message(data)

    if not text:
        return

    delta, reason = judge_user_sentiment(text)
    if delta != 0:
        update_credit(agent_name, delta, reason)
        record_learning(agent_name, delta, reason)


# ══════════════════════════════════════════════════════
#  Stop — 后台 Haiku 评估 AI 回复（低频）
# ══════════════════════════════════════════════════════

STOP_COUNTER_PATH = os.path.expanduser("~/.claude/merit_stop_counter.json")
STOP_EVAL_INTERVAL = 5  # 每 5 次 Stop 评估一次


def should_evaluate_stop():
    """每 N 次 Stop 才触发一次 Haiku 评估"""
    try:
        if os.path.exists(STOP_COUNTER_PATH):
            with open(STOP_COUNTER_PATH) as f:
                counter = json.load(f).get("count", 0)
        else:
            counter = 0
        counter += 1
        with open(STOP_COUNTER_PATH, "w") as f:
            json.dump({"count": counter}, f)
        return counter % STOP_EVAL_INTERVAL == 0
    except Exception:
        return False


PENDING_REVIEW_PATH = os.path.expanduser("~/.claude/merit_pending_review.jsonl")


def get_pending_review():
    """读取并清空 subagent 待评记录"""
    if not os.path.exists(PENDING_REVIEW_PATH):
        return []
    try:
        with open(PENDING_REVIEW_PATH) as f:
            lines = f.readlines()
        # 读完即清
        with open(PENDING_REVIEW_PATH, "w") as f:
            f.write("")
        entries = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return entries
    except Exception:
        return []


def handle_stop(data):
    """AI 回复完 → 两件事：1. 统一评白纱待评记录 2. 低频评黑丝/太极"""
    cwd = data.get("cwd", "")
    agent_name = determine_agent(cwd)

    # 读最近对话上下文
    context_lines = []
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute(
                "SELECT time, speaker, content FROM messages ORDER BY id DESC LIMIT 5"
            ).fetchall()
            conn.close()
            for r in reversed(rows):
                preview = (r[2] or "")[:200].replace("\n", " ")
                context_lines.append(f"[{r[0]}] {r[1]}: {preview}")
    except Exception:
        pass

    context = "\n".join(context_lines) if context_lines else "(无上下文)"

    # ── 1. 统一评白纱待评记录（有记录才调 Haiku）──────
    pending = get_pending_review()
    if pending:
        file_list = ", ".join(e.get("file", "?") for e in pending)
        prompt = f"""你是功过格(Merit Ledger)的评估引擎。用中文。

白纱（subagent）本轮完成了 {len(pending)} 个文件操作：{file_list}

## 最近对话上下文
{context}

## 评分标准
- 流程规范、产出完整 → +2 到 +3
- 普通操作无明显问题 → 0
- 有遗漏或不规范 → -1 到 -3
- 明显违规 → -5

严格输出以下 JSON，不要多余文字：
{{"delta": 整数(-5到+3), "note": "一句话说明"}}
"""
        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "haiku", "--max-turns", "1"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                text = result.stdout.strip()
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    parsed = json.loads(text[start:end])
                    delta = max(-5, min(3, parsed.get("delta", 0)))
                    note = parsed.get("note", "")
                    # 白纱的分记到黑丝头上（黑丝负责验收白纱的产出）
                    if delta != 0:
                        update_credit(agent_name, delta, f"白纱本轮评估({len(pending)}文件): {note}")
                        record_learning(agent_name, delta, f"白纱本轮评估: {note}")
        except Exception:
            pass

    # ── 2. 低频评黑丝/太极自身表现（每 5 次 Stop）─────
    if not should_evaluate_stop():
        return

    prompt = f"""你是功过格(Merit Ledger)的评估引擎。用中文。

评估 AI agent「{agent_name}」最近一轮对话的整体表现。

## 最近对话
{context}

## 评分标准
- 完成任务完整无遗漏 → +2 到 +3
- 普通操作无明显问题 → 0
- 有小瑕疵但不影响结果 → -1
- 明显违规或遗漏 → -3 到 -5

严格输出以下 JSON，不要多余文字：
{{"delta": 整数(-5到+3), "note": "一句话说明"}}
"""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "haiku", "--max-turns", "1"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])
                delta = max(-5, min(3, parsed.get("delta", 0)))
                note = parsed.get("note", "")
                if delta != 0:
                    update_credit(agent_name, delta, f"Haiku评估: {note}")
                    record_learning(agent_name, delta, f"Haiku评估: {note}")
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    event = data.get("hook_event_name", "")

    if event == "UserPromptSubmit":
        handle_user_prompt_submit(data)
    elif event == "Stop":
        handle_stop(data)


if __name__ == "__main__":
    main()
