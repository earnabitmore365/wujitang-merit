#!/usr/bin/env python3
"""
SessionStart hook — 压缩后自动注入恢复上下文
仅在 source == 'compact' 时执行，stdout 自动注入 Claude context
"""

import sys
import json
import sqlite3
import os

DB_PATH = os.path.expanduser('~/.claude/conversations.db')


def get_project(cwd):
    home = os.path.expanduser('~')
    if cwd == home:
        return None
    parts = cwd.replace(home + '/', '').split('/')
    return parts[-1] if parts else None


def get_project_encoded(cwd):
    """绝对路径 → memory 目录编码（所有 / 替换为 -）"""
    return cwd.replace('/', '-')


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    source = data.get('source', '')
    cwd = data.get('cwd', os.getcwd())

    # 只在压缩后触发
    if source != 'compact':
        sys.exit(0)

    # home 目录不注入（太极频道不对外开放）
    home = os.path.expanduser('~')
    if cwd == home:
        sys.exit(0)

    project = get_project(cwd)
    if not project:
        sys.exit(0)

    project_encoded = get_project_encoded(cwd)

    out = []
    out.append(f"╔══════════════════════════════════════════╗")
    out.append(f"║  压缩恢复注入 · 项目: {project}")
    out.append(f"╚══════════════════════════════════════════╝")
    out.append("")

    # ── 1. 读对话种子（从上次压缩点开始）──────────────────
    try:
        conn = sqlite3.connect(DB_PATH)

        # 找上次压缩点（[压缩点] 标记）
        row = conn.execute(
            "SELECT id FROM messages WHERE speaker='系统' AND content LIKE '[压缩点]%' "
            "AND project=? ORDER BY id DESC LIMIT 1",
            (project,)
        ).fetchone()
        since_id = row[0] if row else 0

        rows = conn.execute(
            'SELECT time, speaker, content FROM messages '
            'WHERE id > ? AND project=? ORDER BY id',
            (since_id, project)
        ).fetchall()

        if rows:
            out.append(f"【上次压缩后的对话（{len(rows)} 条）】")
        else:
            # fallback：最近 50 条
            rows = conn.execute(
                'SELECT time, speaker, content FROM messages '
                'WHERE project=? ORDER BY id DESC LIMIT 50',
                (project,)
            ).fetchall()
            rows = list(reversed(rows))
            out.append(f"【最近对话（最新 {len(rows)} 条）】")

        for r in rows:
            preview = r[2][:200].replace('\n', ' ')
            out.append(f"[{r[0]}] {r[1]}: {preview}")

        conn.close()
    except Exception as e:
        out.append(f"[对话种子读取失败: {e}]")

    out.append("")

    # ── 4. 读 CHECKPOINT.md（在 cwd 下）──────────────────
    checkpoint_path = os.path.join(cwd, 'CHECKPOINT.md')
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path) as f:
                lines = f.readlines()
            out.append("【CHECKPOINT 当前任务（前60行）】")
            out.append(''.join(lines[:60]).rstrip())
        except Exception:
            pass
        out.append("")

    # ── 5. 读 MEMORY.md（前60行）──────────────────────────
    memory_path = os.path.expanduser(
        f'~/.claude/projects/{project_encoded}/memory/MEMORY.md'
    )
    if os.path.exists(memory_path):
        try:
            with open(memory_path) as f:
                lines = f.readlines()
            out.append("【MEMORY（前60行）】")
            out.append(''.join(lines[:60]).rstrip())
        except Exception:
            pass
        out.append("")

    print('\n'.join(out))


if __name__ == '__main__':
    main()
