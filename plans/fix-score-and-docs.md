# 遗留清单 1-2-3

## 任务

1. **白纱积分复核**：--deposit 5 被石卫解析成计划项 bug，补回错扣分
2. **claude_code.md 补踩坑**：channel 禁用 EnterPlanMode/ExitPlanMode/AskUserQuestion
3. **stone_guard 设计文档更新**：自造 plan mode（pending→activate→active）

## 步骤

### 1. 白纱积分复核
- 查 credit_manager.py mission_submit 的 --deposit 解析逻辑
- 修复 bug（--deposit 应是押金参数不是计划项）
- 补回白纱错扣的分

### 2. claude_code.md 踩坑记录
- 读当前 claude_code.md 踩坑清单
- 追加：channel flag 禁用 plan mode 三工具

### 3. stone_guard 设计文档
- 读 stone_guard_v7_design.md
- 追加自造 plan mode 章节（pending/activate 流程）

## 涉及文件

- `~/.claude/merit/credit_manager.py`（修 --deposit bug）
- `/Volumes/SSD-2TB/文档/claude_code.md`（踩坑清单）
- `~/.claude/projects/-Users-allenbot/memory/stone_guard_v7_design.md`（设计文档）
