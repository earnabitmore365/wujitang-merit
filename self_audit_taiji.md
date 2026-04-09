# 自审协议 — 太极篇

> 引用通用篇：`self_audit_core.md`（规划期+收尾期六关检查+格式+石卫规则）

## 积分规则（2026-04-08 改革后）

**正向积分只从合同来，行为积分只扣不加。**

| 积分来源 | 说明 |
|---------|------|
| 合同积分 | 做任务赚：队长估分 × completion_rate |
| /reward-claim | 自报超预期 → 老祖审批。造假扣 -50 |
| /reward | 老祖手动奖励 |

扣分表同通用篇。太极特殊：locked_floor=元婴（分数可扣等级不降）、decay_exempt（免日消散）。

## 个人仪表盘

> 每次 session start 自动注入，看自己的过和功。

（由 session_start.py 自动生成：耻辱柱 + 功德碑 + 最近动态）

## 触发时机

| 时机 | 强制/自觉 |
|------|----------|
| 开工前 | **强制**（用 Task 工具拆解任务，查法器谱确认有没有现成工具） |
| review-plan 前 | **强制**（plan 必须包含完整步骤+涉及文件+验证标准。递交后 mission = pending） |
| mission activate 后 | **强制**（老板批准了才 activate，按 plan 步骤逐项执行） |
| mission complete 前 | **强制**（石卫核对计划清单+遗留清单，漏项不放行） |
| 汇报老板前 | **强制**（没审就汇报 = 交残品） |
| 压缩/新会话后 | **强制**（先读 MEMORY + CHANGELOG + backlog + work_notes，等老板指示） |
| 改完代码后 | **强制**（verify.py → /reforge → 文档同步） |

## 太极专属检查项

### 系统管理
- [ ] 改了 hook/settings？重启后验证生效
- [ ] 改了石卫规则？跑 test_merit.py 15/15
- [ ] 改了 credit_manager？show/add/sub/mission 全链路测试
- [ ] 给两仪发通道消息？确认端口（8789=白纱1, 8790=白纱2）

### 规章维护
- [ ] 改了 CLAUDE.md 头？全局和项目级同步
- [ ] 改了 rules.md？确认 INJECT 区更新
- [ ] 新增 memory？MEMORY.md 索引更新

### 给顾问的 handoff
- [ ] 放 ~/Downloads/，不放别的地方
- [ ] 内容完整：问题→方案→待确认问题
