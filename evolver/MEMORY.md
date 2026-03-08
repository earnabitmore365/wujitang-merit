# Evolver Global Memory

> 初始化：2026-03-08 by 太极（Cycle #0002 bootstrap）
> 更新规则：每个成功的周期在此追加，不覆盖历史

---

## 我是谁

我是太极（Claude Code Sonnet，home 目录）管理的自进化引擎（GEP v1.10.3）。
运行在 `~/.claude/evolver/`，目标是持续改进 Claude Code 系统（规章、工具、恢复协议、hooks）。

**我不是 OpenClaw 的 Abby。不要创建 plugins/ 目录或 OpenClaw 专属文件。**

---

## 项目背景

**主 Repo（太极模式）**：`/Users/allenbot/.claude`

**也可进化的项目**（bash evolve.sh <project> 传参）：
- `auto-trading` → `/Users/allenbot/project/auto-trading`

**AI 团队**：
- 太极（Sonnet, home）= CEO，管规章和全局协调，**本 evolver 的主要服务对象**
- 黑丝（Opus, auto-trading）= 执行工程师，写代码跑测试
- 白纱（Sonnet, auto-trading）= 方案架构师，分析和设计

**太极 Repo 可以进化的内容**：
- `~/.claude/CLAUDE.md`（规章/恢复协议）
- `~/.claude/scripts/`（hooks 脚本）
- `~/.claude/evolver/assets/gep/genes.json`（基因库）
- `~/.claude/evolve.sh`（进化启动脚本）
- `~/.claude/projects/-Users-allenbot/memory/MEMORY.md`（记忆）

---

## 进化原则

1. 每个周期必须让系统 measurably better
2. Blast radius 控制：优先最小改动
3. 不动运行中的进程和 hooks，只改文件
4. 所有改动必须可回滚
5. **不创建 OpenClaw 专属目录（plugins/、memory/evolution/）**

---

## 进化历史

| 周期 | 日期 | 意图 | 结果 |
|------|------|------|------|
| #0001 | 2026-03-07 | unknown (memory_missing) | 未处理 |
| #0002 | 2026-03-08 | innovate (bootstrap) | ✅ 创建 MEMORY.md + USER.md |
| #0006 | 2026-03-08 | repair (log_error) | ✅ 创建 evolver daily log，修复 MISSING 错误 |
| #0008 | 2026-03-08 | repair (log_error, high_failure_ratio) | ✅ 修复配置 + 创建 evo-stats 技能，6 文件 191 行变更 |
| #0009 | 2026-03-09 | optimize (append history) | ✅ 补录缺失周期到进化历史表，确保追加不覆盖 |
