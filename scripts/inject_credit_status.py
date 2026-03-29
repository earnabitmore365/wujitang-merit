"""
信用状态注入片段 — 供 session_start.py 调用
安装后由 install.sh 自动注入到 session_start.py
"""

import json
import os


def inject_credit_status(cwd):
    """注入信用等级状态（所有会话启动时）"""
    credit_path = os.path.expanduser('~/.claude/credit.json')
    if not os.path.exists(credit_path):
        return
    try:
        with open(credit_path) as f:
            credit_data = json.load(f)
        home = os.path.expanduser('~')
        if 'auto-trading' in cwd:
            agent_name = '黑丝'
        elif cwd == home:
            agent_name = '太极'
        else:
            agent_name = '太极'
        agent_info = credit_data.get('agents', {}).get(agent_name, {})
        if agent_info:
            score = agent_info['score']
            level = agent_info['level']
            title = agent_info['title']
            print(f"【信用状态】{agent_name} · Lv.{level} {title} · {score}分")
            print("")
    except Exception:
        pass
