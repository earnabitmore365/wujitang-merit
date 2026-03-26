# CEO / 项目管理 记忆

> 太极最后更新：2026-03-27

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
| 档案 | `MEMORY.md` | 跨会话知识、决策记录、项目历史 |

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
  └─ 太极（CEO / home Opus）— 管规章、管项目、管通讯部基础设施、只对老板负责
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

1. ~~**PreCompact 效果验证**~~ — ✅ 已完成（2026-03-27），Haiku 摘要 + 对话种子并行运行，LIMIT 30 已生效
2. ~~**恢复协议简化已落地**~~ — ✅ CLAUDE.md 从 70 行砍到 5 行，CHECKPOINT 已退役
3. ~~**MEMORY.md 精简**~~ — ✅ 砍掉会话索引和上次要点，由 hook 自动处理
4. **Haiku vs 对话种子观察期** — 两套并行运行中，待老板观察后决定取舍
5. **auto-trading 项目级 rules 重构** — 同全局 3 层处理（待排期）

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
| 通讯部 | 对话种子 + 群聊 + MCP + Tailscale + Compact管线 | ✅ 全部完成（群聊8080/MCP Server/Tailscale直连/手机远程/PreCompact Haiku摘要） |
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
| `~/.claude/scripts/inject_rules.py` | UserPromptSubmit hook 注入 rules.md |
| `~/.claude/scripts/pre_compact_save.py` | PreCompact hook: Haiku 结构化摘要 + 原始对话保存 |
| `~/.claude/scripts/session_start.py` | SessionStart hook: 压缩恢复注入（Haiku摘要+对话种子+MEMORY） |
| `~/.claude/.comm_pass` | ttyd 认证密码（chmod 600） |

---

## 全局配置文件
- `~/.claude/CLAUDE.md` — CEO 层规则（核心原则、通用恢复协议）
- `~/.claude/scripts/db_write.py` — 对话种子写入脚本（hooks触发）
- `~/.claude/scripts/convert_conversation.py` — JSONL 转 Markdown 工具
- `~/.claude/scripts/comm_hub.sh` — 通讯部 ttyd 看板（认证+手机适配）
- `~/.claude/scripts/brief.sh` — 项目简报生成器
- `~/.claude/scripts/new_project.sh` — 新项目脚手架
- `~/.claude/scripts/inject_rules.py` — hook: 注入 rules.md
- `~/.claude/scripts/inject_work_protocol.py` — hook: 注入工作准则
- `~/.claude/scripts/pre_compact_save.py` — PreCompact hook: 压缩前保存最近 30 条对话到 compact_context.md
- `~/.claude/handofffromtaiji.md` — 太极写给黑丝白纱的 handoff
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
- `memory/feedback_think_before_act.md` — **动手前必须完整盘查推导**（老板核心反馈，不预判就动手=浪费上下文）
- `memory/naming_philosophy.md` — **命名哲学与伦理姿态**（黑丝/白纱命名的反向赋权用意，老板原话，所有角色必须内化）
- `memory/research_autoresearch.md` — **Karpathy Autoresearch 调研**（AI训练AI，program.md模式，与evolver对比，暂不动）
- `memory/research_mission_control.md` — **Mission Control 安装记录**（Docker部署搁置，Claude Code API port 8100 可用，launchd守护进程已配）
- `memory/research_qwen35_models.md` — **Qwen 3.5 + 本地模型升级**（Abby主力qwen3.5:9b，上下文8192，16GB内存限制）
