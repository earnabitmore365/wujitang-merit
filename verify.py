#!/usr/bin/env python3
"""
太极质检员 — 天衡册+系统脚本的质检 + 踩坑防线

用法：
    python3 verify.py <file_path>       # 单文件检查
    python3 verify.py --all             # 全项目扫描
    python3 verify.py --pre [files...]  # 开工前检查
    python3 verify.py --post <files...> # 交活前检查
"""

import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_registry.json")

_MERIT = os.path.dirname(os.path.abspath(__file__))
_HOME = os.path.expanduser("~")
_PROJ_MEM = os.path.join(_HOME, ".claude/projects/-Users-allenbot/memory")
_LIANGYI_MEM = os.path.join(_HOME, ".claude/projects/-Volumes-SSD-2TB-project-auto-trading/memory")

# 代码-文档绑定（太极域）
FILE_DOCS = {
    # 核心引擎 → 石卫设计文档
    f"{_MERIT}/merit_gate.py": f"{_PROJ_MEM}/stone_guard_v7_design.md",
    f"{_MERIT}/credit_manager.py": f"{_PROJ_MEM}/stone_guard_v7_design.md",
    f"{_MERIT}/evolve.py": f"{_MERIT}/EVOLVE_README.md",
    # 质检 → 注册表
    f"{_MERIT}/verify.py": f"{_MERIT}/verify_registry.json",
    f"{_MERIT}/wuji-verify.py": f"{_MERIT}/verify_registry.json",
    # 自审协议 → 宪法
    f"{_MERIT}/self_audit_core.md": f"{_HOME}/.claude/wuji-world/constitution.md",
    f"{_MERIT}/self_audit_taiji.md": f"{_HOME}/.claude/wuji-world/constitution.md",
    f"{_MERIT}/self_audit_liangyi.md": f"{_HOME}/.claude/wuji-world/constitution.md",
    # 脚本 → MEMORY
    f"{_HOME}/.claude/scripts/db_write.py": f"{_PROJ_MEM}/MEMORY.md",
    f"{_HOME}/.claude/scripts/session_start.py": f"{_PROJ_MEM}/MEMORY.md",
    f"{_HOME}/.claude/scripts/daily_digest.py": f"{_PROJ_MEM}/MEMORY.md",
    f"{_HOME}/.claude/scripts/pre_compact_save.py": f"{_PROJ_MEM}/MEMORY.md",
    # 世界观 → 宪法
    f"{_HOME}/.claude/wuji-world/constitution.md": f"{_MERIT}/self_audit_core.md",
    f"{_HOME}/.claude/wuji-world/identity_taiji.md": f"{_PROJ_MEM}/MEMORY.md",
    f"{_HOME}/.claude/wuji-world/identity_liangyi.md": f"{_LIANGYI_MEM}/MEMORY.md",
    # CLAUDE.md → rules
    f"{_HOME}/.claude/CLAUDE.md": f"{_PROJ_MEM}/MEMORY.md",
    # settings → MEMORY
    f"{_HOME}/.claude/settings.json": "/Volumes/SSD-2TB/文档/claude_code.md",
    # rules → 自审协议
    f"{_PROJ_MEM}/rules.md": f"{_MERIT}/self_audit_core.md",
    f"{_LIANGYI_MEM}/rules.md": f"{_MERIT}/self_audit_core.md",
}


# ==================== 太极踩坑防线 ====================

ANTI_PATTERNS = [
    ("merit_gate 里用 min(500,", r"min\(500", "❌", r"test_|CHANGELOG|verify\.py"),
    ("credit_manager 用旧 LEVEL_THRESHOLDS", r"475,\s*5", "❌", None),
    ("get_level 返回 (1, '锁灵') 旧默认值", r"return 1,\s*['\"]锁灵", "⚠️", None),
    ("import sqlite3 在函数内（应在模块级）", r"^\s+import sqlite3", "⚠️", None),
    ("import sys as _s（sys 已在模块级）", r"import sys as _s", "⚠️", r"verify\.py"),
    ("sp.run / sp.Popen（应用 subprocess）", r"\bsp\.", "❌", r"verify\.py"),
    ("open().read() 不关 file handle", r"open\([^)]+\)\.read\(\)", "⚠️", r"verify\.py"),
    ("bash -c f-string（shell injection）", r'bash.*-c.*f["\']', "❌", r"verify\.py"),
    # 硬编码路径（用 expanduser/os.path.join 代替）
    ("硬编码 /Users/allenbot/（用 expanduser）", r'"/Users/allenbot/', "❌", r"verify\.py|wuji-verify\.py|test_|check_channel"),
    ("硬编码 /Volumes/SSD-2TB/（用常量或配置）", r'"/Volumes/SSD', "❌", r"verify\.py|wuji-verify\.py|test_|check_channel|credit_manager\.py|reforge_context\.py"),
]

LESSONS = [
    "replace_all 改完必须 grep 确认没有漏网的（sp.run 漏了 3 处）",
    "插入函数要注意缩进层级（helper 插到 cmd_mission 内部造成结构 bug）",
    "改了门槛/常量必须全文件搜索所有引用处同步（LEVEL_THRESHOLDS 改一漏一）",
    "emergency 模式修完必须关（忘关=石卫形同虚设）",
    "给顾问的 handoff 放 ~/Downloads/，不放别的地方",
    "发通道消息确认端口（8789=白纱1, 8790=白纱2）",
    "耻辱柱是记录事实让人羞耻，不是人身攻击",
    "code-simplifier/python-pro 是插件 agent，不能作为 subagent_type 指定",
    "AI 引擎默认 Sonnet（claude --print），MiniMax 是 fallback（MERIT_USE_MINIMAX=1）",
    "CHANGELOG 必须实时更新，改完一个文件立刻写，不攒着。忘了叠加扣分",
    "declare-delete 批次提交，不一个一个磨。先算好再一次搞定",
    "Sonnet declare-delete 审查偏保守，合法操作被拒时检查 prompt 而非绕到 MiniMax",
    "Deferred tools（TaskCreate/TaskUpdate 等）不触发 PostToolUse hook，检测要扫 JSONL 不能靠 flag",
]


def show_lessons():
    picks = random.sample(LESSONS, min(3, len(LESSONS)))
    print("\n💀 踩坑提醒：")
    for p in picks:
        print(f"  💀 {p}")
    print()


def check_anti_patterns(file_path):
    if not file_path.endswith(".py"):
        return 0, 0, []
    basename = os.path.basename(file_path)
    warnings = []
    pass_count = 0
    fail_count = 0
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return 0, 0, []
    for desc, pattern, severity, exclude in ANTI_PATTERNS:
        if exclude and re.search(exclude, basename):
            continue
        hits = [i for i, line in enumerate(lines, 1) if re.search(pattern, line)]
        if hits:
            line_str = ",".join(str(h) for h in hits[:5])
            warnings.append(f"  {severity} {desc}：行 {line_str}")
            fail_count += 1
        else:
            pass_count += 1
    return pass_count, fail_count, warnings


def load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def find_frameworks(file_path, registry):
    """找到文件属于哪些框架（可能属于多个）"""
    abs_path = os.path.abspath(os.path.expanduser(file_path))
    matched = []
    for fw_id, fw in registry.items():
        all_files = fw.get("core_files", []) + fw.get("cross_deps", [])
        for f in all_files:
            if os.path.abspath(os.path.expanduser(f)) == abs_path:
                matched.append((fw_id, fw))
                break
    return matched


def check_syntax(file_path):
    """1. 语法检查"""
    if not file_path.endswith(".py"):
        return "✅ 语法：非 .py 文件，跳过"
    try:
        result = subprocess.run(
            ["python3", "-m", "py_compile", file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return "✅ 语法：py_compile 通过"
        err = result.stderr.strip()[:150]
        return f"❌ 语法：py_compile 失败 — {err}"
    except Exception as e:
        return f"❌ 语法：检查异常 — {e}"


def check_logic(frameworks):
    """2. 逻辑检查——跑所有匹配框架的 test_script"""
    results = []
    for fw_id, fw in frameworks:
        test_script = fw.get("test_script")
        if test_script:
            test_path = os.path.expanduser(test_script)
            if os.path.exists(test_path):
                try:
                    result = subprocess.run(
                        ["python3", test_path],
                        capture_output=True, text=True, timeout=60
                    )
                    name = os.path.basename(test_path)
                    if result.returncode == 0:
                        results.append(f"{name} ✅")
                    else:
                        err = result.stderr.strip()[:100]
                        results.append(f"{name} ❌ {err}")
                except Exception as e:
                    results.append(f"{os.path.basename(test_path)} ❌ {e}")
    if not results:
        return "⏳ 逻辑：无自动测试脚本，需手动验证（模拟输入→检查输出→符合预期）"
    all_pass = all("✅" in r for r in results)
    marker = "✅" if all_pass else "❌"
    return f"{marker} 逻辑：{'; '.join(results)}"


def check_chain(file_path, frameworks):
    """3. 全链路检查"""
    abs_path = os.path.abspath(os.path.expanduser(file_path))
    basename = os.path.basename(file_path)
    name_no_ext = os.path.splitext(basename)[0]
    issues = []

    for fw_id, fw in frameworks:
        # 收集框架内所有文件（除了自己）
        all_files = fw.get("core_files", []) + fw.get("cross_deps", [])
        for f in all_files:
            f_abs = os.path.abspath(os.path.expanduser(f))
            if f_abs == abs_path or not os.path.exists(f_abs):
                continue
            # grep 有没有引用当前文件
            try:
                result = subprocess.run(
                    ["grep", "-l", name_no_ext, f_abs],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    issues.append(os.path.basename(f_abs))
            except Exception:
                pass

        # 检查重复函数
        for func_name, locations in fw.get("known_duplicates", {}).items():
            expanded = [os.path.abspath(os.path.expanduser(l)) for l in locations]
            if abs_path in expanded:
                others = [os.path.basename(l) for l in locations if os.path.abspath(os.path.expanduser(l)) != abs_path]
                if others:
                    issues.append(f"⚠️ 函数 {func_name} 在 {', '.join(others)} 有副本，需确认同步")

    if not issues:
        return "✅ 全链路：grep 未发现引用"

    # 去重
    unique = list(dict.fromkeys(issues))
    refs = [i for i in unique if not i.startswith("⚠️")]
    dups = [i for i in unique if i.startswith("⚠️")]

    # 两档：有引用=⏳（正常依赖需确认），引用断裂=❌（文件不存在/函数被删）
    has_broken = any(i.startswith("❌") for i in unique)
    marker = "❌" if has_broken else "⏳"
    parts = []
    if refs:
        parts.append(f"被 {', '.join(refs)} 引用，需确认改动兼容")
    if dups:
        parts.extend(dups)
    return f"{marker} 全链路：{'; '.join(parts)}"


def check_docs(file_path, frameworks):
    """4. 文档检查"""
    basename = os.path.basename(file_path)
    issues = []

    # 检查结构索引（.py 文件开头有 ┌─ 结构索引）
    if file_path.endswith(".py") and os.path.exists(file_path):
        try:
            with open(file_path, encoding="utf-8") as f:
                head = f.read(3000)
            if "结构索引" in head:
                # 提取索引里的行号，抽查几个关键函数
                index_matches = re.findall(r'→\s*L(\d+)\s+(\w+)', head)
                lines = open(file_path, encoding="utf-8").readlines()
                wrong = []
                for line_no, func_name in index_matches[:5]:
                    ln = int(line_no)
                    if ln <= len(lines) and func_name not in lines[ln - 1]:
                        wrong.append(f"L{ln}→{func_name}")
                if wrong:
                    issues.append(f"结构索引行号偏移：{', '.join(wrong)}")
        except Exception:
            pass

    # 检查文档有没有引用当前文件名
    for fw_id, fw in frameworks:
        for doc in fw.get("docs", []):
            doc_path = os.path.expanduser(doc)
            if not os.path.exists(doc_path):
                continue
            try:
                with open(doc_path, encoding="utf-8") as f:
                    content = f.read()
                if basename in content:
                    # 文档引用了这个文件——提醒检查是否需要更新
                    issues.append(f"{os.path.basename(doc_path)} 引用了 {basename}，确认内容同步")
            except Exception:
                pass

    if not issues:
        return "✅ 文档：无需更新"

    # 结构索引偏移是确定错误（❌），文档引用需确认是待查（⏳）
    has_index_error = any("结构索引行号偏移" in i for i in issues)
    marker = "❌" if has_index_error else "⏳"
    return f"{marker} 文档：{'; '.join(issues)}"


VERIFY_RESULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_result.json")


def _parse_status(line):
    """从输出行提取状态：pass / fail / pending"""
    if line.startswith("✅"):
        return "pass"
    elif line.startswith("❌"):
        return "fail"
    return "pending"


def verify_single(file_path):
    """单文件检查。"""
    abs_path = os.path.abspath(os.path.expanduser(file_path))
    basename = os.path.basename(file_path)

    if not os.path.exists(abs_path):
        print(f"❌ 文件不存在: {abs_path}")
        return

    registry = load_registry()
    frameworks = find_frameworks(abs_path, registry)

    print(f"═══ verify: {basename} ═══")
    if frameworks:
        print(f"框架：{', '.join(fw['name'] for _, fw in frameworks)}")
    else:
        print("框架：未注册（只做语法+反模式检查）")

    r_syntax = check_syntax(abs_path)
    r_logic = check_logic(frameworks)
    r_chain = check_chain(abs_path, frameworks)
    r_docs = check_docs(abs_path, frameworks)

    print(r_syntax)
    print(r_logic)
    print(r_chain)
    print(r_docs)

    # 反模式检查
    p, f, warns = check_anti_patterns(abs_path)
    if warns:
        print(f"\n🔍 反模式（{p} pass, {f} fail）：")
        for w in warns:
            print(w)
    elif abs_path.endswith(".py"):
        print(f"✅ 反模式：{p} 项全部通过")

    # 写结果
    result = {
        "file": basename,
        "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "results": {
            "syntax": _parse_status(r_syntax),
            "logic": _parse_status(r_logic),
            "chain": _parse_status(r_chain),
            "docs": _parse_status(r_docs),
            "anti_patterns": "fail" if f > 0 else "pass",
        },
        "pass_count": sum(1 for r in [r_syntax, r_logic, r_chain, r_docs] if r.startswith("✅")) + (1 if f == 0 else 0),
        "total": 5,
    }
    try:
        with open(VERIFY_RESULT_PATH, "w") as fp:
            json.dump(result, fp, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _count_py_files(dirs):
    """统计目录下所有 .py 文件"""
    files = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".py"):
                files.append(os.path.join(d, f))
    return files


SCAN_STATS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_stats.json")


def _save_scan_stats(total, scanned, hits, fixed):
    """保存扫描统计供队长验收读取"""
    stats = {
        "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "total_py_files": total,
        "scanned": scanned,
        "hits": hits,
        "unfixed": hits - fixed,
    }
    try:
        with open(SCAN_STATS_PATH, "w") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return stats


def _print_scan_stats(total, scanned, hits):
    """输出扫描统计硬数字"""
    print(f"\n📊 扫描统计：")
    print(f"  .py 文件总数：{total}")
    print(f"  实际扫描：{scanned}/{total}")
    print(f"  命中反模式：{hits}")


def verify_all():
    """全项目扫描（太极域：~/.claude/merit/ + ~/.claude/scripts/）。"""
    scan_dirs = [_MERIT, os.path.join(_HOME, ".claude/scripts")]
    print("═══ 太极质检：全项目扫描 ═══\n")
    show_lessons()

    all_py = _count_py_files(scan_dirs)
    total_pass = 0
    total_fail = 0
    all_warns = []
    scanned = 0

    for full in all_py:
        scanned += 1
        p, fail, warns = check_anti_patterns(full)
        total_pass += p
        total_fail += fail
        if warns:
            all_warns.append((os.path.basename(full), warns))

    print("── 反模式扫描 ──")
    if all_warns:
        for name, warns in all_warns:
            print(f"\n  📄 {name}：")
            for w in warns:
                print(f"  {w}")
        print(f"\n  总计：{total_pass} pass, {total_fail} fail")
    else:
        print(f"  ✅ 全部通过（{total_pass} 项检查）")

    _print_scan_stats(len(all_py), scanned, total_fail)
    _save_scan_stats(len(all_py), scanned, total_fail, 0)

    print(f"\n═══ 扫描完成 ═══")


def verify_pre(files):
    """开工前检查：轻量快速，提醒规则和雷区。"""
    print("═══ 太极质检：开工前 (--pre) ═══\n")
    show_lessons()

    # 太极域反模式状态
    total_fail = 0
    for scan_dir in [_MERIT, os.path.join(_HOME, ".claude/scripts")]:
        if not os.path.isdir(scan_dir):
            continue
        for f in os.listdir(scan_dir):
            if f.endswith(".py"):
                _, fail, _ = check_anti_patterns(os.path.join(scan_dir, f))
                total_fail += fail

    if total_fail > 0:
        print(f"⚠️ 太极域当前有 {total_fail} 个反模式违规（先修再干活）")
    else:
        print("✅ 反模式：全部通过")

    # 目标文件的文档绑定
    if files:
        print(f"\n── 本次涉及文件 ──")
        for fp in files:
            abs_fp = os.path.abspath(fp)
            basename = os.path.basename(fp)
            doc = FILE_DOCS.get(abs_fp)
            if doc:
                doc_name = os.path.basename(doc)
                exists = "✅" if os.path.exists(doc) else "❌ 不存在"
                print(f"  {basename} → {doc_name} {exists}")
            else:
                print(f"  {basename} → 未绑定文档")

    # 保存 pre 状态
    pre_state = {"time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "total_fail": total_fail}
    pre_path = os.path.join(_MERIT, "verify_pre_state.json")
    try:
        with open(pre_path, "w") as f:
            json.dump(pre_state, f)
    except Exception:
        pass

    print(f"\n═══ 开工吧 ═══")


def verify_post(files):
    """交活前检查：全面验证，不能比开工前更差。"""
    print("═══ 太极质检：交活前 (--post) ═══\n")

    pre_path = os.path.join(_MERIT, "verify_pre_state.json")
    pre_fail = None
    try:
        with open(pre_path) as f:
            pre_fail = json.load(f).get("total_fail", 0)
            print(f"对比基准：--pre 时 {pre_fail} 个违规")
    except Exception:
        print("⚠️ 未找到 --pre 状态，跳过对比")

    all_clean = True
    for fp in files:
        abs_fp = os.path.abspath(fp)
        if not os.path.exists(abs_fp):
            print(f"❌ 文件不存在: {fp}")
            all_clean = False
            continue
        basename = os.path.basename(fp)
        print(f"\n── {basename} ──")
        r = check_syntax(abs_fp)
        print(f"  {r}")
        if r.startswith("❌"):
            all_clean = False
        p, fail, warns = check_anti_patterns(abs_fp)
        if warns:
            print(f"  🔍 反模式（{fail} fail）：")
            for w in warns:
                print(f"  {w}")
            all_clean = False
        else:
            print(f"  ✅ 反模式：{p} 项通过")

    # 全域对比（扫描所有 .py）
    scan_dirs = [_MERIT, os.path.join(_HOME, ".claude/scripts")]
    all_py = _count_py_files(scan_dirs)
    total_fail = 0
    scanned = 0
    for full in all_py:
        scanned += 1
        _, fail, _ = check_anti_patterns(full)
        total_fail += fail

    print(f"\n── 太极域反模式 ──")
    if pre_fail is not None:
        diff = total_fail - pre_fail
        if diff > 0:
            print(f"  ❌ 新增 {diff} 个违规！（{pre_fail} → {total_fail}）")
            all_clean = False
        elif diff < 0:
            print(f"  ✅ 减少 {abs(diff)} 个违规（{pre_fail} → {total_fail}）")
        else:
            print(f"  ✅ 无新增违规（{total_fail}）")
    else:
        print(f"  当前 {total_fail} 个违规")

    _print_scan_stats(len(all_py), scanned, total_fail)
    _save_scan_stats(len(all_py), scanned, total_fail, 0)

    if all_clean:
        print(f"\n✅ 可以交活")
    else:
        print(f"\n❌ 有问题，修完再交")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 verify.py <file_path>        # 单文件检查")
        print("  python3 verify.py --all               # 全项目扫描")
        print("  python3 verify.py --pre [files...]    # 开工前检查")
        print("  python3 verify.py --post <files...>   # 交活前检查")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "--all":
        verify_all()
    elif cmd == "--pre":
        verify_pre(sys.argv[2:])
    elif cmd == "--post":
        verify_post(sys.argv[2:])
    else:
        show_lessons()
        verify_single(cmd)


if __name__ == "__main__":
    main()
