#!/usr/bin/env python3
"""UserPromptSubmit hook: 注入 rules.md 父类规则到上下文
只注入 <!-- INJECT START --> 和 <!-- INJECT END --> 之间的内容（父类）。
子类留在 rules.md 完整版，AI 遇到具体场景时自行查阅。
"""
import json
import os
import sys

# 从 stdin 读取 hook 数据（含 cwd）
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

cwd = data.get("cwd", os.getcwd())
home = os.path.expanduser("~")

# 项目路径编码：去掉开头 /，所有 / 换 -
project_encoded = cwd.replace("/", "-")
# 处理下划线→连字符的编码差异
project_dir = os.path.join(home, ".claude", "projects", project_encoded)
if not os.path.isdir(project_dir):
    project_dir = os.path.join(home, ".claude", "projects", project_encoded.replace("_", "-"))

project_rules = os.path.join(project_dir, "memory", "rules.md")
global_rules = os.path.join(home, ".claude", "projects", "-Users-allenbot", "memory", "rules.md")


def extract_inject_section(path):
    """提取 INJECT START 和 INJECT END 之间的内容"""
    if not os.path.exists(path):
        return ""
    with open(path, "r") as f:
        content = f.read()
    start = content.find("<!-- INJECT START -->")
    end = content.find("<!-- INJECT END -->")
    if start >= 0 and end >= 0:
        return content[start + len("<!-- INJECT START -->"):end].strip()
    # 没有标记：fallback 注入全文（兼容没重构的项目 rules）
    return content.strip()


parts = []
seen = set()

for label, path in [
    ("全局规则", global_rules),
    ("项目规则", project_rules),
]:
    real = os.path.realpath(path)
    if real in seen or not os.path.exists(path):
        continue
    seen.add(real)
    content = extract_inject_section(path)
    if content:
        parts.append(f"=== {label} ===\n{content}")

if parts:
    print("\n---\n".join(parts))
