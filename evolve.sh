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
else
  REPO_ROOT="$HOME/project/$PROJECT"
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
TIMESTAMP=$(date '+%s%3N')
PROMPT_FILE="$EVOLVER_WORKSPACE/evolution/gep_prompt_run_${TIMESTAMP}.txt"

MEMORY_DIR="$EVOLVER_WORKSPACE" \
OPENCLAW_WORKSPACE="$EVOLVER_WORKSPACE" \
EVOLVER_REPO_ROOT="$REPO_ROOT" \
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
echo "🤖 Claude Code 执行中..."
cat "$LATEST" | env -u CLAUDECODE claude -p \
  --allowedTools "Read,Write,Edit,Bash" \
  > "$RESPONSE_FILE"

# ── Step 4: Solidify ─────────────────────────────────────────────────
echo "💾 Solidify..."
MEMORY_DIR="$EVOLVER_WORKSPACE" \
OPENCLAW_WORKSPACE="$EVOLVER_WORKSPACE" \
EVOLVER_REPO_ROOT="$REPO_ROOT" \
EVOLVER_ROLLBACK_MODE=stash \
node "$EVOLVER_DIR/index.js" solidify

echo ""
echo "✅ 进化完成（run_${TIMESTAMP}）"
