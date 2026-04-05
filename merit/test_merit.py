#!/usr/bin/env python3
"""
天衡册端到端测试 — 永久保留，verify.py 调用

跑法：python3 test_merit.py
输出：N/15 通过
"""

import io
import json
import os
import sys
from contextlib import redirect_stdout

# 确保能导入 merit_gate
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from merit_gate import (
    SCORING_TABLE, get_level, get_shiwei_rank, determine_agent,
    judge_user_sentiment, load_mission, save_mission,
    log_shiwei_action, handle_pre_tool_use,
    check_destructive, check_bash_destructive,
    PROTECTED_EXTENSIONS, SHIWEI_LOG_DIR,
)

PASSED = 0
FAILED = 0


def test(name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  ✅ {PASSED + FAILED:2d}/15 {name}")
    else:
        FAILED += 1
        print(f"  ❌ {PASSED + FAILED:2d}/15 {name}: {detail}")


def capture_stdout(func, *args, **kwargs):
    buf = io.StringIO()
    with redirect_stdout(buf):
        func(*args, **kwargs)
    return buf.getvalue()


def main():
    print("═══ test_merit.py — 天衡册端到端测试 ═══\n")

    # 1. SCORING_TABLE 完整性
    test("SCORING_TABLE 完整", len(SCORING_TABLE) == 13, f"期望13项，实际{len(SCORING_TABLE)}")

    # 2. SCORING_TABLE 值范围（500分制 ×2.5）
    vals = list(SCORING_TABLE.values())
    test("SCORING_TABLE 值范围", min(vals) >= -50 and max(vals) <= 20, f"范围 {min(vals)}~{max(vals)}")

    # 3. get_level 锁灵
    lv, title = get_level(0)
    test("get_level 0→锁灵", title == "锁灵", f"实际: {title}")

    # 4. get_level 金丹（500分制：250+）
    lv, title = get_level(250)
    test("get_level 250→金丹", title == "金丹", f"实际: {title}")

    # 5. get_level 化神（500分制：475+）
    lv, title = get_level(475)
    test("get_level 475→化神", title == "化神", f"实际: {title}")

    # 6. determine_agent 太极
    result = determine_agent({"cwd": "/Users/allenbot"})
    test("determine_agent home→太极", result == "太极", f"实际: {result}")

    # 7. determine_agent 两仪
    result = determine_agent({"cwd": "/Users/allenbot/project/auto-trading"})
    test("determine_agent trading→两仪", result == "两仪", f"实际: {result}")

    # 8. 正面语气识别
    delta, _ = judge_user_sentiment("嗯嗯，这个主意不错")
    test("语气识别 正面", delta > 0, f"delta={delta}")

    # 9. 负面语气识别
    delta, _ = judge_user_sentiment("你搞什么东西")
    test("语气识别 负面", delta < 0, f"delta={delta}")

    # 10. check_destructive .db 拦截
    reason = check_destructive({"tool_input": {"file_path": "/tmp/test.db"}})
    test("check_destructive .db", reason is not None, "应该拦截但没有")

    # 11. check_destructive .py 放行
    reason = check_destructive({"tool_input": {"file_path": "/tmp/test.py"}})
    test("check_destructive .py", reason is None, f"不应拦截但拦了: {reason}")

    # 12. check_bash_destructive 安全命令
    reason = check_bash_destructive("ls -la /tmp")
    test("bash_destructive ls", reason is None, f"不应拦截: {reason}")

    # 13. 石卫段位查询
    test("shiwei_rank 0→黑铁", get_shiwei_rank(0) == "黑铁")

    # 14. 石卫段位查询 高段
    test("shiwei_rank 95→钻石", get_shiwei_rank(95) == "钻石")

    # 15. 石卫日志写入
    from datetime import datetime
    log_shiwei_action("Test", "test", "test_merit", "测试", "TEST")
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(SHIWEI_LOG_DIR, f"{today}.md")
    exists = os.path.exists(log_path)
    has_content = False
    if exists:
        with open(log_path) as f:
            has_content = "test_merit" in f.read()
    test("石卫日志写入", exists and has_content, "日志文件不存在或内容不对")

    print(f"\n{'═' * 40}")
    print(f"结果: {PASSED}/{PASSED + FAILED} 通过")
    if FAILED > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
