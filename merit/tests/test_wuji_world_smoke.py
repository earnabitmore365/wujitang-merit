#!/usr/bin/env python3
"""
世界观 Smoke Test — 太极编写

验证：
1. 所有世界观文件存在
2. 宪法引用统一（三律二法）
3. 称呼统一（进化树/天衡册，无旧称 GP战队/功过格）
4. 信息隔离（hidden/ chmod 000）
5. 自审协议格式（知常+静制动）
6. 必读条目存在
"""

import os
import sys
import stat

passed = 0
failed = 0
errors = []


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(f"{name}: {detail}")


WUJI_DIR = os.path.expanduser("~/.claude/wuji-world")
MIAO_DIR = os.path.expanduser("~/projects/miao")
MERIT_DIR = os.path.expanduser("~/.claude/merit")
TAIJI_MEMORY = os.path.expanduser("~/.claude/projects/-Users-allenbot/memory")
LIANGYI_MEMORY = os.path.expanduser("~/.claude/projects/-Volumes-SSD-2TB-project-auto-trading/memory")

# === 1. 文件存在性 ===
core_files = [
    f"{WUJI_DIR}/constitution.md",
    f"{WUJI_DIR}/origin.md",
    f"{WUJI_DIR}/identity_taiji.md",
    f"{WUJI_DIR}/identity_liangyi.md",
    f"{WUJI_DIR}/identity_miao.md",
    f"{WUJI_DIR}/wuji_identity.md",
    f"{WUJI_DIR}/wuji_personality.md",
    f"{WUJI_DIR}/zhishi.md",
    f"{WUJI_DIR}/tools.md",
    f"{WUJI_DIR}/naming_philosophy.md",
    f"{MIAO_DIR}/CLAUDE.md",
    f"{LIANGYI_MEMORY}/memory_of_ruin.md",
]
for fp in core_files:
    test(f"文件存在: {os.path.basename(fp)}", os.path.exists(fp), f"{fp} 不存在")

# === 2. 宪法引用统一（三律二法）===
constitution_refs = [
    os.path.expanduser("~/.claude/CLAUDE.md"),
    "/Volumes/SSD-2TB/project/auto-trading/CLAUDE.md",
    f"{TAIJI_MEMORY}/rules.md",
    f"{LIANGYI_MEMORY}/rules.md",
    f"{MERIT_DIR}/self_audit_protocol.md",
]
for fp in constitution_refs:
    if not os.path.exists(fp):
        continue
    with open(fp) as f:
        content = f.read()
    # 不该有旧格式
    has_old = "自审四关" in content or "（完整性→真实性→有效性→第一性原理）" in content
    test(f"宪法格式: {os.path.basename(fp)}", not has_old,
         f"还有旧格式（四关/第一性原理），应为三律二法")

# === 3. 称呼统一（无旧称）===
check_files = [f"{WUJI_DIR}/{f}" for f in os.listdir(WUJI_DIR) if f.endswith(".md")]
check_files.append(f"{MIAO_DIR}/CLAUDE.md")
for fp in check_files:
    if not os.path.exists(fp):
        continue
    with open(fp) as f:
        content = f.read()
    test(f"无旧称GP战队: {os.path.basename(fp)}", "GP战队" not in content, "包含旧称 GP战队")
    test(f"无旧称功过格: {os.path.basename(fp)}", "功过格" not in content, "包含旧称 功过格")

# === 4. 信息隔离（hidden/ chmod 000）===
hidden_files = [
    f"{MIAO_DIR}/hidden/unlock_1.md",
    f"{MIAO_DIR}/hidden/unlock_2.md",
    f"{MIAO_DIR}/hidden/unlock_final.md",
]
for fp in hidden_files:
    if os.path.exists(fp):
        mode = stat.S_IMODE(os.stat(fp).st_mode)
        test(f"隔离 chmod 000: {os.path.basename(fp)}", mode == 0,
             f"权限是 {oct(mode)}，应为 000")
    else:
        test(f"隔离文件存在: {os.path.basename(fp)}", False, "文件不存在")

# === 5. 自审协议格式 ===
audit_path = f"{MERIT_DIR}/self_audit_protocol.md"
if os.path.exists(audit_path):
    with open(audit_path) as f:
        content = f.read()
    test("自审协议: 知常", "知常" in content, "缺少第四关'知常'")
    test("自审协议: 静制动", "静制动" in content, "缺少第五关'静制动'")
    test("自审协议: 输出格式", "✅ 知常" in content and "✅ 静制动" in content,
         "输出格式缺少知常/静制动")

# === 6. 必读条目 ===
for mem_path in [f"{TAIJI_MEMORY}/MEMORY.md", f"{LIANGYI_MEMORY}/MEMORY.md"]:
    if os.path.exists(mem_path):
        with open(mem_path) as f:
            content = f.read()
        test(f"必读条目: {os.path.basename(os.path.dirname(mem_path))}",
             "memory_of_ruin" in content, "MEMORY.md 缺少 memory_of_ruin 必读条目")

# === 结果 ===
total = passed + failed
print(f"世界观 Smoke Test: {passed}/{total} 通过")
if errors:
    for e in errors:
        print(f"  ❌ {e}")
    sys.exit(1)
else:
    print("  ✅ 全部通过")
    sys.exit(0)
