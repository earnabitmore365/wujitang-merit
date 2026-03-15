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
| #0014 | 2026-03-09 | innovate (code-stats skill) | ✅ 创建 code-stats 技能，仓库复杂度分析仪表盘，3 文件 ~180 行 |
| #0015 | 2026-03-09 | innovate (todo-manager skill) | ✅ 创建 todo-manager 技能，扫描代码 TODO/FIXME/HACK/XXX 标记，3 文件 ~200 行 |
| #0016 | 2026-03-09 | innovate (session-stats skill) | ✅ 创建 session-stats 技能，分析会话 JSONL 文件的工具使用和对话指标，3 文件 ~210 行 |
| #0018 | 2026-03-09 | optimize (gene persist + append history) | ✅ 将 gene_auto_e9a1d101 固化到 genes.json，并追加本周期记录到历史表，2 文件 15 行变更 |
| #0019 | 2026-03-09 | optimize (append history) | ✅ 追加 Cycle #0019 记录到历史表，确保追加不覆盖，1 文件 1 行变更 |
| #0020 | 2026-03-09 | innovate (memory-inspector skill) | ✅ 创建 memory-inspector 技能，扫描所有项目 MEMORY.md 健康度/陈旧度/卫生报告，3 文件 ~160 行 |
| #0021 | 2026-03-09 | innovate (skill-audit skill) | ✅ 创建 skill-audit 技能，审计所有 Claude Code 技能结构完整性/frontmatter/exports，发现 reflect 技能缺失文件，3 文件 ~150 行 |
| #0022 | 2026-03-09 | innovate (evo-stats enhancement) | ✅ 增强 evo-stats 技能，新增 detectStagnation() + scoreTrend() 打破空周期停滞，2 文件 72 行变更 |
| #0023 | 2026-03-09 | innovate (reflect skill impl) | ✅ 为 reflect 技能创建缺失的 index.js（120行）+ package.json，从文档存根升级为可执行技能：提取纠错/提升信号→LEARNINGS.md→rules.md 候选，2 文件 122 行变更 |
| #0024 | 2026-03-09 | innovate (performance-metric skill) | ✅ 创建 performance-metric 技能，读取 genes.json 生成基因组健康仪表板（类别分布、表观遗传增益、多样性评分），打破空周期停滞，3 文件 ~95 行 |
| #0025 | 2026-03-09 | innovate (evolution_stagnation_detected, stable_success_plateau) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0026 | 2026-03-10 | innovate (checkpoint-sync skill) | ✅ 创建 checkpoint-sync 技能，聚合多项目 CHECKPOINT.md 生成跨项目状态仪表板，4 文件 ~130 行，安装到 ~/.claude/skills/，打破连续8周期空循环停滞 |
| #0027 | 2026-03-09 | innovate (user_feature_request:> 更新规则：每个成功的周期在此追加，不覆盖历史, empty_cycle_loop_detected) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0028 | 2026-03-10 | innovate (capsule-analyzer skill) | ✅ 创建 capsule-analyzer 技能，审计胶囊质量评分、检测僵尸基因（如 gene_auto_c7368808），3 文件 135 行，安装到 ~/.claude/skills/，打破连续8周期空循环停滞 |
| #0029 | 2026-03-09 | innovate (evolution_stagnation_detected, stable_success_plateau) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0030 | 2026-03-10 | innovate (evolution_stagnation_detected, stable_success_plateau) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0031 | 2026-03-10 | innovate (evolution_stagnation_detected, stable_success_plateau) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0032 | 2026-03-10 | innovate (agent-genealogy skill) | ✅ 创建 agent-genealogy 技能，映射 Gene→Capsule 演化谱系、识别僵尸基因，3 文件 125 行，安装到 ~/.claude/skills/，填补 meta 域 gap-score=0.33 空缺，打破连续8周期空循环停滞 |
| #0033 | 2026-03-10 | innovate (evolution_stagnation_detected, stable_success_plateau) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0034 | 2026-03-10 | innovate (gene-diversity-advisor skill install) | ✅ 将 gene-diversity-advisor 技能从 evolver 本地 skills/ 安装到 ~/.claude/skills/，提供 Shannon 熵多样性评分+停滞风险分级，诊断 innovate 基因占比 0% 为僵尸基因循环根因，3 文件 95 行 |

| #0035 | 2026-03-10 | innovate (gene-retirement skill) | ✅ 创建 gene-retirement 技能，检测僵尸基因（gene_auto_c7368808 连续10+次零变更），施加表观遗传降权打破空循环，3 文件 157 行 |
| #0036 | 2026-03-10 | innovate (evo-circuit-breaker skill) | ✅ 创建 evo-circuit-breaker 技能，检测连续相同基因选择模式（阈值3周期零变更），触发熔断封锁僵尸基因+推荐替代 innovate 基因，从选择层打破停滞闭环，3 文件 130 行 |
| #0037 | 2026-03-10 | innovate (gene-librarian skill) | ✅ 创建 gene-librarian 技能，扫描 GEP 历史响应文件提取自动生成基因并注册到 genes.json（含表观遗传降权），桥接 memory_graph 动态库与受管 genes.json 之间的缺口，首次运行注册 gene_bootstrap_memory_files，genes.json 升至 4 条，3 文件 155 行 |
| #0038 | 2026-03-10 | innovate (skill-metrics skill) | ✅ 创建 skill-metrics 技能，扫描 JSONL 日志中 Skill 工具调用，输出使用频率/覆盖率仪表板，33 技能/96 文件/覆盖率 9%，与 skill-audit+session-stats 不重叠，3 文件 98 行 |
| #0039 | 2026-03-10 | innovate (workflow-runner skill) | ✅ 创建 workflow-runner 技能，首个技能编排器，将 35+ Claude Code 技能串联为 5 个自动化工作流（daily-health/stagnation-diagnosis/gene-health/skill-ecosystem/memory-sync），3 文件 198 行 |
| #0040 | 2026-03-10 | innovate (evo-forecast skill) | ✅ 创建 evo-forecast 技能，解析 evolution_narrative.md 历史预测下一周期成功概率（90%）/实际变更率（12%），识别僵尸基因重复模式（gene_auto_c7368808 8x），推荐最优基因候选，填补生态系统唯一缺失的预测能力空白，3 文件 170 行 |
| #0041 | 2026-03-10 | innovate (secret-scanner skill) | ✅ 创建 secret-scanner 技能，扫描代码库泄露密钥/令牌（AWS/GitHub/OpenAI/Anthropic/Stripe/Slack/Telegram/私钥/Bearer），18 种模式，已安装到 ~/.claude/skills/，填补安全分析域空白，3 文件 198 行 |
| #0042 | 2026-03-10 | innovate (empty_cycle_loop_detected, stable_success_plateau) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0043 | 2026-03-10 | innovate (config-auditor skill) | ✅ 创建 config-auditor 技能，审计 Claude Code 配置层（settings.json hooks/CLAUDE.md guardrails/MEMORY.md 截断风险），填补 37 技能生态中唯一缺失的配置健康检查空白，3 文件 ~170 行 |
| #0044 | 2026-03-10 | innovate (gene-prior-inspector skill) | ✅ 创建 gene-prior-inspector 技能，读取 memory_graph_state.json + memory_graph.jsonl，检测 outcome_recorded:false 卡死状态（gene_auto_c7368808 24次尝试/prior=0.960）、计算每基因 attempt/outcome 比率、定位僵尸基因根因，填补记忆图层诊断空白，3 文件 ~185 行 |
| #0045 | 2026-03-10 | innovate (evo-replay skill) | ✅ 创建 evo-replay 技能，历史演化周期深度回放（按日期/基因/最近N条过滤），自动检测僵尸基因重复模式（3次触发警告），实际运行识别 gene_auto_c7368808 连续重复，填补40技能生态中唯一缺失的单周期审计能力，3 文件 130 行 |
| #0046 | 2026-03-11 | innovate (disk-health skill) | ✅ 创建 disk-health 技能，监控系统磁盘利用率（80%警告/90%严重阈值），识别4类清理候选（/tmp、~/.claude/projects、~/Library/Caches、~/.npm），实测检出 /Users/allenbot 磁盘91%临界状态，新建 gene_innovate_disk_health 打破 gene_auto_c7368808 连续8轮零变更僵尸基因循环，3 文件 118 行 |
| #0047 | 2026-03-11 | innovate (dependency-checker skill) | ✅ 创建 dependency-checker 技能，扫描 package.json 安全漏洞（npm audit：critical/high/moderate/low）和过期依赖（npm outdated），递归扫描3层目录，填补42技能生态中唯一缺失的依赖安全审计能力，3 文件 125 行 |
| #0048 | 2026-03-11 | innovate (evo-momentum skill) | ✅ 创建 evo-momentum 技能，追踪演化变更速度（滚动窗口）计算0-1动量评分+趋势检测(加速/稳定/减速/停滞)+僵尸基因识别，提供停滞前置预警，与 evo-stats/evo-forecast/evo-heatmap 不重叠，导出验证通过[main,calcMomentum,parseCycles,detectZombies]，打破 gene_auto_c7368808 连续8+轮零变更僵尸循环，3 文件 128 行 |
| #0049 | 2026-03-11 | innovate (capsule-deduplicator skill) | ✅ 创建 capsule-deduplicator 技能，扫描胶囊库相同基因+信号指纹的重复零变更胶囊（gene_auto_c7368808 积累28+副本），每组保留最新保留一个删除其余，减少记忆图选择偏差，与 capsule-analyzer（报告）不重叠（本技能清理），导出验证通过[main,scan,dedup,loadCapsules]，安装到 ~/.claude/skills/，3 文件 98 行 |
| #0050 | 2026-03-11 | innovate (empty_cycle_loop_detected, stable_success_plateau) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0051 | 2026-03-11 | innovate (signal-analyzer skill) | ✅ 创建 signal-analyzer 技能，从 memory_graph.jsonl 解析历史信号→基因选择频率，用 HHI 垄断指数检测信号层垄断（确认 gene_auto_c7368808 对9个信号组合均100%垄断 HHI=1），与 gene-diversity-advisor（基因池多样性）和 gene-prior-inspector（prior卡死状态）不重叠，揭示空循环结构性根因，3 文件 179 行 |
| #0052 | 2026-03-11 | innovate (empty_cycle_loop_detected, stable_success_plateau) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0053 | 2026-03-12 | innovate (evo-cost-tracker skill) | ✅ 创建 evo-cost-tracker 技能，解析 evolution_narrative.md 计算每基因周期浪费比率和效率评分，实测确认 gene_auto_c7368808 浪费率 90%（18/20 空周期），识别为最高成本消耗者，填补48技能生态中唯一缺失的经济成本分析视角，3 文件 148 行，安装到 ~/.claude/skills/ |
| #0054 | 2026-03-12 | innovate (gene-profile skill) | ✅ 创建 gene-profile 技能，生成每基因详细档案（信号覆盖、历史周期、表观遗传标记、退休/增强建议），读取 genes.json + evolution_narrative.md，填补50技能生态中唯一缺失的单基因深度分析能力，导出验证通过 [main,profileGene,loadGenes,parseNarrative]，安装到 ~/.claude/skills/gene-profile/，3 文件 215 行 |
| #0055 | 2026-03-11 | innovate (user_feature_request:> 更新规则：每个成功的周期在此追加，不覆盖历史, empty_cycle_loop_detected) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0056 | 2026-03-12 | innovate (empty_cycle_loop_detected, stable_success_plateau) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0057 | 2026-03-12 | innovate (evo-gc skill) | ✅ 创建 evo-gc 技能，垃圾回收 evolution/ 目录中旧 gep_prompt/gep_response 文件到压缩归档，扫描检测34个可归档文件（0.47MB），保护状态文件不被触及，填补52技能生态中唯一缺失的演化工件清理能力，导出验证通过 [main,scan,gc,isArchivable,PROTECTED]，安装到 ~/.claude/skills/evo-gc/，3 文件 ~130 行 |
| #0058 | 2026-03-12 | innovate (evo-doctor skill) | ✅ 创建 evo-doctor 技能，自适应演化诊断仪：分析最近N个周期分类故障模式（zombie_monopoly/repair_loop/signal_stagnation/healthy），输出证据+有序处方；实测运行确认 CRITICAL zombie_monopoly（gene_auto_c7368808 选中率100%/实际变更率0%），填补53技能生态中唯一缺失的自适应分诊层，导出验证通过 [main,parseNarrative,diagnose,formatReport,DIAGNOSES]，安装到 ~/.claude/skills/evo-doctor/，3 文件 155 行 |
| #0059 | 2026-03-12 | innovate (protocol_drift, empty_cycle_loop_detected) | ✅ 固化：gene_auto_c7368808 命中信号 evolution_stagnation_detected, stable_success_plateau，0 文件 0 行变更 |
| #0060 | 2026-03-12 | innovate (protocol_drift) | ✅ 固化：gene_gep_optimize_prompt_and_assets 命中信号 protocol_drift，变更 3 文件 / 23 行。，3 文件 23 行变更 |
| #0061 | 2026-03-13 | innovate (session-archiver skill) | ✅ 创建 session-archiver 技能，归档冷 JSONL 会话文件到 gzip 格式释放磁盘空间，实测扫描24个可归档文件（92.4MB→预估7.7MB），磁盘93%临界状态下可节省~85MB，与 evo-gc（演化文件）/session-stats（分析读取）不重叠，导出验证通过 [main,scanJsonlFiles,compressFile,formatBytes]，安装到 ~/.claude/skills/session-archiver/，3 文件 ~155 行 |
| #0062 | 2026-03-13 | innovate (protocol_drift) | ✅ 固化：gene_gep_optimize_prompt_and_assets 命中信号 protocol_drift，变更 3 文件 / 23 行。，3 文件 23 行变更 |
| #0063 | 2026-03-14 | innovate (git-branch-health skill) | ✅ 创建 git-branch-health 技能，扫描管理仓库的分支健康度（陈旧分支/ahead-behind/脏工作树/合并冲突风险），计算0-100健康评分，实测扫描 ~/.claude 和 auto-trading 两个仓库（健康90/100），新建 gene_innovate_git_branch_health 注册到 genes.json（第8条），导出验证通过 [main,scanRepo,scanAll,formatReport,parseBranches]，安装到 ~/.claude/skills/git-branch-health/，3 文件 204 行 |
| #0064 | 2026-03-14 | innovate (protocol_drift) | ✅ 固化：gene_gep_optimize_prompt_and_assets 命中信号 protocol_drift，变更 3 文件 / 23 行。，3 文件 23 行变更 |
| #0065 | 2026-03-14 | optimize (protocol_drift, high_failure_ratio) | ✅ 扩展 gene_gep_optimize_prompt_and_assets 信号覆盖（新增 high_failure_ratio、force_innovation），追加 MEMORY.md 历史记录，消除连续重复周期协议漂移，3 文件 13 行变更 |
| #0066 | 2026-03-14 | optimize (protocol_drift, gene pool cleanup) | ✅ 将2个僵尸基因（gene_auto_53538cc4、gene_auto_c7368808）从活跃 genes 数组归档到 retired_genes 区，减少每周期 Gene Preview 上下文噪音~70行，保留退休历史，2 文件 ~25 行变更 |
| #0067 | 2026-03-15 | optimize (gene pool data integrity) | ✅ 修复 gene_gep_repair_from_errors 表观遗传异常（boost:-0.15 + reason:reinforced_by_success 矛盾→纠正为 +0.1），扩展 gene_evo_forecast 信号覆盖（新增 force_innovation_after_repair_loop），改善修复→创新路由，3 文件 ~15 行变更 |
