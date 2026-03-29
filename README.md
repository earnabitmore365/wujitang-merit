# Haiku Gate — 信用积分门卫系统

> Claude Code 的 AI 行为管控系统。Haiku 当队长，硬规则当队员，积分动态调节严格度。

## 架构

```
haiku_gate.py（Haiku 门卫部）
  │
  ├── 第一层：队员巡逻（硬规则，毫秒级）
  │     ├── Lv.1 全锁 → ask 老板
  │     ├── 破坏性操作 → deny + 自动扣分
  │     └── Agent 类型/模型限制 → deny
  │
  └── 第二层：Haiku 队长（智能判断，1-8秒）
        ├── 读上下文 + 当前操作 → 判断合规性
        ├── 自动加减分 → 更新 credit.json
        └── 记录做对/做错 → LEARNINGS.md
```

## 等级体系

| 等级 | 分数 | 称号 | 门卫严度 |
|------|------|------|----------|
| Lv.1 | 0-19 | 锁灵 | 全锁，老板签字 |
| Lv.2 | 20-49 | 筑基 | 严查（6项检查） |
| Lv.3 | 50-79 | 金丹 | 常规（3项检查） |
| Lv.4 | 80-94 | 元婴 | 轻查（仅破坏性） |
| Lv.5 | 95-100 | 化神 | 门卫休息 |

## 安装

```bash
git clone https://github.com/earnabitmore365/haiku-gate.git
cd haiku-gate
bash install.sh
```

## 使用

```bash
# 查看积分
python3 ~/.claude/scripts/credit_manager.py show

# 加分
python3 ~/.claude/scripts/credit_manager.py add 黑丝 3 "完成任务无纠错"

# 减分
python3 ~/.claude/scripts/credit_manager.py sub 黑丝 10 "完整性违规"

# 历史
python3 ~/.claude/scripts/credit_manager.py history 黑丝
```

## 文件清单

| 文件 | 用途 |
|------|------|
| `scripts/haiku_gate.py` | 门卫主脚本（PreToolUse hook） |
| `scripts/credit_manager.py` | 积分管理工具 |
| `scripts/inject_credit_status.py` | SessionStart 注入片段 |
| `credit.json.template` | 积分初始模板 |
| `install.sh` | 安装脚本 |
| `docs/credit_system_design.md` | 完整手册 |
