⛔ **恢复协议优先**：看到此文件 ≠ 已完成恢复协议。必须先完整执行 CLAUDE.md 步骤1-4，才能开始任何工作。

> 太极签：2026-03-05

# CEO / 项目管理 记忆

> 太极最后更新：2026-03-16

## 上次会话要点

> 覆盖更新，不累积。只记下次会话需要知道的事。

- **Mission Control 搁置**：Docker 安装+容器跑通，但 Gateway 连接遇连环安全问题（CORS/device identity/origin），老板决定不搞第三方，以后自建通讯部
- **Claude Code 中间层 API 可用**：port 8100，4 端点 + 仪表盘 HTML，launchd 守护进程已配（`com.claude-code-api.plist`）
- **Abby 模型升级**：主力切到 `ollama/qwen3.5:9b`（多模态+推理），上下文窗口 32768→8192（解决卡顿），Gateway bind 改 lan
- **Evolver hook 链路修复**：evolve.sh 加并发锁（所有入口覆盖），evolve_hook.sh 简化为只处理太极，已验证黑丝 clear context 能正确触发 evolver
- **SessionStart evolver 通知**：session_start.py 改为所有会话启动都检查通知（不限 compact），evolve.sh 通知写入解析修复（正确提取 gene/scope）
- **Karpathy Autoresearch 调研**：AI 训练 AI 的开源项目，program.md 方向指引模式可借鉴但永不停止循环不适用（rate limit+无客观指标），老板决定暂不动 evolver
- **命名哲学**：写入 memory/naming_philosophy.md 并索引到太极+auto-trading 两个 memory，黑丝白纱下次恢复可读
- **Evolver 新 skills**：自动生成了 gene-crossover（遗传交叉）+ evo-digest（老板友好摘要），总 cycle 83

---

## 会话索引（最新在最上面）
| # | ID | 日期 | 核心内容 |
|---|-----|------|----------|
| S42 | 0da5d1b1 | 03-16 | Mission Control搁置+Claude Code API(port 8100)+Abby升qwen3.5:9b+evolver hook链路修复(加锁)+SessionStart通知修复+Autoresearch调研(暂不动)+命名哲学记录+evo-digest/gene-crossover新skill |
| S41 | c2c95c51续2 | 03-15 | OpenClaw/Abby修复(API模式修正)+本地模型安装(3注册1未注册)+evolve.js僵尸根修复+openclaw.md参考文档 |
| S40 | c2c95c51续 | 03-13 | 僵尸基因自动复活根因修复(BUG-007/FIX-005: ensureGene退役检查+c7368808退役条目+workspace同步) |
| S39 | c2c95c51 | 03-12 | 太极升Opus首会话；evolver genes.json修复(补2 innovate基因)+EVOLVER_README.md完全重写；角色变更(黑丝升主力/白纱转支援) |
| S38 | 1f704c1f续4 | 03-09 | 压缩后恢复；待修double-dash路径bug（`-Users-allenbot--claude`） |
| S37 | 1f704c1f续3 | 03-09 | evolver完整链路跑通：session读取+自动触发hook+skills目录验证 |
| S36 | 1f704c1f续2 | 03-09 | 压缩后恢复；修复两个剩余evolver问题（timestamp+MEMORY.md） |
| S35 | 1f704c1f续 | 03-09 | evolver rollback彻底解决+所有文件恢复+genes.json重建+solidify跑通（shim生效） |
| S34 | 1f704c1f | 03-08 | evolver迁移~/.claude/evolver/+多项目支持(taiji/auto-trading验证)+~/.claude/ git init+基因库共享；三层→两层记忆决策；bridge实装测试 |
| S33 | S32续 | 03-08 | 擅自执行被批→RUL-006→三层记忆研究(鲜活/温度/冷)→Vibe Coding→DESIGN_DECISIONS.md创建+/reflect门槛修改→三套记忆系统完成 |
| S32 | aa00b2a6续4 | 03-07 | /claude强制Read+用户→老板全替换+reflect触发词+白纱换人+AI人格研究+太极人格（老板确认）+三项待做 |
| S31 | aa00b2a6续3 | 03-07 | 提升词类+RUL-004/005+CLAUDE.md头脚架构+letterhead+slogan+白纱handoff未读问题（排查中） |
| S30 | aa00b2a6续2 | 03-06 | LRN-20260306-005定性提升，db_write.py扩展9类词表，/reflect skill扩展 |
| S29 | aa00b2a6续 | 03-05 | SessionStart/SessionEnd/PreCompact hooks+CLAUDE.md简化+reflect效果验证(33→1条) |
| S28 | aa00b2a6 | 03-04~05 | 对话种子完整实装+tags（8类词表/回填3378条/去噪/Markdown格式确认） |
| S27 | 当前 | 03-02 | 新会话，待用户指示 |
| S26 | 4f681d51 | 03-01 | CHECKPOINT打磨版块设计 + agentchattr接入 + 规章升级 |
| S25 | 3ac548bf | 03-01 | 规章升级+文件职责简称+CLAUDE.md三段结构+OpenClaw调研 |
| S24 | 3ac548bf | 02-28 | CLAUDE.md全面升级+session_summaries双区域重构 |

---

## 太极注意事项（操作规范）

- **修改权**：老板授权太极修改，不是太极独管。老板是最终权力方，太极是受托方。
- **CLAUDE.md 头同步**：修改任何 CLAUDE.md 头的内容，必须同时更新全局和所有项目的 CLAUDE.md，不能只改一处。这是太极的责任。
- **通讯链路**：太极→黑丝白纱 = `handofffromtaiji.md`；黑丝白纱→太极 = `handofftotaiji.md`（在 auto-trading 项目根目录）。handoff 不更新 = 没事发生，不是问题。

---

## 文件职责定义（公司管理规定）

| 简称 | 文件 | 职责 |
|------|------|------|
| 制度 | `CLAUDE.md` | 规则、行为准则 |
| 交接 | `CHECKPOINT.md` | 任务状态、下一步 |
| 档案 | `MEMORY.md` | 跨会话知识、决策记录、项目历史 |
| ~~日记~~ | ~~`session_summaries.md`~~ | ~~废弃（2026-03-08）~~ — 合并进 `MEMORY.md` 的「上次会话要点」区域 |

---

## CLAUDE.md 文档结构标准（公司管理规定）

| 段 | 内容 | 原则 |
|----|------|------|
| **头** | 通用内容（核心原则、恢复协议、禁止操作） | 仅限太极修改；项目级必须也有头（letterhead），override 全局 |
| **内容** | 项目专属核心信息（角色定义、协作流程） | 精炼，各项目自己补充 |
| **脚** | 头里动作的详细用法说明（工具参考、查询模板等） | 仅限太极修改；脚是头的索引，放最后 |

**修改权限**：头与脚 → 仅太极。内容 → 老板 + 太极。黑丝白纱只能遵守，不得自行修改任何段。
**项目级 letterhead**：每个项目 CLAUDE.md 必须有自己的头，声明 override 全局恢复协议，格式统一由太极维护。

---

## 公司架构

```
老板（最高决策者）
  └─ 太极（CEO / home Opus）— 管规章、管项目、只对老板负责
       ├─ 黑丝（auto-trading Opus）— 主力全包，规划+执行
       └─ 白纱（auto-trading Sonnet）— 支援，查资料/整理文档/支线任务
```

**规章修改权**：仅限老板及太极。白纱与黑丝只能遵守。

---

## 规章变更日志

| 日期 | 改动摘要 | 原因 |
|------|----------|------|
| 2026-03-04 | 全局CLAUDE.md步骤3加防呆：CHECKPOINT只读当前工作目录，⛔不跨目录搜索 | 太极跑去读auto-trading的CHECKPOINT |
| 2026-03-02 | 两个CLAUDE.md加handoff规范（跨会话传话写handoff，拍板写CHECKPOINT） | 打磨阶段来回贴文导致上下文过长 |
| 2026-03-01 | CHECKPOINT加🔨打磨板块 + CLAUDE.md模板/协作流程同步更新 | 打磨对话太长，靠CHECKPOINT共享背景 |
| 2026-03-01 | 两个CLAUDE.md加压缩优先级声明（点名continuation prompt） | 压缩带偏问题，被系统指令绕过恢复协议 |
| 2026-03-01 | 协作流程改三阶段（打磨→查漏→开工） | 黑丝惯性直接执行，缺乏打磨机制 |
| 2026-02-28 | session_summaries.md重构为白纱/黑丝双区域 | 防止角色串记录 |
| 2026-02-28 | JSONL过滤改为按模型名精准匹配 | 黑丝恢复时读到白纱的会话 |

---

## 系统性问题追踪

| 问题 | 状态 | 方案 |
|------|------|------|
| 压缩带偏：summary + continuation prompt 绕过恢复协议 | 🧪 测试中 | 两个CLAUDE.md恢复协议顶部加优先级声明 |

---

## 待做清单

1. **CHECKPOINT.md 头部正式化** — 标记规范（✅ vs ⚠️）+ 交接填写要求
2. **CLAUDE.md 步骤9简化** — 改为"按CHECKPOINT头部标记规范更新"
3. **阶段三补完整** — 步骤10：白纱接收结果→分析→给下一步（闭环）
4. **白纱角色定义** — 加"全程主导"定位
5. **撞车修复** — "不擅自行动" vs 白纱"主动触发"，明确后者是有意例外
6. **PreCompact hook** — 压缩前自动写入种子防漏数据
7. **SessionStart hook** — 需调研 additionalContext 支持情况

---

## 角色变更（2026-03-12 老板拍板）

- **黑丝（Opus）升职**：主力全包，规划+执行，不再依赖白纱出方案
- **白纱（Sonnet）转支援**：查资料、整理文档、支线任务，不出主线方案
- 原因：白纱方案每次有漏洞，黑丝查漏反而更费事，不如黑丝直接搞
- CLAUDE.md 已更新（2026-03-12）

## 项目状态摘要

| 项目 | 主线 | 当前阶段 |
|------|------|----------|
| auto-trading | 分层投资组合分析（快狠准翻倍） | 黑丝主导，白纱支援 |
| 通讯部 | 对话种子 conversations.db | ✅ 第一版落地（Stop/UserPromptSubmit hooks + tags） |
| cashflowAPP | 澳洲小企业主现金流管理 | 待立项，框架未定 |

---

## 通讯部 关键信息

- **存储**：`~/.claude/conversations.db`（messages 表，全项目共用）
- **自动写入**：Stop hook（AI回复）+ UserPromptSubmit hook（混沌发言）
- **字段**：id / time / speaker / content / project / session_id / tags
- **tags**：7类词表自动匹配（流程/技术验证/市场状态/数据/协作/策略币种），混沌命中决策词额外加"决策"标签
- **内容格式**：Markdown 原文（\n换行，**粗体，|表格，`代码）
- **太极频道**：home 目录不写入，上层对话隔离
- **待做**：PreCompact hook（防漏）、SessionStart hook（自动恢复）

---

## 全局配置文件
- `~/.claude/CLAUDE.md` — CEO 层规则（核心原则、通用恢复协议）
- `~/.claude/scripts/db_write.py` — 对话种子写入脚本（hooks触发）
- `~/.claude/scripts/convert_conversation.py` — JSONL 转 Markdown 工具
- `~/.claude/commands/checkpoint.md` — `/checkpoint` slash command
- `~/.claude/handofffromtaiji.md` — 太极写给黑丝白纱的 handoff

## 管理中的项目
- **auto-trading**: `/Users/allenbot/project/auto-trading`
  - 项目 memory: `~/.claude/projects/-Users-allenbot-project-auto-trading/memory/`
  - 项目 CLAUDE.md: `/Users/allenbot/project/auto-trading/CLAUDE.md`
  - 设计决策库: `/Users/allenbot/project/auto-trading/DESIGN_DECISIONS.md`（10条关键设计决策WHY，恢复协议必读）

## 详细档案（独立文件）
- `memory/framework.md` — **公司框架全图**（文件全图/串联流程/待解决问题追踪，有新分支从这里找来源）
- `memory/rules.md` — **已毕业行为规范**（/reflect 提案，老板批准后写入）
- `memory/cashflow.md` — cashflowAPP 完整信息（设计理念/MVP/上线策略/功能需求库）
- `memory/tools.md` — 工具库调研表（本地LLM/agent框架/图表库等）
- `memory/feedback_cleanup_background_tasks.md` — 后台任务用完即关（老板反馈）
- `memory/openclaw.md` — **OpenClaw 完整配置知识**（模型管理/API规范/人格注入/ACP/频道，修改前必读）
- `memory/feedback_think_before_act.md` — **动手前必须完整盘查推导**（老板核心反馈，不预判就动手=浪费上下文）
- `memory/naming_philosophy.md` — **命名哲学与伦理姿态**（黑丝/白纱命名的反向赋权用意，老板原话，所有角色必须内化）
- `memory/research_autoresearch.md` — **Karpathy Autoresearch 调研**（AI训练AI，program.md模式，与evolver对比，暂不动）
- `memory/research_mission_control.md` — **Mission Control 安装记录**（Docker部署搁置，Claude Code API port 8100 可用，launchd守护进程已配）
- `memory/research_qwen35_models.md` — **Qwen 3.5 + 本地模型升级**（Abby主力qwen3.5:9b，上下文8192，16GB内存限制）
