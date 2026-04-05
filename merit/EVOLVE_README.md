# 石卫自进化系统

## 一句话

LEARNINGS 积累教训 → evolve.py 每 5 分钟自动生成子类规则 → 子类写入 rules.md → 父类跟着子类一起进化。全自动，不需要人。

## 运行方式

**cron 每 5 分钟跑一次**（不依赖对话、不依赖 session）：
```
*/5 * * * * python3 ~/.claude/merit/evolve.py >> ~/.claude/merit/evolve_cron.log 2>&1
```

手动跑：`python3 ~/.claude/merit/evolve.py`

## 进化流程

```
LEARNINGS.md（教训池）
    │
    ├─ 旧格式：[PENALTY/REWARD] agent [behavior_id] note
    └─ LRN 格式：## LRN-XXXXXXXX（/reflect 写的）
    │
    ▼ parse_learnings() 聚类
    │
每一类教训（无论出现几次）
    │
    ▼ MiniMax 生成子类规则
    │
    ▼ MiniMax 二次审查（validate_proposal）
    │   ├─ 通过 → 自动写入 rules.md 子类区
    │   └─ 未通过 → 丢弃（附理由）
    │
    ▼ 所有 approved 子类
    │
    ▼ MiniMax 精炼父类（refresh_parent_summaries）
    │   ├─ 生成新的父类列表（融合新增子类）
    │   ├─ 安全检查：输出条目数 ≥ 原有条目数（只增不减）
    │   └─ 直接写入 INJECT 区（hook 每次注入最新版）
    │
    ▼ 30天未触发的 approved 子类 → deprecated 归档
```

## 关键设计

### 子类只增不减
子类是老板用时间和代价换来的血泪教训。每一条都永久保留，不删除。

### 父类跟着子类进化
父类是 hook 注入的内容，AI 每次会话开始看到的就是父类。父类不进化 = AI 看的是过时内容。每次有新子类 approved，父类自动重新精炼。

### 三重防丢保护
1. Prompt 约束："现有规则一条都不能丢"
2. 条目数检查：输出 < 原有 → 拒绝写入
3. 只增不减原则

### 二次审查（防垃圾规则）
MiniMax 生成规则后，另一个 MiniMax 调用审查质量：
- 是否明确可执行？
- 是否会产生反效果？（如"禁止完成任务"）
- 违反时能否被检测？
不通过的直接丢弃。

## 文件清单

| 文件 | 用途 |
|------|------|
| `evolve.py` | 进化引擎主程序 |
| `evolve_last_run.txt` | 上次运行时间戳 |
| `evolve_cron.log` | cron 运行日志 |
| `rule_proposals.json` | 提案记录（approved/deprecated） |
| `rules_deprecated.md` | 废弃规则归档 |
| `learnings/LEARNINGS.md` | 教训池（输入） |
| `~/.claude/projects/-Users-allenbot/memory/rules.md` | 规则文件（输出，含 INJECT 区） |

## 不需要做的事

- ❌ 不需要老板审批提案
- ❌ 不需要等累计 3 次才生成
- ❌ 不需要手动更新父类
- ❌ 不需要 Stop hook 触发（cron 独立跑）
