# ~/.claude/ 系统架构文档

> 最后更新：2026-03-27

这是 Claude Code 的配置目录，包含自定义 hooks 管线、evolver 进化系统、learnings 学习系统、以及 Claude Code 系统自带文件。

---

## 目录总览

```
~/.claude/
├── CLAUDE.md                 # 全局行为准则（太极维护，所有项目继承）
├── settings.json             # hooks 配置 + 权限 + MCP servers
├── settings.local.json       # 本地覆盖配置
├── conversations.db          # 对话种子数据库（全项目共用）
├── history.jsonl             # Claude Code 会话历史（系统管理）
├── handofffromtaiji.md       # 太极→黑丝白纱 跨会话通讯
├── .comm_pass                # ttyd 看板认证密码（chmod 600）
├── evolve.sh → evolver/      # symlink，向后兼容
│
├── scripts/                  # 🔧 所有自定义脚本（hooks + 工具）
├── evolver/                  # 🧬 进化系统（全部归此目录）
├── learnings/                # 📝 学习系统（/reflect 产出）
├── skills/                   # ⚡ slash command 技能
├── commands/                 # 📋 用户自定义命令
├── agents/                   # 🤖 subagent 定义（180+）
├── plugins/                  # 🔌 marketplace 插件
├── archive/                  # 📦 归档旧文件
│
├── projects/                 # Claude Code 系统：项目会话 + memory
├── sessions/                 # Claude Code 系统：活跃会话
├── session-env/              # Claude Code 系统：会话环境变量
├── plans/                    # Claude Code 系统：Plan Mode 文件
├── paste-cache/              # Claude Code 系统：粘贴缓存
├── shell-snapshots/          # Claude Code 系统：shell 状态快照
├── backups/                  # Claude Code 系统：配置备份
├── cache/                    # Claude Code 系统：缓存
├── image-cache/              # Claude Code 系统：图片缓存
├── debug/                    # Claude Code 系统：调试日志
├── file-history/             # Claude Code 系统：文件变更历史
├── tasks/                    # Claude Code 系统：任务追踪
├── todos/                    # Claude Code 系统：TODO 追踪
└── telemetry/                # Claude Code 系统：遥测数据
```

---

## Hooks 管线（核心系统）

所有 hooks 配置在 `settings.json` → `hooks` 字段。每个事件触发对应脚本，脚本从 stdin 接收 JSON，stdout 注入 Claude 上下文。

### 事件 → 脚本 对应关系

| 事件 | 脚本 | 作用 |
|------|------|------|
| **Stop** | `db_write.py` | AI 回复结束，写入 conversations.db |
| **UserPromptSubmit** | `db_write.py` | 老板发言，写入 conversations.db |
| **UserPromptSubmit** | `inject_rules.py` | 注入 rules.md 到上下文（stdout） |
| **PreCompact** | `db_write.py` | 压缩前写 `[压缩点]` 标记 |
| **PreCompact** | `evolve_hook.sh` | 触发太极自进化（后台） |
| **PreCompact** | `pre_compact_save.py` | Haiku 生成结构化摘要 + 原始对话保存 |
| **PreCompact** | `reflect_hook.py` | 累计 reflect 待处理信号计数 |
| **SessionStart** | `session_start.py` | 注入恢复上下文（Haiku 摘要 + 对话种子 + MEMORY） |
| **SessionEnd** | `db_write.py` | 写 `[会话结束]` 标记 |
| **SessionEnd** | `reflect_hook.py` | 累计 reflect 待处理信号计数 |
| **SessionEnd** | `evolve_hook.sh` | 触发太极自进化（后台） |
| **PostToolUse** | `post_tool_validate.sh` | Write/Edit 后验证（matcher: `Write\|Edit`） |

### MCP Servers

| 名称 | 脚本 | 作用 |
|------|------|------|
| sequential-thinking | npx 包 | 顺序思考 MCP |
| reflect | `scripts/reflect_mcp.py` | Reflect MCP 接口 |

---

## scripts/ 文件详解

### Hook 脚本（settings.json 直接调用）

| 文件 | stdin 字段 | 输出 | 核心逻辑 |
|------|-----------|------|----------|
| **db_write.py** | hook_event_name, session_id, transcript_path, prompt | conversations.db 写入 | 按事件类型处理：Stop→解析 JSONL 末尾 assistant 回复写入；UserPromptSubmit→写老板发言；PreCompact→写压缩点标记；SessionEnd→写会话结束标记。speaker 判断：model 名(opus→黑丝, sonnet→白纱) + agent_id 覆盖。tags 自动匹配 8 类词表。 |
| **session_start.py** | source, cwd | stdout 注入上下文 | source=compact 时注入完整恢复：对话种子(LIMIT 30) + MEMORY.md(前120行)。所有来源都注入：evolver 通知 + reflect 待处理提醒 + PreCompact 上下文快照。 |
| **pre_compact_save.py** | cwd, session_id | 文件写入 compact_context.md | 从 JSONL 提取最近 50 条对话(合并连续同角色) → 调 `claude -p --model haiku` 生成结构化摘要(当前任务/已完成/待做/关键决策/关键数据) → 两者写入项目目录 compact_context.md。 |
| **inject_rules.py** | cwd | stdout 注入 rules | 读取对应项目的 memory/rules.md，注入到上下文。 |
| **reflect_hook.py** | hook_event_name | 文件写入 pending_signals.json | PreCompact/SessionEnd 时累加 pending_count，记录上次 reflect 时间。 |
| **evolve_hook.sh** | cwd (via stdin JSON) | 后台启动 evolve.sh | cwd 为 home 或 ~/.claude 时，nohup 启动太极自进化。 |
| **post_tool_validate.sh** | — | — | Write/Edit 操作后的验证 hook。 |

### 工具脚本（非 hook，手动或其他方式调用）

| 文件 | 用途 |
|------|------|
| **comm_hub.sh** | ttyd 三实例看板（start/stop/status），认证用 .comm_pass |
| **brief.sh** | 项目简报生成器，从 conversations.db 提取摘要到剪贴板 |
| **group_chat.py** | 群聊服务（多实例协作通讯） |
| **conversations_mcp.py** | 对话种子 MCP Server 接口 |
| **reflect_mcp.py** | Reflect MCP Server 接口 |
| **convert_conversation.py** | JSONL → Markdown 转换工具 |
| **import_history.py** | 历史会话批量导入（写入 dashboard.db，已废弃） |
| **new_project.sh** | 新项目脚手架（生成 CLAUDE.md/handoff/context/review） |
| **validate-modules.js** | Node 模块验证 |

---

## Compact 管线（压缩恢复完整流程）

```
老板输入 /compact
    │
    ▼
┌─ PreCompact 阶段 ─────────────────────────┐
│  1. db_write.py → 写 [压缩点] 到 DB        │
│  2. evolve_hook.sh → 后台启动太极进化       │
│  3. pre_compact_save.py →                   │
│     a. 从 JSONL 提取对话(≤50条，合并)       │
│     b. 调 Haiku 生成结构化摘要              │
│     c. 写入 compact_context.md              │
│  4. reflect_hook.py → 累加 pending 计数     │
└────────────────────────────────────────────┘
    │
    ▼
  Claude Code 截断 JSONL（系统行为）
    │
    ▼
┌─ SessionStart 阶段 ───────────────────────┐
│  session_start.py（source=compact）         │
│  注入到 stdout（进入 Claude 上下文）：       │
│  1. evolver 通知（如有）                    │
│  2. reflect 待处理提醒（如有）              │
│  3. compact_context.md 快照（Haiku 摘要     │
│     + 原始对话），注入后删除                │
│  4. 对话种子（LIMIT 30，从上次压缩点起）    │
│  5. MEMORY.md（前 120 行）                  │
└────────────────────────────────────────────┘
    │
    ▼
  老板下一条消息触发 UserPromptSubmit
    │
    ▼
┌─ UserPromptSubmit 阶段 ───────────────────┐
│  1. db_write.py → 写老板发言到 DB           │
│  2. inject_rules.py → 注入 rules.md        │
└────────────────────────────────────────────┘
```

**并行观察中**：Haiku 摘要（结构化）和对话种子（原始记录）同时注入，待观察效果后决定取舍。

---

## conversations.db 结构

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT,           -- YYYY-MM-DD HH:MM:SS
    speaker TEXT,        -- 无极/黑丝/白纱/系统/未知
    content TEXT,        -- Markdown 原文
    project TEXT,        -- 项目目录编码名（如 -Users-allenbot-project-auto-trading）
    session_id TEXT,     -- Claude Code 会话 ID
    tags TEXT            -- 逗号分隔，自动匹配 8 类词表
);

CREATE TABLE stop_points (
    speaker TEXT,
    project TEXT,
    last_id INTEGER,
    stopped_at TEXT,
    PRIMARY KEY (speaker, project)
);
```

**Tags 词表（8类）**：流程 / 技术验证 / 市场状态 / 数据 / 决策词 / 协作 / 纠错 / 提升 / 策略币种

**Speaker 判断逻辑**：
1. `agent_id` 以 "baisha" 开头 → 白纱
2. model 含 "opus" → 黑丝
3. model 含 "sonnet" → 白纱
4. 老板发言 → 无极
5. 系统事件 → 系统

**项目判断**：通过 session_id 在 `~/.claude/projects/` 查找对应 JSONL 文件所在目录。SKIP_DIRS 排除 home 目录等非项目会话。

---

## evolver/ 进化系统

```
evolver/
├── EVOLVER.md              # 进化系统文档
├── evolve.sh               # 主入口脚本（手动/hook 调用）
├── MEMORY.md               # 进化系统知识库
├── USER.md                 # 进化系统用户配置
├── evolution/              # 进化历史记录（每 cycle 一个 JSON）
├── assets/gep/             # GEP 基因池（genes.json, capsules.json 等）
├── distill_prompt_*.txt    # 蒸馏 prompt 记录（getMemoryDir() 写入此处）
├── distill_request.json    # 蒸馏请求状态
├── tools/                  # 进化引擎（原 ~/.claude/tools/evolver/）
├── logs/                   # 进化日志
├── cycle_notifications.jsonl  # 新 cycle 通知（SessionStart 读取后清空）
├── skills_list_cache.json  # skills 列表缓存
└── evolver_update_check.json
```

**触发方式**：PreCompact/SessionEnd → `evolve_hook.sh` → `evolve.sh taiji`（后台）

---

## learnings/ 学习系统

```
learnings/
├── LEARNINGS.md           # 待毕业学习点（/reflect 产出）
├── LEARNINGS_ARCHIVE.md   # 已毕业归档（promoted → rules.md）
└── pending_signals.json   # 待处理信号计数（reflect_hook.py 维护）
```

**流程**：对话中的纠错/提升信号 → `/reflect` 提取 → LEARNINGS.md → 出现次数达标 → 提案升级到 rules.md → 归档到 LEARNINGS_ARCHIVE.md

**升级条件**：纠错类 1 次即升级，提升类 3 次升级。

---

## skills/ 技能目录

包含 slash command 技能（`/reflect`、`/evo-digest`、`/gene-crossover` 等）。部分是本地目录，部分是指向 `~/.agents/skills/` 或 `/private/tmp/claude-evolver/skills/` 的 symlink。

---

## commands/ 用户命令

| 文件 | 触发方式 | 作用 |
|------|---------|------|
| claude.md | `/claude` | 读取并展示 CLAUDE.md |
| letterfromtaiji.md | `/letterfromtaiji` | 读取太极 handoff |
| ralph.md | `/ralph` | Ralph Loop 代码审查循环 |

---

## agents/ subagent 定义

180+ 个 agent 定义文件（`.md` 格式 + frontmatter）。包含全局通用 agent 和 evolver 专用 agent。项目级 agent 在各项目 `.claude/agents/` 下。

---

## projects/ 项目会话存储

```
projects/
├── -Users-allenbot/                      # 太极（home 目录）
│   ├── memory/                            # 太极 memory 文件
│   │   ├── MEMORY.md                      # 主索引
│   │   ├── rules.md                       # 已毕业全局规则
│   │   ├── framework.md                   # 公司框架全图
│   │   └── ...                            # 其他 memory 文件
│   └── *.jsonl                            # 会话 JSONL 文件
│
├── -Users-allenbot-project-auto-trading/  # auto-trading 项目
│   ├── memory/
│   │   ├── MEMORY.md
│   │   ├── rules.md                       # 项目专属规则
│   │   └── ...
│   └── *.jsonl
│
└── ...                                    # 其他项目
```

**编码规则**：绝对路径 `/` → `-`，`_` → `-`（Claude Code 内部行为）。例：`/Users/allenbot/project/auto-trading` → `-Users-allenbot-project-auto-trading`

---

## archive/ 归档

已不活跃的旧文件，保留备查：

| 文件 | 原位置 | 说明 |
|------|--------|------|
| dashboard.db | 根目录 | 0 字节，已废弃 |
| taiji_last_session.md | 根目录 | 旧会话 dump |
| prompt.md | 根目录 | OpenClaw 问题排查笔记 |
| stats-cache.json | 根目录 | 旧缓存 |
| openclaw.json | 根目录 | OpenClaw 配置 |
| group_chat.log | 根目录 | 群聊日志 |

---

## 关键路径速查

| 要改什么 | 看哪里 |
|----------|--------|
| Hook 触发配置 | `settings.json` → hooks |
| 对话写入逻辑 | `scripts/db_write.py` |
| 压缩恢复注入 | `scripts/session_start.py` |
| 压缩前保存 | `scripts/pre_compact_save.py` |
| 规则注入 | `scripts/inject_rules.py` |
| 进化系统 | `evolver/` |
| 学习/反思 | `learnings/` + `scripts/reflect_hook.py` |
| 全局行为准则 | `CLAUDE.md` |
| 项目 memory | `projects/{项目编码名}/memory/` |
| 已毕业规则 | `projects/{项目编码名}/memory/rules.md` |
| MCP servers | `settings.json` → mcpServers |
| 看板/通讯 | `scripts/comm_hub.sh` |
| 跨会话通讯 | `handofffromtaiji.md` |
