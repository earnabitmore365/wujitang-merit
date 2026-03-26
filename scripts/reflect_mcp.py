#!/usr/bin/env python3
"""
Reflect MCP Server — 自我改进工具
提供 reflect_scan / reflect_status / reflect_rules / clear_pending 四个工具。
Claude 自动判断何时调用。

注册方式（settings.json mcpServers）:
  "reflect": {"command": "python3", "args": ["~/.claude/scripts/reflect_mcp.py"]}
"""

import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ── 路径 ──────────────────────────────────────────────────────────────
HOME = str(Path.home())
DB_PATH = os.path.join(HOME, ".claude", "conversations.db")
LEARNINGS_PATH = os.path.join(HOME, ".claude", "learnings", "LEARNINGS.md")
LEARNINGS_ARCHIVE_PATH = os.path.join(HOME, ".claude", "learnings", "LEARNINGS_ARCHIVE.md")
GLOBAL_RULES_PATH = os.path.join(
    HOME, ".claude", "projects", "-Users-allenbot", "memory", "rules.md"
)
AT_RULES_PATH = os.path.join(
    HOME, ".claude", "projects", "-Users-allenbot-project-auto-trading", "memory", "rules.md"
)

mcp = FastMCP("reflect")


def _get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
def reflect_scan(hours: int = 8) -> str:
    """扫描最近对话中的纠错和提升信号。
    从 conversations.db 提取带有「纠错」「提升」标签的消息，
    以及最近 N 小时内老板（无极）的所有发言（用于捕捉隐性信号）。

    Args:
        hours: 扫描最近多少小时的对话，默认 8 小时

    Returns:
        结构化的信号列表，供分析和写入 LEARNINGS.md
    """
    conn = _get_db()

    # 1. 带标签的纠错/提升消息（最近 50 条）
    tagged = conn.execute(
        "SELECT time, speaker, content, tags FROM messages "
        "WHERE tags LIKE '%纠错%' OR tags LIKE '%提升%' "
        "ORDER BY id DESC LIMIT 50"
    ).fetchall()

    # 2. 最近 N 小时老板的全部发言（捕捉隐性信号）
    since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    recent_boss = conn.execute(
        "SELECT time, speaker, content FROM messages "
        "WHERE time >= ? AND speaker = '无极' ORDER BY id",
        (since,),
    ).fetchall()

    conn.close()

    lines = []
    lines.append(f"## 纠错/提升标签消息（最近50条）\n")
    if tagged:
        for r in tagged:
            lines.append(f"[{r['time']}] {r['speaker']} [{r['tags']}]: {r['content'][:300]}")
    else:
        lines.append("（无标签消息）")

    lines.append(f"\n## 老板最近 {hours} 小时发言\n")
    if recent_boss:
        for r in recent_boss:
            lines.append(f"[{r['time']}] {r['content'][:200]}")
    else:
        lines.append("（无发言）")

    return "\n".join(lines)


@mcp.tool()
def reflect_status() -> str:
    """查看当前 LEARNINGS.md 状态：pending 条目数、升级候选、以及最近新增的学习点。

    Returns:
        LEARNINGS.md 的摘要信息
    """
    if not os.path.exists(LEARNINGS_PATH):
        return "LEARNINGS.md 不存在"

    with open(LEARNINGS_PATH, "r") as f:
        content = f.read()

    entries = re.split(r"(?=## LRN-)", content)
    entries = [e for e in entries if e.strip() and e.strip().startswith("## LRN-")]

    pending = []
    candidates = []

    for block in entries:
        id_match = re.search(r"## (LRN-\S+)", block)
        if not id_match:
            continue
        entry_id = id_match.group(1)

        type_match = re.search(r"\*\*类型\*\*：(\S+)", block)
        n_match = re.search(r"\*\*出现次数\*\*：(\d+)", block)
        lesson_match = re.search(r"\*\*教训\*\*：(.+)", block)

        entry_type = type_match.group(1) if type_match else "未知"
        count = int(n_match.group(1)) if n_match else 0
        lesson = lesson_match.group(1).strip()[:100] if lesson_match else ""

        pending.append({"id": entry_id, "type": entry_type, "count": count, "lesson": lesson})

        # 升级条件：纠错1次即升 / 其他3次
        if (entry_type == "纠错" and count >= 1) or count >= 3:
            candidates.append({"id": entry_id, "type": entry_type, "count": count, "lesson": lesson})

    lines = [f"## LEARNINGS.md 状态\n"]
    lines.append(f"- Pending 条目: **{len(pending)}** 条")
    lines.append(f"- 升级候选: **{len(candidates)}** 条")

    if candidates:
        lines.append(f"\n### 升级候选（纠错1次/提升3次即升级到 rules.md）\n")
        for c in candidates:
            lines.append(f"- {c['id']} [{c['type']}] 出现 {c['count']} 次: {c['lesson']}")

    if pending:
        lines.append(f"\n### 全部 pending 条目\n")
        for p in pending:
            lines.append(f"- {p['id']} [{p['type']}] ×{p['count']}: {p['lesson']}")

    return "\n".join(lines)


@mcp.tool()
def reflect_rules(project: str = "global") -> str:
    """查看当前已毕业的行为规范（rules.md）。

    Args:
        project: 查哪个项目的 rules，"global" 或 "auto-trading"

    Returns:
        rules.md 的完整内容
    """
    path = AT_RULES_PATH if project == "auto-trading" else GLOBAL_RULES_PATH

    if not os.path.exists(path):
        return f"rules.md 不存在: {path}"

    with open(path, "r") as f:
        content = f.read()

    # 统计规则数
    rule_count = len(re.findall(r"^## RUL-", content, re.MULTILINE))

    return f"## {project} rules.md（{rule_count} 条规则）\n\n{content}"


FLAG_PATH = os.path.join(HOME, ".claude", "learnings", "pending_signals.json")


@mcp.tool()
def clear_pending() -> str:
    """清除 reflect 待处理信号标记。执行完 /reflect 后调用此工具，
    将 last_reflect 推进到当前时间，pending_count 清零。

    Returns:
        清除结果
    """
    import json

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(FLAG_PATH), exist_ok=True)
    with open(FLAG_PATH, "w") as f:
        json.dump(
            {
                "last_reflect": now,
                "last_scan": now,
                "pending_count": 0,
                "message": "无待处理信号",
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return f"✅ 已清除待处理信号，last_reflect 更新为 {now}"


if __name__ == "__main__":
    mcp.run()
