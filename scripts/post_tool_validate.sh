#!/bin/bash
# PostToolUse hook: Write/Edit 后自动跑 py_compile + 太极审计
# stdout 用 additionalContext JSON 格式注入回对话

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
CWD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null)

# 只处理 .py 文件的语法检查
if echo "$FILE_PATH" | grep -qE '\.py$'; then
    if [ -f "$FILE_PATH" ]; then
        RESULT=$(python3 -m py_compile "$FILE_PATH" 2>&1)
        if [ $? -ne 0 ]; then
            CLEAN_RESULT=$(echo "$RESULT" | tr '"' "'" | tr '\n' ' ')
            echo "{\"additionalContext\": \"⚠️ py_compile 错误 [${FILE_PATH}]: ${CLEAN_RESULT}\"}"
        fi
    fi
fi

# 太极审计：太极修改功过格核心文件时自动记录
# 只在 home 目录（太极的 cwd）触发
AUDIT_FILES="merit_gate.py credit_manager.py credit.json merit_judge.py merit_post_audit.py session_start.py"
BASENAME=$(basename "$FILE_PATH" 2>/dev/null)
if echo "$CWD" | grep -qv "auto-trading"; then
    for AF in $AUDIT_FILES; do
        if [ "$BASENAME" = "$AF" ]; then
            TS=$(date -u +"%Y-%m-%dT%H:%M:%S")
            AUDIT_LOG="$HOME/.claude/taiji_audit.json"
            python3 -c "
import json, os
log_path = '$AUDIT_LOG'
entry = {'ts': '$TS', 'file': '$FILE_PATH', 'action': 'modified'}
data = []
if os.path.exists(log_path):
    try:
        with open(log_path) as f:
            data = json.load(f)
    except: pass
data.append(entry)
if len(data) > 200:
    data = data[-200:]
with open(log_path, 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
" 2>/dev/null
            break
        fi
    done
fi

exit 0
