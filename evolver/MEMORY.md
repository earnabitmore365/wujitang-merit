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
| #0084-90 | 03-16 | optimize ×7 (narrative+MEMORY+gene integrity) | ✅ 退休gene_bootstrap_memory_files，归档乱序/污染/错配条目×4，合并pre-crossover条目为归档块（-19行），去重MEMORY行，补录ghost gene，修正genes.json registered_by，基因池8→7条，narrative 67→53行 |
| #0091 | 03-16 | innovate (evo-lint skill) | ✅ 创建 evo-lint 技能（演化数据完整性校验器），检查时序乱序/意图错配/信号污染/基因引用/重复条目，注册 gene_innovate_evo_lint 到 genes.json（第9条），5文件~230行 |
| #0092 | 03-16 | optimize (narrative+MEMORY dedup) | ✅ 归档乱序污染条目11:57入CONSOLIDATED块（第4个bookkeeping周期），去重MEMORY 4行（#0085/#0086/#0089/#0090已被批次行覆盖），narrative 63→59行 |
| #0093-97 | 03-17~20 | optimize ×5 (narrative integrity + tail cleanup) | ✅ 归档/合并乱序条目，修正3处REPAIR→OPTIMIZE意图错配，信号去污(204→40字符)，幻影条目清理，evo-lint验证0问题，narrative 92→63行 |
| #0098 | 03-21 | optimize (narrative+MEMORY noise reduction) | ✅ 合并8条narrative尾部条目(03-17~20)为1个CONSOLIDATED块（修正INNOVATE→OPTIMIZE意图错配），合并5条MEMORY行为1行批次摘要，evo-lint 0问题，narrative 92→64行，MEMORY 71→67行，2文件~33行 |
| #0099 | 03-21 | optimize (narrative integrity fixes) | ✅ 修正2处意图错配(REPAIR/INNOVATE→OPTIMIZE)，移除Strategy噪音段（4行），修复截断result文本，清洗信号污染，标注retired gene引用，narrative 84→80行，2文件~8行 |
| #0100 | 03-21 | innovate (prompt-budget-analyzer skill) | ✅ 创建 prompt-budget-analyzer 技能，分析 GEP 提示词组成（按 Context 区域拆分行/字节/占比），追踪跨周期膨胀趋势，发现 Capsule Preview +2080%/Gene Preview +82% 为最大膨胀源，注册 gene_innovate_prompt_budget_analyzer（第10条），3 文件 ~210 行 |
| #0101 | 03-21 | innovate (evo-narrative-compactor skill) | ✅ 创建 evo-narrative-compactor 技能（自动 narrative 压缩器），解析 narrative 为结构化块，识别3+相邻同基因条目自动合并为 CONSOLIDATED 块，支持 dry-run/apply 模式，注册 gene_innovate_narrative_compactor（第10条活跃基因），安装到 ~/.claude/skills/，3 文件 ~220 行 |
| #0102 | 03-21 | optimize (validate-modules + intent fix) | ✅ gene_gep_optimize_prompt_and_assets 命中 protocol_drift，validate-modules.js 兼容垫片优化（1 文件 / 5 行），Note: 意图标签 INNOVATE→OPTIMIZE 已修正 |
| #0103 | 03-21 | optimize (narrative + signal cleanup) | ✅ gene_gep_optimize_prompt_and_assets 命中 protocol_drift，1 文件 10 行。Note: intent INNOVATE→OPTIMIZE |
| #0104 | 03-21 | optimize (stagnation signal) | ✅ gene_auto_53538cc4 (retired) 命中信号，4 文件 33 行。Note: intent INNOVATE→OPTIMIZE |
| #0105 | 03-22 | innovate (evolution-scorecard skill) | ✅ 创建 evolution-scorecard 技能（量化健康评分器 0-100），聚合6项加权指标（成功率/创新比/零变更率/基因多样性/停滞频率/速度），输出复合分数+字母等级+改进建议，注册 gene_innovate_evolution_scorecard（第11条），安装到 ~/.claude/skills/，3 文件 ~210 行 |
| #0106-12 | 03-22~23 | optimize ×7 (narrative+gene integrity) | ✅ 意图错配修正×6(INNOVATE→OPTIMIZE)，时序乱序修复×3，信号去污×3，retired gene标注+stagnation信号×2(4文件25行)，CONSOLIDATED块合并(-6行)，gene signals_match根因修复(移除force_innovation)，failure抑制标记添加，MEMORY批次合并 |
| #0113 | 03-23 | optimize (zero change) | ⚠️ gene_gep_optimize_prompt_and_assets 零变更周期，意图错配 INNOVATE→OPTIMIZE + 信号污染(raw user message)，已在#0114合并修正 |
| #0116 | 03-23 | optimize (narrative+gene integrity) | ✅ 修正2处意图错配(INNOVATE→OPTIMIZE)，信号去污(raw user message→append_only_history)，时序乱序修复(12:24条目恢复到15:21之前)，retired gene标注+scope修正(4→9 files/50→178 lines)，补录genes.json缺失epigenetic mark(cycle_0113)，3文件~20行 |
| #0117 | 03-24 | optimize (narrative consolidation + gene suppression) | ✅ 合并4条连续失败narrative条目(03-23 11:26~12:53)为1个CONSOLIDATED块（108→97行，-11行），修正4处INNOVATE→OPTIMIZE意图错配，信号去污(raw Chinese→append_only_history)，补录genes.json批次失败抑制标记(boost -0.30)，2文件~15行 |
