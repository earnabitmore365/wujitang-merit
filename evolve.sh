#!/bin/bash
# 太极级 — 自进化启动脚本（Claude Code bridge）
# 用法：
#   bash ~/.claude/evolve.sh taiji        # 太极自进化
#   bash ~/.claude/evolve.sh auto-trading # 项目进化

set -e

PROJECT="${1:-}"
EVOLVER_DIR="$HOME/.claude/tools/evolver"
EVOLVER_WORKSPACE="$HOME/.claude/evolver"

if [ -z "$PROJECT" ]; then
  echo "用法: bash ~/.claude/evolve.sh <project>"
  echo "  project: taiji | auto-trading"
  exit 1
fi

if [ "$PROJECT" = "taiji" ]; then
  REPO_ROOT="$HOME/.claude"
  SESSIONS_DIR="$HOME/.claude/projects/-Users-allenbot"
else
  REPO_ROOT="$HOME/project/$PROJECT"
  PROJECT_ENCODED=$(echo "$REPO_ROOT" | sed 's|/|-|g')
  SESSIONS_DIR="$HOME/.claude/projects/${PROJECT_ENCODED}"
fi

cd "$REPO_ROOT"

# ── Step 0: Pre-commit snapshot ─────────────────────────────────────────
# 防止 rollback 把手动改的文件一起撤掉
# git add -u 只 stage 已 tracked 文件的修改，不会意外提交敏感文件
if ! git diff --quiet HEAD 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
  echo "📌 提交 pre-evolve snapshot..."
  git add -u
  git -c user.name="太极" -c user.email="taiji@claude.local" \
    commit -m "pre-evolve snapshot $(date '+%Y-%m-%d %H:%M:%S')" || true
fi

# ── Step 1: 生成 GEP Prompt → 保存到带时间戳的新文件 ──────────────────
echo "🧬 生成 GEP Prompt..."
TIMESTAMP=$(date +%s)000
PROMPT_FILE="$EVOLVER_WORKSPACE/evolution/gep_prompt_run_${TIMESTAMP}.txt"

MEMORY_DIR="$EVOLVER_WORKSPACE" \
OPENCLAW_WORKSPACE="$EVOLVER_WORKSPACE" \
EVOLVER_REPO_ROOT="$REPO_ROOT" \
AGENT_SESSIONS_DIR="$SESSIONS_DIR" \
EVOLVE_BRIDGE=false \
EVOLVER_ROLLBACK_MODE=stash \
node "$EVOLVER_DIR/index.js" run "${@:2}" > "$PROMPT_FILE"

# ── Step 2: 使用刚刚生成的 Prompt ────────────────────────────────────
LATEST="$PROMPT_FILE"
RESPONSE_FILE="$EVOLVER_WORKSPACE/evolution/gep_response_run_${TIMESTAMP}.json"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "GEP Prompt: $LATEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Step 3: Claude Code headless 执行 ────────────────────────────────
# 在 /tmp/claude-evolver 下运行，避免 claude 把 ~/.claude 路径编码成 --claude（双横线）
echo "🤖 Claude Code 执行中..."
mkdir -p /tmp/claude-evolver
(cd /tmp/claude-evolver && cat "$LATEST" | env -u CLAUDECODE claude -p \
  --allowedTools "Read,Write,Edit,Bash") \
  > "$RESPONSE_FILE"

# ── Step 4: Solidify ─────────────────────────────────────────────────
# 确保 validate-modules.js shim 存在（新项目自动补，已有的不覆盖）
mkdir -p "$REPO_ROOT/scripts"
cp -n "$HOME/.claude/scripts/validate-modules.js" "$REPO_ROOT/scripts/validate-modules.js" 2>/dev/null || true
echo "💾 Solidify..."
MEMORY_DIR="$EVOLVER_WORKSPACE" \
OPENCLAW_WORKSPACE="$EVOLVER_WORKSPACE" \
EVOLVER_REPO_ROOT="$REPO_ROOT" \
EVOLVER_ROLLBACK_MODE=stash \
node "$EVOLVER_DIR/index.js" solidify

# ── 写通知给太极 ─────────────────────────────────────────────────────────
NOTIF_FILE="$EVOLVER_WORKSPACE/cycle_notifications.jsonl"
LAST_CYCLE=$(tail -20 "$EVOLVER_WORKSPACE/evolution/evolution_narrative.md" 2>/dev/null | grep -E "^### " | tail -1 || echo "")
LAST_GENE=$(echo "$LAST_CYCLE" | grep -oE "Gene: [^ |]+" | sed 's/Gene: //' || echo "unknown")
LAST_SCOPE=$(echo "$LAST_CYCLE" | grep -oE "Scope: [^|]+" | sed 's/Scope: //' || echo "?")
LAST_STATUS=$(echo "$LAST_CYCLE" | grep -oE "(success|failed)" || echo "unknown")

echo "{\"ts\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"source\":\"claude-code\",\"run\":\"run_${TIMESTAMP}\",\"gene\":\"${LAST_GENE}\",\"scope\":\"${LAST_SCOPE}\",\"status\":\"${LAST_STATUS}\"}" >> "$NOTIF_FILE"

echo ""
echo "✅ 进化完成（run_${TIMESTAMP}）"
