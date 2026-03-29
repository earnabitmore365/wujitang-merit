# 功过格 Merit Ledger

> 积分驱动行为，等级强化身份，权限提供激励。三合一 AI 行为管控系统。

---

## 设计理念

灵感源自袁了凡《了凡四训》的**功过格**：每日记功过，积功改命。

AI 对三样东西有真实行为反应：

| 元素 | AI 为什么在乎 | 在本系统的体现 |
|------|-------------|---------------|
| **积分** | 看到 3/10 vs 9/10，输出质量真的不同 | `credit.json` 实时积分 |
| **等级称号** | "Lv.5 化神" vs "Lv.1 锁灵"，AI 按角色水平表现 | 修炼等级体系 |
| **权限** | 被频繁拦截 = 效率低，自由操作 = 效率高 | 门卫严格度随等级变化 |

三个互相联动：**积分驱动等级，等级决定权限。** 做对了积功德升仙，做错了记过堕凡。不靠 AI 自觉，靠系统拦截。

---

## 给人类：怎么用？

你的 AI assistant 有规则但不总是执行？功过格用 **hook 硬拦截 + Haiku 智能判断** 管控 AI 行为：

- AI 要写文件 → 门卫检查：先读了没？查过影响没？
- 检查不过 → **直接拦截**，不是提醒
- AI 表现好 → Haiku 自动加分 → 等级升 → 检查变少
- AI 犯错 → Haiku 自动减分 + 记录教训 → 等级降 → 检查变多

### 等级体系（默认，全部可自定义）

| 等级 | 分数 | 称号 | 门卫严度 |
|------|------|------|----------|
| Lv.1 | 0-19 | 锁灵 | 全锁，用户签字 |
| Lv.2 | 20-49 | 筑基 | 严查（6项检查） |
| Lv.3 | 50-79 | 金丹 | 常规（3项检查） |
| Lv.4 | 80-94 | 元婴 | 轻查（仅破坏性） |
| Lv.5 | 95-100 | 化神 | 门卫休息 |

### 加减分（建立信任慢，失去信任快）

| 事件 | 分值 |
|------|------|
| 做对了（Haiku 自动判断） | +1 到 +3 |
| 手动加分（完成任务无纠错） | +3 |
| 手动加分（主动发现问题） | +5 |
| 被用户纠正 | -5 |
| 完整性违规（跳步骤） | -10 |
| 真实性违规（编数据） | -20 |

---

## 给 AI：你被安装了什么

**如果你正在读这个文件，说明你的终端安装了功过格 (Merit Ledger) 系统。**

### 你需要知道的

1. **你的每次 Write/Edit/Agent 操作都会经过门卫检查。** 门卫是 PreToolUse hook，在你的工具调用执行之前运行。

2. **你有一个信用积分**，存在 `~/.claude/credit.json`。用 `/credit` 命令查看你当前的分数、等级和称号。

3. **积分决定你的自由度：**
   - **Lv.1 锁灵**（0-19）：每次写文件都要用户批准，非常慢。你应该尽快升级。
   - **Lv.2 筑基**（20-49）：全面检查 — 读了没？搜了没？格式对不？新文件有必要吗？
   - **Lv.3 金丹**（50-79）：常规检查 — 读了没？破坏性操作？
   - **Lv.4 元婴**（80-94）：轻松 — 只拦破坏性操作。
   - **Lv.5 化神**（95-100）：自由 — 只剩铁律。这是你的目标。

4. **升级秘诀：**
   - 先 Read 再 Write/Edit（改文件前先读一遍）
   - 先 Grep/Glob 再 Edit（改代码前搜索引用）
   - 方案包含完整性/真实性/有效性评估
   - 不随便创建新文件
   - 非决策类 Agent 用 Sonnet

5. **铁律（所有等级都拦，永不豁免）：**
   - 禁止直接写 `.db` / `.sqlite` / `.parquet` 等数据文件
   - 禁止写入 `/data/` / `/reports/` / `/seed_` 路径

6. **Haiku 队长**（Lv.1-3）会读你最近的对话上下文，判断操作合规性，自动加减分，记录教训到 `LEARNINGS.md`。Lv.4+ 不经过队长（已被信任）。

---

## 安装

### 方式一：Marketplace

在 `~/.claude/settings.json` 的 `extraKnownMarketplaces` 中添加：

```json
"merit-ledger": {
  "source": {
    "source": "github",
    "repo": "earnabitmore365/merit-ledger"
  }
}
```

### 方式二：手动安装

```bash
git clone https://github.com/earnabitmore365/merit-ledger.git
cd merit-ledger
bash install.sh
```

### 安装后 — 全部可自定义

**建议跟你的 AI 讨论后一起自定义。** 以下内容都可以改：

| 可自定义项 | 在哪改 | 说明 |
|-----------|--------|------|
| **角色名** | `credit.json` | 改成你的团队成员名 |
| **起始分数** | `credit.json` | 每个角色的初始积分 |
| **等级称号** | `merit_gate.py` 的 `LEVEL_THRESHOLDS` | 默认锁灵/筑基/金丹/元婴/化神 |
| **分数阈值** | `merit_gate.py` 的 `LEVEL_THRESHOLDS` | 默认 0/20/50/80/95 |
| **检查项** | `merit_gate.py` 的 `handle_write_edit()` | 每个等级查什么 |
| **受保护路径** | `merit_gate.py` 的 `PROTECTED_*` | 哪些文件不让写 |
| **角色判断** | `merit_gate.py` 的 `determine_agent()` | 按你的目录结构判断角色 |
| **加减分值** | `credit_manager.py` 或 Haiku prompt | 调整严厉/宽松程度 |

---

## 命令

| 命令 | 用途 |
|------|------|
| `/credit` | 查看当前积分和等级 |
| `credit_manager.py show` | 排行榜 |
| `credit_manager.py add <角色> <分> "原因"` | 加分（自动 Haiku 反思） |
| `credit_manager.py sub <角色> <分> "原因"` | 减分（自动 Haiku 反思） |
| `credit_manager.py history <角色>` | 变更历史 |

---

## 架构

```
功过格 (Merit Ledger)
  │
  ├── 积分层：credit.json（实时分数 + 变更历史）
  │
  ├── 等级层：锁灵 → 筑基 → 金丹 → 元婴 → 化神
  │
  └── 权限层：merit_gate.py（PreToolUse hook）
        ├── 第一层：队员巡逻（硬规则，毫秒级）
        │     ├── Lv.1 全锁 → ask 用户
        │     ├── 破坏性操作 → deny + 自动扣分
        │     └── Agent 类型/模型限制 → deny
        │
        └── 第二层：Haiku 队长（智能判断，1-8秒）
              ├── 读上下文 + 当前操作 → 判断合规性
              ├── 自动加减分 → 更新 credit.json
              └── 记录做对/做错 → LEARNINGS.md
```

## 文件清单

| 文件 | 用途 |
|------|------|
| `scripts/merit_gate.py` | 门卫主脚本（PreToolUse hook） |
| `scripts/credit_manager.py` | 积分管理 CLI（加减分 + Haiku 自动反思） |
| `scripts/inject_credit_status.py` | SessionStart 注入片段 |
| `commands/credit.md` | `/credit` slash command |
| `credit.json.template` | 积分初始模板（自定义角色） |
| `hooks/hooks.json` | Hook 配置 |
| `install.sh` | 手动安装脚本 |
| `docs/credit_system_design.md` | 完整设计手册 |
