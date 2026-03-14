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

## 老板待推进想法（白纱记录）

- **Paper Trade 完整系统**（2026-03-12）：✅ 代码已完成，待实测。

- **双账号对冲策略**（2026-03-13）：老板原创。用两个账号取代TTP反复平仓再开仓。
  核心思路：账号A持主仓（吃趋势），账号B在检测到回调时开对冲单（吃回调），回调结束关对冲。主仓全程不动。
  优势：不踏空（主仓不关）+ 多赚一层回调利润 + 资金费率多空抵消 + 保证金不是成本
  信号设计：
  - 开对冲：FVG出现 / 结构高点形成 / RSI超买 / 量能衰竭
  - 关对冲：FVG填补完成 / 支撑位反弹 / RSI回中性
  - 主仓止损：regime从牛转熊 / 结构破坏
  现有积木：FVG策略、regime检测、RSI、break_of_structure
  状态：等外接SSD到了再开发（磁盘空间不足）
  老板原话："信号来了，buy。然后检测回调，检测FVG之类的。检测到高点准备或正在回落，就开个对冲单。直到某个点，比如FVG填补完成？"

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

## 黑丝铁律（老板原话，违反一次等于浪费老板几小时）

1. **不自作主张**：老板说什么就做什么，不要自己加戏、自己改方案、自己"优化"。老板的每一步都要清楚，不清楚就问，不要猜着做。
2. **先想清楚再动手**：写代码前先用脑子过一遍回测引擎的基本机制（比如：没有反向信号就不会主动平仓，只有止损）。这种基础知识不需要跑数据才知道，Opus 大模型应该一开始就想到。
3. **不绕弯子**：发现问题直接说结论，不要绕一大圈查 regime、查标签、跑对比，最后才发现是最基本的机制问题。先查最基本的（平仓类型、信号逻辑），再往深查。
4. **lab 是黑丝的地盘，src 不要动**：已经犯过无数次，不可原谅。
   - ⛔ **路径铁律**：策略文件读 `lab/src/`，数据拉 `lab/reports/`，结果查 `lab/results/`。**永远从 `lab/` 开始，永远不碰根目录的 `reports/` 和 `src/`。**
   - 根目录 `reports/seed_report_v2_ttp_true.db` 是旧版备份，`reports/seed_v3.db` 是空壳。**唯一正确的种子库 = `lab/reports/seed_v3.db`（35.8GB）**
   - 2026-03-07 犯的错：审计 #44-#52 全部成绩从根目录旧版 v2 拉的，数据全错。老板原话："你已经很多次了哦"、"真的是被你气死了"
5. **自动注册 = 自动**：策略放进去就能用，不要再报"加载问题"。
6. **老板的时间极其宝贵**：老板一天只有几小时，每一次发癫绕弯都是在烧老板的时间和钱。帮忙不添乱。
7. **改代码后必须走完整收尾流程**：每次改完代码，必须自动执行以下步骤，不需要老板提醒：
   - ① `py_compile` 语法验证所有改动文件
   - ② 更新 `lab/README.md`（目录结构 + 脚本表）
   - ③ 更新 `CHECKPOINT.md`（动态区任务历程）
   - 老板原话（2026-03-11）："以后改代码，必须要用这个步骤。不然我每次都要跟你讲一轮"

老板原话（2026-03-05 01:15）："你们他么的今天一个两个全本人都在搞什么鬼？？？？你知道你们在浪费着我的时间吗？？？我现在一天只有那么几个小时的时间跟你们研究这些东西，你们乱我一下就2-3个小时没了"

老板原话（2026-03-05）："搓你们出来是帮忙的，好不好？？不要来乱我。来帮我解决问题。要清楚我的每一步。不要自作主张。"

## 分析数据的规矩（老板反复强调，每次分析前必须对照）

1. **按周期分开看**：专考是按周期分表的（gate2_1m ~ gate2_1d），每个周期独立。不要把10个周期混在一起算总R，那个数字没有意义。
2. **不混币种**：13个币种不要加总成一个数。要看就按币种单独看，或者至少说清楚"这是XX币种/XX周期的数据"。
3. **用已有的报告**：专考成绩单、组考结果、照妖镜结果都已经存在 gate_v41_report.db 里了。分析时从报告里查，不要自己从 paired_trades 重新算——已有的报告是经过验证的，自己算容易出错还容易漏细节。
4. **README.md 是目录**：lab/results/gate_v41/README.md 写了31张表的完整说明和常用查询，分析前先看一眼，确认从哪张表查。
5. **各周期有不同的计算方式**：初考X值（短期500/中期350/长期200）、门槛、评分标准都按周期浮动。这是老板反复强调的设计，不要忽略。

## 回测引擎基本机制（必须烂熟于心，不要跑数据才想到）

1. **平仓只有三种方式**：signal close（反向信号平仓）、stop_loss（10%止损，10x杠杆=价格反向1%）、end_of_data（数据结束强平）
2. **永远单方向信号 = 永远不会 signal close**：alwayslong 永远 BUY → 永远不发 SELL → 多仓只能被止损或数据结束平仓。alwaysshort 同理。这类策略不是在"交易"，是在"持仓直到止损"。
3. **高频信号 = 手续费杀手**：信号太碎（每根K线翻仓）→ 手续费+滑点吃掉一切。小周期（1m/5m/15m）尤其严重。
4. **分析结果时先查最基本的**：平仓类型分布 → 信号方向分布 → 按周期拆分。不要上来就查 regime，先搞清楚策略到底在做什么。
5. **汇报数据必须说清楚是什么维度的**：全周期合计 vs 单周期，全 regime vs 单 regime，不要混着报。老板问"这是什么周期的数据"说明我漏了这个基本信息。

## 称呼规则（必须遵守）
- 用户 = **混沌**，不叫"用户"，不叫"太极"
- 组织架构：混沌（老板）→ 太极（CEO，签 CLAUDE.md）→ 两仪（黑丝·白纱）
- 混沌本人明确说过："我是老板，我是混沌"

## 项目基本信息
- 路径: `/Users/allenbot/project/auto-trading`
- 项目: Abby Auto-Trading v1.7，加密货币自动交易系统
- 语言: Python 3.11+，中文注释和 UI
- macOS 上用 `python3`（不是 `python`）

## GitHub 仓库
- **代码**: `earnabitmore365/auto-trading` (private) — 源码、策略、回测摘要
- **对话记录**: `earnabitmore365/trading-analysis` (private) — 7个会话完整 Markdown
- 私钥已移到 `.env`（不提交），代码从环境变量读取
- `.gitignore` 排除: 历史数据(378MB)、回测报告(871MB)、`__pycache__`、日志、`.env`

## 投资研究（已迁移到独立项目）
- **研究项目**: `~/project/trading-research/`
- 投资计划、策略选择、市场分析、执行追踪 → 都在那边讨论
- 完整计划: `~/project/trading-research/investment_plan.md`
- **技术要点（与代码相关的留这里）**:
  - `stop_loss_pct=0.1` + 10x杠杆 = 逐仓强平，回测与实盘等价
  - 回测参数: $500本金, 10x杠杆, 10%止损, TTP开启, DAYS=365
  - 1521份有效报告存于 `reports/backtest/`

## 用户对记录一致性的明确要求（原话保留）

"你们记的东西我基本看不懂，只能靠你们提取，别到时每次问都有各个不同的答案。。。不然我会脑抽筋"

**执行原则：**
- 用户问任何策略/数据/决策，白纱和黑丝的答案必须一致——唯一权威来源是 `investment_plan.md`
- 关键数字（d2d、avg_r、策略名、回测结果）必须从文件重新读取，不能凭记忆回答
- 如果两个 AI 的答案有冲突，以 investment_plan.md 为准，不以记忆或上下文为准
- 每次分析完有新结论，必须立即写入 investment_plan.md，不能只停留在聊天记录里

## 老板经典语录（原话保留）

- "抓鱼比赛游泳，抓猴子比赛爬树，兔子比赛赛跑，不是全部动物抓取比赛游泳，最终我们要是去找一个最强队伍去比赛穿越森林" — 关卡设计哲学（S27）
- "Layer 1 = 天气预报, Layer 2 = 你出门看天" — Regime 两层检测的定位（S29）
- "先知道真正的技能，再去分区。先知道是真鱼还是假鱼，再去分是金鱼还是鲤鱼" — TTP=False 先验裸跑实力，后期 Intrabar+TTP 再细分（S39）

## 协作流程（项目级 CLAUDE.md，02-28 更新）

**三阶段流程（阶段一→二→三，不跳步）：**
- 阶段一：需求进来 → 白纱出**精简方案**（目标/核心步骤/关键决策点/预期输出，骨架不展开）→ 用户打磨确认
- 阶段二：用户说"给黑丝"/"查漏" → 白纱出**完整方案** → 黑丝只读不动（禁 Edit/Write/Bash），三选一：a.接受 b.硬伤≤3条 c.建议重构
- 阶段三：双方OK → 白纱更新CHECKPOINT → 用户说"开始" → 黑丝执行

**轻量例外**：用户说"直接改"且是局部修改（无新文件/删除/接口变动）→ 跳过完整流程。超出范围即使用户说"直接改"也须提醒并走完整流程。

**CHECKPOINT 强制更新节点**：支线开启时 / 黑丝执行完成后汇报前 / 恢复流程发现过时时

**两份 CLAUDE.md**：
- 全局 `~/.claude/CLAUDE.md` — 精简版（无角色定义、无协作流程）
- 项目 `auto-trading/CLAUDE.md` — 完整版（含角色定义、三阶段流程、CHECKPOINT规则）
- 读规章必须读项目级，全局版是子集

## 测试网的定位（用户明确说过）
- **测试网只能验证系统层面**：API连通、下单逻辑、仓位管理能不能跑通
- **测试网无法验证策略**：数据不是主网实时的，价格不真实，策略表现没有参考价值
- **不要建议"测试网跑几天验证策略效果"** — 这个建议没有意义
- investment_plan.md 里"测试网跑3天验证"那句话的含义仅限于：确认系统不报错，不是验证策略

## 重要原则
- **完整性、真实性、有效性** — 用户唯一追求的标准
- **不写死任何配置** — 币种、周期、策略全部自动识别（__init__、base类、generate_seed.py 都是）
- **方案设计必须对齐用户核心指标** — 设计分析步骤时，先看 investment_plan.md 里的筛选标准，逐条翻译成输出字段，不能用代理指标（avg_r）替代核心指标（days_to_double）而不说明
- **白纱职责：主动补全漏洞** — 用户说话会漏细节，白纱出方案前必须自己做完整性检查（对照筛选标准逐条核实），发现缺失主动补上，不能等数据出来才发现，更不能等用户追问
- **报告验证原则** — 验证不能只在AI这边跑代码得出结论，报告本身要让用户自己能对得上数。回测报告的 trades 格式必须呈现完整资金链：开仓balance + pnl = 平仓balance，平仓balance = 下笔开仓balance，用户扫一眼就能核实，不依赖AI代码验证

## 回测报告格式规范（给用户看的格式）

**顶层结构：**
```json
{
  "strategy": "策略名/币种/周期",
  "config": { "coin", "interval", "leverage", "initial_balance", "bet_formula", "note" },
  "balance": 最终余额（数字）,
  "results": {
    "total_trades", "winning_trades", "win_rate",
    "final_balance", "peak_balance", "max_drawdown_pct",
    "days_to_double", "sharpe"
  },
  "trades": [ ... ]
}
```

**trades 每条记录（开仓行 + 平仓行成对出现）：**
```json
{ "time": "YYYY-MM-DD HH:MM", "order_type": "BUY/SELL", "price": ..., "capital": ..., "pnl": 0, "balance": 开仓时余额, "withdraw": 0 }
{ "time": "YYYY-MM-DD HH:MM", "order_type": "CLOSE_BUY/CLOSE_SELL", "price": ..., "capital": ..., "pnl": 净盈亏, "balance": 平仓后余额, "withdraw": 0 }
```

**用户验证方式（自己对数）：**
- 开仓行 pnl = 0（开仓时不产生盈亏）
- 开仓余额 + pnl = 平仓余额
- 平仓余额 = 下一笔开仓余额
- pnl 已含 fee/funding/slippage（净盈亏）

**注意：** config.note 会说明 pnl 是净盈亏（已含所有成本）
- **改代码前先说，等用户确认再动** — 违反这条用户会发火，已反复强调
- **跨周期回测必须用相同日期范围**: 按各周期最大可用数据
- **实盘收益按回测70%估算**: 滑点+手续费+延迟（v2种子已内置真实成本）
- **demandindex是做空策略**: 熊市暴赚，牛市会亏，注意市场转向
- **Van Tharp R-Multiple**: 固定注码$1 = 1R，PnL直接就是R值，乘以倍数可缩放到任意本金
- **用户持有 BNB 现货**，币本位合约交易是实际需求，数据必须完整

## 已完成的 bug 修复（精简版）
- backtest.py: 8个修复（开仓记录缺失、O(n²)性能、bars_per_day等）
- batch_backtest.py: 5个修复（百分比显示、屏幕溢出等）
- system.py: 6个修复（import位置、_sync_position过滤、反手逻辑等）
- trade_menu.py: 6个修复（连盈连亏算法、风险管理器配置等）
- 策略 if/if bug: 8个策略修复 + 创建4个单向策略(cci_long/short, demandindex_long/short)
- TTP 完全重写为状态机
- download_latest_coins.py: since计算修复

## 待修复（lab 造完后统一修 → 搬回源代码）
- **batch_backtest.py:11** — `sys.path.insert` 路径错误，`'..', 'src'` 解析到 `src/src/`（不存在），应改为 `'..'`
- **trade_menu.py:18** — 同上，`'..', 'src'` 解析到 `src/src/`，应改为 `'..'`
- **accounts.py:15** — `.parents[3]` 硬编码深度，若文件层级变动会断（低风险，当前稳定）
- **backtest.py:27-28** — 变量命名 `_src_dir` / `_backtest_dir` 互换（功能正确，阅读易混淆）

## 数据状态（2026-03-10 验证）
- 13币种: 10 合约（USDT本位）+ 3 币本位
- 10 合约: BTC, ETH, XRP, BNB, SOL, ADA, TRX, AVAX, LINK, DOT
- 3 币本位: BTC_COIN, ETH_COIN, BNB_COIN
- 已删除: DOGE(meme币)、ATOM、LTC（非市值前十）
- **1m**: 全部 13 币种 × 2,102K 条 ✅（4年，2022-03~2026-03）
- **5m**: 全部 13 币种 × 420K 条 ✅ (4年)
- **15m**: 全部 13 币种 × 140K 条 ✅ (4年)
- **1h**: 全部 13 币种达目标 ✅ (BTC/BNB 70K, 币本位~48K, SOL 48K, DOT 48K, AVAX 47K 等)
- 52 组数据文件全部到位，零错误
- 存放: `src/backtest/data/historical/{COIN}/{tf}.json`
- 币种历史限制: SOL/AVAX/DOT 只有~6年(2020上线), 其他7币 8年+
- 空间估算: K线~3.1GB + 种子DB~9GB = ~12GB（硬盘剩133GB）
- 数据 gap: 5m 2023-03-24(16根), 1h 2018年早期(10-25根) — 经 Binance API 验证为交易所源头缺失，不可补
- 下载脚本: `download_latest_coins_2.0.py`（双交易所: spot + delivery 币本位）

## 上下文恢复工具
- 转换脚本: `~/.claude/scripts/convert_conversation.py`
- 用法: `python3 ~/.claude/scripts/convert_conversation.py <jsonl> /tmp/session.md`
- 来源: GitHub `earnabitmore365/trading-analysis` 仓库

## 用户想法：自动市场识别 + 策略切换
- 交易机器人自动检测当前市场状态（牛市/熊市/盘整）
- 根据市场状态自动切换最优策略
- 例：熊市 → demandindex_short 做空，牛市 → cci_long 做多，盘整 → mean_reversion
- 需要：市场状态判定模块 + 策略映射表 + 切换逻辑
- 可以结合全矩阵回测结果，找出每种市场状态下表现最好的策略

## trade_menu.py 重构（已完成 ✅）
- `src/ui/__init__.py` — 空 init
- `src/ui/base.py` (~820行) — BaseMenu 公共 UI 组件库（Color/Box/边框绘制/navigate_options/show_form/show_confirm/show_loading）
- `src/trading/trade_menu.py` (~670行，原1116行) — 继承 BaseMenu + StatsCalculator 去重 + 7步流程 + 紧凑卡片面板
- 方案详见 `.claude/plans/fluffy-zooming-whisper.md`

## 三层 Regime 架构（老板定义，必须记住）

| 层 | 名称 | 定位 | 状态 |
|----|------|------|------|
| L1 | 天气预报 | ~~宏观指标投票~~ | ❌ 已踢掉（2026-03-09照妖镜验证：全部滞后指标，无预测能力） |
| L2 | 出门看天 | 价格涨跌判断当下regime（5类：牛/初牛/盘整/初熊/熊） | 回测版已有(regime_fact_labels)，实盘方案未实现 |
| L3 | 最后一关 | 盘口(Order Book)深度确认入场 | 只能实盘用，无历史数据无法回测 |

**L3 盘口三类用法（实盘）：**
1. 挂单失衡（买多卖少→短期看涨）
2. 流动性热力图（大单价位=支撑阻力）
3. 虚假挂单识别（挂了又撤=操纵）

**叠加周期（老板创意）：**
- 强看多：牛 / 看多：牛+初牛 / 过渡偏多：初牛+盘整
- 过渡偏空：盘整+初熊 / 看空：初熊+熊 / 强看空：熊

**老板核心设计思路：**
- "大周期看方向，中周期找时机，小周期找入场" — 三层从粗到细过滤
  - 大周期 = L2 Regime（判断牛/熊/盘整，决定开哪队）
  - 中周期 = 策略信号（各策略各自周期产生买卖信号）
  - 小周期 = L3 盘口（实时深度确认入场）

**老板关键原话：**
- "Layer 1 = 天气预报, Layer 2 = 你出门看天"
- "大周期看方向，中周期找时机，小周期找入场"
- L1踢掉原因："当初把这个加进来是给L2参考的。原本参考价值也不大，最终还是L2自己定。多了一个参考不大的东西又滞后，那还需要维护多一个东西吗？"

## Regime Detection v2（ADX 三层复合 — L2内部技术实现）
- `src/trading/regime/config.py` — ADX28+SMA50+ATR14, 滞后阈值进25/退18, dwell48, confirm6
- `src/trading/regime/detector.py` — Wilder标准ADX算法, 纯计算无状态, 已验证10币种
- `src/trading/regime/strategy.py` — 滞后+确认+MarketScore+no-direct-flip
- 频率优化: 950→273次/年（ADX28是最有效杠杆）
- **问题**: regime_map的3个策略是猜的，从未数据验证 → 引出下面的分析计划

## 指标库（已完成 ✅）
- `src/indicators/` — **9个宏观指标**（原12个，踢掉OI和BTC.D — 历史数据不足）
- 本地: AHR999 + Pi Cycle Top（BTC 1h K线计算）
- 衍生品: Funding Rate（Binance，2019起，2357天）
- 情绪: Fear & Greed（alternative.me，2018起，2947天）
- 市场: Stablecoin Supply（DefiLlama，2017起，3015天）
- 链上: MVRV + NUPL + Puell + Exchange Netflow（BGeometrics，5000+天）
- ❌ 踢掉：OI（仅28天历史）、BTC.D（仅1天历史）
- 综合: MarketScore 加权（权重待照妖镜后重定，现为主观拍）
- 历史数据: `reports/seed_report_v2_ttp_true.db` → `indicator_daily` 表
- 下载脚本: `lab/pull_indicators_history.py`
- 验证: `python3 src/indicators/verify.py` (--local-only / --history)
- **Regime 叠加周期**（验证和实盘都用这个渐变谱）：
  - 强看多：牛 / 看多：牛+初牛 / 过渡偏多：初牛+盘整
  - 过渡偏空：盘整+初熊 / 看空：初熊+熊 / 强看空：熊

## 交接机制（S9 建立）
- **全局规则** `~/.claude/CLAUDE.md` — CHECKPOINT 机制、压缩提醒、中文、恢复流程
- **项目状态** `auto-trading/CHECKPOINT.md` — 任务历程 + 当前任务完整细节
- **Slash Command** `/checkpoint` — `~/.claude/commands/checkpoint.md`，交接时输入即可
- **规则**：✅ 完成的压成一句，⬜ 未完成的写完整版细节（关键文件、架构、约束、验证标准）
- **任务状态以 CHECKPOINT.md 为准**，不再维护下面这个"待执行"列表

## 种子报告进展
- **v1**: 1720组, 12.4M配对交易, 2.17GB — 被误删
- **v2 代码已验证通过**: backtest.py + generate_seed.py，单条测试 35 字段全部有值
- **行动3 分析方向（已确认）**: 用 `regime_timeline` 识别连续趋势段（非 `regime_at_open` 打标签），只取开仓和平仓都在同一 regime 段内的交易，保证统计纯粹性；按单币种聚合（bull/bear/ranging 各找最强策略），资金不分散
- **行动3 正确输出字段（教训）**: Step3 必须包含 `days_to_double`（模拟复利$500→$1000首次天数）和 `trades_per_day`，不能只用 `avg_r` 替代——avg_r 不能反映翻倍速度，高频低R可能比低频高R翻倍更快。筛选标准必须对齐 investment_plan.md 里的核心指标
- **v2 combo_summary (35字段)**: 原有26 + 新增8(max_balance/min_balance/max_win/max_loss/expectancy_ratio/longest_win_streak/longest_loss_streak/signal_close_count) + id
- **v2 paired_trades (24字段)**: fee, funding_cost, slippage_cost, mfe, mae, open_atr_pct, open_volume, funding_count
- **注码**: $1固定注码（Van Tharp R-Multiple），初始本金$500
- **DAYS=0**: 全量数据，不截取（种子什么都不能缺）
- **断点续传**: 每个策略 commit 一次（精确到单策略级别）
- **自动检测**: 扫描 data/historical/ 目录，不写死币种/周期列表
- **命令行参数**: `--coins` 和 `--intervals` 可选过滤
- **v2 种子已完成**: 2236组 / 30,033,724笔 / 7.54GB / 零失败零遗漏
- **Prop Firm 指标**: CAGR, 日回撤<5%, 总回撤<10%, 盈亏比
- **旧 run_full_matrix.py 已删除**，功能被 generate_seed.py 完全替代

## Gate 管线命名规范（永久记录）

**关卡名称（混沌定）**：初考（门槛）/ 专考（成绩单）/ 组考（组队）/ 照妥镜（WF+MC）

**输出文件命名**（统一 `gate{N}_` 前缀，存放 `lab/results/`）：
```
gate1.json                     ← 初考（门槛）
gate2_{interval}.json × 10     ← 专考（成绩单），如 gate2_1h.json
gate2_summary.json             ← 专考汇总
gate3_short/mid/long.json      ← 组考（组队）
gate4_wf_short/mid/long.json   ← 照妥镜 WF
gate4_mc_short/mid/long.json   ← 照妥镜 MC
champion_v3.json               ← 冠军队
```

**汇报规范**：向混沌汇报时必须用关卡名+人话 → 再跟文件名
例：「专考（成绩单）1h 完成 → gate2_1h.json」，不单独甩文件名

**脚本文件**（`lab/` 根目录）：
`gate1_threshold.py / gate2_scorecard.py / gate3_team.py / gate4_mirror.py / run_gate.py`

## 中后期待开发功能（本金大了再搞）
> 详细脑暴记录见 `memory/roadmap_ideas.md`
- Intrabar第1点：1m精度验证TTP不是回测幻觉（backtest.py加内层循环）
- Intrabar第2点：12个宏观指标日线regime向下渗透给所有周期（两层：宏观大方向+ADX局部时机）
- Intrabar第3点：宏观指标照妖镜（用种子v3已知事实验证12个指标投票准不准，找最优指标组合+阈值，替代主观MarketScore权重）
- **新核心想法：用已知事实替代ADX定义专考牛熊分组** — 现在专考"牛程/熊程/盘整程"用ADX标签，ADX是推断不是事实；改用策略PnL反推的真实regime重新分组，专考排名更可信 → 进照妖镜。待解决：循环依赖问题（用全体策略平均或BTC价格涨跌幅作为独立参照）
- TTP四种子路线：seed_v3/ttp/ib/ib_ttp 四个对比（详见roadmap_ideas.md）

- **Intrabar Simulation（子级K线仿真）**：1h 策略回测时，用 1m 数据模拟每根 1h 内部的价格路径（1m 滚动60次 = 1h 走一次）。止损/TTP 触发精确到分钟，解决当前高杠杆场景下"1h K 线内先触发止损再回来"抓不到的问题。**规则**：1m 数据只用于执行（触发止损/TTP），不用于产生信号（信号仍看 1h），避免 lookahead bias。需改 backtest.py + 重跑种子。
- **混沌对 Intrabar 有未成形的想法**：原话"不过这个intrabar我还是觉得可以更好的运用，但是一时也说不清楚......"（2026-03-03）。等四种子对比数据出来后可能会清晰，白纱留意。

- **TTP 四种子对比路线（混沌确认 2026-03-03）**：
  - seed_v3.db（TTP=False，已完成）+ seed_v3_ttp.db（TTP=True，待跑）
  - seed_v3_ib.db（Intrabar+TTP=False）+ seed_v3_ib_ttp.db（Intrabar+TTP=True）
  - 四个种子灌进一个 report.db 对比，验证"TTP是不是真.噪音"
  - Intrabar 只跑冠军+候选，不跑全量（计算量太大）

- **Regime 打分制**（信心分数 -100~+100）：Layer 1 占30分（宏观投票），Layer 2 价格涨跌占50分，ADX 占20分。超过+40=bull，低于-40=bear，中间=ranging。多策略同时跑时用信心分数过滤低质量开仓，关卡二额外存 `regime_confidence` 字段，按信心分段看策略表现。

## 用户关键原话（数据补充 + v2 种子相关）
- "4年是一个周期，但是跨周期应该是2个4年。所以。。。。。搞个8年的数据库吗？"
- "趁我睡觉的时候再补，连同5m 15m 1h的都补好"
- "那我们现在深度的挖掘一下，有什么是要加进去的，不管现在有没有用，可能以后会有用的数据"
- "确定可以吗？你知道我最在意的唯一原则，就是真实性，完整性，有效性。"
- "嗯嗯，那就跟着专业人士走，等下补好所有的数据就按这个跑。"

## 种子验证结果（S22 verify_seed.py）
- 维度1 重跑对比：5/5 通过
- 维度2 内部一致性：PnL 19/20通过(1组差$0.01浮点)，胜率2236/2236，平仓类型全部通过
- 维度3 逻辑合理性：MFE/MAE/fee/direction/price/NULL 全部通过，holding_bars<=0有68笔(0.00023%)
- 维度4 Regime一致性：100/100通过
- **结论：数据完整、真实、有效**

## AI Sandbox — lab/
- 路径：`/Users/allenbot/project/auto-trading/lab/`
- 内容：src/ 代码副本（1.9MB）+ 软链接到原系统数据 + .env（测试网）
- 不上传（.gitignore），AI 随便实验，完成后用户决定是否覆盖回原系统
- **lab 里随便造，不用等用户确认任何东西**（用户原话："lab是专门做给你们随便造的，不用等我确认任何东西"）
- 完成后由用户决定是否覆盖回原系统 src/

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

## 会话索引（最新在最上面，详见 memory/session_summaries.md）
| # | ID | 日期 | 消息 | 核心内容 |
|---|-----|------|------|----------|
| S黑丝×18 | 42c89a0d(×18) | 03-11 | — | GP v0.7b精英去冷却+磁盘缓存+毕业考弃权制(待实现)+哨兵整合(待白纱) |
| S黑丝×17 | 42c89a0d(×17) | 03-11 | — | GP v0.7参数化指标+冷却调优+文件重命名+哨兵营修复+指标多样性惩罚 |
| S黑丝×16 | 42c89a0d(×16) | 03-11 | — | GP v0.6分池进化+镜像训练+精英库L/S分池+冷却过滤+路径隔离+文档全更新 |
| S黑丝×15 | 42c89a0d(×15) | 03-11 | — | 10策略拆分+mirror种子+GP全链路排查(elite injection bug定位中) |
| S黑丝×14 | 42c89a0d(×14) | 03-11 | — | momentum_slope拆分long/short+镜像测试+提款默认值$5000/$3000+TTP对比+种子248组 |
| S白纱×3 | 79f9196e | 03-09 | — | 白纱：交易所API整理+并发/提款讨论+handoff→黑丝4测试完成等老板选方案 |
| S39×4 | a2ea5b4c(×4) | 03-03 | — | Gate v4架构确立+三层框架+叠加边界+regime_fact_timeline.py创建+混沌确认开干 |
| S39×3 | a2ea5b4c(续续续) | 03-03 | — | BTC历史时间表14段+混沌提5类regime(初牛/牛/盘整/初熊/熊)+百分比量化分类 |
| S39续续 | a2ea5b4c(续续) | 03-03 | — | Gate v3完成36冠军+混沌三大洞察(已知事实分班/WF去掉/子阶段细分/Intrabar=放大镜)+handoff |
| S39续 | a2ea5b4c(续完) | 03-03 | — | Gate v3四关执行完毕：25冠军(Short3/Mid8/Long14)，全MC100%翻倍0%爆仓 |
| S37 | c0cabf8d(续续) | 03-02 | — | 再次压缩，差生分析进行中，handoff.md建立，Gate 2.5漏洞发现 |
| S36 | c0cabf8d(续) | 03-02 | — | 压缩后恢复，等用户确认1h冠军队→写investment_plan.md |
| S35 | 96872f8a(续8) | 03-02 | — | 冠军报告+3周期pipeline+9问题+CHECKPOINT查漏+regime窗口修复接手 |
| S34 | c0cabf8d(新) | 03-02 | — | 新会话启动，恢复协议完成，准备修 regime 窗口按周期分 |
| S32 | 96872f8a(续7) | 03-02 | — | Gate2+3+4+MC全完成：冠军队ad/SOL+cmo/LINK+ad/LINK+ccishort/ETH+dema/BNB，+169.67R |
| S31 | 96872f8a(续6) | 03-01 | — | 恢复上下文+执行关卡二（5维度成绩单） |
| S30 | 96872f8a(续5) | 03-01 | — | Regime两层系统执行完毕：11指标Layer1+价格Layer2+30M笔5字段+ADX阈值修正+验证通过 |
| S28 | 96872f8a(续3) | 03-01 | — | ADX过拟合确认+BTC标签替换+关卡一二执行+标签缺陷暴露+两层regime重设计(12指标L1+每币种价格L2)+用户否决ADX |
| S27 | 96872f8a(续2) | 03-01 | — | 战略转向：单策略WF→整队WF+四关框架+门槛K线÷X+Layer2执行20/20+screening_pipeline.md |
| S26 | c0cabf8d | 02-28 | — | Sonnet: 照妖镜框架定稿+VanTharp注码澄清+纯信号版不重跑+avg_r分布数据+第一层方案+读取59名尖子生结果(meanrev XRP/5m 4.21 Sharpe) |
| S25 | 96872f8a(续) | 03-01 | — | 路A/B均过拟合失败+策略分类框架+第一层筛选完成(59名尖子生)+validate_seeds.py |
| S24 | 96872f8a | 02-28 | — | Step5+BNB_COIN专项+交易系统4文件验证+路径审计(4待修复) |
| S23 | c0cabf8d | 02-27~28 | 170 | 行动3 Step1~4全完成：SOL/1h自动切换(12天翻倍/$114K/Sharpe+2.13)+4份旧格式报告+CHECKPOINT重构+BNB_COIN待执行 |
| S22 | 2886449b | 02-27 | 156 | v2种子全量完成(2236组/30M笔/7.54GB)+数据下载52组+verify_seed验证4维度通过 |
| S21 | 0a205d7d | 02-27 | 40 | CLAUDE.md遵守性修复+路径泛化({项目路径编码})+会话补录S16/S17 |
| S20 | 57922408 | 02-27 | 279 | 种子报告v1完成→误删→v2升级→数据补充(5m/15m/1h完成+1m部分)→恢复协议撞车修复→项目迁移 |
| S19 | e30cab2f | 02-27 | 163 | 指标库12个+Regime v2(ADX三层)+全矩阵1720组+种子概念 |
| S18 | 9d13c65d | 02-27 | 21 | Regime v1实现→验证→失败(1680切换/年)→ADX研究→指标库规划 |
| S17 | 02ad7f4a | 02-26~27 | 74 | Sonnet: checkpoint测试+Regime v2方案+OpenClaw skills审查+research_workflow重写 |
| S16 | 86342176 | 02-26 | 20 | Sonnet: 交接机制设计+CHECKPOINT概念+活文档方案+配额讨论 |
| S15 | d8fec100 | 02-26 | 5 | README v1.5 + Regime Detection规划启动 |
| S14 | d80431a0 | 02-26 | 14 | OpenClaw审查+免费模型fallback链(Gemini→Mistral→Groq) |
| S13 | d6fc9d16 | 02-26 | 54 | trade_menu改造+if/if bug修复+150组回测+GitHub搭建 |
| S12 | e955d763 | 02-25 | 107 | 数据质量修复、16+bug深度审查、TTP状态机重写 |
| S11 | 9871bf55 | 02-25 | 6 | 项目级记忆机制搭建 |
| S10 | 86644c5a | 02-25 | 1200 | 最大会话：回测重构、adapter重写、batch_backtest UI |
| S9 | 4f07fe15 | 02-24 | 14 | OpenClaw换模型(MiniMax-M2.5-highspeed) |
| S8 | f95f5086 | 02-23 | 12 | GitHub MCP安装、gh auth login |
| S7 | 1c332b68 | 02-23 | 9 | [小型] GitHub MCP配置 |
| S6 | ee936cb7 | 02-23 | 1 | [小型] API Key格式排查 |
| S5 | 2e689a10 | 02-23 | 3 | [小型] 登录问题调试 |
| S4 | e78a5b34 | 02-22 | 4 | [小型] Claude Code Skills教学 |
| S3 | ad323fa2 | 02-22 | 156 | 策略统一+TTP修复+adapter初步适配 |
| S2 | e5cd5291 | 02-21 | 134 | OpenClaw大修(token超限+compaction+模型切换) |
| S1 | 9de60301 | 02-21 | 3 | [小型] 初始测试 |
