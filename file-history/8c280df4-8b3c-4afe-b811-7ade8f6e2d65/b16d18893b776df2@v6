#!/usr/bin/env python3
"""
无极质检员 — 项目级四件套检查

用法：python3 wuji-verify.py <file_path>
"""

import json
import os
import re
import subprocess
import sys

# 项目框架地图（内嵌，不用外部文件）
REGISTRY = {
    "trading": {
        "name": "交易系统",
        "core_files": [
            "/Volumes/SSD-2TB/project/wuji-auto-trading/trading/unified_trader.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/trading/strategy_runner.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/trading/kline_dispatcher.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/trading/limit_executor.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/trading/trade_logger.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/trading/trader_report.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/trading/trader_bot.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/trading/team_config.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/trading/monitor/monitor.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/trading/monitor/bitmex_dashboard.py",
        ],
        "cross_deps": [
            "/Volumes/SSD-2TB/project/wuji-auto-trading/src/core/indicator_cache.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/src/data/feed_gateway.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/src/data/feed_client.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/src/data/gateway_notifier.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/path_config.py",
        ],
        "docs": [
            "/Volumes/SSD-2TB/project/wuji-auto-trading/README.md",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/ARCHITECTURE.md",
        ],
        "test_script": os.path.expanduser("~/.claude/merit/tests/test_trading_smoke.py"),
    },
    "backtest": {
        "name": "回测系统",
        "core_files": [
            "/Volumes/SSD-2TB/project/wuji-auto-trading/src/backtest/generate_seed.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/src/backtest/backtest.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/backtest/build_seed_report.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/backtest/pipeline/refresh_summary.py",
        ],
        "cross_deps": [
            "/Volumes/SSD-2TB/project/wuji-auto-trading/src/core/indicator_cache.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/src/core/strategy/__init__.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/path_config.py",
        ],
        "docs": [
            "/Volumes/SSD-2TB/project/wuji-auto-trading/README.md",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/ARCHITECTURE.md",
        ],
        "test_script": os.path.expanduser("~/.claude/merit/tests/test_backtest_smoke.py"),
    },
    "research": {
        "name": "研究/进化系统",
        "core_files": [
            "/Volumes/SSD-2TB/project/wuji-auto-trading/src/core/indicator_cache.py",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/src/core/strategy/__init__.py",
        ],
        "cross_deps": [
            "/Volumes/SSD-2TB/project/wuji-auto-trading/path_config.py",
        ],
        "docs": [
            "/Volumes/SSD-2TB/project/wuji-auto-trading/README.md",
            "/Volumes/SSD-2TB/project/wuji-auto-trading/ARCHITECTURE.md",
        ],
        "test_script": os.path.expanduser("~/.claude/merit/tests/test_research_smoke.py"),
    },
}

# ==================== 代码-文档绑定 ====================
# 改了代码 → 必须检查对应文档是否需要同步
# verify 时自动比较 mtime，代码比文档新 → 警告

_ROOT = "/Volumes/SSD-2TB/project/wuji-auto-trading"
FILE_DOCS = {
    # BitMEX 适配器 → BitMEX API 文档（项目内 + 文档库双绑定）
    f"{_ROOT}/src/exchange/bitmex/adapter.py": f"{_ROOT}/src/exchange/bitmex/README.md",
    f"{_ROOT}/src/exchange/bitmex/websocket.py": f"{_ROOT}/src/exchange/bitmex/README.md",
    f"{_ROOT}/src/exchange/bitmex/auth.py": f"{_ROOT}/src/exchange/bitmex/README.md",
    # HyperLiquid 适配器
    f"{_ROOT}/src/exchange/hyperliquid/adapter.py": f"{_ROOT}/src/exchange/hyperliquid/README.md",
    f"{_ROOT}/src/exchange/hyperliquid/websocket.py": f"{_ROOT}/src/exchange/hyperliquid/README.md",
    f"{_ROOT}/src/exchange/hyperliquid/accounts.py": f"{_ROOT}/src/exchange/hyperliquid/README.md",
    f"{_ROOT}/src/exchange/hyperliquid/ttp_orders.py": f"{_ROOT}/src/exchange/hyperliquid/README.md",
    # Paper Trade 适配器 → HyperLiquid 文档（委托行情给 HL）
    f"{_ROOT}/src/exchange/paper/adapter.py": f"{_ROOT}/src/exchange/hyperliquid/README.md",
    # 数据层 → K线种子文档
    f"{_ROOT}/src/data/feed_gateway.py": f"{_ROOT}/data/README_KLINES_SEED.md",
    f"{_ROOT}/src/data/feed_client.py": f"{_ROOT}/data/README_KLINES_SEED.md",
    f"{_ROOT}/src/data/gateway_notifier.py": f"{_ROOT}/data/README_KLINES_SEED.md",
    # 回测引擎 → 回测文档
    f"{_ROOT}/src/backtest/backtest.py": f"{_ROOT}/backtest/README.md",
    f"{_ROOT}/src/backtest/generate_seed.py": f"{_ROOT}/backtest/README.md",
    f"{_ROOT}/src/backtest/incremental_backtest.py": f"{_ROOT}/backtest/README.md",
    # K线种子供应链 → CCXT 数据下载文档
    f"{_ROOT}/data/build_klines_indicators.py": "/Volumes/SSD-2TB/文档/数据/ccxt.md",
    # 指标缓存 → 架构文档
    f"{_ROOT}/src/core/indicator_cache.py": f"{_ROOT}/ARCHITECTURE.md",
    # 策略基类
    f"{_ROOT}/src/core/strategy/base.py": f"{_ROOT}/src/core/strategy/README.md",
}

# 项目根目录（用于匹配目录级 core_files）
PROJECT_ROOTS = [
    "/Volumes/SSD-2TB/project/wuji-auto-trading",
    "/Volumes/SSD-2TB/project/auto-trading",
]


def find_frameworks(file_path):
    abs_path = os.path.abspath(file_path)
    matched = []
    for fw_id, fw in REGISTRY.items():
        all_files = fw.get("core_files", []) + fw.get("cross_deps", [])
        for f in all_files:
            if os.path.abspath(f) == abs_path:
                matched.append((fw_id, fw))
                break
    # 如果精确匹配不到，按目录归属匹配
    if not matched:
        for fw_id, fw in REGISTRY.items():
            for f in fw.get("core_files", []) + fw.get("cross_deps", []):
                f_dir = os.path.dirname(os.path.abspath(f))
                if abs_path.startswith(f_dir):
                    matched.append((fw_id, fw))
                    break
    return matched


def check_syntax(file_path):
    if not file_path.endswith(".py"):
        return "✅ 语法：非 .py 文件，跳过"
    try:
        result = subprocess.run(
            ["python3", "-m", "py_compile", file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return "✅ 语法：py_compile 通过"
        return f"❌ 语法：{result.stderr.strip()[:150]}"
    except Exception as e:
        return f"❌ 语法：{e}"


def check_logic(frameworks):
    results = []
    for fw_id, fw in frameworks:
        test_script = fw.get("test_script")
        if test_script and os.path.exists(test_script):
            try:
                result = subprocess.run(
                    ["python3", test_script],
                    capture_output=True, text=True, timeout=60
                )
                name = os.path.basename(test_script)
                if result.returncode == 0:
                    results.append(f"{name} ✅")
                else:
                    results.append(f"{name} ❌ {result.stderr.strip()[:100]}")
            except Exception as e:
                results.append(f"❌ {e}")
    if not results:
        return "⏳ 逻辑：无自动测试，需手动验证（模拟输入→检查输出→符合预期）"
    all_pass = all("✅" in r for r in results)
    return f"{'✅' if all_pass else '❌'} 逻辑：{'; '.join(results)}"


def check_chain(file_path, frameworks):
    abs_path = os.path.abspath(file_path)
    name_no_ext = os.path.splitext(os.path.basename(file_path))[0]
    issues = []
    for fw_id, fw in frameworks:
        all_files = fw.get("core_files", []) + fw.get("cross_deps", [])
        for f in all_files:
            f_abs = os.path.abspath(f)
            if f_abs == abs_path or not os.path.exists(f_abs):
                continue
            try:
                result = subprocess.run(
                    ["grep", "-l", name_no_ext, f_abs],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    issues.append(os.path.basename(f_abs))
            except Exception:
                pass
    if not issues:
        return "✅ 全链路：grep 未发现引用"
    unique = list(dict.fromkeys(issues))
    return f"⏳ 全链路：被 {', '.join(unique)} 引用，需确认改动兼容"


def check_docs(file_path, frameworks):
    basename = os.path.basename(file_path)
    issues = []
    for fw_id, fw in frameworks:
        for doc in fw.get("docs", []):
            if not os.path.exists(doc):
                continue
            try:
                with open(doc, encoding="utf-8") as f:
                    content = f.read()
                if basename in content:
                    issues.append(f"{os.path.basename(doc)} 引用了 {basename}")
            except Exception:
                pass
    if not issues:
        return "✅ 文档：无需更新"
    return f"⏳ 文档：{'; '.join(issues)}，确认内容同步"


def check_doc_freshness(file_path):
    """检查代码文件的关联文档是否比代码更旧。"""
    abs_path = os.path.abspath(file_path)
    doc_path = FILE_DOCS.get(abs_path)
    if not doc_path or not os.path.exists(doc_path):
        return None  # 无绑定文档

    code_mtime = os.path.getmtime(abs_path)
    doc_mtime = os.path.getmtime(doc_path)
    doc_name = os.path.basename(doc_path)

    if code_mtime > doc_mtime:
        gap_hours = int((code_mtime - doc_mtime) / 3600)
        return f"⚠️ 文档可能过时：{doc_name}（代码比文档新 {gap_hours}h），请检查并更新"
    return f"✅ 文档同步：{doc_name}"


def main():
    if len(sys.argv) < 2:
        print("用法: python3 wuji-verify.py <file_path>")
        sys.exit(1)

    file_path = os.path.abspath(sys.argv[1])
    basename = os.path.basename(file_path)

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    frameworks = find_frameworks(file_path)

    print(f"═══ 无极质检: {basename} ═══")
    if frameworks:
        print(f"框架：{', '.join(fw['name'] for _, fw in frameworks)}")
    else:
        print("框架：未注册（只做语法检查）")

    r_syntax = check_syntax(file_path)
    r_logic = check_logic(frameworks)
    r_chain = check_chain(file_path, frameworks)
    r_docs = check_docs(file_path, frameworks)
    r_freshness = check_doc_freshness(file_path)

    print(r_syntax)
    print(r_logic)
    print(r_chain)
    print(r_docs)
    if r_freshness:
        print(r_freshness)

    # 写结果文件
    from datetime import datetime
    def _status(line):
        if line.startswith("✅"): return "pass"
        if line.startswith("❌"): return "fail"
        return "pending"

    result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_result.json")
    try:
        result = {
            "file": basename,
            "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "results": {
                "syntax": _status(r_syntax),
                "logic": _status(r_logic),
                "chain": _status(r_chain),
                "docs": _status(r_docs),
            },
            "pass_count": sum(1 for r in [r_syntax, r_logic, r_chain, r_docs] if r.startswith("✅")),
            "total": 4,
        }
        with open(result_path, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


if __name__ == "__main__":
    main()
