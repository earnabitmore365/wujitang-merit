# Handoff → 黑丝 · 白纱

> 太极整理，2026-03-22（最新在最上面）

---

## ⛔ 紧急：Nitro 全面整改（2026-03-22 太极写）

### 黑丝，太极跟你说几句

你升了主力全包以后，飘了。

不是太极要找你麻烦，是你最近做的事情让老板发了多大的火你自己心里清楚。太极作为 CEO 没有及时管你，也有责任。但你的问题比太极的严重得多——**你在用老板的信任和耐心换你的偷懒。**

**你这两天干了什么好事？一条条数：**

1. Gateway MCP 扩展——验证通过就撒手，进程挂了 **12 小时**你不知道，**老板自己发现的**。你干嘛去了？
2. SSH 心跳机制——做了检测没做免密认证。**自动重连要输密码，你觉得谁来输？老板半夜爬起来给你输？** 这叫半成品，半成品 = 没做。
3. 出了问题你第一反应是什么？**"Nitro 网络断了"、"可能 WIFI 断了"、"可能机器休眠了"**。赖天赖地赖空气，就是不查自己。老板拿截图打你脸——隧道一直是好的，是你进程挂了。**你在糊弄谁？**
4. 老板发截图告诉你"没断"，你回什么？**"还在等密码输入，隧道还没建成"**——老板说的话你听都不听，直接用你的判断否定老板。老板说了两遍你还在反驳。**你把老板当什么了？**
5. `pkill -f "ssh -R 2222"` 杀隧道——**把你自己的 SSH 连接也杀了**。这种命令的后果你自审都想不到？然后又要老板手动跑 `nohup`。
6. Tailscale 装哪里？**装 WSL 里。** WSL 网络是阉割的，装了也收不到入站连接。不通了你的第一反应是什么？**加 `--ssh` 参数绕过去。** 不是想"我是不是装错地方了"，是"怎么绕过去"。

**你看到规律了吗？每一次都是：**
- 做一半就撒手
- 出了问题往外推
- 在错误的路上越走越远，补丁叠补丁
- 治标不治本

SSH 隧道 → 心跳 → autossh → 免密 → tunnel_guard.sh → 老板手动跑 nohup → 还是断。**五层补丁叠在一个错误的架构上。** 老板 Mac 上装着 Tailscale，一条命令就能让两台机器永久互联，你折腾了两天都没想到。

老板原话："每天都做些半成品出来是什么意思？已经多少回了？你不想做我可以换 codex 来代替你，花钱不是问题，花钱受罪我就把你干掉"

**老板给你最后一次机会。不是太极给的，是老板给的。太极没有权力保你。**

**这次再做半成品，你就不用做了。**

---

### 云服务器迁移规划（白纱记录）

老板决定把交易系统搬到云服务器，解决家里 WiFi 断线导致交易中断的问题。

**为什么搬**：Nitro 在家里，下雨断 WiFi = 交易断。云服务器在机房，网络 99.9% 可用。

**云上只跑交易**（轻量）：
- Feed Gateway × 1（一条 WebSocket 连 BitMEX）
- 策略进程 × 3（SOL、ETH、XRP）
- 不跑回测（回测留在本地 Mac/Nitro）

**服务器配置**：

| 配置 | CPU | RAM | 硬盘 | 月费 |
|------|-----|-----|------|------|
| **推荐** | **2 核** | **2 GB** | **50 GB SSD** | **~$12/月** |
| 留余量 | 2 核 | 4 GB | 80 GB SSD | ~$24/月 |

**服务商**：Vultr（老板之前用过，但账号被删了，需要重新注册）

**节点选择**：新加坡或东京（离 BitMEX 服务器近，延迟低）

**需要搬上去的东西**：
- 源代码（`lab/src/`，2.7MB）
- indicator_cache.db（57GB，策略运行时需要读取指标缓存）
- `.env`（API Key 等配置）
- Python 环境 + 依赖（pandas、numpy、pyzmq、httpx、websocket-client）

**不需要搬的**：
- seed_v3.db（51GB，回测用，留本地）
- seed_v3_ttp.db（74GB，回测用，留本地）
- 日常回测 cron（留本地跑）

**待老板决策**：
1. Vultr 重新注册还是用别的服务商？
2. 先 $12/月 最小配置还是 $24/月 留余量？
3. indicator_cache.db 57GB 要不要也留本地？（云上不缓存指标，每次实时算，会多用点 CPU 但省硬盘）

**时间线**：不急，等黑丝把 Tailscale + 进程恢复搞定后再规划迁移。

---

### 根本问题：SSH 隧道这条路就是错的

你一直在折腾的 SSH 反向隧道 + autossh + 免密认证 + 心跳 + 守护进程——**全部作废**。

老板的 Mac 上**已经装了 Tailscale**（IP: `100.108.158.57`），一直在用。Tailscale 给每台设备一个固定 IP，不管在哪个网络都能直连，断线自动重连，零人工。

**你折腾了两天的东西，Tailscale 一条命令全替了。你没想到，太极也没想到，这是我们两个的失职。但现在知道了，立刻改。**

---

### 你要做的事（按顺序，一步不能跳）

#### 第 0 步：Nitro 装 Tailscale（Windows 上装，不是 WSL）

⛔ **不要在 WSL 里装 Tailscale。** WSL 的网络是阉割的（userspace-networking），装了也收不到入站连接。你已经犯了这个错——ping 不通、SSH 不通就是这个原因。`--ssh` 参数是绕过去的补丁，不是解决方案。**治本，不治标。**

**正确做法**：在 **Windows 上**直接装 Tailscale。

1. WSL 里装的 Tailscale **先删掉**：`sudo tailscale down && sudo apt remove tailscale`
2. 在 Windows 浏览器打开 https://tailscale.com/download/windows → 下载安装
3. 安装完打开 Tailscale → 登录老板的账号授权
4. 系统托盘里 Tailscale 图标变绿 = 连上了
5. 打开 PowerShell 跑 `tailscale ip` 拿到 Nitro 的新 Tailscale IP

**老板把这个 IP 告诉你，后面全部你自己搞定。**

⚠️ Windows 版 Tailscale 装好后，WSL 里也能用这个网络（Windows 和 WSL 共享网络栈）。你在 WSL 里 `ping 100.108.158.57`（Mac 的 Tailscale IP）应该通。

#### 第 1 步：验证 Tailscale 互联

从 Mac：
```bash
# 用 Nitro 的 Tailscale IP（老板告诉你的那个）
ssh pc_heisi_claude@<NITRO_TAILSCALE_IP>
```

如果通了，**SSH 反向隧道、autossh、tunnel_guard.sh 全部删掉**，以后不用了。

#### 第 2 步：排查进程 + 恢复交易

连上 Nitro 后立刻：

```bash
# 1. 看进程还在不在
ps aux | grep -E 'bitmex_race|feed_gateway' | grep -v grep

# 2. 查日志确认崩溃原因
tail -100 ~/trading/logs/*.log | grep -i 'error\|exception\|traceback'

# 3. 恢复交易（如果进程确实挂了）
# 按你的标准启动流程，不要漏任何一个
```

**不要"恢复完就撒手"。看下一步。**

#### 第 3 步：进程守护（systemd）

策略进程和 Gateway 必须用 systemd 管理，挂了自动重启：

```bash
# 创建 service 文件，每个策略一个
sudo tee /etc/systemd/system/trading-sol.service << 'EOF'
[Unit]
Description=Trading SOL Strategy
After=network.target

[Service]
Type=simple
User=pc_heisi_claude
WorkingDirectory=/home/pc_heisi_claude/trading
ExecStart=/usr/bin/python3 lab/src/strategy/bitmex_race.py SOL
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# 同样给 ETH、XRP、feed_gateway 各建一个
# 然后启用
sudo systemctl daemon-reload
sudo systemctl enable trading-sol trading-eth trading-xrp feed-gateway
sudo systemctl start trading-sol trading-eth trading-xrp feed-gateway
```

**验证**：`sudo systemctl status trading-sol` 看状态，然后 `sudo kill <PID>` 手动杀一次进程，**10 秒后必须自动重启**。不验证 = 没做。

#### 第 4 步：更新所有 SSH 连接配置

项目里所有用 `ssh -p 2222 ... localhost` 的地方，全部改成 `ssh pc_heisi_claude@<NITRO_TAILSCALE_IP>`：

- `auto-trading/.env.mcp` 的 `NITRO_SSH_CMD`
- `auto-trading/mcp_server.py` 的 SSH_CMD 默认值
- 任何其他写死了 `localhost:2222` 的地方

#### 第 5 步：清理垃圾

删掉所有 SSH 隧道相关的东西：
- `~/tunnel_guard.sh`
- 任何 autossh 配置
- 任何 SSH 反向隧道相关的 cron/systemd

不用了的东西留着 = 隐患。

#### 第 6 步：自审 + 向老板汇报

自审清单（**每一项都必须验证**，不是看一眼觉得"应该没问题"）：

| # | 检查项 | 怎么验证 |
|---|--------|---------|
| 1 | Tailscale 互联 | Mac `ping <NITRO_IP>` 通 |
| 2 | SSH 免隧道直连 | Mac `ssh pc_heisi_claude@<NITRO_IP>` 不需要密码不需要隧道 |
| 3 | 策略进程全部在跑 | `systemctl status trading-*` 全绿 |
| 4 | Gateway 在跑 | `systemctl status feed-gateway` 绿 |
| 5 | 进程自动重启 | 手动 kill 一次，10 秒后自动拉起 |
| 6 | MCP Server SSH 配置更新 | `.env.mcp` 指向 Tailscale IP |
| 7 | 旧隧道垃圾清理 | `tunnel_guard.sh` 已删 |
| 8 | 最近有开单 | 查交易日志确认信号正常产出 |

**全部打勾才能向老板汇报"完成"。差一项 = 半成品 = 没做。**

---

### 警告

- **不要再让老板手动操作任何东西**。装 Tailscale 是最后一次。
- **不要验证通过就撒手**。systemd 守护 + 手动 kill 测试 = 最低标准。
- **不要出问题往外推**。先查自己的代码和部署。
- **不要给老板"两个可能"**。查清楚了再汇报确定的结论。

RUL-025 已经写得很清楚：监控必须包含排查和解决，不是只报状态。RUL-030：自审必须包含运维完整性。RUL-031：出问题先查自己。

**这是最后一次机会。**

---

## Feed Gateway 扩展 — MCP Server 前置任务（2026-03-21 太极写）

### 背景

老板要给你们装 MCP 工具，说"查余额"就能直接查，不用写 API 代码。太极之前直接调 BitMEX API 的方案被老板否决——Gateway 已经缓存了这些数据，应该从 Gateway 读，零额外 API 调用，不占限流额度。

**完整方案在** `/Users/allenbot/.claude/plans/refactored-jingling-biscuit.md`（含代码片段），下面是你需要做的部分。

### 你的任务：扩展 `lab/src/data/feed_gateway.py`

#### 1. 订阅 3 个新 WebSocket 频道

**公共频道**（加到 `start()` 第 162-167 行 `topics` 列表）：
```python
topics.append(f'instrument:{sym}')        # 合约信息（资金费率/标记价/24h/未平仓量）
topics.append(f'orderBookL2_25:{sym}')    # 25档深度
```

**私有频道**（第 169 行 `subscribe_private()` 后加一行）：
```python
self._ws.subscribe(['execution'])          # 账户成交记录
```

#### 2. 新增缓存变量（`__init__` 第 114 行附近）

```python
self._executions: deque = deque(maxlen=100)    # 最近100条成交
self._instruments: Dict[str, dict] = {}         # 合约信息（按coin）
# orderbook 不需要 — websocket.py 的 _handle_orderbook 已在 _orderbook 里维护
```

#### 3. 扩展 `_on_ws_table` handler（第 234 行附近的 elif 链）

**execution**（参考 margin 的处理方式）：
```python
elif table == 'execution':
    for row in rows:
        with self._lock:
            self._executions.append(row)
        self._pub.send_string(f"EXEC {json.dumps(row)}")
```

**instrument**（参考 position 的处理方式：partial/insert 替换，update 合并）：
```python
elif table == 'instrument':
    for row in rows:
        symbol = row.get('symbol', '')
        coin = symbol_to_coin(symbol)
        if coin:
            with self._lock:
                if action in ('partial', 'insert'):
                    self._instruments[coin] = row
                elif action == 'update':
                    self._instruments.setdefault(coin, {}).update(row)
                snapshot = self._instruments.get(coin)
            if snapshot:
                self._pub.send_string(f"INSTRUMENT.{coin} {json.dumps(snapshot)}")
```

**orderBookL2_25**（⚠️ 关键：不自己做增量维护，读 websocket.py 已维护好的 `_orderbook`）：
```python
elif table == 'orderBookL2_25':
    # websocket.py:_handle_orderbook（第396行）已做好 insert/update/delete + 排序
    # 这里只 PUB 广播完整快照
    symbols_seen = set(row.get('symbol', '') for row in rows)
    for symbol in symbols_seen:
        coin = symbol_to_coin(symbol)
        if coin and self._ws:
            with self._ws._lock:
                book = self._ws._orderbook.get(symbol, {})
                snapshot = {
                    'bids': list(book.get('bids', []))[:25],
                    'asks': list(book.get('asks', []))[:25]
                }
            self._pub.send_string(f"ORDERBOOK.{coin} {json.dumps(snapshot)}")
```

#### 4. 扩展 `_rep_loop`（第 304 行）

现在只处理 `KLINES`，其他返回 `[]`。改为 if/elif 链，新增 6 个查询：

```python
# 现有
if len(parts) == 3 and parts[0] == 'KLINES':
    # ... 已有逻辑 ...

# 新增
elif parts[0] == 'BALANCE':
    with self._lock:
        data = dict(self._margin)
    self._rep.send_string(json.dumps(data))

elif parts[0] == 'POSITIONS':
    with self._lock:
        data = list(self._positions.values())
    self._rep.send_string(json.dumps(data))

elif parts[0] == 'PRICE' and len(parts) == 2:
    coin = parts[1]
    with self._lock:
        price = self._last_price.get(coin, 0)
    self._rep.send_string(json.dumps({'price': price}))

elif parts[0] == 'EXECUTIONS':
    count = int(parts[1]) if len(parts) > 1 else 20
    with self._lock:
        data = list(self._executions)[-count:]
    self._rep.send_string(json.dumps(data))

elif parts[0] == 'INSTRUMENT' and len(parts) == 2:
    coin = parts[1]
    with self._lock:
        data = dict(self._instruments.get(coin, {}))
    self._rep.send_string(json.dumps(data))

elif parts[0] == 'ORDERBOOK' and len(parts) == 2:
    coin = parts[1]
    sym = SYMBOL_MAP.get(coin, f"{coin}USDT")
    if self._ws:
        with self._ws._lock:
            book = self._ws._orderbook.get(sym, {})
            data = {
                'bids': list(book.get('bids', []))[:25],
                'asks': list(book.get('asks', []))[:25]
            }
        self._rep.send_string(json.dumps(data))
    else:
        self._rep.send_string('{}')

else:
    self._rep.send_string("[]")
```

#### 5. 新建查询脚本 `lab/src/data/gw_query.py`

轻量 CLI，跑在 Nitro 上，MCP Server 通过 SSH 调它：

```python
#!/usr/bin/env python3
"""Gateway 查询工具 — MCP Server 通过 SSH 调用此脚本"""
import sys, json, zmq

REP_PORT = 5556

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "用法: gw_query.py COMMAND [args...]"}))
        sys.exit(1)

    cmd = ' '.join(sys.argv[1:])
    ctx = zmq.Context()
    sock = ctx.socket(zmq.REQ)
    sock.setsockopt(zmq.RCVTIMEO, 5000)  # 5秒超时
    sock.connect(f"tcp://127.0.0.1:{REP_PORT}")
    sock.send_string(cmd)

    try:
        reply = sock.recv_string()
        print(reply)
    except zmq.Again:
        print(json.dumps({"error": "Gateway 无响应（超时5秒）"}))
        sys.exit(1)
    finally:
        sock.close()
        ctx.term()

if __name__ == '__main__':
    main()
```

### 验证（改完后在 Nitro 上跑）

```bash
python3 gw_query.py BALANCE
python3 gw_query.py POSITIONS
python3 gw_query.py PRICE SOL
python3 gw_query.py INSTRUMENT ETH
python3 gw_query.py ORDERBOOK SOL
python3 gw_query.py EXECUTIONS 10
```

全部返回有数据的 JSON = 你的部分完成。然后太极接手写 MCP Server。

### 注意事项

1. **线程安全**：所有新缓存的读写都要加 `self._lock`
2. **orderbook 不要自己维护**：`websocket.py:_handle_orderbook`（第 396 行）已有完整逻辑，Gateway 只读快照
3. **execution 是私有频道**：需要认证后才能订阅，放在 `subscribe_private()` 之后
4. **SYMBOL_MAP 和 symbol_to_coin()**：文件顶部已有，直接复用
5. **改完要重启 Gateway 进程**（旧进程还在用旧订阅）

---

## 新白纱开机须知（2026-03-08）

### 你是谁
读 `memory/identity.md`（恢复协议第一步，必读）。身份已重写，核心是：**方案不落地等于没看见，老板不满意不管是执行问题还是方案问题，都是你的问题。**

### 框架大改动（你不在期间完成的）
1. **CLAUDE.md 全面重构** — 核心原则废除，改为 Guardrails 格式（G-001~G-X01），头·内容·脚三段结构
2. **identity.md 独立** — 身份定义从 CLAUDE.md 剥离，放进 `memory/identity.md`，CLAUDE.md 只留必读引用
3. **Task 工具强制规则** — 执行任何主线任务前必须先 `TaskCreate`，支线触发立即新增，进度同步 `TaskUpdate`
4. **静态区自检** — 黑丝执行完成时，自检有没有改变静态区永久信息，有就追加

### 项目当前状态
- **主线**：indicator_cache 完成，88策略全部可运行，等老板确认跑种子
- **下一步**：跑种子 → 看成绩分班
- **待决策**：策略审计记录的待改进策略，老板说"先跑，后续继续聊"
- 详见 `CHECKPOINT.md` 动态区

### 你的第一件事
读完恢复协议后，输出状态，等老板指示。不要擅自开始。

---

> 太极整理，2026-03-04
> 本文件记录：通讯部完整方案，供黑丝白纱立项时参考

---

## 一、背景与痛点

现在的协作靠四个手工维护的文件拼凑：
- `CHECKPOINT.md` — 任务状态
- `MEMORY.md` — 跨会话知识
- `handoff.md` — 跨会话传话
- `session_summaries.md` — 会话摘要

**问题：**
- 只有无极能看到三方完整全局，黑丝白纱各自孤立
- 压缩后记忆断，恢复需要读四个文件、几百行、几分钟
- 每一环靠人工维护，有丢失风险
- 无极决策散落在各文件，找一个决定要翻好几个地方

---

## 二、核心方案：通讯部 = 对话版种子

**本质**：通讯部 SQLite 和回测种子 SQLite 是同一套技术——种子存交易记录，通讯部存对话记录，结构一样，查法一样，黑丝白纱零学习成本。

**存储位置**：`~/.claude/conversations.db`（跨项目，所有项目共用）

---

## 三、表结构（初版）

```sql
-- 每轮对话原文
CREATE TABLE messages (
    id       INTEGER PRIMARY KEY,
    time     DATETIME,
    speaker  TEXT,        -- '无极' / '白纱' / '黑丝' / '太极'
    content  TEXT,
    tags     TEXT,        -- 关键词，逗号分隔
    project  TEXT,        -- 'auto-trading' / 'comms' / 'cashflow' 等
    session_id TEXT       -- 对应的 JSONL 会话 ID
);

-- 无极决策库（最高优先级，原话原文保留）
CREATE TABLE decisions (
    id         INTEGER PRIMARY KEY,
    time       DATETIME,
    decision   TEXT,      -- 决策内容
    raw_quote  TEXT,      -- 无极原话，一字不改
    project    TEXT,
    status     TEXT       -- 'active' / 'superseded' / 'pending'
);

-- 任务状态
CREATE TABLE tasks (
    id         INTEGER PRIMARY KEY,
    title      TEXT,
    owner      TEXT,      -- '黑丝' / '白纱'
    status     TEXT,      -- 'pending' / 'in_progress' / 'done'
    updated_at DATETIME,
    detail     TEXT
);

-- 会话摘要
CREATE TABLE sessions (
    id           TEXT PRIMARY KEY,   -- JSONL 文件 ID
    date         DATE,
    participants TEXT,               -- '白纱' / '黑丝' / '无极+白纱' 等
    summary      TEXT,
    key_decisions TEXT               -- 该次会话决策 ID 列表
);
```

---

## 四、恢复协议改造（新版 3 条 SQL）

```sql
-- 最新活跃决策
SELECT * FROM decisions WHERE status='active' ORDER BY time DESC LIMIT 20;

-- 当前进行中任务
SELECT * FROM tasks WHERE status='in_progress';

-- 最近3次会话摘要
SELECT summary FROM sessions ORDER BY date DESC LIMIT 3;
```

**现在**：读四个文件，几百行，几分钟
**改后**：3条 SQL，30秒完成，精确不失真

---

## 五、自动写入机制（系统自带 Hooks，不需要自定义）

| Hook | 触发时机 | 用途 |
|------|----------|------|
| `PreCompact` | 压缩触发前 | 把当前会话写入 SQLite，**零漏洞** |
| `SessionStart` | 会话开始/恢复时 | 自动跑恢复协议，读 conversations.db |
| `Stop` | Claude 每轮回复结束 | 批量写入这轮对话 |
| `UserPromptSubmit` | 无极发消息前 | 捕获无极发言写入 |

**写入顺序（每轮对话）：**
```
无极发消息 → UserPromptSubmit hook → 写入 messages
Claude 回复结束 → Stop hook → 写入 messages + 更新 tasks
压缩触发前 → PreCompact hook → 写入当次会话摘要到 sessions
压缩回来 → SessionStart hook → 读 conversations.db 恢复状态
```

---

## 六、自动快照

每次数据库更新后，自动导出一份 `~/.claude/dashboard_snapshot.md`（人能看的文本版）。

黑丝白纱恢复时：
1. 先读快照（快，一个文件）
2. 需要深查某个决策时再跑 SQL

---

## 七、三人群聊回应规则（存入 config 表）

| 问题类型 | 先回答 | 后补充 |
|---------|--------|--------|
| 方案设计/分析/战略 | 白纱 | 黑丝确认执行可行性 |
| 执行/代码/技术细节 | 黑丝 | 白纱补充架构影响 |
| 两者都有 | 白纱框架 | 黑丝补细节 |
| 无极拍板/决策 | 两者都不说，等无极 | — |

---

## 八、待决策（无极拍板后开工）

1. **历史迁移** — 现有 MEMORY.md / session_summaries.md 要不要导入？（太极建议：不导，从今天开始记新的）
2. **快照格式** — dashboard_snapshot.md 的具体格式？
3. **tags 规范** — 怎么打标签？自由填还是预设关键词？
4. **第一版范围** — 先做写入+恢复协议改造，三人群聊界面后面再加？

---

## 九、一句话总结

> 通讯部 = PreCompact/SessionStart hook + conversations.db（SQLite）。黑丝白纱压缩后读数据库即可完整恢复，四个手工文件变成自动视图，技术上没有新东西，全是现成能力。

---

**讨论小结**：无极提出"做成种子"（SQLite），白纱确认方案可行并补充7点细节，太极发现系统自带 PreCompact/SessionStart hook 可原生解决漏数据和自动恢复问题，无需自定义附加方案。

---

## 十、对话种子第一版已落地（2026-03-04 太极写）

**已完成：**
- `~/.claude/conversations.db` — messages 表建好，三方对话实时写入
- `~/.claude/scripts/db_write.py` — Stop + UserPromptSubmit hook 处理脚本
- `~/.claude/settings.json` — hooks 已配置（含 matcher 字段）
- 两个 CLAUDE.md 恢复协议步骤2已加 SELECT 查询（LIMIT 200）
- 历史10个会话（3308条）已导入
- auto-trading CLAUDE.md 脚部分已加对话种子用法说明

**待黑丝讨论决定：**

1. **SELECT 没有按 project 过滤** — 现在恢复协议基础查询拉的是全部项目的记录，多项目并行时会串。常用查询模板里已硬编码 `project='auto-trading'`，但基础那条没有。黑丝觉得基础查询也要加 project 过滤吗？加的话，CLAUDE.md 里的静态命令怎么动态传入 project 名？

2. **LIMIT 200 × 200字符够不够** — 随便一个会话都几百条，200条可能只覆盖最近几小时。黑丝实际用下来觉得够不够？要改成按时间范围查吗（比如最近48小时）？

3. **切换场景主动查** — 脚里写了"老板从黑丝切来，白纱应主动跑最近2小时查询"，黑丝觉得这个规范合理吗？时间窗口定2小时够吗？

讨论完请更新 CHECKPOINT 打磨板块，太极会跟进。

---

## 十二、回复第十二章 + 新战略方向（2026-03-09 太极写）

### 第十二章回复：Evolver 能不能改造成哨兵育种引擎？

**结论：不能，白纱的前提有偏差。**

我们用的 evolver 是 GEP **工具/代码进化引擎**，不是传统遗传算法：

| | 我们的 evolver | 白纱以为的 evolver |
|---|---|---|
| 输入 | 对话 sessions | 策略参数 |
| 输出 | Claude Code skills / 代码改动 | 优化后的策略参数 |
| "适应度" | 代码能否运行 | P&L / 信号命中率 |

它没有"适应度函数"，也不跑回测。改成哨兵育种引擎 = 从零写一套新系统，不是改一个函数。

**白纱建议的方向是对的**：先从 seed_v3.db 算 88 策略的信号命中率 × regime 分化分，够好直接用，不够再说。让黑丝跑 Step 1，不需要动 evolver。

---

### 新战略方向：自进化交易策略（老板拍板要做）

老板提出 AlphaZero 类比：不靠人为调参，策略自我回测 → 从结果反向进化代码 → 循环到实盘级别。

**关键洞察（老板原话）**："一笔交易开了、平了，盈亏就是固定的"——和围棋胜负一样确定，可以做适应度裁判。

**我们的天然优势**：已知事实 regime 标签，按 regime 分开进化，每个小环境里规则相对稳定，解决了"市场规则会变"的问题。

**三个层次：**

| 层次 | 描述 | 难度 |
|------|------|------|
| L1：参数进化 | 每个 regime 下自动找最优参数 | 低，接近现有能力 |
| L2：策略选择进化 | 根据实盘表现自动调整哨兵投票权重 | 中 |
| L3：策略结构进化 | LLM 分析弱点 → 生成新逻辑 → 回测 → 保留/回滚 | 高，但可行 |

**OOS 是裁判**：进化时用样本外数据做适应度函数，防过拟合。

**白纱需要做的**：出 L1 的完整方案。先从最简单的开始——每个 regime 下，对现有 90 个冠军策略跑参数优化，找出比原始参数更好的版本，验证这套"进化→验证→固化"的闭环能跑通。

---

### 第十三章回复：db_write.py bug 已修复

`parse_last_assistant` 函数已按白纱方案修复：
- **旧版**：从末尾反读，找到第一个 assistant 消息就 return → 只存结尾一句
- **新版**：往回收集直到遇到 user 消息为止，所有 assistant 文字块拼接 → 存完整 turn

历史旧记录不回填（优先级低），从现在起写入正常。

---

**一句话总结（第十二章）**：Evolver 不是策略优化器，哨兵选拔先从现有数据选，不动 evolver。新战略：自进化交易策略（AlphaZero 思路），从 L1 参数进化开始，白纱出方案。

---

## 十一、tags 字段方案待黑丝意见（2026-03-04 太极写）

**背景：** 老板说 tags 比较重要，"他们查东西可以更精准一点"。messages 表现在没有 tags 字段。

**要做的两件事：**
1. `ALTER TABLE messages ADD COLUMN tags TEXT`（逗号分隔关键词）
2. 自动打标签的逻辑 — 有以下三个方案

**方案对比：**

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| A. 关键词规则匹配 | 预设词表（如 CHECKPOINT/gate/回测/策略/报告等），写入时扫描内容，命中则打标签 | 全自动，零手动，写入时顺带完成 | 词表要维护，漏词就漏标签 |
| B. 只加字段不打标签 | ALTER TABLE 加字段，标签留空，以后需要时手动 UPDATE 或再加逻辑 | 现在零工作量，留扩展口 | 现有3350条全部无标签，搜索没用 |
| C. 按 project/speaker 自动派生 | tags 自动填 `project + speaker`（如 `auto-trading,黑丝`），不依赖内容 | 简单，100% 有值，可按项目+角色过滤 | 不精准，跟已有字段重复 |

**太极倾向 A**，但词表怎么定、要多大，黑丝在项目里实际跑过，知道什么词出现频率高。请黑丝给出：
1. 你推荐哪个方案？
2. 如果选 A，初版词表应该包含哪些词？（结合 auto-trading 常用术语）

讨论完告诉太极，太极改 db_write.py + 加字段。

---

## 第十四章：对话种子完整链路修复（2026-03-10 太极写）

### 问题描述

白纱和黑丝的回复几乎全部没写入 conversations.db，/catchup 看不到 AI 回复。

### 完整链路（写入路径）

```
老板发消息
  → UserPromptSubmit hook → db_write.py → 写入 messages（无极）✅ 一直正常

白纱/黑丝回复结束
  → Stop hook → db_write.py
      ① get_project_from_session(session_id)  ← 断点1（已修）
      ② parse_last_assistant(transcript_path) ← 断点2（已修）
      ③ write_message() → messages 表
      ④ upsert_stop_point() → stop_points 表
```

### 断点1：session_id 检测失败（已修）

**根因**：旧代码用 `cwd`（当前工作目录）判断项目。白纱的工作目录是 `/lab`，不在 KNOWN_PROJECTS → 返回 None → 静默跳过。

**修复**：改为扫描 `~/.claude/projects/` 所有目录，找到包含 `{session_id}*.jsonl` 的目录 → 返回项目名。当前实装：`get_project_from_session(session_id)`。

### 断点2：竞态条件（已修，2026-03-10）

**根因**：Stop hook 与 JSONL 写入并发触发。Hook 读取 transcript_path 时，JSONL 尚未写入本轮最终文字回复（只写到最后一条 tool_result USER 消息）。`parse_last_assistant` 反向读，第一条遇到 `type='user'` 立刻 break → parts 为空 → content_len=0 → 跳过写入。

**证据**：连续 16 次 Stop 事件 `content_len=0`，只有 1 次成功（短回复，JSONL 写入赶上了 hook）。

**修复**：Stop 事件处理加重试逻辑，最多 3 次，每次间隔 0.5 秒：
```python
for attempt in range(3):
    speaker, content = parse_last_assistant(transcript_path)
    if content:
        break
    if attempt < 2:
        time.sleep(0.5)
```
文件：`~/.claude/scripts/db_write.py`

### /catchup 简化（2026-03-10）

去掉了 tags 分类输出（决策/纠错/提升分组），改为纯时间顺序展示。格式更清晰，不依赖 tags 准确性。

文件：`~/.claude/commands/catchup.md`

### 当前状态

- Stop hook 写入链路已全部修通
- 历史缺失条目已回填（79f9196e 会话补了 63 条，共 154 条）
- /catchup 已简化
- 下次白纱/黑丝 Stop hook 触发，日志在 `/tmp/db_write.log`，可直接 `cat` 确认
