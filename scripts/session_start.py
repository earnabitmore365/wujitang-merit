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
    """绝对路径 → projects 目录下的实际目录名（处理 Claude 的 _→- 编码）"""
    projects_base = os.path.expanduser('~/.claude/projects')
    encoded = cwd.replace('/', '-')
    if os.path.isdir(os.path.join(projects_base, encoded)):
        return encoded
    # Claude 的编码也会把 _ 替换成 -
    alt = encoded.replace('_', '-')
    if os.path.isdir(os.path.join(projects_base, alt)):
        return alt
    return encoded


def inject_evolver_notifications():
    """读取 evolver cycle 通知并输出，读完后清空"""
    notif_path = os.path.expanduser('~/.claude/evolver/cycle_notifications.jsonl')
    if not os.path.exists(notif_path):
        return
    try:
        with open(notif_path) as f:
            lines = f.readlines()
        if not lines:
            return

        out = []
        out.append("╔══════════════════════════════════════════╗")
        out.append("║  Evolver 新 Cycle 通知")
        out.append("╚══════════════════════════════════════════╝")
        out.append("")

        for line in lines[-10:]:  # 最多显示最近 10 条
            line = line.strip()
            if not line:
                continue
            try:
                n = json.loads(line)
                status_icon = '✅' if n.get('status') == 'success' else '❌'
                out.append(
                    f"{status_icon} [{n.get('ts','?')[:16]}] "
                    f"{n.get('source','?')} | "
                    f"gene: {n.get('gene','?')} | "
                    f"scope: {n.get('scope','?').strip()} | "
                    f"{n.get('run','?')}"
                )
            except json.JSONDecodeError:
                out.append(f"  {line}")

        out.append("")
        print('\n'.join(out))

        # 清空已读通知
        with open(notif_path, 'w') as f:
            f.write('')
    except Exception as e:
        print(f"[evolver 通知读取失败: {e}]")


def inject_reflect_pending():
    """读取 pending_signals.json，有未处理信号就提醒执行 /reflect"""
    flag_path = os.path.expanduser('~/.claude/learnings/pending_signals.json')
    if not os.path.exists(flag_path):
        return
    try:
        with open(flag_path) as f:
            data = json.load(f)
        pending = data.get('pending_count', data.get('new_signals', 0))
        if pending > 0:
            last_reflect = data.get('last_reflect', data.get('last_check', '未知'))
            print(f"⚠️ 有 {pending} 条纠错/提升信号待处理（自 {last_reflect} 起），建议执行 /reflect")
            print("")
    except Exception:
        pass


def inject_compact_context(cwd):
    """注入 PreCompact hook 保存的上下文快照，注入后删除"""
    projects_base = os.path.expanduser('~/.claude/projects')
    # 处理下划线→连字符的编码差异
    project_encoded = cwd.replace('/', '-')
    project_dir = os.path.join(projects_base, project_encoded)
    if not os.path.isdir(project_dir):
        project_dir = os.path.join(projects_base, project_encoded.replace('_', '-'))
    context_path = os.path.join(project_dir, 'compact_context.md')
    if not os.path.exists(context_path):
        return
    try:
        with open(context_path, encoding='utf-8') as f:
            content = f.read()
        if content.strip():
            print("【PreCompact 上下文快照】")
            print(content)
            print("")
        # 注入后删除（一次性）
        os.remove(context_path)
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    source = data.get('source', '')
    cwd = data.get('cwd', os.getcwd())

    home = os.path.expanduser('~')

    # 所有会话启动都检查 evolver 通知（不限 compact）
    inject_evolver_notifications()

    # 所有会话启动都检查 reflect 待处理信号（不限 compact）
    inject_reflect_pending()

    # 所有会话启动都检查 PreCompact 上下文快照
    inject_compact_context(cwd)

    # 非压缩来源：只注入 evolver 通知 + reflect 提醒 + compact 快照，不做完整压缩注入
    if source != 'compact':
        sys.exit(0)

    # home 目录：compact 快照已注入，不需要完整压缩注入
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
    # 兼容新旧两种项目名格式（短名如 'auto-trading' / 全名如 '-Users-allenbot-project-auto-trading'）
    try:
        conn = sqlite3.connect(DB_PATH)

        # 找上次压缩点（[压缩点] 标记），两种项目名都查
        row = conn.execute(
            "SELECT id FROM messages WHERE speaker='系统' AND content LIKE '[压缩点]%' "
            "AND project IN (?, ?) ORDER BY id DESC LIMIT 1",
            (project, project_encoded)
        ).fetchone()
        since_id = row[0] if row else 0

        rows = conn.execute(
            'SELECT time, speaker, content FROM messages '
            'WHERE id > ? AND project IN (?, ?) ORDER BY id DESC LIMIT 30',
            (since_id, project, project_encoded)
        ).fetchall()
        rows = list(reversed(rows))

        if rows:
            out.append(f"【上次压缩后的对话（最新 {len(rows)} 条）】")
        else:
            # fallback：最近 30 条
            rows = conn.execute(
                'SELECT time, speaker, content FROM messages '
                'WHERE project IN (?, ?) ORDER BY id DESC LIMIT 30',
                (project, project_encoded)
            ).fetchall()
            rows = list(reversed(rows))
            out.append(f"【最近对话（最新 {len(rows)} 条）】")

        for r in rows:
            preview = r[2][:500].replace('\n', ' ')
            out.append(f"[{r[0]}] {r[1]}: {preview}")

        conn.close()
    except Exception as e:
        out.append(f"[对话种子读取失败: {e}]")

    out.append("")

    # ── 4. 读 MEMORY.md（前120行）──────────────────────────
    memory_path = os.path.expanduser(
        f'~/.claude/projects/{project_encoded}/memory/MEMORY.md'
    )
    if os.path.exists(memory_path):
        try:
            with open(memory_path) as f:
                lines = f.readlines()
            out.append("【MEMORY（前120行）】")
            out.append(''.join(lines[:120]).rstrip())
        except Exception:
            pass
        out.append("")

    # ── 6. Evolver 通知（项目也能看到）──────────────────────
    inject_evolver_notifications()

    print('\n'.join(out))


if __name__ == '__main__':
    main()
