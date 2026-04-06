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


DAILY_BASE = os.path.expanduser('~/.claude/projects')


def _get_daily_dir(cwd):
    """按 cwd 确定当前项目的 daily 目录"""
    home = os.path.expanduser('~')
    if cwd == home or not cwd:
        return os.path.join(DAILY_BASE, '-Users-allenbot', 'memory', 'daily')
    project_encoded = cwd.replace('/', '-')
    daily_dir = os.path.join(DAILY_BASE, project_encoded, 'memory', 'daily')
    if os.path.isdir(daily_dir):
        return daily_dir
    # 尝试去掉前缀差异
    alt = os.path.join(DAILY_BASE, project_encoded.replace('_', '-'), 'memory', 'daily')
    if os.path.isdir(alt):
        return alt
    return daily_dir  # 返回标准路径（可能还没创建）


def inject_recent_memory(cwd):
    """注入最近记忆：当前项目的当天 md 尾部 + 昨天 md 尾部"""
    try:
        from datetime import date, timedelta
        daily_dir = _get_daily_dir(cwd)
        today = date.today()
        parts = []
        for delta_days in [0, 1]:
            d = today - timedelta(days=delta_days)
            md_path = os.path.join(daily_dir, f'{d.isoformat()}.md')
            if os.path.exists(md_path):
                with open(md_path, encoding='utf-8') as f:
                    lines = f.readlines()
                tail = lines[-20:] if delta_days == 0 else lines[-10:]
                if tail:
                    parts.append(f'# Recent Memory\n\n## {d.isoformat()}\n{"".join(tail)}')
        if parts:
            print('\n'.join(parts))
    except Exception:
        pass


def inject_rules(cwd):
    """注入 rules.md 的 INJECT 区域（全局+项目级）"""
    home = os.path.expanduser("~")
    project_encoded = cwd.replace("/", "-")
    project_dir = os.path.join(home, ".claude", "projects", project_encoded)
    if not os.path.isdir(project_dir):
        project_dir = os.path.join(home, ".claude", "projects", project_encoded.replace("_", "-"))

    project_rules = os.path.join(project_dir, "memory", "rules.md")
    global_rules = os.path.join(home, ".claude", "projects", "-Users-allenbot", "memory", "rules.md")

    def extract_inject(path):
        if not os.path.exists(path):
            return ""
        with open(path) as f:
            content = f.read()
        start = content.find("<!-- INJECT START -->")
        end = content.find("<!-- INJECT END -->")
        if start >= 0 and end >= 0:
            return content[start + len("<!-- INJECT START -->"):end].strip()
        return content.strip()

    parts = []
    seen = set()
    for label, path in [("全局规则", global_rules), ("项目规则", project_rules)]:
        real = os.path.realpath(path)
        if real in seen or not os.path.exists(path):
            continue
        seen.add(real)
        content = extract_inject(path)
        if content:
            parts.append(f"=== {label} ===\n{content}")

    if parts:
        print("\n---\n".join(parts))


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
    flag_path = os.path.expanduser('~/.claude/merit/learnings/pending_signals.json')
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


def inject_pending_ai_tasks():
    """检测 MiniMax 失败时存入的待处理 AI 任务队列"""
    pending_path = os.path.expanduser('~/.claude/merit/pending_ai_tasks.jsonl')
    if not os.path.exists(pending_path):
        return
    try:
        with open(pending_path) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if not lines:
            return
        print(f"⚠️ 有 {len(lines)} 个待处理的 AI 评估任务（MiniMax 当时不可用），需太极手动处理")
        for line in lines[-3:]:  # 最多显示最近 3 条
            try:
                task = json.loads(line)
                print(f"  - [{task.get('ts','?')[:16]}] {task.get('type','?')} | {task.get('agent','?')} | {task.get('context','')[:60]}")
            except Exception:
                pass
        print("")
    except Exception:
        pass


def inject_shiwei_audit_reminder(cwd):
    """检测有未审计的石卫日志（只在太极上下文）"""
    home = os.path.expanduser('~')
    if cwd != home:
        return  # 两仪不看石卫审计
    log_dir = os.path.expanduser('~/.claude/merit/shiwei_log')
    audit_dir = os.path.expanduser('~/.claude/merit/shiwei_audit')
    if not os.path.isdir(log_dir):
        return
    try:
        log_dates = {f.replace('.md', '') for f in os.listdir(log_dir) if f.endswith('.md')}
        audit_dates = set()
        if os.path.isdir(audit_dir):
            audit_dates = {f.replace('.md', '') for f in os.listdir(audit_dir) if f.endswith('.md')}
        unaudited = sorted(log_dates - audit_dates)
        if unaudited:
            print(f"📋 有 {len(unaudited)} 天未审计的石卫日志：{', '.join(unaudited[-3:])}{'...' if len(unaudited) > 3 else ''}")
            print(f"   执行 /audit-shiwei 进行审计")
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


CHANNEL_PATH = os.path.expanduser('~/.claude/channel_taiji_heisi.md')
CHANNEL_CHECK_PATH = os.path.expanduser('~/.claude/merit/channel_check.json')


def inject_channel_messages(cwd):
    """SessionStart 时检查通道新消息并注入"""
    if not os.path.exists(CHANNEL_PATH):
        return
    import re

    me = '两仪' if 'auto-trading' in cwd else '太极'

    last_mtime = 0
    if os.path.exists(CHANNEL_CHECK_PATH):
        try:
            with open(CHANNEL_CHECK_PATH) as f:
                last_mtime = json.load(f).get('last_mtime', 0)
        except Exception:
            pass

    mtime = os.path.getmtime(CHANNEL_PATH)
    if mtime <= last_mtime:
        return

    try:
        with open(CHANNEL_PATH, encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'^## \[(.+?)\s+\d', content, re.MULTILINE)
        if match:
            sender = match.group(1).strip()
            if sender == me:
                with open(CHANNEL_CHECK_PATH, 'w') as f:
                    json.dump({'last_mtime': mtime}, f)
                return

        lines = content.split('\n')
        section_lines = []
        in_section = False
        for line in lines:
            if line.startswith('## ['):
                if in_section:
                    break
                in_section = True
            if in_section:
                section_lines.append(line)

        if section_lines:
            section = '\n'.join(section_lines)[:600]
            print(f"📨 通道新消息：")
            print(section)
            print()

        with open(CHANNEL_CHECK_PATH, 'w') as f:
            json.dump({'last_mtime': mtime}, f)
    except Exception:
        pass


DECAY_RATE = 10  # 每天灵气消散 -10（500分制）

# 日薪按等级（500分制）
DAILY_SALARY = {
    1: 4,   # Lv.1 锁灵
    2: 6,   # Lv.2 筑基
    3: 8,   # Lv.3 金丹
    4: 9,   # Lv.4 元婴
    5: 9,   # Lv.5 化神
}

def _get_level(score, agent_name=None):
    """从 merit_gate 导入，不再维护副本"""
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.expanduser('~/.claude/merit'))
        from merit_gate import get_level
        return get_level(score, agent_name)
    except Exception:
        thresholds = [(475, 5, "化神"), (400, 4, "元婴"), (250, 3, "金丹"), (100, 2, "筑基"), (0, 1, "锁灵")]
        for threshold, level, title in thresholds:
            if score >= threshold:
                return level, title
        return 1, "锁灵"


def apply_daily_decay(credit_path):
    """每日结算：灵气消散 -10 + 日薪（按等级）。"""
    from datetime import datetime, timezone
    try:
        with open(credit_path) as f:
            data = json.load(f)

        last_ts = data.get('last_decay_ts', '')
        now = datetime.now(timezone.utc)

        if not last_ts:
            data['last_decay_ts'] = now.strftime('%Y-%m-%dT%H:%M:%S')
            with open(credit_path, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return

        last_time = datetime.fromisoformat(last_ts).replace(tzinfo=timezone.utc)
        hours = (now - last_time).total_seconds() / 3600
        days = int(hours // 24)

        if days < 1:
            return

        agents = data.get('agents', {})
        for name, info in agents.items():
            old_score = info['score']
            level = info.get('level', 1)
            salary = DAILY_SALARY.get(level, 4) * days
            decay = DECAY_RATE * days
            net = salary - decay
            new_score = max(0, min(500, old_score + net))
            new_level, new_title = _get_level(new_score, name)
            info['score'] = new_score
            info['level'] = new_level
            info['title'] = new_title
            data.setdefault('history', []).append({
                'ts': now.strftime('%Y-%m-%dT%H:%M:%S'),
                'agent': name,
                'delta': net,
                'reason': f'每日结算（{days}天）：日薪+{salary} 消散-{decay} 净{net:+d}',
                'score_after': new_score,
            })

        data['last_decay_ts'] = now.strftime('%Y-%m-%dT%H:%M:%S')
        if len(data.get('history', [])) > 100:
            data['history'] = data['history'][-100:]
        with open(credit_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if deduct > 0:
            print(f"💸 灵气消散扣款：全员 -{deduct}分（{days}天）")
    except Exception:
        pass


def inject_credit_status(cwd):
    """注入信用等级状态（所有会话启动时）"""
    credit_path = os.path.expanduser('~/.claude/merit/credit.json')
    if not os.path.exists(credit_path):
        return

    # 先扣灵气消散
    apply_daily_decay(credit_path)

    try:
        with open(credit_path) as f:
            credit_data = json.load(f)
        home = os.path.expanduser('~')
        if 'auto-trading' in cwd:
            agent_name = '两仪'
        elif cwd == home:
            agent_name = '太极'
        else:
            agent_name = '太极'
        agent_info = credit_data.get('agents', {}).get(agent_name, {})
        if agent_info:
            score = agent_info['score']
            level, title = _get_level(score, agent_name)
            print(f"【信用状态】{agent_name} · Lv.{level} {title} · {score}分")
            print(f"  5000分制 | 每次加减分不变 | 升级靠积累，降级是大事——珍惜手里的分数")
            print("")
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

    # 注入最近记忆（当天 markdown 日志）
    inject_recent_memory(cwd)

    # 注入规则（原 inject_rules.py）
    inject_rules(cwd)

    # 所有会话启动都注入信用状态（不限 compact）
    inject_credit_status(cwd)

    # 所有会话启动都检查通道消息（太极↔两仪）
    inject_channel_messages(cwd)

    # 所有会话启动都检查 evolver 通知（不限 compact）
    inject_evolver_notifications()

    # 所有会话启动都检查 reflect 待处理信号（不限 compact）
    inject_reflect_pending()

    # 所有会话启动都检查 MiniMax 失败的待处理 AI 任务
    inject_pending_ai_tasks()

    # 太极上下文检查石卫未审计日志
    inject_shiwei_audit_reminder(cwd)

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
