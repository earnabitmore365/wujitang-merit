#!/bin/bash
# 自动进化 hook — PreCompact / SessionEnd 触发
# 后台跑，不阻塞主会话

# 从 stdin 读取 hook JSON，提取 cwd
CWD=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('cwd',''))" 2>/dev/null)

HOME_DIR="$HOME"

# 按 cwd 判断项目
if [ "$CWD" = "$HOME_DIR/.claude" ]; then
  PROJECT="taiji"
elif [ "$CWD" = "$HOME_DIR/project/auto-trading" ]; then
  PROJECT="auto-trading"
else
  exit 0
fi

LOG="/tmp/evolve_hook_${PROJECT}.log"
nohup bash "$HOME_DIR/.claude/evolve.sh" "$PROJECT" > "$LOG" 2>&1 &

echo "🧬 evolver 已在后台启动（$PROJECT），日志：$LOG"
