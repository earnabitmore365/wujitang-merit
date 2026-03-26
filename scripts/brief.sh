#!/bin/bash
# 通讯部 — 项目简报生成器
# 用法：
#   brief.sh <project> [--days N] [--tags TAG]
#   brief.sh auto-trading --days 3
#   brief.sh auto-trading --days 1 --tags 决策
#
# 从 conversations.db 提取指定项目的对话摘要，复制到剪贴板

DB="$HOME/.claude/conversations.db"
PROJECT=""
DAYS=1
TAGS=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        --days) DAYS="$2"; shift 2 ;;
        --tags) TAGS="$2"; shift 2 ;;
        *) PROJECT="$1"; shift ;;
    esac
done

if [ -z "$PROJECT" ]; then
    echo "用法: brief.sh <project> [--days N] [--tags TAG]"
    echo "  例: brief.sh auto-trading --days 3"
    echo "  例: brief.sh auto-trading --days 1 --tags 决策"
    exit 1
fi

if [ ! -f "$DB" ]; then
    echo "❌ 数据库不存在: $DB"
    exit 1
fi

# 用 python3 参数化查询，防 SQL 注入
BRIEF_OUTPUT=$(python3 - "$DB" "$PROJECT" "$DAYS" "$TAGS" << 'PYEOF'
import sqlite3
import sys
from datetime import datetime, timedelta

db_path, project, days_str, tags_filter = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
days = int(days_str)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 用本地时间计算截止时间（数据库存的是本地时间）
cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

if tags_filter:
    cur.execute(
        "SELECT time, speaker, content, tags FROM messages "
        "WHERE project = ? AND time >= ? AND tags LIKE ? "
        "ORDER BY id ASC",
        (project, cutoff, f"%{tags_filter}%")
    )
else:
    cur.execute(
        "SELECT time, speaker, content, tags FROM messages "
        "WHERE project = ? AND time >= ? "
        "ORDER BY id ASC",
        (project, cutoff)
    )

rows = cur.fetchall()
conn.close()

if not rows:
    msg = f"📭 {project} 最近 {days} 天无对话记录"
    if tags_filter:
        msg += f"（tags: {tags_filter}）"
    print(msg)
    sys.exit(0)

lines = []
lines.append(f"# {project} 简报")
lines.append(f"**范围**: 最近 {days} 天 | **记录数**: {len(rows)}")
if tags_filter:
    lines.append(f"**过滤**: tags 含 \"{tags_filter}\"")
lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
lines.append("")
lines.append("---")
lines.append("")

current_date = None
for time_str, speaker, content, tags in rows:
    date_part = time_str[:10] if time_str else "未知"
    if date_part != current_date:
        current_date = date_part
        lines.append(f"## {current_date}")
        lines.append("")

    time_part = time_str[11:16] if time_str and len(time_str) >= 16 else ""
    tag_str = f" `[{tags}]`" if tags else ""
    preview = content[:200] + "..." if content and len(content) > 200 else (content or "")
    preview = preview.replace("\n", " ").strip()
    lines.append(f"**{time_part} {speaker}**{tag_str}: {preview}")
    lines.append("")

print("\n".join(lines))
PYEOF
)

echo "$BRIEF_OUTPUT"

if [ -n "$BRIEF_OUTPUT" ]; then
    echo "$BRIEF_OUTPUT" | pbcopy
    echo "📋 已复制到剪贴板"
fi
