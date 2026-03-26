#!/bin/bash
# 通讯部 — 新项目脚手架生成器
# 用法：
#   new_project.sh <project-name> [--trading]
#   new_project.sh my-app
#   new_project.sh my-trading-bot --trading
#
# 在 ~/project/<name>/ 下生成标准项目文件骨架
# rules.md 不在项目目录生成（由 hook 体系管理，在 ~/.claude/projects/ 下）

PROJECT_NAME=""
IS_TRADING=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --trading) IS_TRADING=true; shift ;;
        *) PROJECT_NAME="$1"; shift ;;
    esac
done

if [ -z "$PROJECT_NAME" ]; then
    echo "用法: new_project.sh <project-name> [--trading]"
    echo "  例: new_project.sh my-app"
    echo "  例: new_project.sh my-trading-bot --trading"
    exit 1
fi

PROJECT_DIR="$HOME/project/$PROJECT_NAME"
DATE=$(date +%Y-%m-%d)

if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️  项目目录已存在: $PROJECT_DIR"
    echo "   如需重新生成，请先删除目录"
    exit 1
fi

echo "🚀 创建项目: $PROJECT_NAME → $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"

# --- CLAUDE.md ---
cat > "$PROJECT_DIR/CLAUDE.md" << EOF
# $PROJECT_NAME — CLAUDE.md

> 创建日期: $DATE
> ⛔ 此文件头部（letterhead）由太极维护，黑丝白纱不得修改

---

## 项目概述

（待太极完善）

## 角色分工

- **黑丝（Opus）**：主力，规划+执行
- **白纱（Sonnet）**：支援，查资料/整理文档/支线任务

## 协作流程

（待太极完善）
EOF

# --- CHECKPOINT.md ---
cat > "$PROJECT_DIR/CHECKPOINT.md" << EOF
# $PROJECT_NAME — CHECKPOINT

> 最后更新: $DATE

## 当前状态

🆕 项目刚创建，待启动

## 下一步

（待规划）
EOF

# --- handoff 文件 ---
cat > "$PROJECT_DIR/handofffromtaiji.md" << EOF
# 太极 → 黑丝/白纱

> $DATE

（暂无传达事项）
EOF

cat > "$PROJECT_DIR/handofftotaiji.md" << EOF
# 黑丝/白纱 → 太极

> $DATE

（暂无回信）
EOF

# --- context.md（给外部顾问看） ---
cat > "$PROJECT_DIR/context.md" << EOF
# $PROJECT_NAME — 项目上下文

> 此文件用于向外部 AI 顾问（Gemini/Grok 等）提供项目背景
> 最后更新: $DATE

## 项目目标

（待填写）

## 技术栈

（待填写）

## 当前阶段

🆕 刚创建
EOF

# --- review.md ---
cat > "$PROJECT_DIR/review.md" << EOF
# $PROJECT_NAME — 外部审查意见

> 记录 Gemini/Grok 等外部 AI 的审查反馈
> 最后更新: $DATE

（暂无审查记录）
EOF

# --- Memory 目录（在 ~/.claude/projects/ 下） ---
PATH_ENCODED=$(echo "$PROJECT_DIR" | sed 's|^/|-|;s|/|-|g')
MEMORY_DIR="$HOME/.claude/projects/$PATH_ENCODED/memory"
mkdir -p "$MEMORY_DIR"

cat > "$MEMORY_DIR/MEMORY.md" << EOF
# $PROJECT_NAME — Memory

> 创建日期: $DATE

## 上次会话要点

（新项目，暂无记录）

## 会话索引（最新在最上面）
| # | ID | 日期 | 核心内容 |
|---|-----|------|----------|
EOF

# --- Trading 专属文件 ---
if $IS_TRADING; then
    cat > "$PROJECT_DIR/DESIGN_DECISIONS.md" << EOF
# $PROJECT_NAME — 设计决策库

> 记录关键设计决策的 WHY
> 最后更新: $DATE

（暂无决策记录）
EOF
    echo "📈 Trading 模式：已生成 DESIGN_DECISIONS.md"
fi

echo ""
echo "✅ 项目脚手架已生成:"
echo "   📁 $PROJECT_DIR/"
ls -1 "$PROJECT_DIR/" | sed 's/^/      /'
echo "   📁 $MEMORY_DIR/"
ls -1 "$MEMORY_DIR/" | sed 's/^/      /'
echo ""
echo "⚠️  下一步: 太极需手动完善 CLAUDE.md 头部（letterhead）"
