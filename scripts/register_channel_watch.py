#!/usr/bin/env python3
"""SessionStart 时注册通道文件到 FileChanged watchPaths"""
import json, os, sys

data = json.load(sys.stdin)
channel = os.path.expanduser("~/.claude/channel_taiji_liangyi.md")

# 返回 watchPaths 让 FileChanged 监控通道文件
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "watchPaths": [channel]
    }
}))
