---
name: reflect
description: 从对话种子里提取纠错和学习点，积累到 LEARNINGS.md，纠错立即升级（1次）、提升出现3次升级到 rules.md。老板说 /reflect、"反思一下"或"我的准则是什么"时触发。
user-invocable: true
---

# Reflect — 自我改进

> 哲学：**被纠正一次，永远不犯第二次。主动提升，不等老板来说。**

## 触发方式
- 老板说 `/reflect`
- 老板说"反思一下"、"总结教训"、"有没有学到什么"
- 老板说"我的准则是什么"

---

## 执行步骤

### 步骤1：从对话种子拉信号（纠错 + 提升）

```python
python3 -c "
import sqlite3, os
conn = sqlite3.connect(os.path.expanduser('~/.claude/conversations.db'))
rows = conn.execute('''
    SELECT time, speaker, content, tags
    FROM messages
    WHERE tags LIKE '%纠错%' OR tags LIKE '%提升%'
    ORDER BY id DESC LIMIT 50
''').fetchall()
for r in rows:
    print(f'[{r[0]}] {r[1]} [{r[3]}]: {r[2][:300]}')
conn.close()
"
```

同时也拉最近会话全文（补捉标签未覆盖的隐性信号）：
```python
python3 -c "
import sqlite3, os
from datetime import datetime, timedelta
conn = sqlite3.connect(os.path.expanduser('~/.claude/conversations.db'))
since = (datetime.now() - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
rows = conn.execute('''
    SELECT time, speaker, content FROM messages
    WHERE time >= ? ORDER BY id
''', (since,)).fetchall()
for r in rows:
    print(f'[{r[0]}] {r[1]}: {r[2][:200]}')
conn.close()
"
```

### 步骤2：识别信号（纠错 + 提升 + 正向确认）

扫描以下模式（老板原话优先，保留原文）：

**显性纠错（高可信）：**
- "不要这样"、"不对"、"错了"、"你怎么XXX"、"干什么飞机"
- "你老是XXX"、"又XXX了"、"我不是叫你XXX"
- "你先别XXX"、"我说的是XXX不是XXX"

**隐性纠错（中可信）：**
- 老板解释了一遍 Claude 没做到的事
- 老板重复说了同一件事（说明上次没记住）
- 老板补充细节（说明 Claude 输出不完整）

**提升信号（中可信）：**
- "还可以更XXX"、"可以更细心"、"应该主动XXX"
- "不用我问/去问才知道"、"本来应该"、"你自己应该"
- AI 漏做了某件本应主动做的事，但用户没有发怒，只是指出

**正向确认（记录最佳实践）：**
- "就这样"、"对"、"完美"、"就是这个意思"
- 后续不再重复要求同一件事

### 步骤3：写入 LEARNINGS.md

路径：`~/.claude/learnings/LEARNINGS.md`

每条格式：
```
## LRN-{YYYYMMDD}-{NNN}

- **日期**：{date}
- **优先级**：low / medium / high / critical
- **状态**：pending / 出现{N}次 / promoted
- **类型**：纠错 / 提升 / 最佳实践 / 老板偏好
- **触发原话**（保留原文）："{老板原话}"
- **教训**：{一句话总结，AI应该做什么/不做什么}
- **出现次数**：{N}（同一模式跨会话累计）

---
```

### 步骤4：检查升级候选

读 LEARNINGS.md，找出现次数 ≥ 3 的条目：

```python
python3 -c "
import re, os
with open(os.path.expanduser('~/.claude/learnings/LEARNINGS.md')) as f:
    content = f.read()
# 纠错类：出现1次即升级（立即毕业）；提升/其他类：出现3次才升级
entry_blocks = re.split(r'(?=## LRN-)', content)
candidates = []
for block in entry_blocks:
    id_match = re.search(r'## (LRN-\S+)', block)
    if not id_match:
        continue
    entry_id = id_match.group(1)
    type_match = re.search(r'\*\*类型\*\*：(\S+)', block)
    n_match = re.search(r'\*\*出现次数\*\*：(\d+)', block)
    if not n_match:
        continue
    n = int(n_match.group(1))
    entry_type = type_match.group(1) if type_match else '未知'
    if (entry_type == '纠错' and n >= 1) or n >= 3:
        candidates.append((entry_id, entry_type, n))
for id, t, n in candidates:
    print(f'{id} [{t}]: {n}次')
"
```

### 步骤4b：升级后归档

条目升级（promoted）到 rules.md 后，从 LEARNINGS.md 移到 `~/.claude/learnings/LEARNINGS_ARCHIVE.md`：
1. 将该条目的状态改为 `✅ promoted → {目标rules.md} {RUL-ID}`
2. 将整条从 LEARNINGS.md 剪切到 LEARNINGS_ARCHIVE.md 末尾
3. LEARNINGS.md 只保留 pending 条目，保持精简

### 步骤5：提案输出

向老板输出结构化报告：

```
## 本次 Reflect 结果

### 新增学习点（{N} 条）
1. [LRN-YYYYMMDD-001] **{教训}**
   触发原话："..."
   建议操作：记录备查

### 升级候选（纠错类1次立即升级 / 提升类出现≥3次，写进 rules.md）
1. [LRN-XXXXXXXX-XXX] [{类型}] 出现 {N} 次
   **教训**：{内容}
   **建议写入 rules.md**：`{具体措辞}`
   [批准] / [跳过] / [修改措辞]

### 本次无新发现
（如无纠错信号）
```

**⚠️ 安全机制：** 任何 CLAUDE.md 修改，必须老板明确批准后才写入，不自动修改。

---

## 集成说明

- **数据源**：`~/.claude/conversations.db` messages 表（tags LIKE '%纠错%'）
- **学习草稿**：`~/.claude/learnings/LEARNINGS.md`（pending，未毕业）
- **已升级归档**：`~/.claude/learnings/LEARNINGS_ARCHIVE.md`（promoted，仅追溯用）
- **升级目标（系统自带 memory 目录）**：
  - 全局规则 → `~/.claude/projects/-Users-allenbot/memory/rules.md`
  - auto-trading 规则 → `~/.claude/projects/-Users-allenbot-project-auto-trading/memory/rules.md`
  - 其他项目同理，放对应项目的 memory/rules.md
- **与对话种子协作**：对话种子负责存原话，reflect 负责从原话里提取规律
