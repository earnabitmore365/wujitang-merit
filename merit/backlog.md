# 遗留清单（持久化）

> 发现问题加进来，做完了才删。每次【自审】从这里读，不从脑子编。

## 待处理

- [ ] **evolve.py 有效触发统计**：需交叉比对 shiwei_log + daily md（低优先级，石卫还在黑铁）
- [ ] **stone_guard_v7_design.md 更新**：需补 review-plan/verify/500分制/段位等今天的改动
- [ ] **merit_gate.py 结构索引行号偏移**：500分制改动后又偏了

## 已完成

- [x] 太极独立 conversations_taiji.db（2026-04-02）
- [x] Haiku 弃用，MiniMax only + 失败存队列（2026-04-02）
- [x] 石卫操作日志 shiwei_log/（2026-04-02）
- [x] 石卫段位 shiwei_credit.json（2026-04-02）
- [x] /audit-shiwei command（2026-04-02）
- [x] session_start 未审计提醒（2026-04-02）
- [x] evolve.py 规则进化引擎 + rule_proposals.json（2026-04-02）
- [x] daily_digest.py 集成 evolve.py 4am cron（2026-04-02）
- [x] credit_system_design.md 全文重写 v7（2026-04-02）
- [x] review-plan CLI 激励机制（2026-04-02）
- [x] mission 积分统一：SCORING_TABLE 过程发放（2026-04-02）
- [x] verify.py 四件套质检 + verify_registry.json（2026-04-02）
- [x] wuji-verify.py 项目级质检（信息隔离）（2026-04-03）
- [x] test_merit.py 15/15 + test_memory.py 10/10（2026-04-03）
- [x] _get_level 副本消除（session_start 从 merit_gate import）（2026-04-03）
- [x] 假公式奖励分追回 -10（2026-04-03）
- [x] verify check_logic 跑所有框架测试（2026-04-03）
- [x] COMPLETION_KEYWORDS 补充 8 个词（2026-04-03）
- [x] SSH 豁免（2026-04-03）
- [x] 500 分制迁移（阈值×5 + SCORING_TABLE×2.5 + 灵气消散-10 + 日薪）（2026-04-03）
- [x] 两仪 CLAUDE.md 同步（review-plan + 无极质检）（2026-04-03）
- [x] 交易/回测/研究框架注册 verify_registry（2026-04-03）
- [x] 两仪定 Lv.3 金丹 250 分（2026-04-03）
- [x] /reflect 9条 LEARNINGS + 4条升级 rules.md（2026-04-02）
