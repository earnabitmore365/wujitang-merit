#!/bin/bash
# Haiku Gate 安装脚本
# 用法: bash install.sh

set -e

CLAUDE_DIR="$HOME/.claude"
SCRIPTS_DIR="$CLAUDE_DIR/scripts"
SETTINGS="$CLAUDE_DIR/settings.json"
CREDIT="$CLAUDE_DIR/credit.json"
SESSION_START="$SCRIPTS_DIR/session_start.py"
LEARNINGS_DIR="$CLAUDE_DIR/learnings"

echo "╔══════════════════════════════════════╗"
echo "║   Haiku Gate 信用积分系统 安装       ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 1. 复制脚本
echo "→ 复制脚本到 $SCRIPTS_DIR/"
mkdir -p "$SCRIPTS_DIR"
cp scripts/haiku_gate.py "$SCRIPTS_DIR/"
cp scripts/credit_manager.py "$SCRIPTS_DIR/"
echo "  ✅ haiku_gate.py"
echo "  ✅ credit_manager.py"

# 2. 初始化积分（不覆盖已有）
if [ ! -f "$CREDIT" ]; then
    cp credit.json.template "$CREDIT"
    echo "  ✅ credit.json 已初始化"
else
    echo "  ⏭️  credit.json 已存在，跳过"
fi

# 3. 创建 learnings 目录
mkdir -p "$LEARNINGS_DIR"
echo "  ✅ learnings/ 目录就绪"

# 4. 更新 settings.json — 添加 PreToolUse hook
if [ -f "$SETTINGS" ]; then
    if grep -q "haiku_gate.py" "$SETTINGS"; then
        echo "  ⏭️  settings.json 已包含 haiku_gate hook"
    else
        echo ""
        echo "⚠️  请手动在 settings.json 的 PreToolUse 数组中添加："
        echo '  {'
        echo '    "matcher": "Write|Edit|Agent",'
        echo '    "hooks": [{"type": "command", "command": "python3 ~/.claude/scripts/haiku_gate.py"}]'
        echo '  }'
        echo ""
        echo "  （自动修改 settings.json 有风险，手动更安全）"
    fi
else
    echo "  ⚠️  settings.json 不存在，请先初始化 Claude Code"
fi

# 5. 注入 session_start.py — 添加 inject_credit_status
if [ -f "$SESSION_START" ]; then
    if grep -q "inject_credit_status" "$SESSION_START"; then
        echo "  ⏭️  session_start.py 已包含信用状态注入"
    else
        echo ""
        echo "⚠️  请手动在 session_start.py 的 main() 函数中添加："
        echo '  # 在 inject_evolver_notifications() 之前加：'
        echo '  inject_credit_status(cwd)'
        echo ""
        echo "  inject_credit_status 函数定义见 scripts/inject_credit_status.py"
    fi
else
    echo "  ⏭️  session_start.py 不存在，跳过"
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   安装完成                           ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "验证命令："
echo "  python3 $SCRIPTS_DIR/credit_manager.py show"
echo ""
echo "文档："
echo "  docs/credit_system_design.md"
