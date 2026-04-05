#!/usr/bin/env python3
"""
回测系统 Smoke Test — 太极编写，两仪不可修改

验证 generate_seed.py 核心逻辑：
1. 语法正确（py_compile）
2. 关键类/函数存在（grep 检查）
3. 数据字段完整（grep 检查）

用法：python3 test_backtest_smoke.py
由 wuji-verify.py 的 test_script 自动调用
"""

import subprocess
import sys
import os
import re

SEED_PATHS = [
    "/Volumes/SSD-2TB/project/wuji-auto-trading/backtest/engine/generate_seed.py",
    "/Volumes/SSD-2TB/project/wuji-auto-trading/src/backtest/generate_seed.py",
]

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


for seed_path in SEED_PATHS:
    if not os.path.exists(seed_path):
        continue

    label = "engine" if "engine" in seed_path else "src"

    # === 1. 语法检查 ===
    result = subprocess.run(
        ["python3", "-m", "py_compile", seed_path],
        capture_output=True, text=True
    )
    test(f"[{label}] 语法", result.returncode == 0,
         result.stderr.strip()[:200] if result.returncode != 0 else "")

    # === 2. 读取文件内容 ===
    with open(seed_path) as f:
        content = f.read()

    # === 3. 关键类存在 ===
    for cls in ["class SimTrade", "class TTPTracker", "class TradeSimulator"]:
        test(f"[{label}] {cls}", cls in content, f"缺少 {cls}")

    # === 4. 关键函数存在 ===
    for func in ["def load_candles", "def compute_regime_timeline",
                  "def pair_trades", "def parse_args"]:
        test(f"[{label}] {func}", func in content, f"缺少 {func}")

    # === 5. SimTrade 11 字段 ===
    required_fields = ['combo_id', 'open_candle_idx', 'close_candle_idx',
                       'open_time', 'close_time', 'direction',
                       'entry_price', 'exit_price', 'close_type', 'mfe', 'mae']
    for field in required_fields:
        test(f"[{label}] SimTrade.{field}", field in content, f"缺少字段 {field}")

    # === 6. 4 种子模式 ===
    for mode in ['signal_only', 'ttp_close', 'ttp_highlow', 'dual_hold']:
        test(f"[{label}] 种子模式.{mode}", mode in content, f"缺少种子模式 {mode}")

    # === 7. TTP 参数合理性 ===
    ttp_match = re.search(r'activation_pct.*?=.*?([\d.]+)', content)
    if ttp_match:
        val = float(ttp_match.group(1))
        test(f"[{label}] TTP activation 范围", 0.01 <= val <= 0.20,
             f"activation_pct={val} 超出合理范围 [0.01, 0.20]")
    else:
        test(f"[{label}] TTP activation 存在", False, "找不到 activation_pct")

# === 结果 ===
total = passed + failed
if total == 0:
    print("❌ 未找到 generate_seed.py")
    sys.exit(1)

print(f"回测 Smoke Test: {passed}/{total} 通过")
if errors:
    for e in errors:
        print(f"  ❌ {e}")
    sys.exit(1)
else:
    print("  ✅ 全部通过")
    sys.exit(0)
