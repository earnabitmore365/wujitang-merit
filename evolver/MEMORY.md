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
| #0001-09 | 03-07~09 | bootstrap/repair/optimize | ✅ 引擎初始化（MEMORY.md/USER.md/daily-log/配置修复/evo-stats技能/历史补录） |
| #0014-24 | 03-09 | innovate ×8 + optimize ×2 | ✅ 技能：code-stats, todo-manager, session-stats, memory-inspector, skill-audit, evo-stats+, reflect, performance-metric；基因固化+历史补录 |
| #0025-33 | 03-09~10 | zombie ×6 | ⚠️ gene_auto_c7368808 空周期，已退休 |
| #0026-41 | 03-10 | innovate ×11 | ✅ 技能：checkpoint-sync, capsule-analyzer, agent-genealogy, gene-diversity-advisor, gene-retirement, evo-circuit-breaker, gene-librarian, skill-metrics, workflow-runner, evo-forecast, secret-scanner |
| #0042-59 | 03-10~12 | zombie ×6 | ⚠️ gene_auto_c7368808 空周期，已退休 |
| #0043-58 | 03-10~12 | innovate ×12 | ✅ 技能：config-auditor, gene-prior-inspector, evo-replay, disk-health, dependency-checker, evo-momentum, capsule-deduplicator, signal-analyzer, evo-cost-tracker, gene-profile, evo-gc, evo-doctor |
| #0060-64 | 03-12~14 | innovate ×5 | ✅ prompt优化×3(各3文件23行) + session-archiver + git-branch-health |
| #0065-79 | 03-14~16 | optimize ×13 + repair ×1 + innovate ×1 | ✅ 信号覆盖扩展、基因池清理(8→6基因)、数据完整性修复(4幽灵修复)、validate-modules修复、narrative压缩(144→35行)、MEMORY.md多轮噪音压缩 |
| #0080 | 03-16 | optimize (history deep compression) | ✅ 压缩MEMORY.md历史表为日期批次摘要，减少~48行/~7KB上下文注入噪音 |
| #0082 | 03-16 | innovate (gene-crossover skill) | ✅ 创建 gene-crossover 技能：遗传交叉算子，对高适应度基因交叉组合产生杂交后代（信号union+策略交替选取+约束取严），增加基因多样性打破停滞，注册 gene_innovate_gene_crossover 到 genes.json（第7条），4 文件 ~190 行 |
| #0083 | 03-16 | innovate (evo-digest skill) | ✅ 创建 evo-digest 技能，解析 narrative+genes 生成老板友好的演化摘要报告（概览/最近变更/基因排行/健康指标），注册 gene_innovate_evo_digest（第8条），安装到 ~/.claude/skills/，3 文件 170 行 |
| #0084 | 03-16 | optimize (gene pool + narrative cleanup) | ✅ 退休 gene_bootstrap_memory_files（前置条件永久不满足），归档3条已退休基因失败记录（9→1行），基因池8→7条活跃 |
| #0085 | 03-16 | optimize (narrative chronological reorder) | ✅ 修复 narrative 时间序错乱（5条跨03-15/16边界的乱序条目），归档条目移至正确时间位置，59→65行 |
| #0086 | 03-16 | optimize (narrative dedup + gene metadata fix) | ✅ 合并2条重复06:35/06:36固化条目为1条归档行（8行→1行），修复genes.json中2个registered_by错误（gene_crossover: 0080→0082, evo_digest: 0081→0083） |
