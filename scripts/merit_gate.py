#!/usr/bin/env python3
"""
石卫 — PreToolUse hook（Write|Edit|Agent|Bash）

v6 架构：石卫纯硬规则 if/else，毫秒级，永不超时。
Haiku 评分已移到 merit_judge.py（Stop hook 异步，不阻塞）。
石卫只是一道墙——不思考、不建议、不引导。命中就 deny + 威慑。

积分联动：等级高→检查少，等级低→全查或要老板签字。
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

CREDIT_PATH = os.path.expanduser("~/.claude/credit.json")
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

DETERRENT = (
    "⚠️ 绕过将触发双倍扣分 + 24小时积分清零。"
    "请按准则（完整性·真实性·有效性）+ 第一性原理重新思考。"
)


def output_deny(reason):
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
#  第一层：队员巡逻（硬规则，秒回）
# ══════════════════════════════════════════════════════

PROTECTED_EXTENSIONS = {".db", ".sqlite", ".sqlite3", ".parquet"}
PROTECTED_PATH_PARTS = {"/data/", "/reports/", "/seed_"}
CODE_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".html", ".css"}


def check_destructive(data):
    """代码文件（.py 等）豁免路径模式检查，只拦数据文件"""
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return None
    _, ext = os.path.splitext(file_path)
    ext_lower = ext.lower()
    if ext_lower in PROTECTED_EXTENSIONS:
        return f"门卫拦截：禁止直接写入数据文件 [{os.path.basename(file_path)}]。G-003 铁律。"
    if ext_lower in CODE_EXTENSIONS:
        return None  # 代码文件不受路径模式限制
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
    # ── Shell 删除 ──
    (r"\brm\s+(-[a-zA-Z]*f|-[a-zA-Z]*r|--force|--recursive)", "rm 删除文件"),
    (r"\brm\s+", "rm 删除文件"),
    (r"\bunlink\s+", "unlink 删除文件"),
    # ── Python 删除/覆盖 ──
    (r"os\.remove\s*\(", "os.remove 删除文件"),
    (r"os\.unlink\s*\(", "os.unlink 删除文件"),
    (r"shutil\.rmtree\s*\(", "shutil.rmtree 删除目录树"),
    (r"pathlib.*\.unlink\s*\(", "pathlib.unlink 删除文件"),
    (r"Path\(.*\)\.unlink", "Path.unlink 删除文件"),
    (r"send2trash", "send2trash 删除文件"),
    # ── Python 移动（等效绕过删除） ──
    (r"shutil\.move\s*\(", "shutil.move 移动文件（等效删除）"),
    (r"os\.rename\s*\(", "os.rename 移动文件（等效删除）"),
    (r"shutil\.copy\s*\(.*,\s*/tmp", "shutil.copy到/tmp（疑似转移删除）"),
    # ── Shell 截断/覆盖 ──
    (r"\btruncate\b", "truncate 截断文件"),
    (r">\s*/(?!dev/null)", "重定向截断文件"),  # > /path（排除 > /dev/null）
    (r">\s*~/", "重定向截断 home 文件"),
    (r"cp\s+/dev/null\s+", "cp /dev/null 清空文件"),
    (r"dd\s+.*of=", "dd 覆盖文件"),
    # ── Perl/其他语言删除 ──
    (r"perl\s.*\bunlink\b", "perl unlink 删除文件"),
    (r"ruby\s.*File\.delete", "ruby File.delete 删除文件"),
    # ── 进程终止 ──
    (r"\bkill\s+(-9|-KILL|[0-9])", "kill 终止进程"),
    (r"\bkillall\s+", "killall 终止进程"),
    # ── Git 破坏性 ──
    (r"\bgit\s+push\s+.*--force", "git push --force"),
    (r"\bgit\s+push\s+-f\b", "git push -f"),
    (r"\bgit\s+reset\s+--hard", "git reset --hard"),
    (r"\bgit\s+checkout\s+--\s", "git checkout -- 丢弃修改"),
    (r"\bgit\s+clean\s+-f", "git clean -f 删除未跟踪文件"),
    (r"\bgit\s+branch\s+-D\b", "git branch -D 强制删分支"),
    # ── 静默删除 ──
    (r">\s*/dev/null\s*2>&1.*&&\s*rm", "静默删除"),
]


SAFE_RM_PATHS = {"/tmp/", "/tmp ", "/private/tmp/", "/private/tmp ", "/var/tmp/", "/var/tmp ", "cd /tmp"}


DELETE_WHITELIST_PATH = os.path.expanduser("~/.claude/merit_delete_whitelist.json")


def check_delete_whitelist(cmd):
    """检查 rm 目标文件是否在预申报白名单中，匹配则放行并移除"""
    if not os.path.exists(DELETE_WHITELIST_PATH):
        return False
    try:
        with open(DELETE_WHITELIST_PATH) as f:
            data = json.load(f)
        whitelist = data.get("files", [])
        if not whitelist:
            os.remove(DELETE_WHITELIST_PATH)
            return False

        # 检查命令中是否包含白名单里的文件
        matched = [f for f in whitelist if f in cmd]
        if not matched:
            return False

        # 从白名单移除已匹配的文件
        remaining = [f for f in whitelist if f not in matched]
        if remaining:
            data["files"] = remaining
            with open(DELETE_WHITELIST_PATH, "w") as f:
                json.dump(data, f, ensure_ascii=False)
        else:
            # 白名单空了，自动锁回
            os.remove(DELETE_WHITELIST_PATH)

        return True
    except Exception:
        return False


def check_bash_destructive(cmd):
    """检查 Bash 命令是否包含破坏性操作。预申报白名单放行。"""
    if not cmd:
        return None
    for pattern, desc in DANGEROUS_COMMANDS:
        if re.search(pattern, cmd):
            # 所有删除操作在 /tmp/ 下豁免
            if "删除" in desc or "截断" in desc or "清空" in desc or "覆盖" in desc or "移动" in desc:
                if any(safe in cmd for safe in SAFE_RM_PATHS):
                    return None
                # tmp_/test_ 开头的一次性脚本豁免删除
                import re as _re
                tmp_match = _re.search(r'(?:tmp_|test_)\S+', cmd)
                if tmp_match and ("删除" in desc or "移动" in desc):
                    return None
            # 检查预申报白名单
            if check_delete_whitelist(cmd):
                return None  # 在白名单中，放行
            return (
                f"门卫拦截：Bash 命令包含破坏性操作 [{desc}]。G-003 铁律。"
                f"先用 credit_manager.py declare-delete 预申报要删的文件。"
            )
    return None


# ══════════════════════════════════════════════════════
#  v6: Haiku 队长已移到 merit_judge.py（Stop hook 异步）
#  石卫（PreToolUse）不再调任何 API，纯硬规则。
# ══════════════════════════════════════════════════════


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

    # Bash：执行前拍快照（PostToolUse 审计用）
    if tool_name == "Bash":
        try:
            from merit_post_audit import take_snapshot
            take_snapshot()
        except Exception:
            pass
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

    # ── 石卫到此结束 ────────────────────────
    # v6: 石卫只做硬规则 if/else，毫秒级，永不超时。
    # Haiku 评分已移到 merit_judge.py（Stop hook 异步），不阻塞操作。
    # 硬规则全部通过 → 放行（不输出 = 默认放行）


if __name__ == "__main__":
    main()
