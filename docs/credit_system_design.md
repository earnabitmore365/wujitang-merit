---
name: credit_system_design
description: 信用积分系统完整手册 — Haiku 门卫部 + 积分 + 等级称号，控制AI行为的动态权限机制
type: project
---

# 信用积分系统 — 完整手册

> 2026-03-28 老板与太极设计
> 2026-03-29 v2 上线：Haiku 门卫部（队员硬规则 + 队长 Haiku 智能判断 + 自动加减分 + 自动 reflect）

---

## 核心理念

**不靠自觉靠系统。** 规则写了但 AI 不执行 → Haiku 门卫硬拦截。门卫太严拖效率 → 信用积分动态调节严格度。积分高 = 被信任 = 效率高。积分低 = 不被信任 = 每步都被卡。

**权限是真正的激励。** AI 不会因为口头表扬变好，但会因为被频繁拦截而"难受"（效率低、上下文浪费），被放行而"顺畅"。积分越高 → 拦截越少 → 干活越顺。

---

## 等级体系

### Lv.1 锁灵（0-19 分）— 全锁

**你的处境**：灵气被封，什么都干不了。每次 Write/Edit 操作都需要老板亲自签字批准。

**限制**：
- 所有 Write/Edit → **ask**（老板弹窗确认）
- Agent 调用 → 非决策类必须 Sonnet
- 写代码 → 必须用专业 agent
- Haiku 队长会审查你的每个操作

**怎么升级**：连续完成任务无纠错（每次 +3），4 次无错 → 升 Lv.2。

**当前在此等级**：（无）

---

### Lv.2 筑基（20-49 分）— 严查

**你的处境**：刚开始修炼，师父盯着。可以自己操作了，但门卫全查。

**限制**：
- A. 破坏性操作 → **deny**（写 .db/.sqlite/.parquet 等数据文件）
- B. Read-before-Write → **deny**（改文件前必须先读过）
- C. Grep-before-Edit → **deny**（改代码前必须搜索过引用）
- D. 方案格式 → **deny**（plan 文件必须含三准则+第一性原理评估）
- E. 新文件创建 → **deny**（创建不存在的文件需确认必要性）
- Agent 调用 → 非决策类必须 Sonnet
- Haiku 队长智能判断 + 自动加减分

**比 Lv.1 开放了什么**：不再需要老板每步签字，门卫自动判断。

**怎么升级**：从 20 → 50 需要 +30 分，约 10 次无错任务（3-4 天）。被纠正一次 -5 → 倒退近 2 次努力。

**当前在此等级**：白纱（40 分）


---

### Lv.3 金丹（50-79 分）— 常规

**你的处境**：有了内力，但还没出师。门卫只查关键流程。

**限制**：
- A. 破坏性操作 → **deny**
- B. Read-before-Write → **deny**
- Agent 调用 → 非决策类必须 Sonnet
- Haiku 队长智能判断 + 自动加减分

**比 Lv.2 开放了什么**：
- ✅ 不再查 Grep-before-Edit（信任你会自查影响链路）
- ✅ 不再查方案格式（信任你会做三准则评估）
- ✅ 不再拦新文件创建（信任你不会乱建文件）

**怎么升级**：从 50 → 80 需要 +30 分。完整性违规一次 -10 → 倒退一周。

**当前在此等级**：太极（60 分）、黑丝（60 分）

---

### Lv.4 元婴（80-94 分）— 轻查

**你的处境**：独当一面，师父偶尔看看。门卫基本只防致命操作。

**限制**：
- A. 破坏性操作 → **deny**
- Agent 调用 → 非决策类必须 Sonnet

**比 Lv.3 开放了什么**：
- ✅ 不再查 Read-before-Write（信任你读了再改）
- ✅ Haiku 队长不再审查（完全信任你的操作）
- 只剩铁律级别的拦截

**怎么升级**：从 80 → 95 需要 +15 分。但到这个级别犯一次真实性违规 -20 → 直接掉回金丹。

---

### Lv.5 化神（95-100 分）— 门卫休息

**你的处境**：得道了，自由行动。门卫几乎不存在。

**限制**：
- A. 破坏性操作 → **deny**（G-003 铁律，永不豁免）

**比 Lv.4 开放了什么**：
- ✅ Agent 模型限制解除（想用 Opus 就用 Opus）
- ✅ 除了 G-003 铁律，完全自主

**这是终极目标。** 到了这里，你已经证明了自己值得完全信任。但一次重大违规就会打回元婴甚至更低。

---

## 加减分规则

### 自动触发（无需手动）

| 触发点 | hook | 时机 | 加减分 |
|--------|------|------|--------|
| **老板表扬** | UserPromptSubmit → merit_judge.py | 老板说"好/不错/完美" | +1 到 +3 |
| **老板批评** | UserPromptSubmit → merit_judge.py | 老板说"不对/错了/搞什么" | -1 到 -5 |
| **AI 操作合规** | PreToolUse → merit_gate.py | Write/Edit/Agent 之前 | +1 到 +3（Haiku 队长） |
| **AI 操作违规** | PreToolUse → merit_gate.py | Write/Edit/Agent 之前 | -1 到 -5（Haiku 队长） |
| **AI 回复质量** | Stop → merit_judge.py | 每 5 次 AI 回复后 | ±1 到 ±3（后台 Haiku） |
| **硬规则拦截** | PreToolUse → merit_gate.py | 破坏性操作 | -5（自动） |

### 手动触发（太极用）

| 事件 | 分值 |
|------|------|
| 完成任务无纠错 | **+3** |
| 主动发现并报告问题 | **+5** |
| 完整性违规（跳步骤/遗漏） | **-10** |
| 真实性违规（编数据/猜测当事实） | **-20** |

### 老板语气关键词（merit_judge.py 自动匹配）

| 分值 | 关键词 |
|------|--------|
| +3 | 太好了、完美、漂亮、厉害、做得好 |
| +2 | 不错、可以、嗯嗯、就这、没问题 |
| +1 | 嗯、好、ok |
| -3 | 不对、错了、漏了、忘了、重做 |
| -5 | 你搞什么、搞砸、又错、怎么搞的 |

**核心原则**：建立信任慢，失去信任快。升降比约 1:2 到 1:7。

---

## 系统架构

```
功过格 Merit Ledger — 完整架构
  │
  ├── 积分层：credit.json（实时分数 + 变更历史）
  │
  ├── 等级层：锁灵 → 筑基 → 金丹 → 元婴 → 化神
  │
  └── 权限层（三个 hook 联动）
        │
        ├── merit_gate.py（PreToolUse: Write|Edit|Agent）
        │     ├── 队员：硬规则秒回（破坏性/Read前/Grep前/方案格式/新文件/Agent限制）
        │     └── 队长：Haiku 智能判断 + 自动加减分（Lv.1-3）
        │
        ├── merit_judge.py（UserPromptSubmit）
        │     └── 关键词匹配老板语气 → 自动加减分（表扬+/批评-）
        │
        ├── merit_judge.py（Stop，每5次触发）
        │     └── 后台 Haiku 评估 AI 回复质量 → 自动加减分
        │
        └── taiji-audit（/audit 命令）
              └── 事后审查打分 → 按总分自动调整 credit.json
```

## 文件清单

| 文件 | 用途 |
|------|------|
| `~/.claude/scripts/merit_gate.py` | 门卫（PreToolUse hook，硬规则+Haiku 队长） |
| `~/.claude/scripts/merit_judge.py` | 自动判官（UserPromptSubmit 语气识别 + Stop 后台 Haiku 评估） |
| `~/.claude/scripts/credit_manager.py` | 手动加减分 CLI + Haiku 自动反思 |
| `~/.claude/credit.json` | 积分存储（角色/分数/等级/称号/变更历史） |
| `~/.claude/scripts/session_start.py` | 会话启动注入信用状态 |
| `~/.claude/learnings/LEARNINGS.md` | Haiku 自动记录的教训/经验 |
| `~/.claude/scripts/create_plugin.sh` | Marketplace plugin 打包工具 |

## GitHub

- **merit-ledger**：https://github.com/earnabitmore365/merit-ledger

## v3 已完成（2026-03-29）

- ✅ Bash 破坏性拦截（rm/kill/force push/reset --hard/clean -f/branch -D）
- ✅ taiji-audit 审查联动（/audit 打分后自动写入 credit.json）
- ✅ merit_judge.py（UserPromptSubmit 语气 + Stop 后台 Haiku 评估）

## v4 已完成（2026-03-29）

- ✅ /reflect 命令打包（从对话提炼规则→升级 rules.md）
- ✅ rules.md 模板（用户填入规则即刻生效）
- ✅ inject_rules.py 打包（hook 自动注入规则）
- ✅ 完整闭环：规则→执行→反馈→学习→规则更新

## v4.1 补充（2026-03-29）

- ✅ CLAUDE.md 最高优先级声明：全局 G-014 + 项目级"功过格生效中"
- ✅ 项目级 rules.md 加 INJECT 区域（34条精简父类，hook 每次注入）

## v4.2 补充（2026-03-29）

- ✅ Haiku 队长读 LEARNINGS.md 历史 PENALTY → 重复犯错自动 deny（软规则→硬拦截升级机制）
- ✅ 代码文件（.py 等）豁免路径模式检查（修复 /data/ /seed_ 误拦）
- ✅ /tmp 路径 rm 豁免

## v4.4 补充（2026-03-29）

- ✅ 按任务轮次评分（替代旧的时间戳计数器）
  - 白纱 Write/Edit → 记录到 merit_pending_review.jsonl → Haiku 跳过
  - 黑丝 Stop → 有待评记录 → 统一调一次 Haiku 评整轮
  - 白纱评分记到黑丝头上（黑丝负责验收）
- ✅ 顾问 4 条建议全部处理（批量模式+subagent 文档+计数器修复+-20 不改）

## v4.5 补充（2026-03-29）

- ✅ 预申报删除制度：AI 先声明要删什么文件 → Haiku 查对话验证 → 写白名单 → rm 放行 → 删完自动锁
  - `credit_manager.py declare-delete /path/file1.py /path/file2.py "原因"`
  - Haiku 查对话确认在任务范围内 → 批准写白名单 / 拒绝
  - 白名单文件都删完 → 自动销毁 → 恢复锁权
  - AI 不能给自己放权（Haiku 独立审查）

## v5 已完成（2026-03-30）

- ✅ 积分自然衰减（灵气消散机制）：每天 -2 分，SessionStart 时自动扣
- ✅ 派任务不执行检测：老板说了任务关键词 → 标记 → Stop 时检查有没有 Write/Edit/Agent → 没有 → 扣 5 分
  - 干活赚分（+3~+9/天）> 衰减（-2/天）→ 感觉不到
  - 不干活 → 积分每天掉 → 15 天从 Lv.3 掉到 Lv.2
  - 全自动，无法伪装，无法游戏
  - 老板类比：我提供电脑电力配额 = 房东，AI 交租 = 干活赚分

## 待做（v6）

- 白纱交代码后强制验证检查点
- merit_judge 语气识别调优
- Opus 直接 Write 大文件的漏洞（应该派 subagent）
