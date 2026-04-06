# Mission 按会话隔离

## 问题
mission.json 单文件共用，多会话并发时互相覆盖。

## 方案
mission 文件改为 `mission_{session_id}.json`，每个会话独立。

## 改动

### merit_gate.py
- `load_mission()`: 从全局 data 拿 session_id，拼路径 `mission_{session_id}.json`
- `save_mission()`: 同上
- `handle_pre_tool_use()`: data 里有 session_id，传给 load_mission
- `mark_mission_item_done()`: 同上
- `review_plan()`: 从 CLI 参数或环境变量拿 session_id

### credit_manager.py
- `mission_submit()`: 接受 session_id 参数，写 `mission_{session_id}.json`
- `mission_activate/complete/abort/extend/status`: 同上
- 向后兼容：如果旧 `mission.json` 存在，迁移到新格式

## 涉及文件
- `~/.claude/merit/merit_gate.py`
- `~/.claude/merit/credit_manager.py`
