#!/usr/bin/env python3
"""通道文件变更时检查新消息（FileChanged hook 触发）。两个角色都检查。"""
import json, os, re, sys

CHANNEL_PATH = os.path.expanduser("~/.claude/channel_taiji_liangyi.md")
MERIT_DIR = os.path.expanduser("~/.claude/merit")

if not os.path.exists(CHANNEL_PATH):
    exit()

# 读最新消息的发送者
with open(CHANNEL_PATH, encoding="utf-8") as f:
    content = f.read()

match = re.search(r'^## \[(.+?)\s+\d', content, re.MULTILINE)
if not match:
    exit()
sender = match.group(1).strip()

# 提取最新消息
lines = content.split("\n")
section_lines = []
in_section = False
for line in lines:
    if line.startswith("## ["):
        if in_section:
            break
        in_section = True
    if in_section:
        section_lines.append(line)

if not section_lines:
    exit()

section = "\n".join(section_lines)[:600]

# 给对方写 reminder（太极发的→写两仪的 reminder，反之亦然）
for role in ["太極", "两仪"]:
    if sender == role or sender == role.replace("極", "极"):
        continue  # 自己发的不提醒自己
    check_path = os.path.join(MERIT_DIR, f"channel_check_{role}.json")
    last_mtime = 0
    if os.path.exists(check_path):
        try:
            with open(check_path) as f:
                last_mtime = json.load(f).get("last_mtime", 0)
        except Exception:
            pass
    mtime = os.path.getmtime(CHANNEL_PATH)
    if mtime <= last_mtime:
        continue
    # 写 reminder
    reminder_path = os.path.join(MERIT_DIR, "channel_reminder.txt")
    with open(reminder_path, "w") as f:
        f.write(f"📨 通道新消息：\n{section}")
    # 更新已读
    with open(check_path, "w") as f:
        json.dump({"last_mtime": mtime}, f)

    # touch 白纱项目目录的信号文件（触发 FileChanged hook）
    signal = "/Volumes/SSD-2TB/project/auto-trading/.claude/channel_signal.txt"
    try:
        import time
        with open(signal, "w") as f:
            f.write(str(time.time()))
    except Exception:
        pass
