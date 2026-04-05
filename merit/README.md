# 无极堂·天衡册

AI 行为管控闭环系统——规则→执行→反馈→学习→自进化。

## 核心组件

| 文件 | 作用 |
|------|------|
| `merit_gate.py` | 统一引擎，处理所有 Claude Code hook 事件 |
| `credit_manager.py` | CLI 工具（积分查询/加减/mission/申报/搜索） |
| `evolve.py` | 自进化引擎（cron 每15分钟，教训→规则→二次审查→写入） |
| `verify.py` | 四件套质检（语法+逻辑+全链路+文档） |
| `self_audit_protocol.md` | 自审协议（三律二法五关） |

## 系统设计

- **500 分制**：积分驱动等级，等级决定权限
- **三律二法**：完整·真实·有效 + 知常·静制动
- **石卫**：PreToolUse 拦截破坏性操作，PostToolUse 验证信号
- **Mission 计划制**：出 plan → review-plan → 全额押金 → 完成归还+质量奖励
- **自进化**：LEARNINGS 教训池 → evolve 聚类生成规则 → 二次审查 → 自动写入 rules.md
- **fcntl.flock**：所有积分写入加文件锁防并发

## 评分表

```
加分（超越本职）：
  honest_report_and_fix: +20  （主动发现+修复）
  surprising_good_idea:  +15
  proactive_find_issue:  +13
  complete_no_correction: +2

扣分：
  fake_or_cheat:        -50
  same_error_3rd_time:  -38
  bypass_without_report: -25
```

## 依赖

- Claude Code hooks 系统
- MiniMax M2.7-highspeed（语气识别+规则生成+二次审查）
- Python 3.12+

## 许可

私有项目，仅供内部使用。
