#!/usr/bin/env python3
"""
研究/进化系统 Smoke Test — 太极编写，两仪不可修改

验证 indicator_cache.py 核心逻辑：语法+关键函数+指标注册
"""

import subprocess
import sys
import os
import re

CACHE_PATH = "/Volumes/SSD-2TB/project/wuji-auto-trading/src/core/indicator_cache.py"

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


if not os.path.exists(CACHE_PATH):
    print("❌ indicator_cache.py 不存在")
    sys.exit(1)

# 语法
result = subprocess.run(
    ["python3", "-m", "py_compile", CACHE_PATH],
    capture_output=True, text=True
)
test("语法", result.returncode == 0,
     result.stderr.strip()[:200] if result.returncode != 0 else "")

with open(CACHE_PATH) as f:
    content = f.read()

# 关键函数
for func in ["def init_cache", "def get_indicator", "def close_cache",
             "def list_indicators", "def set_active_namespace",
             "def preload_from_duckdb"]:
    test(f"{func}", func in content, f"缺少 {func}")

# 核心指标注册
for indicator in ["rsi", "atr", "sma", "ema", "macd", "bb"]:
    test(f"指标.{indicator}", f"compute_{indicator}" in content,
         f"缺少 compute_{indicator}")

# namespace 支持（normal/flipped）
test("namespace normal", "'normal'" in content, "缺少 normal namespace")
test("namespace flipped", "'flipped'" in content or "flipped" in content,
     "缺少 flipped namespace")

# 结果
total = passed + failed
print(f"研究系统 Smoke Test: {passed}/{total} 通过")
if errors:
    for e in errors:
        print(f"  ❌ {e}")
    sys.exit(1)
else:
    print("  ✅ 全部通过")
    sys.exit(0)
