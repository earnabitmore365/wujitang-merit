#!/bin/bash
# 自动进化 hook — PreCompact / SessionEnd 触发（全局级）
# auto-trading 由项目级 hooks 直接调 evolve.sh，不经过此文件
# 锁机制已在 evolve.sh 本身，此处不需要

STDIN_DATA=$(cat)
CWD=$(echo "$STDIN_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('cwd',''))" 2>/dev/null)

case "$CWD" in
  "$HOME/.claude"|"$HOME")
    LOG="/tmp/evolve_hook_taiji.log"
    nohup bash "$HOME/.claude/evolver/evolve.sh" taiji > "$LOG" 2>&1 &
    echo "🧬 evolver 已在后台启动（taiji），日志：$LOG"
    ;;
esac
