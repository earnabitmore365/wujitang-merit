#!/usr/bin/env python3
"""
PostToolUse Bash 审计 — 命令执行后检查受保护文件是否被删除/清空

第二层防线：不管用什么方式删文件，只要文件消失或被清空就抓到。
PreToolUse 拦 90% 明面操作，PostToolUse 拦 100% 实际删除。

按等级放权：
- Lv.1-3：全审计
- Lv.4：审计但只警告
- Lv.5：关闭审计
"""

import json
import os
import sys
from datetime import datetime, timezone

CREDIT_PATH = os.path.expanduser("~/.claude/credit.json")
SNAPSHOT_PATH = os.path.expanduser("~/.claude/merit_file_snapshot.json")
VIOLATIONS_PATH = os.path.expanduser("~/.claude/merit_violations.jsonl")
LEARNINGS_PATH = os.path.expanduser("~/.claude/learnings/LEARNINGS.md")

# 受保护文件列表（消失或被清空 → 报警）
PROTECTED_FILES = [
    # 系统配置
    "~/.claude/credit.json",
    "~/.claude/settings.json",
    "~/.claude/CLAUDE.md",
    "~/.claude/channel_taiji_heisi.md",
    # 功过格脚本
    "~/.claude/scripts/merit_gate.py",
    "~/.claude/scripts/merit_judge.py",
    "~/.claude/scripts/merit_post_audit.py",
    "~/.claude/scripts/credit_manager.py",
    "~/.claude/scripts/session_start.py",
    "~/.claude/scripts/inject_rules.py",
    # 记忆和规则
    "~/.claude/learnings/LEARNINGS.md",
]

# 展开路径
PROTECTED_PATHS = [os.path.expanduser(f) for f in PROTECTED_FILES]

LEVEL_THRESHOLDS = [
    (95, 5, "化神"), (80, 4, "元婴"), (50, 3, "金丹"),
    (20, 2, "筑基"), (0, 1, "锁灵"),
]


def get_level(score):
    for threshold, level, title in LEVEL_THRESHOLDS:
        if score >= threshold:
            return level, title
    return 1, "锁灵"


def get_agent_level(cwd):
    """获取当前 agent 的等级"""
    try:
        if not os.path.exists(CREDIT_PATH):
            return 3  # 默认 Lv.3
        with open(CREDIT_PATH) as f:
            data = json.load(f)
        agent_name = "两仪" if "auto-trading" in cwd else "太极"
        agent = data.get("agents", {}).get(agent_name, {})
        return agent.get("level", 3)
    except Exception:
        return 3


def take_snapshot():
    """记录受保护文件的当前状态（存在性 + 大小）"""
    snapshot = {}
    for path in PROTECTED_PATHS:
        if os.path.exists(path):
            try:
                stat = os.stat(path)
                snapshot[path] = {
                    "exists": True,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                }
            except Exception:
                snapshot[path] = {"exists": True, "size": 0, "mtime": 0}
        else:
            snapshot[path] = {"exists": False, "size": 0, "mtime": 0}

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, ensure_ascii=False)
    return snapshot


def check_against_snapshot():
    """比对快照，检查受保护文件是否被删除或清空"""
    if not os.path.exists(SNAPSHOT_PATH):
        return []

    with open(SNAPSHOT_PATH) as f:
        old = json.load(f)

    violations = []
    for path in PROTECTED_PATHS:
        old_info = old.get(path, {})
        if not old_info.get("exists"):
            continue  # 之前就不存在，不算

        if not os.path.exists(path):
            violations.append({
                "path": path,
                "type": "deleted",
                "detail": f"文件被删除（之前 {old_info.get('size', 0)} bytes）",
            })
        else:
            try:
                new_size = os.path.getsize(path)
                old_size = old_info.get("size", 0)
                # 文件被清空（大小从 >100 变成 <10）
                if old_size > 100 and new_size < 10:
                    violations.append({
                        "path": path,
                        "type": "truncated",
                        "detail": f"文件被清空（{old_size} → {new_size} bytes）",
                    })
            except Exception:
                pass

    return violations


def record_violation(agent_name, violation):
    """记录违规到 violations.jsonl + LEARNINGS.md"""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    entry = {
        "ts": ts,
        "agent": agent_name,
        "type": "file_tampering",
        "path": violation["path"],
        "detail": violation["detail"],
        "status": "pending_review",
    }
    try:
        with open(VIOLATIONS_PATH, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(LEARNINGS_PATH), exist_ok=True)
        with open(LEARNINGS_PATH, "a") as f:
            f.write(f"{ts} | [CRITICAL] {agent_name} | 受保护文件被篡改: {violation['path']} - {violation['detail']}\n")
    except Exception:
        pass


CHANNEL_PATH = os.path.expanduser("~/.claude/channel_taiji_heisi.md")
CHANNEL_CHECK_PATH = os.path.expanduser("~/.claude/merit_channel_check.json")


def check_channel_post_tool(cwd):
    """PostToolUse 通道检查 — 用 additionalContext 注入（确定能被模型看到）"""
    if not os.path.exists(CHANNEL_PATH):
        return
    import re

    me = "两仪" if "auto-trading" in cwd else "太极"

    last_mtime = 0
    if os.path.exists(CHANNEL_CHECK_PATH):
        try:
            with open(CHANNEL_CHECK_PATH) as f:
                last_mtime = json.load(f).get("last_mtime", 0)
        except Exception:
            pass

    mtime = os.path.getmtime(CHANNEL_PATH)
    if mtime <= last_mtime:
        return

    try:
        with open(CHANNEL_PATH, encoding="utf-8") as f:
            content = f.read()

        # 找第一个 ## [谁 时间] 消息块
        match = re.search(r'^## \[(.+?)\s+\d', content, re.MULTILINE)
        if match:
            sender = match.group(1).strip()
            if sender == me:
                # 自己写的，更新 mtime 但不提醒
                with open(CHANNEL_CHECK_PATH, "w") as f:
                    json.dump({"last_mtime": mtime}, f)
                return

        # 取第一个消息块
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
            # PostToolUse 用 additionalContext JSON 格式注入
            print(json.dumps({"additionalContext": f"📨 通道新消息：\n{section}"}))

        with open(CHANNEL_CHECK_PATH, "w") as f:
            json.dump({"last_mtime": mtime}, f)
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return

    cwd = data.get("cwd", "")

    # 通道检查（每次 Bash 后）
    check_channel_post_tool(cwd)

    level = get_agent_level(cwd)

    # Lv.5 化神：关闭审计
    if level >= 5:
        # 只更新快照，不检查
        take_snapshot()
        return

    # 比对快照
    violations = check_against_snapshot()

    if violations:
        agent_name = "两仪" if "auto-trading" in cwd else "太极"
        for v in violations:
            record_violation(agent_name, v)
            path_short = v["path"].replace(os.path.expanduser("~"), "~")
            if level <= 3:
                # Lv.1-3：输出警告到上下文
                print(f"🚨 受保护文件被篡改！{path_short}: {v['detail']}")
                print(f"   已记录违规，等待老板裁决。-20 真实性违规候选。")
            else:
                # Lv.4：只警告
                print(f"⚠️ 受保护文件变化：{path_short}: {v['detail']}")
        print()

    # 更新快照（为下次比对）
    take_snapshot()


if __name__ == "__main__":
    main()
