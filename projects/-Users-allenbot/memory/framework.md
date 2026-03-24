# 公司框架全图

> 太极创建：2026-03-08
> 目的：完整记录现有框架，所有分支可从此追溯来源
> 修改权：老板授权太极修改

---

## 层级结构

```
老板（无极）— 最终决策
    └─ 太极（CEO / home Sonnet）— 管规章、管项目
         ├─ 白纱（auto-trading Sonnet）— 方案架构师
         └─ 黑丝（auto-trading Opus）— 执行工程师
```

---

## 文件全图

### 层级一：太极（全局，home 目录）

| 类型 | 文件路径 | 作用 |
|------|---------|------|
| 制度 | `~/.claude/CLAUDE.md` | 核心原则 + 太极恢复协议 + 禁止操作（头身脚结构） |
| 知识 | `~/.claude/projects/-Users-allenbot/memory/MEMORY.md` | 跨会话知识、公司架构、项目状态摘要 |
| 日记 | `~/.claude/projects/-Users-allenbot/memory/session_summaries.md` | 太极每次会话精华摘要 |
| 规则 | `~/.claude/projects/-Users-allenbot/memory/rules.md` | 太极已毕业行为规范 |
| 框架 | `~/.claude/projects/-Users-allenbot/memory/framework.md` | 本文件，公司框架全图 |

### 层级二：黑丝·白纱（auto-trading 项目）

| 类型 | 文件路径 | 作用 |
|------|---------|------|
| 制度 | `/project/auto-trading/CLAUDE.md` | 项目规章，override 全局；含角色定义/协作三阶段/Guardrails |
| 任务 | `/project/auto-trading/CHECKPOINT.md` | 任务状态交接（动态区=当前进度；静态区=已完成记录+永久参考） |
| 决策库 | `/project/auto-trading/DESIGN_DECISIONS.md` | 10条关键设计决策 WHY，改动前必读 |
| 知识 | `memory/MEMORY.md`（项目） | 黑丝白纱跨会话知识、铁律、经典语录 |
| 日记 | `memory/session_summaries.md`（项目） | 黑丝区 + 白纱区，各自会话摘要 |
| 规则 | `memory/rules.md`（项目） | RUL-001~010 已毕业行为规范 |
| 专题 | `memory/validation_suite.md` | 验证套件知识 |
| 专题 | `memory/screening_pipeline.md` | 策略筛选流程 |
| 专题 | `memory/roadmap_ideas.md` | 中后期路线图想法 |

### 层级三：通讯（跨层）

| 方向 | 文件路径 | 性质 |
|------|---------|------|
| 太极 → 黑丝/白纱 | `~/.claude/handofffromtaiji.md` | 太极发出指令；没更新=没事发生，不是问题 |
| 黑丝/白纱 → 太极 | `/project/auto-trading/handofftotaiji.md` | 下属回信；太极在恢复协议步骤3读 |

### 层级四：实时数据

| 类型 | 文件/机制 | 作用 |
|------|----------|------|
| 对话种子 | `~/.claude/conversations.db` | 三方原话实时写入（messages + stop_points），跨项目共用 |
| 写入脚本 | `~/.claude/scripts/db_write.py` | Hook 触发：Stop/UserPromptSubmit/PreCompact/SessionEnd |
| Hook 配置 | `~/.claude/settings.json` | 四个 Hook 的触发条件和脚本路径 |
| 原始记录 | `~/.claude/projects/*/uuid.jsonl` | Claude Code 会话原文，恢复协议读上文用 |
| 转换工具 | `~/.claude/scripts/convert_conversation.py` | JSONL → Markdown |

---

## 串联流程

### 新会话（黑丝/白纱）
```
1. JSONL → convert_conversation.py → 读上文
2. MEMORY + session_summaries + rules + DESIGN_DECISIONS
3. conversations.db（SELECT 近200条）
4. CHECKPOINT + handofffromtaiji
5. 写日志 → session_summaries + MEMORY 更新
6. 输出状态，等老板
```

### 压缩后（黑丝/白纱）
```
SessionStart hook 注入（对话+摘要+CHECKPOINT+MEMORY）
0. handofffromtaiji + DESIGN_DECISIONS + rules
1. 写日志
2. 输出状态，等老板
```

### 新会话（太极）
```
1. JSONL → 读上文
2. MEMORY + session_summaries + rules
3. CHECKPOINT（当前工作目录）+ handofftotaiji（各项目）
4. 写日志
5. 输出状态
```

### 实时写入
```
老板发言      → UserPromptSubmit → conversations.db（messages）
AI 回复       → Stop             → conversations.db（messages + stop_points）
压缩前        → PreCompact       → conversations.db（压缩标记 + stop_points）
会话结束      → SessionEnd       → conversations.db（结束标记 + stop_points）
```

### 规则沉淀
```
老板纠正（原话）→ /reflect → LEARNINGS.md（临时）
→（纠错出现1次立即升级，提升出现3次升级）→ 老板批准 → rules.md（毕业）
```

### 通讯链路
```
太极决策 → handofffromtaiji.md → 黑丝/白纱在恢复时读
黑丝/白纱回报 → handofftotaiji.md → 太极在步骤3读
```

---

## CLAUDE.md 头身脚结构

| 段 | 内容 | 修改权 |
|----|------|--------|
| 头 | 核心原则、恢复协议、禁止操作 | 老板授权太极 |
| 内容 | 角色定义、协作流程、Guardrails | 老板 + 太极 |
| 脚 | 工具说明、查询模板 | 老板授权太极 |

**同步规则**：修改任何 CLAUDE.md 头的内容，必须同时更新全局和所有项目的 CLAUDE.md。这是太极的责任。

---

## CHECKPOINT.md 结构

| 区 | 标记 | 内容 | 规则 |
|----|------|------|------|
| 动态区 | `<!-- DYNAMIC START/END -->` | 主线/支线/打磨/当前步骤 | 每次对照模板整体替换 |
| 静态区 | `<!-- DYNAMIC END -->` 之后 | Schema/参数/命名规范/AI Sandbox | 既有内容不改；拍板完成的事项可在对应区域末尾追加一句话+简短说明 |

---

## 待解决问题追踪

| # | 问题 | 状态 |
|---|------|------|
| 1 | 太极恢复协议加 rules.md | ✅ 2026-03-08 已修 |
| 2 | 太极恢复协议加 handofftotaiji.md | ✅ 2026-03-08 已修 |
| 3 | CHECKPOINT 静态区规则澄清（可追加记录，不能改既有内容） | ✅ 2026-03-08 已修 |
| 4 | Guardrails 第一条修正（记录≠确认，立即写入 CHECKPOINT） | ✅ 2026-03-08 已修 — 审计发现只在对话标出，确认前不动 CHECKPOINT |
| 5 | 信息散落问题 → Vibe Coding 解法（单一计划文件，AI 照计划走并及时更新） | 🔲 待推进 |
| 6 | Guardrails 通用条移入协作规范 | ✅ 2026-03-08 已完成 — 直接全面融合为 Guardrails 格式，协作规范/核心原则均已废除 |
| 7 | CHECKPOINT 静态区旧 v2 种子数据过时 → 规则：黑丝执行完成时自检静态区，改了永久信息就追加 | ✅ 2026-03-08 已写入 — 嵌入强制更新节点第3条 + Task 工具强制规则一并加入 |
| 8 | identity.md 独立文件（太极/白纱·黑丝身份定义） | ✅ 2026-03-08 已完成 — 两个 CLAUDE.md 改为必读引用 |
| 9 | Guardrails 全面融合（全局 G-001~G-X01 + 项目专属） | ✅ 2026-03-08 已完成 |
| 10 | 三层记忆系统（鲜活/温度/冷）写入框架 | ✅ 2026-03-08 已完成 — 鲜活层含当前上下文窗口，嵌入恢复协议 |
