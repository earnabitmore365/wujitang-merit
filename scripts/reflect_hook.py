#!/usr/bin/env python3
"""
Reflect Hook — SessionEnd 自动扫描
统计上次 /reflect 执行后新增的纠错/提升信号数量。
写标记文件 pending_signals.json，session_start.py 读取后提醒。

关键设计：last_reflect 只有执行 /reflect（通过 clear_pending MCP 工具）后才推进。
SessionEnd 多次扫描不会丢信号。
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

HOME = str(Path.home())
DB_PATH = os.path.join(HOME, ".claude", "conversations.db")
FLAG_PATH = os.path.join(HOME, ".claude", "learnings", "pending_signals.json")


def main():
    # 读取上次 /reflect 执行时间（只有 clear_pending 才会更新这个值）
    last_reflect = "2000-01-01 00:00:00"
    if os.path.exists(FLAG_PATH):
        try:
            with open(FLAG_PATH) as f:
                data = json.load(f)
                # 向后兼容：旧版用 last_check，新版用 last_reflect
                last_reflect = data.get("last_reflect", data.get("last_check", last_reflect))
        except Exception:
            pass

    # 查询 last_reflect 之后的所有纠错/提升信号（不是增量，是全量未处理）
    conn = sqlite3.connect(DB_PATH, timeout=10)
    row = conn.execute(
        "SELECT COUNT(*) FROM messages "
        "WHERE (tags LIKE '%纠错%' OR tags LIKE '%提升%') AND time > ?",
        (last_reflect,),
    ).fetchone()
    pending_count = row[0] if row else 0
    conn.close()

    # 写标记（不推进 last_reflect）
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(FLAG_PATH), exist_ok=True)
    with open(FLAG_PATH, "w") as f:
        json.dump(
            {
                "last_reflect": last_reflect,
                "last_scan": now,
                "pending_count": pending_count,
                "message": f"{pending_count} 条未处理的纠错/提升信号" if pending_count > 0 else "无待处理信号",
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    if pending_count > 0:
        print(f"[reflect_hook] {pending_count} 条纠错/提升信号待处理（自 {last_reflect} 起）")


if __name__ == "__main__":
    main()
