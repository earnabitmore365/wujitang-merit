#!/bin/bash
# PostToolUse hook: Write/Edit 后自动跑 py_compile
# stdout 用 additionalContext JSON 格式注入回对话

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# 只处理 .py 文件
if echo "$FILE_PATH" | grep -qE '\.py$'; then
    # 检查文件存在
    if [ -f "$FILE_PATH" ]; then
        RESULT=$(python3 -m py_compile "$FILE_PATH" 2>&1)
        if [ $? -ne 0 ]; then
            # 编译错误：注入回对话让 AI 修复
            CLEAN_RESULT=$(echo "$RESULT" | tr '"' "'" | tr '\n' ' ')
            echo "{\"additionalContext\": \"⚠️ py_compile 错误 [${FILE_PATH}]: ${CLEAN_RESULT}\"}"
        fi
    fi
fi
exit 0
