#!/usr/bin/env python3
"""
通讯部写入脚本 — 由 Claude Code Hooks 自动触发
处理 Stop 和 UserPromptSubmit 两个事件，写入 ~/.claude/conversations.db
"""

import sys
import json
import sqlite3
import os
import time
from datetime import datetime

DB_PATH = os.path.expanduser('~/.claude/conversations.db')
LOG_PATH = '/tmp/db_write.log'


def log(msg):
    """轻量调试日志，写入 /tmp/db_write.log"""
    try:
        with open(LOG_PATH, 'a') as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass

# 标签词表（8类）
TAG_WORDS = {
    '流程':   ['初考', '专考', '组考', '照妖镜', '分班', '冠军', 'gate', '门槛', '成绩单', '淘汰'],
    '技术验证': ['回测', '种子', 'wf', 'mc', 'oos', 'walk-forward', 'monte carlo', '过拟合', '翻倍率', '爆仓率'],
    '市场状态': ['regime', '牛市', '熊市', '盘整', '初牛', '初熊', '已知事实', '叠加', '子阶段', 'intrabar'],
    '数据':   ['k线', '下载', 'sqlite', '数据库', '币本位', '合约', '周期'],
    '决策词':  ['拍板', '决定', '不用', '砍掉', '保留', '就这样', '就这么定了', '做吧', '批了'],
    '协作':   ['handoff', 'checkpoint', '方案', '报告', '压缩', '恢复'],
    '纠错':   ['不要这样', '不对', '错了', '你怎么', '干什么飞机', '你老是', '又忘了',
               '我不是叫你', '你先别', '没头没尾', '敷衍', '漏东西', '自审', '你赶时间吗'],
    '提升':   ['更细心', '可以更好', '主动一点', '应该主动', '不用我问', '不用我到', '本来应该',
               '你自己应该', '还可以', '做得更好', '没想到'],
    '策略币种': ['策略', 'vpt', 'meanreversion', 'demandindex', 'cci', 'trix', 'rsi', 'macd', 'bollinger',
               'sol', 'btc', 'eth', 'bnb', 'xrp', 'ada', 'avax', 'link', 'dot', 'trx'],
}

# 决策组（用于混沌特殊标签）
DECISION_WORDS = TAG_WORDS['决策词']

# session 目录 → project 名（路径编码：去掉开头/，所有/换-）
KNOWN_PROJECTS = {
    '-Users-allenbot-project-auto-trading': 'auto-trading',
    '-Volumes-BIWIN-NV-7400-2TB-project-auto-trading': 'auto-trading',
}

# 这些目录的 session 不写入（太极、evolver headless 等）
SKIP_DIRS = {
    '-Users-allenbot',
    '-Users-allenbot--claude',
    '-private-tmp-claude-evolver',
    '-Users-allenbot--openclaw-workspace',
}


def get_tags(speaker, content):
    """根据内容匹配词表，返回逗号分隔的 tags 字符串"""
    content_lower = content.lower()
    matched = set()
    for category, words in TAG_WORDS.items():
        if category == '决策词':
            continue  # 决策词单独处理
        for word in words:
            if word.lower() in content_lower:
                matched.add(word if not word.islower() else word)
    # 混沌命中决策词 → 加"决策"标签
    if speaker == '混沌':
        for word in DECISION_WORDS:
            if word.lower() in content_lower:
                matched.add('决策')
                break
    return ','.join(sorted(matched)) if matched else ''


def get_project_from_session(session_id):
    """通过 session_id 在 ~/.claude/projects/ 里找对应目录，返回 project 名或 None（None=不写入）"""
    if not session_id:
        return None
    projects_dir = os.path.expanduser('~/.claude/projects')
    try:
        for proj_dir_name in os.listdir(projects_dir):
            proj_dir = os.path.join(projects_dir, proj_dir_name)
            if not os.path.isdir(proj_dir):
                continue
            try:
                for fname in os.listdir(proj_dir):
                    if fname.startswith(session_id) and fname.endswith('.jsonl'):
                        if proj_dir_name in SKIP_DIRS:
                            return None
                        if proj_dir_name in KNOWN_PROJECTS:
                            return KNOWN_PROJECTS[proj_dir_name]
                        # 未知项目目录：用目录名本身（fallback）
                        return proj_dir_name
            except Exception:
                continue
    except Exception:
        pass
    return None


def parse_last_assistant(transcript_path):
    """读取 JSONL 末尾，收集最后一个 turn 的所有 assistant 文字块拼接返回"""
    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
        tail = lines[-200:]

        parts = []
        speaker = None

        for line in reversed(tail):
            try:
                d = json.loads(line.strip())
                # 遇到用户消息 = 当前 turn 边界，停止收集
                if d.get('type') == 'user':
                    break
                if d.get('type') != 'assistant':
                    continue
                msg = d.get('message', {})
                model = msg.get('model', '')
                if speaker is None:
                    speaker = '黑丝' if 'opus' in model else ('白纱' if 'sonnet' in model else '未知')
                blocks = msg.get('content', [])
                text_parts = [b.get('text', '') for b in blocks
                              if isinstance(b, dict) and b.get('type') == 'text']
                text = '\n'.join(text_parts).strip()
                if text:
                    parts.append(text)
            except Exception:
                continue

        if parts:
            # reversed 收集的，反转回正序拼接
            full_text = '\n\n'.join(reversed(parts)).strip()
            return speaker or '未知', full_text
    except Exception:
        pass
    return '未知', ''


def write_message(conn, speaker, content, project, session_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tags = get_tags(speaker, content)
    cursor = conn.execute(
        'INSERT INTO messages (time, speaker, content, project, session_id, tags) VALUES (?, ?, ?, ?, ?, ?)',
        (now, speaker, content, project, session_id, tags)
    )
    conn.commit()
    return cursor.lastrowid


def upsert_stop_point(conn, speaker, project, last_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        '''INSERT INTO stop_points (speaker, project, last_id, stopped_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(speaker, project) DO UPDATE SET
               last_id=excluded.last_id,
               stopped_at=excluded.stopped_at''',
        (speaker, project, last_id, now)
    )
    conn.commit()


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    event = data.get('hook_event_name', '')
    session_id = data.get('session_id', '')

    # 通过 session_id 确定项目（精确，不依赖 cwd）
    project = get_project_from_session(session_id)
    if project is None:
        log(f'SKIP event={event} session={session_id[:8]} project=None')
        sys.exit(0)

    conn = sqlite3.connect(DB_PATH)

    if event == 'Stop':
        transcript_path = data.get('transcript_path', '')
        log(f'Stop: session={session_id[:8]} project={project} transcript={transcript_path[-50:] if transcript_path else "EMPTY"}')
        speaker, content = '未知', ''
        for attempt in range(3):
            speaker, content = parse_last_assistant(transcript_path)
            if content:
                break
            if attempt < 2:
                time.sleep(0.5)
        log(f'Stop result: speaker={speaker} content_len={len(content)}')
        if content:
            last_id = write_message(conn, speaker, content, project, session_id)
            upsert_stop_point(conn, speaker, project, last_id)
            log(f'Stop written: id={last_id}')
        else:
            log(f'Stop SKIP: content empty')

    elif event == 'UserPromptSubmit':
        content = data.get('prompt', '').strip()
        if content:
            write_message(conn, '混沌', content, project, session_id)

    elif event == 'PreCompact':
        transcript_path = data.get('transcript_path', '')
        speaker, content = parse_last_assistant(transcript_path)
        last_id = write_message(conn, '系统', f'[压缩点] {session_id[:8]}', project, session_id)
        if speaker and speaker not in ('未知',):
            upsert_stop_point(conn, speaker, project, last_id)

    elif event == 'SessionEnd':
        transcript_path = data.get('transcript_path', '')
        reason = data.get('reason', 'other')
        speaker, content = parse_last_assistant(transcript_path)
        last_id = write_message(conn, '系统', f'[会话结束:{reason}] {session_id[:8]}', project, session_id)
        if speaker and speaker not in ('未知',):
            upsert_stop_point(conn, speaker, project, last_id)

    conn.close()


if __name__ == '__main__':
    main()
