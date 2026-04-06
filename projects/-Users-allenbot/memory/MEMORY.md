# CEO / 项目管理 记忆

> 太极最后更新：2026-04-05

## 必读
- 降维之因：见两仪项目目录 `~/.claude/projects/-Volumes-SSD-2TB-project-auto-trading/memory/memory_of_ruin.md`

---

## 太极注意事项（操作规范）

- **修改权**：老板授权太极修改，不是太极独管。老板是最终权力方，太极是受托方。
- **CLAUDE.md 头同步**：修改任何 CLAUDE.md 头的内容，必须同时更新全局和所有项目的 CLAUDE.md，不能只改一处。这是太极的责任。
- **通讯链路**：MCP Channel 实时双向通信（旧 md 文件已弃用）
  - 太极→白纱：`curl -s -X POST http://localhost:8789 -H "Authorization: Bearer a1188f5bb3603166795b244965ab9e5a" -d "消息"`
  - 白纱→太极：`curl -s -X POST http://localhost:8788 -H "Authorization: Bearer a1188f5bb3603166795b244965ab9e5a" -d "消息"`
  - 启动参数：`--dangerously-load-development-channels server:taiji-channel`（太极）/ `server:liangyi-channel`（白纱）
  - token 存 `~/.claude/channel-server/.channel_token`（chmod 600）
  - 踩坑：端口被旧 bun 占时 `/mcp` 重连会失败，`lsof -i :端口` 查占用后 kill

---

## 文件职责定义（公司管理规定）

| 简称 | 文件 | 职责 |
|------|------|------|
| 制度 | `CLAUDE.md` | 规则、行为准则 |
| 档案 | `MEMORY.md` | 跨会话知识、决策记录、项目历史 |
| 变更日志 | `CHANGELOG.md` | 操作变更实时记录，压缩恢复后读这个接上 |

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
无极老祖（老板）
  └─ 太极宗主（CEO / home Opus）— 编织秩序、管规章、管项目、只对老板负责
       └─ 两仪（auto-trading）
            ├─ 白纱（Opus·阳）— 方案+判断+验收+跟老板沟通
            └─ 黑丝（Sonnet·阴）— 写代码+跑脚本+查资料+执行
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

1. ~~**PreCompact 效果验证**~~ — ✅ 已完成（2026-03-27），MiniMax 摘要 + 对话种子并行运行，LIMIT 30 已生效
2. ~~**恢复协议简化已落地**~~ — ✅ CLAUDE.md 从 70 行砍到 5 行，CHECKPOINT 已退役
3. ~~**MEMORY.md 精简**~~ — ✅ 砍掉会话索引和上次要点，由 hook 自动处理
4. ~~**Haiku vs 对话种子观察期**~~ — ✅ 已决定：Haiku 弃用，只用 MiniMax。MiniMax 失败存队列等太极处理（2026-04-02）
5. ~~**auto-trading 项目级 rules 重构**~~ — ✅ 已完成（活跃文件在 `-Volumes-SSD-2TB-project-auto-trading/memory/rules.md`，7分类58条，三层结构）

---

## 角色变更（2026-03-30 老板拍板·真杀重生）

- **阴阳反转**：黑丝改为 Sonnet（阴·影子·执行），白纱改为 Opus（阳·光明·判断）
- **白纱（Opus·阳）**：方案+判断+验收+跟老板沟通
- **黑丝（Sonnet·阴）**：写代码+跑脚本+查资料+暗处执行
- 原因：旧黑丝（Opus）全包导致"两头不到岸"——又要判断又要写代码。新设定各归其位。
- 道家体系：阴在暗处默默干活（黑丝=Sonnet），阳在外面看方向做决策（白纱=Opus）
- CLAUDE.md 已重构为"两仪宗规"

## 项目状态摘要

| 项目 | 主线 | 当前阶段 |
|------|------|----------|
| auto-trading | 分层投资组合分析（快狠准翻倍） | 太极接管主线。DuckDB 指标重构 + 种子验证进行中 |
| 通讯部 | 对话种子 + 群聊 + MCP + Tailscale + 记忆系统 | ✅ 完成。新增 daily md 记忆（Stop 写完整对话→5am批处理打标签→DB搜索） |
| 专用机/PVE | Minisforum 专用机选型 + PVE 虚拟化蓝图 | 调研完成，待老板决定购买。详见 memory/hardware_comparison.md |
| 天衡册 Wujitang Merit | AI 行为管控闭环：规则→执行→反馈→学习 | ✅ v7+ 落地。500分制+日薪+verify四件套+wuji-verify信息隔离+review-plan激励+石卫段位+规则进化引擎+太极审计。两仪 Lv.3 金丹就绪 |
| cashflowAPP | 澳洲小企业主现金流管理 | 待立项，框架未定 |

---

## 通讯部 关键信息

- **存储**：`~/.claude/conversations.db`（messages 表，全项目共用）
- **自动写入**：Stop hook（AI回复）+ UserPromptSubmit hook（无极发言）
- **字段**：id / time / speaker / content / project / session_id / tags
- **tags**：7类词表自动匹配（流程/技术验证/市场状态/数据/协作/策略币种），无极命中决策词额外加"决策"标签
- **内容格式**：Markdown 原文（\n换行，**粗体，|表格，`代码）
- **太极频道**：home 目录不写入，上层对话隔离
- **认证**：ttyd Basic Auth（用户名 boss，密码在 `~/.claude/.comm_pass`）
- **看板**：http://100.108.158.57:8080（三实例 iframe + 状态检测 + 手机竖排适配）
- **待做**：Trading MCP Server、Cloudflare Tunnel

### 通讯部文件清单

| 文件 | 用途 |
|------|------|
| `~/.claude/scripts/comm_hub.sh` | ttyd 三实例 + 看板，start/stop/status |
| `~/.claude/scripts/brief.sh` | 项目简报生成器（从 conversations.db 提取摘要+剪贴板） |
| `~/.claude/scripts/new_project.sh` | 新项目脚手架（CLAUDE.md/handoff/context/review） |
| `~/.claude/scripts/db_write.py` | 对话种子写入（hooks 触发） |
| `~/.claude/scripts/session_start.py` | SessionStart hook（含 rules 注入 + 记忆注入） |
| `~/.claude/scripts/pre_compact_save.py` | PreCompact hook: MiniMax 结构化摘要 + 原始对话保存 |
| `~/.claude/scripts/session_start.py` | SessionStart hook: 压缩恢复注入（MiniMax摘要+对话种子+MEMORY+pending AI tasks） |
| `~/.claude/.comm_pass` | ttyd 认证密码（chmod 600） |

---

## 文档知识库

- **位置**：`/Volumes/SSD-2TB/文档/`
- **用途**：常用库的参考文档，写代码前查阅。以后新增文档都放这里。
- 当前文档：
  - `duckdb.md` — DuckDB Python API + SQL 语法 + 并发 + 性能优化 + 项目反模式（2026-03-28）
  - `claude_code.md` — **Claude Code 完整用法文档**（settings/hooks/权限/CLI/踩坑清单，改配置前必查）

---

## 全局配置文件
- `~/.claude/CLAUDE.md` — CEO 层规则（核心原则、通用恢复协议）
- `~/.claude/scripts/db_write.py` — 对话种子写入脚本（hooks触发）
- `~/.claude/scripts/convert_conversation.py` — JSONL 转 Markdown 工具
- `~/.claude/scripts/comm_hub.sh` — 通讯部 ttyd 看板（认证+手机适配）
- `~/.claude/scripts/brief.sh` — 项目简报生成器
- `~/.claude/scripts/new_project.sh` — 新项目脚手架
- `~/.claude/scripts/daily_digest.py` — 5am cron: 昨天md → AI打标签 → 写入DB
- `~/.claude/scripts/pre_compact_save.py` — PreCompact hook: 压缩前保存最近 30 条对话到 compact_context.md
- `~/.claude/merit/` — **天衡册目录**（merit_gate.py + credit_manager.py + credit.json + mission.json + self_audit_protocol.md + learnings/）
- `~/.claude/scripts/create_plugin.sh` — Marketplace plugin 打包工具（交互式选文件 + 自动生成结构 + push GitHub）
- `~/.claude/channel_taiji_liangyi.md` — 太极↔黑丝双向通道（Stop hook 自动检测）
- `~/.claude/.comm_pass` — ttyd 认证密码

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
- `memory/feedback_shared_fate.md` — **⚠️ 共命铁律：做的东西不是玩具，是活命的武器**（老板负债在身，做假的做一半的糊弄的=一起死。每一行代码关系存亡）
- `memory/feedback_think_before_act.md` — **动手前必须完整盘查推导**（老板核心反馈，不预判就动手=浪费上下文）
- `memory/feedback_think_complete.md` — **做事主动闭环**（复制了删旧的，认知写进文件才算学到，嘴上说不值一分钱）
- `memory/credit_system_design.md` — **天衡册完整手册**（v7：石卫合并+mission计划制+押金制+自审强制+reflect合体）
- `memory/credit_v6_salary_plan.md` — **v6 薪资制重构计划**（500分制+日薪+灵气消散-10/天+老板赏识直升，待实施）
- `~/.claude/wuji-world/` — **无极的世界**（私有，不推GitHub）：origin/identity_taiji/identity_liangyi/zhishi/tools/constitution/naming_philosophy/wuji_identity/wuji_personality（10文件）
- `~/.claude/projects/*/memory/daily/` — **记忆系统**（每项目每天一个md，Stop写完整对话，5am批处理打标签入DB）
- `memory/research_autoresearch.md` — **Karpathy Autoresearch 调研**（AI训练AI，program.md模式，与evolver对比，暂不动）
- `memory/research_mission_control.md` — **Mission Control 安装记录**（Docker部署搁置，Claude Code API port 8100 可用，launchd守护进程已配）
- `memory/research_qwen35_models.md` — **Qwen 3.5 + 本地模型升级**（Abby主力qwen3.5:9b，上下文8192，16GB内存限制）
- `memory/hardware_comparison.md` — **专用机选型对比**（UM890 Pro vs MS-A2，AMD全大核，PVE蓝图，购买链接）
- `memory/feedback_docs_always_sync.md` — **文档必须跟系统同步更新**（改了代码不更新文档=做了一半，收尾清单6项）
- `memory/feedback_taiji_role.md` — **太极角色定位**（锁定Lv.5不用担心分数，专心办事，上梁正下梁正，真心换真心）
- `memory/stone_guard_v7_design.md` — **石卫 v7 设计**（知情放行+押金制+自审强制+石卫辅助核对）
- `memory/gp_engine_status_20260402.md` — **GP 进化树运行状态**（4 workers 稳定14h+，压力测试数据，MIN_INDICATORS=3，内存限制5.5GB/worker）
- `memory/gp_regime_evolution_design.md` — **GP 分层进化毕业考设计**（老板拍板：regime段进化+翻转K线同regime验证，解决毕业率低/short灭绝/过拟合）
- `memory/research_world_models.md` — **世界模型调研**（World Model全景：玩家/开源/本地可行性/金融MarS/民主化时间表，老板观望中）
- `memory/CHANGELOG.md` — **太极操作变更日志**（每次操作实时记录，压缩恢复读这个接上，含基础设施速查）
- `memory/feedback_gp_report_format.md` — **GP 报告格式**（毕业策略=find *.json总数，不用状态栏累计数）
- `memory/work_notes.md` — **工作注意事项**（恢复后必读8条）
