#!/usr/bin/env python3
"""
历史会话导入脚本 — 把 JSONL 会话文件批量写入 dashboard.db
"""

import json
import sqlite3
import os
import glob
from datetime import datetime, timezone

DB_PATH = os.path.expanduser('~/.claude/dashboard.db')
PROJECT_DIR = os.path.expanduser('~/.claude/projects/-Users-allenbot-project-auto-trading')


def get_speaker(msg_type, model):
    if msg_type == 'user':
        return '无极'
    if 'opus' in model:
        return '黑丝'
    if 'sonnet' in model:
        return '白纱'
    return '未知'


def extract_text(content):
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    parts.append(block.get('text', ''))
                # 跳过 thinking / tool_use / tool_result
        return '\n'.join(parts).strip()
    return ''


def parse_jsonl(filepath):
    """解析一个 JSONL 文件，返回 (time, speaker, content, session_id) 列表"""
    messages = []
    session_id = os.path.basename(filepath).replace('.jsonl', '')

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue

            msg_type = d.get('type')
            if msg_type not in ('user', 'assistant'):
                continue

            timestamp_str = d.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # 转本地时间（UTC+8）
                local_dt = dt.astimezone().replace(tzinfo=None)
                time_str = local_dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                continue

            msg = d.get('message', {})
            if msg_type == 'user':
                content = extract_text(msg.get('content', ''))
                speaker = '无极'
            else:
                model = msg.get('model', '')
                content = extract_text(msg.get('content', []))
                speaker = get_speaker('assistant', model)

            if content:
                messages.append((time_str, speaker, content, 'auto-trading', session_id))

    return messages


def main():
    # 取最新10个 JSONL
    files = sorted(
        glob.glob(os.path.join(PROJECT_DIR, '*.jsonl')),
        key=os.path.getmtime,
        reverse=True
    )[:10]

    conn = sqlite3.connect(DB_PATH)

    total = 0
    for filepath in reversed(files):  # 从旧到新写入
        filename = os.path.basename(filepath)
        messages = parse_jsonl(filepath)
        if messages:
            conn.executemany(
                'INSERT INTO messages (time, speaker, content, project, session_id) VALUES (?, ?, ?, ?, ?)',
                messages
            )
            conn.commit()
            print(f'{filename[:8]}... → {len(messages)} 条')
            total += len(messages)

    conn.close()
    print(f'\n共写入 {total} 条')


if __name__ == '__main__':
    main()
