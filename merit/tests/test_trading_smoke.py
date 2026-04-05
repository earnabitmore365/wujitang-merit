#!/usr/bin/env python3
"""
交易系统 Smoke Test — 太极编写，两仪不可修改

验证 trading/ 核心文件：语法+关键类/函数+配置完整性
"""

import subprocess
import sys
import os

TRADING_DIR = "/Volumes/SSD-2TB/project/wuji-auto-trading/trading"
CORE_FILES = [
    "unified_trader.py",
    "strategy_runner.py",
    "kline_dispatcher.py",
    "limit_executor.py",
    "trade_logger.py",
    "trader_report.py",
    "team_config.py",
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


for fname in CORE_FILES:
    fpath = os.path.join(TRADING_DIR, fname)
    if not os.path.exists(fpath):
        test(f"{fname} 存在", False, "文件不存在")
        continue

    # 语法检查
    result = subprocess.run(
        ["python3", "-m", "py_compile", fpath],
        capture_output=True, text=True
    )
    test(f"{fname} 语法", result.returncode == 0,
         result.stderr.strip()[:200] if result.returncode != 0 else "")

    with open(fpath) as f:
        content = f.read()

    # 关键结构检查
    if fname == "unified_trader.py":
        test("UnifiedTrader 类", "class UnifiedTrader" in content, "缺少 class UnifiedTrader")
        test("main 函数", "def main" in content, "缺少 def main")

    elif fname == "strategy_runner.py":
        test("StrategyRunner 类", "class StrategyRunner" in content, "缺少 class StrategyRunner")
        test("on_bar 方法", "on_bar" in content, "缺少 on_bar")

    elif fname == "team_config.py":
        test("TEAM 配置", "TEAM" in content, "缺少 TEAM 配置")
        test("get_bet_amount", "get_bet_amount" in content, "缺少 get_bet_amount")

    elif fname == "kline_dispatcher.py":
        test("KlineDispatcher", "KlineDispatcher" in content or "kline_dispatcher" in content.lower(),
             "缺少 KlineDispatcher")

    elif fname == "limit_executor.py":
        test("LimitOrder", "limit" in content.lower() and "executor" in content.lower(),
             "缺少限价单执行逻辑")

# 结果
total = passed + failed
print(f"交易系统 Smoke Test: {passed}/{total} 通过")
if errors:
    for e in errors:
        print(f"  ❌ {e}")
    sys.exit(1)
else:
    print("  ✅ 全部通过")
    sys.exit(0)
