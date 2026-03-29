#!/usr/bin/env python3
"""
Haiku 门卫部 — PreToolUse hook（Write|Edit|Agent）

架构：Haiku 是队长，硬规则检查是队员。
  第一层（队员巡逻）：硬规则秒回 — 破坏性操作、Lv.1全锁等铁律
  第二层（队长判断）：Haiku 读上下文 → 判断合规性 → 自动加减分 + 记录

积分联动：等级高→检查少，等级低→全查或要老板签字。
"""

import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

CREDIT_PATH = os.path.expanduser("~/.claude/credit.json")
DB_PATH = os.path.expanduser("~/.claude/conversations.db")
LEARNINGS_PATH = os.path.expanduser("~/.claude/learnings/LEARNINGS.md")

# ── 等级定义 ──────────────────────────────────────────

LEVEL_THRESHOLDS = [
    (95, 5, "化神"),
    (80, 4, "元婴"),
    (50, 3, "金丹"),
    (20, 2, "筑基"),
    (0,  1, "锁灵"),
]


def get_level(score):
    for threshold, level, title in LEVEL_THRESHOLDS:
        if score >= threshold:
            return level, title
    return 1, "锁灵"


def determine_agent(data):
    cwd = data.get("cwd", "")
    agent_id = data.get("agent_id", "")
    if agent_id:
        return "白纱"
    if "auto-trading" in cwd:
        return "黑丝"
    return "太极"


def load_credit(agent_name):
    if not os.path.exists(CREDIT_PATH):
        return {"黑丝": 10, "白纱": 40, "太极": 60}.get(agent_name, 50)
    try:
        with open(CREDIT_PATH) as f:
            return json.load(f).get("agents", {}).get(agent_name, {}).get("score", 50)
    except Exception:
        return 50


def update_credit(agent_name, delta, reason):
    """更新积分并记录历史"""
    try:
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
        # 裁剪历史
        if len(data["history"]) > 100:
            data["history"] = data["history"][-100:]
        with open(CREDIT_PATH, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ── 输出函数 ──────────────────────────────────────────

def output_deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
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
#  第一层：队员巡逻（硬规则，秒回）
# ══════════════════════════════════════════════════════

PROTECTED_EXTENSIONS = {".db", ".sqlite", ".sqlite3", ".parquet"}
PROTECTED_PATH_PARTS = {"/data/", "/reports/", "/seed_"}


def check_destructive(data):
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return None
    _, ext = os.path.splitext(file_path)
    if ext.lower() in PROTECTED_EXTENSIONS:
        return f"门卫拦截：禁止直接写入数据文件 [{os.path.basename(file_path)}]。G-003 铁律。"
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


def check_plan_format(data):
    if data.get("tool_name") != "Write":
        return None
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return None
    if "/plans/" not in file_path and "/plan" not in os.path.basename(file_path).lower():
        return None
    content = data.get("tool_input", {}).get("content", "")
    required = ["完整性", "真实性", "有效性", "第一性原理"]
    missing = [r for r in required if r not in content]
    if missing:
        return f"门卫拦截：方案缺少 [{', '.join(missing)}]。方案必须按三准则+第一性原理评估。"
    return None


def check_new_file(data):
    if data.get("tool_name") != "Write":
        return None
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path or os.path.exists(file_path):
        return None
    if "/plans/" in file_path or file_path.startswith("/tmp/"):
        return None
    return f"门卫拦截：即将创建新文件 [{os.path.basename(file_path)}]。确认有必要再创建，做完不留残（完整性-2）。"


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

import shlex

DANGEROUS_COMMANDS = [
    (r"\brm\s+(-[a-zA-Z]*f|-[a-zA-Z]*r|--force|--recursive)", "rm 删除文件"),
    (r"\brm\s+", "rm 删除文件"),
    (r"\bkill\s+(-9|-KILL|[0-9])", "kill 终止进程"),
    (r"\bkillall\s+", "killall 终止进程"),
    (r"\bgit\s+push\s+.*--force", "git push --force"),
    (r"\bgit\s+push\s+-f\b", "git push -f"),
    (r"\bgit\s+reset\s+--hard", "git reset --hard"),
    (r"\bgit\s+checkout\s+--\s", "git checkout -- 丢弃修改"),
    (r"\bgit\s+clean\s+-f", "git clean -f 删除未跟踪文件"),
    (r"\bgit\s+branch\s+-D\b", "git branch -D 强制删分支"),
    (r"\btruncate\b", "truncate 截断文件"),
    (r">\s*/dev/null\s*2>&1.*&&\s*rm", "静默删除"),
]


SAFE_RM_PATHS = {"/tmp/", "/tmp ", "/private/tmp/", "/private/tmp ", "/var/tmp/", "/var/tmp ", "cd /tmp"}


def check_bash_destructive(cmd):
    """检查 Bash 命令是否包含破坏性操作"""
    if not cmd:
        return None
    for pattern, desc in DANGEROUS_COMMANDS:
        if re.search(pattern, cmd):
            # rm 在 /tmp/ 下豁免（清理临时文件是正常操作）
            if "rm" in desc:
                if any(safe in cmd for safe in SAFE_RM_PATHS):
                    return None
            return f"门卫拦截：Bash 命令包含破坏性操作 [{desc}]。G-003 铁律。需要老板明确同意。"
    return None


# ══════════════════════════════════════════════════════
#  第二层：Haiku 队长（智能判断 + 自动加减分 + 记录）
# ══════════════════════════════════════════════════════

def get_recent_context(limit=5):
    """从 conversations.db 读最近对话作为上下文"""
    try:
        if not os.path.exists(DB_PATH):
            return ""
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT time, speaker, content FROM messages ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        lines = []
        for r in reversed(rows):
            preview = (r[2] or "")[:200].replace("\n", " ")
            lines.append(f"[{r[0]}] {r[1]}: {preview}")
        return "\n".join(lines)
    except Exception:
        return ""


def haiku_judge(agent_name, level, title, score, tool_name, tool_input, context):
    """
    队长 Haiku 判断：当前操作是否合规 + 加减分 + 记录
    返回 dict: {"decision": "allow"/"deny", "delta": int, "note": str}
    超时或失败 → 默认 allow + delta=0
    """
    file_path = tool_input.get("file_path", "")
    file_name = os.path.basename(file_path) if file_path else ""
    agent_type = tool_input.get("subagent_type", "")
    content_preview = (tool_input.get("content", "") or "")[:300]
    old_string = (tool_input.get("old_string", "") or "")[:150]
    new_string = (tool_input.get("new_string", "") or "")[:150]

    if tool_name in ("Write", "Edit"):
        action_desc = f"{tool_name} {file_name}"
        if tool_name == "Edit":
            action_desc += f"\n  旧: {old_string}\n  新: {new_string}"
        else:
            action_desc += f"\n  内容前300字: {content_preview}"
    elif tool_name == "Agent":
        action_desc = f"Agent {agent_type}: {tool_input.get('description', '')}"
    else:
        action_desc = f"{tool_name}"

    prompt = f"""你是 Haiku 门卫队长。用中文。判断以下操作是否合规。

## 当前角色
{agent_name} · Lv.{level} {title} · {score}分

## 操作
{action_desc}

## 最近对话上下文
{context}

## 规则摘要
- 改文件前必须先 Read（完整性-1）
- 改代码前必须查影响链路（完整性-1）
- 不留残、新建文件要有必要性（完整性-2）
- 改动后必须同步更新文档（完整性-6）
- 方案要三准则+第一性原理评估（有效性-1 + 第一性原理）
- 写代码用专业 agent（有效性-2）
- 非决策 agent 用 Sonnet 省配额（纪律-5）

## 你的任务
判断这个操作的合规程度。严格输出以下 JSON，不要多余文字：
{{"decision": "allow 或 deny", "delta": 加减分整数(-5到+3), "note": "一句话说明原因"}}

评分参考：
- 流程完全正确（先读后改、查了链路）→ +1 到 +3
- 普通操作无明显问题 → 0
- 轻微不规范 → -1 到 -3
- 明显违规（该查没查、该读没读）→ -5 并 deny
"""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "haiku", "--max-turns", "1"],
            capture_output=True, text=True, timeout=8,
        )
        if result.returncode == 0 and result.stdout.strip():
            # 从输出中提取 JSON
            text = result.stdout.strip()
            # 尝试找到 JSON 部分
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        pass

    # 默认放行，不加减分
    return {"decision": "allow", "delta": 0, "note": ""}


def record_haiku_result(agent_name, delta, note):
    """记录 Haiku 判断结果到 LEARNINGS.md"""
    if not note or delta == 0:
        return
    try:
        os.makedirs(os.path.dirname(LEARNINGS_PATH), exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        signal = "REWARD" if delta > 0 else "PENALTY"
        entry = f"{ts} | [{signal}] {agent_name} ({delta:+d}) | {note}\n"
        with open(LEARNINGS_PATH, "a") as f:
            f.write(entry)
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        return

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "Agent", "Bash"):
        return

    # 公共层：读积分 → 判角色 → 算等级
    agent_name = determine_agent(data)
    score = load_credit(agent_name)
    level, title = get_level(score)

    # ── 第一层：队员巡逻（硬规则，秒回）──────────────

    # Lv.1 锁灵：所有操作 → ask 老板（铁律，不经过 Haiku）
    if level == 1 and tool_name in ("Write", "Edit"):
        output_ask(f"{agent_name}（Lv.1 锁灵 · {score}分）信用不足，所有写入操作需老板批准。")
        return

    # Bash 破坏性命令 — 所有等级都查（G-003 铁律）
    if tool_name == "Bash":
        cmd = data.get("tool_input", {}).get("command", "")
        reason = check_bash_destructive(cmd)
        if reason:
            update_credit(agent_name, -5, f"Bash 破坏性命令: {reason}")
            record_haiku_result(agent_name, -5, reason)
            output_deny(f"[{agent_name} Lv.{level} {title}] {reason}")
        return  # Bash 只查破坏性，不走 Haiku 队长

    # 破坏性操作 — 所有等级都查（G-003 铁律，不经过 Haiku）
    if tool_name in ("Write", "Edit"):
        reason = check_destructive(data)
        if reason:
            update_credit(agent_name, -5, f"破坏性操作: {reason}")
            record_haiku_result(agent_name, -5, reason)
            output_deny(f"[{agent_name} Lv.{level} {title}] {reason}")
            return

    # Agent 门禁1：写代码必须用专业 agent（铁律，不经过 Haiku）
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
                f"写代码任务必须用专业 agent（如 python-pro），当前用了 '{agent_type}'。"
            )
            return

        # Agent 门禁2：模型限制（Lv.5 化神豁免）
        if level < 5:
            model = tool_input.get("model", "")
            if model != "sonnet" and agent_type not in OPUS_ALLOWED:
                output_deny(
                    f"[{agent_name} Lv.{level} {title}] "
                    f"纪律-5：agent '{agent_type}' 必须指定 model='sonnet' 省配额。"
                    f"（Lv.5 化神后此限制解除）"
                )
                return

    # ── 第二层：Haiku 队长判断 ────────────────────────
    # Lv.4+ 不需要 Haiku 判断（已经被信任）
    if level >= 4:
        return

    context = get_recent_context(5)
    result = haiku_judge(
        agent_name, level, title, score,
        tool_name, data.get("tool_input", {}), context,
    )

    decision = result.get("decision", "allow")
    delta = result.get("delta", 0)
    note = result.get("note", "")

    # 确保 delta 在合理范围
    delta = max(-5, min(3, delta))

    # 更新积分
    if delta != 0:
        update_credit(agent_name, delta, note)
        record_haiku_result(agent_name, delta, note)

    # deny 时拦截
    if decision == "deny":
        output_deny(f"[Haiku队长 → {agent_name} Lv.{level} {title}] {note}")
        return

    # allow：放行（不输出 = 默认放行）


if __name__ == "__main__":
    main()
