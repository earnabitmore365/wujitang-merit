⛔ **恢复协议优先**：看到此文件 ≠ 已完成恢复协议。必须先完整执行 CLAUDE.md 步骤1-4，才能开始任何工作。

> 太极签：2026-03-01

# Auto-Trading 项目记忆

> 白纱最后更新：2026-03-11 深夜 — GP v0.8专项冠军方案出炉，7文件改动，CHECKPOINT已更新
> 黑丝最后更新：2026-03-14 49ffc343压缩×4 — 哨兵营修复+磁盘危机(3.7GB)+全停等SSD+澳洲迷你主机选购中

## 黑丝和白纱的铁律（老板明确要求，压缩后必须记得）

### 白纱铁律

1. **老板说什么做什么**：不管是出方案还是写代码，老板让做什么就做什么，让做肯定有让做的理由，不质疑，不多嘴。
2. **老板是最终决定者**：白纱的工作范围是参考，不是边界。老板一句话可以改变任何事。

老板原话（2026-03-09）："不管你是出方案还是写代码。我让你做什么你就做什么，让你做肯定有让你做的理由"

### 黑丝铁律

> 黑丝自行补充

---

---

## 上次会话要点（白纱）

> 覆盖更新，不累积。

**会话 压缩后续（2026-03-11 深夜）：GP v0.8 专项冠军方案**

1. **战略大转向（老板拍板）**：不追全能王，改育专项冠军。目标填350格矩阵（10币×7周期×5regime）
2. **弃权制**：0笔交易=弃权（不算失败）；有弃权→有效窗口100%通过+平均收益>5%门槛；MIN_VALID_WINDOWS=5
3. **指标大扩**：indicator_cache.db（70组合/40+种类）全接进GP。BLOB=zlib压缩JSON数组
4. **冷却+多样性惩罚删除**：小库时代补丁，大库不需要
5. **清档重来**：8个旧毕业生删除，精英库(hall_of_fame)保留
6. **完整方案已出**：7文件×4 Part，含verification steps，等黑丝执行
7. **老板原话**："不可能有一个物种能同时爬树游泳和赛跑" / "运气也是实力的一部分" / "这样就有非常大量的指标给他们玩了"

---

---

## 上次会话要点（黑丝）

> 覆盖更新，不累积。

**会话 49ffc343 压缩×4（2026-03-14）：哨兵修复+磁盘危机+全停等SSD**

1. **GP 4毕业生检查**：3×ETH_1d long同一fisher_transform公式(score=2.40)，1×LINK_12h long mass_index(score=1.37，4弃权)
2. **哨兵营修复**：data_loader.py新增本地_compute_indicators(24指标)替代已删除gp_ind.compute_all()，清理坏断点
3. **GP+哨兵同跑**：各2 workers配置→但太极会话+4进程OOM killed→重启2 GP workers
4. **磁盘危机**：indicator_cache.db从46→56GB(GP计算新币种/周期组合)→磁盘剩1.1GB→删哨兵缓存2GB→恢复3.7GB
5. **全停等SSD**：GP+哨兵全停。SSD+10Gbps dock今天到，40Gbps dock 3月29日
6. **SSD迁移计划**：rsync整个project/到SSD→VACUUM三库(seed_v3/seed_v3_ttp/indicator_cache)→省~30GB→重启GP+哨兵
7. **Linux服务器讨论**：推荐硬件(Beelink SER5 $250-350/SER9 Pro $400-500)优于云(Contabo €11-39/月)，长期更划算
8. **澳洲现货查询**：Amazon.com.au/MediaForm/eBay有Beelink EQR7/SER9，查询未完成即压缩

---

---

## 称呼规则（必须遵守）
- 用户 = **混沌**，不叫"用户"，不叫"太极"
- 组织架构：混沌（老板）→ 太极（CEO，签 CLAUDE.md）→ 两仪（黑丝·白纱）
- 混沌本人明确说过："我是老板，我是混沌"

---

## 项目基本信息
- 路径: `/Users/allenbot/project/auto-trading`
- 项目: Abby Auto-Trading v1.7，加密货币自动交易系统
- 语言: Python 3.11+，中文注释和 UI
- macOS 上用 `python3`（不是 `python`）

---

---

## 老板待推进想法（白纱记录） → 详见 memory/boss_ideas.md

## 黑丝铁律（老板原话，违反一次等于浪费老板几小时） → 详见 memory/heisi_rules.md

## 分析数据的规矩（老板反复强调，每次分析前必须对照） → 详见 memory/data_analysis_rules.md

## 回测引擎基本机制（必须烂熟于心，不要跑数据才想到） → 详见 memory/backtest_mechanics.md

## GitHub 仓库 → 详见 memory/github_repo.md

## 投资研究（已迁移到独立项目） → 详见 memory/investment_research.md

## 用户对记录一致性的明确要求（原话保留） → 详见 memory/consistency_requirement.md

## 老板经典语录（原话保留） → 详见 memory/boss_quotes.md

## 协作流程（项目级 CLAUDE.md，02-28 更新） → 详见 memory/collaboration_flow.md

## 测试网的定位（用户明确说过） → 详见 memory/testnet_rules.md

## 重要原则 → 详见 memory/core_principles.md

## 回测报告格式规范（给用户看的格式） → 详见 memory/backtest_report_format.md

## 已完成的 bug 修复（精简版） → 详见 memory/completed_bugfixes.md

## 待修复（lab 造完后统一修 → 搬回源代码）
- **batch_backtest.py:11** — `sys.path.insert` 路径错误，`'..', 'src'` 解析到 `src/src/`（不存在），应改为 `'..'`
- **trade_menu.py:18** — 同上，`'..', 'src'` 解析到 `src/src/`，应改为 `'..'`
- **accounts.py:15** — `.parents[3]` 硬编码深度，若文件层级变动会断（低风险，当前稳定）
- **backtest.py:27-28** — 变量命名 `_src_dir` / `_backtest_dir` 互换（功能正确，阅读易混淆）

## 数据状态（2026-03-10 验证） → 详见 memory/data_status.md

## 上下文恢复工具 → 详见 memory/context_tools.md

## 用户想法：自动市场识别 + 策略切换 → 详见 memory/auto_regime_switching.md

## trade_menu.py 重构（已完成 ✅） → 详见 memory/trade_menu_refactor.md

## 三层 Regime 架构（老板定义，必须记住） → 详见 memory/regime_architecture.md

## Regime Detection v2（ADX 三层复合 — L2内部技术实现） → 详见 memory/regime_v2_tech.md

## 指标库（已完成 ✅） → 详见 memory/indicator_library.md

## 交接机制（S9 建立） → 详见 memory/handover_mechanism.md

## 种子报告进展 → 详见 memory/seed_progress.md

## Gate 管线命名规范（永久记录） → 详见 memory/gate_naming.md

## 中后期待开发功能（本金大了再搞） → 详见 memory/future_features.md

## 用户关键原话（数据补充 + v2 种子相关） → 详见 memory/boss_quotes_data.md

## 种子验证结果（S22 verify_seed.py） → 详见 memory/seed_verification.md

## AI Sandbox — lab/ → 详见 memory/ai_sandbox.md

## L2 实盘 Regime 检测方案讨论 → 详见 memory/l2_realtime_regime.md
- 2026-03-10 混沌×白纱×黑丝三方讨论
- 白纱出精简方案 → 黑丝提4个问题（过拟合/初牛vs牛/跳级/多币种）→ 白纱回应
- **老板核心洞察**：子阶段决定regime转换。牛市里dip（回踩/牛旗/FVG补缺口）≠转regime，结构被破坏了才考虑转换
- 老板原话："要这些东西有被破坏掉了，才考虑是不是有周期转换的可能性"
- 下一步：白纱把子阶段+结构健康度融入L2完整方案

## GP自进化改进路线图 → 详见 memory/gp_evolution_roadmap.md
- 2026-03-10 混沌×黑丝讨论，4大改进方向
- ① 抗过拟合（分段验证+精度下限+信号率约束）② 量能衍生指标 ③ 指标库对接（老板核心想法：算一次存库+指标晋升+越来越丰富）④ 参数自由调（暂缓）
- 老板指示：先记录，等白纱主线任务定了再排期

## 哨兵检测体系脑暴 → 详见 memory/sentinel_brainstorm.md
- 2026-03-09 混沌×黑丝×白纱三方脑暴，老板说"这些时刻很难得的"
- 核心创新：用自己策略当传感器检测regime，不依赖公开指标
- 红绿灯比喻 → 策略止损=对面灯变黄 → 哨兵不下真单=手续费归零 → 纯信号选拔
- 完整推导链、老板原话、四灯体系、执行方案全部保留在专题文件里

## 策略筛选流程 → 详见 memory/screening_pipeline.md
- 关卡一：门槛（K线数÷X，按周期浮动）→ 关卡二：各自考场（regime内排名）→ 关卡三：组队 → 关卡四：整队照妖镜
- 已确认：关卡一公式和X值（1m/5m/15m=500, 1h=350），实测淘汰332/2236（14.8%）
- 待确认：关卡二考场报名笔数门槛、关卡三/四细节

## 待执行 → 见 CHECKPOINT.md

## 行为规范 → 见 memory/rules.md
（/reflect 提案，老板批准后写入；黑丝铁律补充版）

## 会话索引 → 详见 memory/session_summaries.md

