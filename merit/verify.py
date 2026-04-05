#!/usr/bin/env python3
"""
四件套质检员 — 改完代码必须过的四项检查

用法：python3 verify.py <file_path>

四项检查（全部用系统命令，不依赖 AI）：
1. 语法：py_compile
2. 逻辑：有 test_script 就跑，没有提醒手动验证
3. 全链路：grep 框架内其他文件的引用关系 + 重复函数检查
4. 文档：grep docs 里的引用 + 结构索引行号检查
"""

import json
import os
import re
import subprocess
import sys

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_registry.json")


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


def main():
    if len(sys.argv) < 2:
        print("用法: python3 verify.py <file_path>")
        sys.exit(1)

    file_path = os.path.abspath(os.path.expanduser(sys.argv[1]))
    basename = os.path.basename(file_path)

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    registry = load_registry()
    frameworks = find_frameworks(file_path, registry)

    print(f"═══ verify: {basename} ═══")
    if frameworks:
        fw_names = [fw["name"] for _, fw in frameworks]
        print(f"框架：{', '.join(fw_names)}")
    else:
        print("框架：未注册（只做语法检查）")

    r_syntax = check_syntax(file_path)
    r_logic = check_logic(frameworks)
    r_chain = check_chain(file_path, frameworks)
    r_docs = check_docs(file_path, frameworks)

    print(r_syntax)
    print(r_logic)
    print(r_chain)
    print(r_docs)

    # 写结果文件（mission complete 时读取打分）
    from datetime import datetime
    result = {
        "file": basename,
        "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "results": {
            "syntax": _parse_status(r_syntax),
            "logic": _parse_status(r_logic),
            "chain": _parse_status(r_chain),
            "docs": _parse_status(r_docs),
        },
        "pass_count": sum(1 for r in [r_syntax, r_logic, r_chain, r_docs] if r.startswith("✅")),
        "total": 4,
    }
    try:
        with open(VERIFY_RESULT_PATH, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


if __name__ == "__main__":
    main()
