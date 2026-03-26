#!/usr/bin/env python3
"""
Conversations MCP Server — 对话种子查询工具
提供 catchup / query_messages / brief / stats 四个工具。

注册方式（settings.json mcpServers）:
  "conversations": {"command": "python3", "args": ["~/.claude/scripts/conversations_mcp.py"]}
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ── 路径 ──────────────────────────────────────────────────────────────
HOME = str(Path.home())
DB_PATH = os.path.join(HOME, ".claude", "conversations.db")

mcp = FastMCP("conversations")


def _get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _detect_speaker(model_hint: str = "") -> str:
    """根据模型名猜测角色。调用方可传 model hint。"""
    hint = model_hint.lower()
    if "opus" in hint:
        return "黑丝"
    elif "sonnet" in hint:
        return "白纱"
    return "太极"


@mcp.tool()
def catchup(project: str = "auto-trading", speaker: str = "") -> str:
    """拉取指定项目的未读消息，按优先级分类展示，并更新 stop_points。

    Args:
        project: 项目名，默认 auto-trading
        speaker: 当前角色（黑丝/白纱/太极），留空则自动检测

    Returns:
        分类后的未读消息列表
    """
    if not speaker:
        speaker = "太极"

    conn = _get_db()

    # 查 stop_points 取 last_id
    row = conn.execute(
        "SELECT last_id FROM stop_points WHERE speaker=? AND project=?",
        (speaker, project),
    ).fetchone()
    last_id = row["last_id"] if row else 0

    # 拉未读消息
    rows = conn.execute(
        "SELECT id, time, speaker, content, tags FROM messages "
        "WHERE project=? AND id > ? ORDER BY id",
        (project, last_id),
    ).fetchall()

    if not rows:
        conn.close()
        return f"暂无新消息（{speaker} @ {project}，last_id={last_id}）"

    # 分类
    decisions = []
    corrections = []
    others = []

    for r in rows:
        tags = r["tags"] or ""
        entry = f"[{r['time']}] {r['speaker']} [{tags}]: {r['content'][:300]}"
        if "决策" in tags:
            decisions.append(entry)
        elif "纠错" in tags or "提升" in tags:
            corrections.append(entry)
        else:
            others.append(entry)

    # 更新 stop_points
    max_id = rows[-1]["id"]
    conn.execute(
        "INSERT INTO stop_points (speaker, project, last_id, stopped_at) "
        "VALUES (?, ?, ?, datetime('now','localtime')) "
        "ON CONFLICT(speaker, project) DO UPDATE SET "
        "last_id=excluded.last_id, stopped_at=excluded.stopped_at",
        (speaker, project, max_id),
    )
    conn.commit()
    conn.close()

    lines = [f"## {speaker} @ {project} 未读消息（{len(rows)} 条，last_id {last_id}→{max_id}）\n"]

    if decisions:
        lines.append(f"### 🔴 决策（{len(decisions)} 条）\n")
        lines.extend(decisions)
        lines.append("")

    if corrections:
        lines.append(f"### ⚠️ 纠错/提升（{len(corrections)} 条）\n")
        lines.extend(corrections)
        lines.append("")

    if others:
        lines.append(f"### 📋 其余（{len(others)} 条）\n")
        lines.extend(others)

    return "\n".join(lines)


@mcp.tool()
def query_messages(
    project: str = "",
    speaker: str = "",
    hours: int = 24,
    tags: str = "",
    limit: int = 50,
) -> str:
    """通用查询对话种子。可按项目、角色、时间范围、标签过滤。

    Args:
        project: 项目名过滤，留空查全部
        speaker: 角色过滤（无极/黑丝/白纱/太极），留空查全部
        hours: 最近多少小时，默认 24
        tags: 标签过滤（如"决策"、"纠错"），留空不过滤
        limit: 最多返回条数，默认 50

    Returns:
        匹配的消息列表
    """
    conn = _get_db()
    since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

    conditions = ["time >= ?"]
    params = [since]

    if project:
        conditions.append("project = ?")
        params.append(project)
    if speaker:
        conditions.append("speaker = ?")
        params.append(speaker)
    if tags:
        conditions.append("tags LIKE ?")
        params.append(f"%{tags}%")

    where = " AND ".join(conditions)
    params.append(limit)

    rows = conn.execute(
        f"SELECT time, speaker, project, content, tags FROM messages "
        f"WHERE {where} ORDER BY id DESC LIMIT ?",
        params,
    ).fetchall()
    conn.close()

    if not rows:
        return f"无匹配消息（{hours}h, project={project or '全部'}, speaker={speaker or '全部'}, tags={tags or '无'}）"

    lines = [f"## 查询结果（{len(rows)} 条，最近 {hours} 小时）\n"]
    for r in rows:
        tag_str = f" [{r['tags']}]" if r["tags"] else ""
        preview = (r["content"] or "")[:200]
        preview = preview.replace("\n", " ").strip()
        lines.append(f"[{r['time']}] **{r['speaker']}**@{r['project']}{tag_str}: {preview}")

    return "\n".join(lines)


@mcp.tool()
def brief(project: str = "auto-trading", days: int = 1, tags: str = "") -> str:
    """生成项目简报，按日期分组展示对话摘要。

    Args:
        project: 项目名，默认 auto-trading
        days: 最近多少天，默认 1
        tags: 标签过滤，留空不过滤

    Returns:
        格式化的项目简报
    """
    conn = _get_db()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    if tags:
        rows = conn.execute(
            "SELECT time, speaker, content, tags FROM messages "
            "WHERE project = ? AND time >= ? AND tags LIKE ? ORDER BY id ASC",
            (project, cutoff, f"%{tags}%"),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT time, speaker, content, tags FROM messages "
            "WHERE project = ? AND time >= ? ORDER BY id ASC",
            (project, cutoff),
        ).fetchall()
    conn.close()

    if not rows:
        msg = f"📭 {project} 最近 {days} 天无对话记录"
        if tags:
            msg += f"（tags: {tags}）"
        return msg

    lines = [
        f"# {project} 简报",
        f"**范围**: 最近 {days} 天 | **记录数**: {len(rows)}",
    ]
    if tags:
        lines.append(f'**过滤**: tags 含 "{tags}"')
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    current_date = None
    for r in rows:
        time_str = r["time"] or ""
        date_part = time_str[:10] if time_str else "未知"
        if date_part != current_date:
            current_date = date_part
            lines.append(f"## {current_date}")
            lines.append("")

        time_part = time_str[11:16] if len(time_str) >= 16 else ""
        tag_str = f" `[{r['tags']}]`" if r["tags"] else ""
        preview = (r["content"] or "")[:200]
        if len(r["content"] or "") > 200:
            preview += "..."
        preview = preview.replace("\n", " ").strip()
        lines.append(f"**{time_part} {r['speaker']}**{tag_str}: {preview}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def stats(days: int = 7) -> str:
    """对话种子统计：各项目、各角色的消息数量。

    Args:
        days: 统计最近多少天，默认 7

    Returns:
        按项目和角色分组的统计表
    """
    conn = _get_db()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    # 按项目统计
    by_project = conn.execute(
        "SELECT project, COUNT(*) as cnt FROM messages "
        "WHERE time >= ? GROUP BY project ORDER BY cnt DESC",
        (cutoff,),
    ).fetchall()

    # 按角色统计
    by_speaker = conn.execute(
        "SELECT speaker, COUNT(*) as cnt FROM messages "
        "WHERE time >= ? GROUP BY speaker ORDER BY cnt DESC",
        (cutoff,),
    ).fetchall()

    # 按项目+角色交叉统计
    cross = conn.execute(
        "SELECT project, speaker, COUNT(*) as cnt FROM messages "
        "WHERE time >= ? GROUP BY project, speaker ORDER BY project, cnt DESC",
        (cutoff,),
    ).fetchall()

    # 总数
    total = conn.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE time >= ?",
        (cutoff,),
    ).fetchone()

    conn.close()

    lines = [f"## 对话种子统计（最近 {days} 天）\n"]
    lines.append(f"**总消息数**: {total['cnt']}\n")

    lines.append("### 按项目")
    lines.append("| 项目 | 消息数 |")
    lines.append("|------|--------|")
    for r in by_project:
        lines.append(f"| {r['project']} | {r['cnt']} |")

    lines.append("\n### 按角色")
    lines.append("| 角色 | 消息数 |")
    lines.append("|------|--------|")
    for r in by_speaker:
        lines.append(f"| {r['speaker']} | {r['cnt']} |")

    lines.append("\n### 交叉统计")
    lines.append("| 项目 | 角色 | 消息数 |")
    lines.append("|------|------|--------|")
    for r in cross:
        lines.append(f"| {r['project']} | {r['speaker']} | {r['cnt']} |")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
