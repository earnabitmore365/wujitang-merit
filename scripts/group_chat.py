#!/usr/bin/env python3
"""
通讯部群聊系统 — group_chat.py
一个输入框，@谁谁回答，所有人都能看到。

端口: 8080
访问: http://echo:8080 (Tailscale) 或 http://localhost:8080

用法:
  python3 ~/.claude/scripts/group_chat.py
  # 或后台运行:
  nohup python3 ~/.claude/scripts/group_chat.py > ~/.claude/group_chat.log 2>&1 &
"""

import json
import os
import re
import sqlite3
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from queue import Queue

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

# ============================================================
# 配置
# ============================================================

HOME = str(Path.home())
DB_PATH = os.path.join(HOME, ".claude", "conversations.db")
PORT = 8080
HOST = "0.0.0.0"

# 角色配置
ROLES = {
    "太极": {
        "cwd": HOME,
        "model": "opus",
        "color": "#c084fc",      # 紫色
        "emoji": "☯️",
        "desc": "CEO / 通讯部",
        "project": "home",
    },
    "黑丝": {
        "cwd": os.path.join(HOME, "project", "auto-trading"),
        "model": "opus",
        "color": "#60a5fa",      # 蓝色
        "emoji": "🖤",
        "desc": "主力全包",
        "project": "auto-trading",
    },
    "白纱": {
        "cwd": os.path.join(HOME, "project", "auto-trading"),
        "model": "sonnet",
        "color": "#34d399",      # 绿色
        "emoji": "🤍",
        "desc": "支援查资料",
        "project": "auto-trading",
    },
}

BOSS_NAME = "无极"
BOSS_COLOR = "#f59e0b"

# 任务队列（串行执行，防 API 限流）
task_queue = Queue()

# 对线模式状态
debate_state = {
    "active": False,
    "topic": "",
    "participants": [],
    "max_rounds": 3,
    "current_round": 0,
    "phase": "idle",       # idle / initial / rebuttal / ended
    "history": [],         # [{speaker, content, round}]
    "boss_interjections": [],
    "stop_requested": False,
}
debate_lock = threading.Lock()

# Bypass 模式：关闭 plan mode 限制，允许 AI 执行操作（默认关闭）
bypass_mode = False

# 新话题分隔标记
NEW_SESSION_MARKER = "──── 新话题 ────"

# ============================================================
# 数据库
# ============================================================

def get_db():
    """获取数据库连接（WAL 模式，支持并发读）"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def ensure_reactions_column():
    """确保 reactions 字段存在"""
    conn = get_db()
    try:
        conn.execute("SELECT reactions FROM messages LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE messages ADD COLUMN reactions TEXT DEFAULT '{}'")
        conn.commit()
    conn.close()

def write_message(speaker, content, project="group-chat", tags="", session_id="group"):
    """写入消息到 conversations.db"""
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO messages (time, speaker, content, project, session_id, tags) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (now, speaker, content, project, session_id, tags),
    )
    conn.commit()
    msg_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return msg_id, now

def get_history(limit=50):
    """获取群聊历史"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, time, speaker, content, tags, reactions "
        "FROM messages WHERE project = 'group-chat' "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    # 倒序取，正序返回
    messages = []
    for r in reversed(rows):
        reactions = {}
        if r["reactions"]:
            try:
                reactions = json.loads(r["reactions"])
            except (json.JSONDecodeError, TypeError):
                reactions = {}
        messages.append({
            "id": r["id"],
            "time": r["time"],
            "speaker": r["speaker"],
            "content": r["content"],
            "tags": r["tags"] or "",
            "reactions": reactions,
        })
    return messages

def get_recent_context(limit=10):
    """获取最近 N 条群聊记录，用于注入上下文。遇到新话题标记截断。"""
    conn = get_db()
    rows = conn.execute(
        "SELECT time, speaker, content FROM messages "
        "WHERE project = 'group-chat' "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    lines = []
    for r in reversed(rows):
        # 遇到新话题标记，丢弃之前的内容
        if NEW_SESSION_MARKER in (r["content"] or ""):
            lines.clear()
            continue
        t = r["time"][11:16] if r["time"] and len(r["time"]) >= 16 else ""
        preview = (r["content"] or "")[:300].replace("\n", " ")
        lines.append(f"{r['speaker']}({t}): {preview}")
    return "\n".join(lines)

def update_reaction(msg_id, emoji, actor):
    """更新消息的反应"""
    conn = get_db()
    row = conn.execute("SELECT reactions FROM messages WHERE id = ?", (msg_id,)).fetchone()
    if not row:
        conn.close()
        return None
    try:
        reactions = json.loads(row["reactions"] or "{}")
    except (json.JSONDecodeError, TypeError):
        reactions = {}
    if emoji not in reactions:
        reactions[emoji] = []
    if actor in reactions[emoji]:
        reactions[emoji].remove(actor)  # 取消
    else:
        reactions[emoji].append(actor)  # 添加
    # 清理空列表
    reactions = {k: v for k, v in reactions.items() if v}
    conn.execute(
        "UPDATE messages SET reactions = ? WHERE id = ?",
        (json.dumps(reactions, ensure_ascii=False), msg_id),
    )
    conn.commit()
    conn.close()
    return reactions

# ============================================================
# Claude 调用
# ============================================================

def _build_base_context(role_name):
    """构建角色基础上下文（CLAUDE.md + rules + identity + 身份声明）"""
    role = ROLES[role_name]
    prompt_parts = []

    # 读取项目 CLAUDE.md
    claude_md_path = os.path.join(role["cwd"], "CLAUDE.md")
    if os.path.exists(claude_md_path):
        try:
            with open(claude_md_path, "r") as f:
                prompt_parts.append(f"[项目规则]\n{f.read()[:2000]}")
        except Exception:
            pass

    # 读取 rules.md
    global_rules_path = os.path.join(HOME, ".claude", "projects",
        "-Users-allenbot", "memory", "rules.md")
    if os.path.exists(global_rules_path):
        try:
            with open(global_rules_path, "r") as f:
                prompt_parts.append(f"[行为规范]\n{f.read()[:1500]}")
        except Exception:
            pass

    # 读取 identity.md
    cwd_encoded = role["cwd"].replace("/", "-")
    identity_path = os.path.join(HOME, ".claude", "projects", cwd_encoded, "memory", "identity.md")
    if not os.path.exists(identity_path):
        # Claude 编码也会把 _ 替换成 -
        identity_path = os.path.join(HOME, ".claude", "projects", cwd_encoded.replace("_", "-"), "memory", "identity.md")
    if os.path.exists(identity_path):
        try:
            with open(identity_path, "r") as f:
                prompt_parts.append(f"[你的存在本质]\n{f.read()[:500]}")
        except Exception:
            pass

    return prompt_parts


def _run_claude(role_name, full_prompt):
    """执行 claude -p 子进程，返回输出"""
    role = ROLES[role_name]
    cmd = [
        "claude",
        "-p",
        "--model", role["model"],
    ]
    if not bypass_mode:
        cmd.extend(["--permission-mode", "plan"])
    cmd.append(full_prompt)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=role["cwd"],
            env={**os.environ, "LANG": "en_US.UTF-8"},
        )
        output = result.stdout.strip()
        if not output and result.stderr:
            output = f"[系统错误] {result.stderr[:500]}"
        return output or "[无回复]"
    except subprocess.TimeoutExpired:
        return "[超时] 执行超过 3 分钟，已中断。"
    except Exception as e:
        return f"[调用失败] {str(e)}"


def call_claude(role_name, message):
    """
    调用 claude -p 并返回结果（普通群聊模式）。
    """
    role = ROLES[role_name]
    prompt_parts = _build_base_context(role_name)

    prompt_parts.append(
        f"[你的身份]\n"
        f"你是{role_name}（{role['desc']}）。你在一个群聊中，老板代号\"无极\"。\n"
        f"老板 @了你，请直接回答。用中文。回答简洁有力，不要重复问题。"
    )
    recent = get_recent_context(limit=10)
    if recent:
        prompt_parts.append(f"[群聊上下文 — 最近消息]\n{recent}")
    prompt_parts.append(f"[老板对你说]\n{message}")

    return _run_claude(role_name, "\n\n".join(prompt_parts))

# ============================================================
# 对线模式
# ============================================================

def _build_debate_prompt(role_name, phase, topic, history, opponent_name, boss_interjection=None):
    """构建辩论专用 prompt"""
    role = ROLES[role_name]
    prompt_parts = _build_base_context(role_name)

    prompt_parts.append(
        f"[你的身份]\n"
        f"你是{role_name}（{role['desc']}）。你在一场辩论/评审中，老板代号\"无极\"。\n"
        f"用中文。直接有力，不要客套。"
    )

    if phase == "initial":
        prompt_parts.append(
            f"[辩论模式 — 初始立场]\n"
            f"主题：{topic}\n\n"
            f"你的对手是{opponent_name}。发表你对这个主题的立场和核心论据。\n"
            f"要求：明确立场，给出 2-3 个核心论据，控制在 500 字以内。"
        )
    else:
        # 找对方最新一条和自己最新一条
        opponent_last = ""
        my_last = ""
        earlier_summary = []
        for h in reversed(history):
            if h["speaker"] == opponent_name and not opponent_last:
                opponent_last = h["content"]
            elif h["speaker"] == role_name and not my_last:
                my_last = h["content"]
            elif opponent_last and my_last:
                # 更早的压缩为摘要
                earlier_summary.append(f"第{h['round']}轮 {h['speaker']}：{h['content'][:150]}...")

        round_num = history[-1]["round"] + 1 if history else 1
        context = f"[辩论模式 — 第{round_num}轮反驳]\n主题：{topic}\n\n"
        if opponent_last:
            context += f"对方（{opponent_name}）最新发言：\n{opponent_last}\n\n"
        if my_last:
            context += f"你上轮的立场：\n{my_last}\n\n"
        if earlier_summary:
            context += f"更早的讨论摘要：\n" + "\n".join(earlier_summary[:3]) + "\n\n"
        if boss_interjection:
            context += f"⚠️ [老板插话] {boss_interjection}\n请同时回应老板的意见。\n\n"
        context += (
            "要求：针对对方观点中的具体漏洞进行反驳，强化你的论点，可以引入新论据。\n"
            "控制在 500 字以内，不要重复对方原文，直接切入要害。"
        )
        prompt_parts.append(context)

    return "\n\n".join(prompt_parts)


def process_debate(topic, participants, max_rounds, socketio_app):
    """辩论主循环（在 worker 线程中执行）"""
    global debate_state

    with debate_lock:
        debate_state.update({
            "active": True,
            "topic": topic,
            "participants": participants,
            "max_rounds": max_rounds,
            "current_round": 0,
            "phase": "initial",
            "history": [],
            "boss_interjections": [],
            "stop_requested": False,
        })

    # 系统消息：辩论开始
    sys_id, sys_time = write_message("系统",
        f"⚔️ 对线模式启动 — {participants[0]} vs {participants[1]} | 主题：{topic} | 最多 {max_rounds} 轮",
        tags="对线,发起")
    socketio_app.emit("new_message", {
        "id": sys_id, "time": sys_time, "speaker": "系统",
        "content": f"⚔️ 对线模式启动 — {participants[0]} vs {participants[1]} | 主题：{topic} | 最多 {max_rounds} 轮",
        "tags": "对线,发起", "reactions": {},
    })
    socketio_app.emit("debate_status", {
        "active": True, "round": 0, "max": max_rounds, "phase": "initial",
    })

    # --- 阶段1：初始立场 ---
    for i, p in enumerate(participants):
        if debate_state["stop_requested"]:
            break
        opponent = participants[1 - i]
        socketio_app.emit("typing", {"role": p, "active": True})
        prompt = _build_debate_prompt(p, "initial", topic, [], opponent)
        reply = _run_claude(p, prompt)
        socketio_app.emit("typing", {"role": p, "active": False})

        debate_state["history"].append({"speaker": p, "content": reply, "round": 0})
        reply_id, reply_time = write_message(p, reply, tags="对线,初始立场")
        socketio_app.emit("new_message", {
            "id": reply_id, "time": reply_time, "speaker": p,
            "content": reply, "tags": "对线,初始立场", "reactions": {},
        })

    # --- 阶段2：反驳轮次 ---
    with debate_lock:
        debate_state["phase"] = "rebuttal"

    for round_num in range(1, max_rounds + 1):
        if debate_state["stop_requested"]:
            break
        with debate_lock:
            debate_state["current_round"] = round_num
        socketio_app.emit("debate_status", {
            "active": True, "round": round_num, "max": max_rounds, "phase": "rebuttal",
        })

        for i, p in enumerate(participants):
            if debate_state["stop_requested"]:
                break
            opponent = participants[1 - i]

            # 消费老板插话
            interjection = None
            with debate_lock:
                if debate_state["boss_interjections"]:
                    interjection = "\n".join(debate_state["boss_interjections"])
                    debate_state["boss_interjections"].clear()

            socketio_app.emit("typing", {"role": p, "active": True})
            prompt = _build_debate_prompt(
                p, "rebuttal", topic, debate_state["history"], opponent, interjection
            )
            reply = _run_claude(p, prompt)
            socketio_app.emit("typing", {"role": p, "active": False})

            debate_state["history"].append({"speaker": p, "content": reply, "round": round_num})
            reply_id, reply_time = write_message(p, reply, tags=f"对线,反驳,R{round_num}")
            socketio_app.emit("new_message", {
                "id": reply_id, "time": reply_time, "speaker": p,
                "content": reply, "tags": f"对线,反驳,R{round_num}", "reactions": {},
            })

    # --- 结束 ---
    reason = "老板叫停" if debate_state["stop_requested"] else f"完成 {max_rounds} 轮"
    end_id, end_time = write_message("系统", f"⚔️ 对线结束 — {reason}", tags="对线,结束")
    socketio_app.emit("new_message", {
        "id": end_id, "time": end_time, "speaker": "系统",
        "content": f"⚔️ 对线结束 — {reason}", "tags": "对线,结束", "reactions": {},
    })
    with debate_lock:
        debate_state.update({"active": False, "phase": "ended"})
    socketio_app.emit("debate_status", {"active": False, "phase": "ended"})


# ============================================================
# 消息处理
# ============================================================

def parse_mention(text):
    """
    解析 @mention，返回 (目标角色名, 消息内容)。
    支持: @太极 你好 / @黑丝查余额 / @白纱 帮我看看
    无 @ 时返回 (None, text)
    """
    pattern = r"^@(太极|黑丝|白纱)\s*(.*)"
    match = re.match(pattern, text.strip(), re.DOTALL)
    if match:
        return match.group(1), match.group(2).strip()
    return None, text.strip()

# 高危操作拦截
DANGEROUS_KEYWORDS = ["rm -rf", "DROP TABLE", "git push --force", "reset --hard"]

def check_safety(content):
    """检查消息是否包含高危操作关键词"""
    for kw in DANGEROUS_KEYWORDS:
        if kw.lower() in content.lower():
            return False, f"⚠️ 检测到高危操作 [{kw}]，已拦截。请在终端中手动执行。"
    return True, ""

def process_message(text, responder, listeners, socketio_app):
    """处理老板发来的消息（在 worker 线程中执行）"""
    # 从文本中去掉 @mention 前缀，提取纯内容
    _, content = parse_mention(text)
    if not content:
        content = text
    target = responder  # 回答者由前端传入（第一个点亮的按钮）

    # 写入老板消息
    msg_id, msg_time = write_message(BOSS_NAME, text, tags="群聊")

    # 广播老板消息
    socketio_app.emit("new_message", {
        "id": msg_id,
        "time": msg_time,
        "speaker": BOSS_NAME,
        "content": text,
        "tags": "群聊",
        "reactions": {},
    })

    # @All 模式：所有人都回答
    if responder == '__all__':
        for role_name in ROLES:
            safe, warn_msg = check_safety(content)
            if not safe:
                warn_id, warn_time = write_message("系统", warn_msg, tags="拦截")
                socketio_app.emit("new_message", {
                    "id": warn_id, "time": warn_time, "speaker": "系统",
                    "content": warn_msg, "tags": "拦截", "reactions": {},
                })
                return
            socketio_app.emit("typing", {"role": role_name, "active": True})
            reply = call_claude(role_name, content)
            socketio_app.emit("typing", {"role": role_name, "active": False})
            reply_id, reply_time = write_message(role_name, reply, tags="群聊")
            socketio_app.emit("new_message", {
                "id": reply_id, "time": reply_time, "speaker": role_name,
                "content": reply, "tags": "群聊", "reactions": {},
            })
        return

    if not target or target not in ROLES:
        # 没有点亮任何人，不调用 AI
        return

    # 安全拦截
    safe, warn_msg = check_safety(content)
    if not safe:
        warn_id, warn_time = write_message("系统", warn_msg, tags="拦截")
        socketio_app.emit("new_message", {
            "id": warn_id, "time": warn_time, "speaker": "系统",
            "content": warn_msg, "tags": "拦截", "reactions": {},
        })
        return

    # 通知前端：正在回复
    socketio_app.emit("typing", {"role": target, "active": True})

    # 调用 Claude
    reply = call_claude(target, content)

    # 停止 typing 状态
    socketio_app.emit("typing", {"role": target, "active": False})

    # 写入 AI 回复
    reply_id, reply_time = write_message(target, reply, tags="群聊")

    # 广播 AI 回复
    socketio_app.emit("new_message", {
        "id": reply_id,
        "time": reply_time,
        "speaker": target,
        "content": reply,
        "tags": "群聊",
        "reactions": {},
    })

    # 旁听者反应（排除回答者自己）
    actual_listeners = [l for l in listeners if l != target and l in ROLES]
    for listener in actual_listeners:
        socketio_app.emit("typing", {"role": listener, "active": True})
        raw = ask_listener(listener, target, content, reply)
        socketio_app.emit("typing", {"role": listener, "active": False})

        emoji, reaction_content = parse_listener_reaction(raw)
        if emoji is None:
            continue  # 沉默，不显示

        if emoji == "🖐" and reaction_content:
            # 举手发言 — 显示为小消息
            r_id, r_time = write_message(listener, f"🖐 {reaction_content}", tags="旁听")
            socketio_app.emit("new_message", {
                "id": r_id, "time": r_time, "speaker": listener,
                "content": f"🖐 {reaction_content}", "tags": "旁听",
                "reactions": {},
            })
        else:
            # ✅ 或 ❌ — 显示为标签（附在回答者消息下面）
            socketio_app.emit("listener_reaction", {
                "msg_id": reply_id,
                "listener": listener,
                "emoji": emoji,
                "comment": reaction_content,
            })

# 旁听者反应
def ask_listener(listener_name, responder_name, question, answer):
    """问旁听者对回答的反应"""
    prompt = (
        f"[旁听] 老板对{responder_name}说: {question[:200]}\n"
        f"{responder_name}回答: {answer[:300]}\n\n"
        f"你作为旁听者，回复：✅ 同意 / ❌ 不同意 / 🖐 想说的话 / — 没意见\n"
        f"只回复符号+一句话，不要展开。"
    )
    return call_claude(listener_name, prompt)

def parse_listener_reaction(text):
    """解析旁听者反应：返回 (emoji, content)"""
    text = text.strip()
    if text.startswith("✅"):
        return "✅", text[1:].strip()
    elif text.startswith("❌"):
        return "❌", text[1:].strip()
    elif text.startswith("🖐"):
        return "🖐", text[1:].strip()
    elif text.startswith("—") or text.startswith("-"):
        return None, ""  # 沉默
    # 无法解析，当作举手
    if len(text) > 2:
        return "🖐", text
    return None, ""

# Worker 线程：串行处理消息队列
def message_worker(socketio_app):
    """从队列中取消息，逐个处理（串行，防 API 限流）"""
    while True:
        item = task_queue.get()
        try:
            # 对线任务
            if isinstance(item, dict) and item.get("type") == "debate":
                process_debate(
                    item["topic"], item["participants"],
                    item["max_rounds"], socketio_app,
                )
            # 普通消息
            elif isinstance(item, tuple) and len(item) == 3:
                text, responder, listeners = item
                process_message(text, responder, listeners, socketio_app)
            elif isinstance(item, tuple) and len(item) == 2:
                text, responder = item
                process_message(text, responder, [], socketio_app)
            else:
                process_message(str(item), "", [], socketio_app)
        except Exception as e:
            print(f"[Worker Error] {e}")
            socketio_app.emit("error", {"msg": str(e)})
        finally:
            task_queue.task_done()

# ============================================================
# Flask App
# ============================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = "comm-hq-group-chat"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

@app.route("/")
def index():
    return HTML_PAGE

@app.route("/api/history")
def api_history():
    limit = request.args.get("limit", 50, type=int)
    return jsonify(get_history(limit))

@socketio.on("send_message")
def handle_message(data):
    text = data.get("text", "").strip()
    responder = data.get("responder", "")  # 第一个点亮的 = 回答者
    listeners = data.get("listeners", [])  # 其余点亮的 = 旁听者
    if not text:
        return
    task_queue.put((text, responder, listeners))

@socketio.on("reaction")
def handle_reaction(data):
    msg_id = data.get("id")
    emoji = data.get("emoji")
    if not msg_id or not emoji:
        return
    reactions = update_reaction(msg_id, emoji, BOSS_NAME)
    if reactions is not None:
        emit("reaction_update", {"id": msg_id, "reactions": reactions}, broadcast=True)

@socketio.on("start_debate")
def handle_start_debate(data):
    """老板发起对线"""
    if debate_state.get("active"):
        emit("error", {"msg": "对线正在进行中，请先结束当前对线"})
        return
    topic = data.get("topic", "").strip()
    participants = data.get("participants", [])
    max_rounds = data.get("max_rounds", 3)
    if not topic or len(participants) < 2:
        emit("error", {"msg": "需要主题和至少两个参与者"})
        return
    # 验证参与者
    participants = [p for p in participants if p in ROLES]
    if len(participants) < 2:
        emit("error", {"msg": "至少需要两个有效参与者"})
        return
    # 写入老板消息
    msg_id, msg_time = write_message(BOSS_NAME, f"⚔️ 对线：{topic}", tags="对线,发起")
    socketio.emit("new_message", {
        "id": msg_id, "time": msg_time, "speaker": BOSS_NAME,
        "content": f"⚔️ 对线：{topic}", "tags": "对线,发起", "reactions": {},
    })
    # 入队
    task_queue.put({
        "type": "debate",
        "topic": topic,
        "participants": participants[:2],
        "max_rounds": max_rounds,
    })

@socketio.on("debate_interject")
def handle_debate_interject(data):
    """老板在对线中插话"""
    text = data.get("text", "").strip()
    if not text or not debate_state.get("active"):
        return
    with debate_lock:
        debate_state["boss_interjections"].append(text)
    # 写入并广播
    msg_id, msg_time = write_message(BOSS_NAME, f"✋ {text}", tags="对线,插话")
    socketio.emit("new_message", {
        "id": msg_id, "time": msg_time, "speaker": BOSS_NAME,
        "content": f"✋ {text}", "tags": "对线,插话", "reactions": {},
    })

@socketio.on("stop_debate")
def handle_stop_debate(data=None):
    """老板终止对线"""
    with debate_lock:
        debate_state["stop_requested"] = True

@socketio.on("new_session")
def handle_new_session(data=None):
    """开新话题，清除上下文"""
    msg_id, msg_time = write_message("系统", NEW_SESSION_MARKER, tags="系统,新话题")
    socketio.emit("new_session", {
        "id": msg_id, "time": msg_time,
    })

@socketio.on("toggle_bypass")
def handle_toggle_bypass(data=None):
    """切换 bypass 模式（关闭 plan mode 限制）"""
    global bypass_mode
    bypass_mode = not bypass_mode
    status = "🔓 BYPASS 已开启 — AI 可执行操作" if bypass_mode else "🔒 BYPASS 已关闭 — 恢复只读模式"
    # 写入系统消息
    msg_id, msg_time = write_message("系统", status, tags="系统")
    socketio.emit("new_message", {
        "id": msg_id, "time": msg_time, "speaker": "系统",
        "content": status, "tags": "系统", "reactions": {},
    })
    socketio.emit("bypass_status", {"active": bypass_mode})

# ============================================================
# 内嵌 HTML 前端
# ============================================================

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>通讯部</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<style>
  :root {
    --bg: #0d1117;
    --bg2: #161b22;
    --bg3: #21262d;
    --border: #30363d;
    --text: #e6edf3;
    --text2: #8b949e;
    --boss: #f59e0b;
    --taiji: #c084fc;
    --heisi: #60a5fa;
    --baisha: #34d399;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body {
    height: 100%;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif;
    font-size: 15px;
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }
  #app {
    display: flex;
    flex-direction: column;
    height: 100dvh;
    max-width: 768px;
    margin: 0 auto;
  }

  /* 顶栏 */
  .topbar {
    flex-shrink: 0;
    background: var(--bg2);
    border-bottom: 1px solid var(--border);
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }
  .topbar h1 {
    font-size: 17px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }
  .status-dots {
    display: flex;
    gap: 10px;
    align-items: center;
  }
  .dot-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: var(--text2);
  }
  .dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--border);
    transition: background 0.3s;
  }
  .dot.online { background: #3fb950; }
  .dot.busy { background: var(--boss); animation: pulse 1.2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  /* 打字指示 */
  .typing-bar {
    flex-shrink: 0;
    background: var(--bg2);
    padding: 0 16px;
    height: 0;
    overflow: hidden;
    transition: height 0.2s, padding 0.2s;
    font-size: 13px;
    color: var(--text2);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .typing-bar.active {
    height: 32px;
  }
  .typing-dots {
    display: flex; gap: 3px;
  }
  .typing-dots span {
    width: 5px; height: 5px; border-radius: 50%;
    background: var(--text2);
    animation: typedot 1.4s infinite;
  }
  .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
  .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes typedot { 0%,60%,100%{opacity:0.3;transform:translateY(0)} 30%{opacity:1;transform:translateY(-3px)} }

  /* 消息区 */
  .messages {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 12px 16px;
    scroll-behavior: smooth;
    -webkit-overflow-scrolling: touch;
  }
  .messages::-webkit-scrollbar { width: 4px; }
  .messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  /* 消息条 */
  .msg {
    margin-bottom: 12px;
    max-width: 85%;
    animation: fadeIn 0.2s ease;
  }
  @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
  .msg.boss { margin-left: auto; }
  .msg.ai { margin-right: auto; }
  .msg-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 3px;
    font-size: 12px;
  }
  .msg.boss .msg-header { justify-content: flex-end; }
  .msg-name {
    font-weight: 600;
  }
  .msg-time {
    color: var(--text2);
    font-size: 11px;
  }
  .msg-bubble {
    padding: 10px 14px;
    border-radius: 16px;
    line-height: 1.55;
    word-break: break-word;
    font-size: 14.5px;
  }
  .msg.boss .msg-bubble {
    background: #1c3a5e;
    border-bottom-right-radius: 4px;
    color: #dbeafe;
  }
  .msg.ai .msg-bubble {
    background: var(--bg3);
    border-bottom-left-radius: 4px;
  }

  /* Markdown 内容样式 */
  .msg-bubble pre {
    background: rgba(0,0,0,0.35);
    border-radius: 8px;
    padding: 10px 12px;
    overflow-x: auto;
    margin: 8px 0;
    font-size: 13px;
    line-height: 1.45;
  }
  .msg-bubble code {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 13px;
  }
  .msg-bubble :not(pre)>code {
    background: rgba(0,0,0,0.3);
    padding: 2px 6px;
    border-radius: 4px;
  }
  .msg-bubble p { margin: 6px 0; }
  .msg-bubble p:first-child { margin-top: 0; }
  .msg-bubble p:last-child { margin-bottom: 0; }
  .msg-bubble ul, .msg-bubble ol { padding-left: 20px; margin: 6px 0; }
  .msg-bubble h1,.msg-bubble h2,.msg-bubble h3 { margin: 10px 0 6px; font-size: 15px; }
  .msg-bubble table { border-collapse: collapse; margin: 8px 0; font-size: 13px; }
  .msg-bubble th, .msg-bubble td { border: 1px solid var(--border); padding: 4px 8px; }
  .msg-bubble blockquote { border-left: 3px solid var(--border); padding-left: 10px; color: var(--text2); margin: 6px 0; }

  /* 反应 */
  .msg-reactions {
    display: flex;
    gap: 4px;
    margin-top: 4px;
    flex-wrap: wrap;
  }
  .msg.boss .msg-reactions { justify-content: flex-end; }
  .reaction-btn {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.15s;
    color: var(--text);
    line-height: 1.5;
  }
  .reaction-btn:hover { border-color: var(--text2); background: var(--bg3); }
  .reaction-btn:active { transform: scale(0.92); }
  .reaction-btn.has-reaction { border-color: var(--boss); background: rgba(245,158,11,0.1); }
  .reaction-count {
    font-size: 11px;
    margin-left: 2px;
    color: var(--text2);
  }

  /* 底部输入区 */
  .input-area {
    flex-shrink: 0;
    background: var(--bg2);
    border-top: 1px solid var(--border);
    padding: 8px 12px;
    padding-bottom: max(8px, env(safe-area-inset-bottom));
  }
  .mention-bar {
    display: flex;
    gap: 6px;
    margin-bottom: 8px;
  }
  .mention-btn.active {
    background: rgba(255,255,255,0.15);
    font-weight: 700;
    box-shadow: 0 0 8px rgba(255,255,255,0.2);
  }
  .mention-btn {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.15s;
    color: var(--text);
    user-select: none;
    -webkit-user-select: none;
  }
  .mention-btn:active { transform: scale(0.94); }
  .input-row {
    display: flex;
    gap: 8px;
    align-items: flex-end;
  }
  #msg-input {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 10px 16px;
    color: var(--text);
    font-size: 15px;
    font-family: inherit;
    resize: none;
    max-height: 120px;
    line-height: 1.4;
    outline: none;
    transition: border-color 0.2s;
  }
  #msg-input:focus { border-color: var(--text2); }
  #msg-input::placeholder { color: var(--text2); }
  .send-btn {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--boss);
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    flex-shrink: 0;
  }
  .send-btn:active { transform: scale(0.9); }
  .send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .send-btn svg { width: 18px; height: 18px; fill: #000; }

  /* 系统消息 */
  .sys-msg {
    text-align: center;
    font-size: 12px;
    color: var(--text2);
    margin: 16px 0;
  }

  /* Bypass 开关 */
  .bypass-btn {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.2s;
    line-height: 1;
  }
  .bypass-btn:active { transform: scale(0.9); }
  .bypass-btn.active {
    background: rgba(239,68,68,0.2);
    border-color: #ef4444;
    box-shadow: 0 0 8px rgba(239,68,68,0.4);
    animation: pulse 1.5s infinite;
  }

  /* 对线模式 */
  .debate-panel {
    background: var(--bg3);
    border: 1px solid #ef4444;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: none;
  }
  .debate-panel .dp-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    font-size: 13px;
    color: var(--text2);
  }
  .debate-panel .dp-row:last-child { margin-bottom: 0; }
  .debate-panel label {
    display: flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    font-size: 13px;
    color: var(--text);
  }
  .debate-panel select {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 3px 8px;
    color: var(--text);
    font-size: 13px;
  }
  .debate-bar {
    flex-shrink: 0;
    background: rgba(239,68,68,0.1);
    border-bottom: 1px solid rgba(239,68,68,0.3);
    padding: 0 16px;
    height: 0;
    overflow: hidden;
    transition: height 0.2s;
    font-size: 13px;
    color: #fca5a5;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .debate-bar.active { height: 36px; }
  .debate-bar button {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 3px 10px;
    color: var(--text);
    cursor: pointer;
    font-size: 12px;
    transition: all 0.15s;
  }
  .debate-bar button:active { transform: scale(0.94); }

  /* 空状态 */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text2);
    gap: 8px;
  }
  .empty-state .big { font-size: 48px; }
  .empty-state .label { font-size: 14px; }
</style>
</head>
<body>
<div id="app">

  <div class="topbar">
    <h1>通讯部</h1>
    <div style="display:flex;align-items:center;gap:12px;">
      <button class="bypass-btn" id="new-session-btn" onclick="newSession()" title="新话题：清除上下文">🆕</button>
      <button class="bypass-btn" id="bypass-btn" onclick="toggleBypass()" title="Bypass: 允许AI执行操作">🔒</button>
      <div class="status-dots">
        <div class="dot-item"><span class="dot" id="dot-太极"></span>太极</div>
        <div class="dot-item"><span class="dot" id="dot-黑丝"></span>黑丝</div>
        <div class="dot-item"><span class="dot" id="dot-白纱"></span>白纱</div>
      </div>
    </div>
  </div>

  <div class="typing-bar" id="typing-bar">
    <div class="typing-dots"><span></span><span></span><span></span></div>
    <span id="typing-text"></span>
  </div>

  <div class="debate-bar" id="debate-bar">
    ⚔️ 对线中 — 第 <span id="debate-round">0</span>/<span id="debate-max">3</span> 轮
    <button onclick="debateInterject()">✋ 插话</button>
    <button onclick="stopDebate()">⏹ 结束</button>
  </div>

  <div class="messages" id="messages"></div>

  <div class="input-area">
    <div class="mention-bar" id="mention-bar">
      <button class="mention-btn" id="mbtn-All" onclick="toggleAll()" style="border-color:#fff;color:#fff">@All</button>
      <button class="mention-btn" id="mbtn-太极" onclick="toggleListener('太极')" style="border-color:var(--taiji);color:var(--taiji)">@太极</button>
      <button class="mention-btn" id="mbtn-黑丝" onclick="toggleListener('黑丝')" style="border-color:var(--heisi);color:var(--heisi)">@黑丝</button>
      <button class="mention-btn" id="mbtn-白纱" onclick="toggleListener('白纱')" style="border-color:var(--baisha);color:var(--baisha)">@白纱</button>
      <button class="mention-btn" id="mbtn-debate" onclick="toggleDebatePanel()" style="border-color:#ef4444;color:#ef4444">⚔️ 对线</button>
    </div>
    <div class="debate-panel" id="debate-panel">
      <div class="dp-row">
        对线双方：
        <label><input type="checkbox" id="dp-太极" value="太极"> 太极</label>
        <label><input type="checkbox" id="dp-黑丝" value="黑丝" checked> 黑丝</label>
        <label><input type="checkbox" id="dp-白纱" value="白纱" checked> 白纱</label>
      </div>
      <div class="dp-row">
        轮数：
        <select id="debate-rounds-select">
          <option value="1">1 轮</option>
          <option value="2">2 轮</option>
          <option value="3" selected>3 轮</option>
          <option value="5">5 轮</option>
        </select>
      </div>
    </div>
    <div class="input-row">
      <textarea id="msg-input" rows="1" placeholder="输入消息..." onkeydown="handleKey(event)" oninput="autoGrow(this)"></textarea>
      <button class="send-btn" id="send-btn" onclick="sendMessage()">
        <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
      </button>
    </div>
  </div>

</div>

<script>
const ROLES = """ + json.dumps({k: {"color": v["color"], "emoji": v["emoji"], "desc": v["desc"]} for k, v in ROLES.items()}, ensure_ascii=False) + """;
const BOSS = {name: '""" + BOSS_NAME + """', color: '""" + BOSS_COLOR + """'};

const socket = io();
const msgsEl = document.getElementById('messages');
const inputEl = document.getElementById('msg-input');
const sendBtn = document.getElementById('send-btn');
const typingBar = document.getElementById('typing-bar');
const typingText = document.getElementById('typing-text');

// Markdown 渲染
marked.setOptions({breaks: true, gfm: true});

function renderMd(text) {
  try { return marked.parse(text); }
  catch { return text.replace(/</g,'&lt;').replace(/\\n/g,'<br>'); }
}

function nameColor(speaker) {
  if (speaker === BOSS.name) return BOSS.color;
  return ROLES[speaker]?.color || '#8b949e';
}

function isBoss(speaker) {
  return speaker === BOSS.name;
}

// 创建消息 DOM
function createMsgEl(msg) {
  const boss = isBoss(msg.speaker);
  const div = document.createElement('div');
  div.className = 'msg ' + (boss ? 'boss' : 'ai');
  div.dataset.id = msg.id;

  const timeStr = (msg.time || '').slice(11, 16);
  const emoji = boss ? '' : (ROLES[msg.speaker]?.emoji || '') + ' ';

  div.innerHTML =
    '<div class="msg-header">' +
      '<span class="msg-name" style="color:' + nameColor(msg.speaker) + '">' + emoji + msg.speaker + '</span>' +
      '<span class="msg-time">' + timeStr + '</span>' +
    '</div>' +
    '<div class="msg-bubble">' + (boss ? escHtml(msg.content) : renderMd(msg.content)) + '</div>' +
    '<div class="listener-tags" id="lt-' + msg.id + '"></div>';
  return div;
}

function escHtml(s) {
  return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\\n/g,'<br>');
}

function buildReactions(id, reactions) {
  const emojis = ['✅','❌','🖐'];
  return emojis.map(e => {
    const actors = (reactions && reactions[e]) || [];
    const has = actors.length > 0;
    const count = actors.length > 0 ? '<span class="reaction-count">' + actors.length + '</span>' : '';
    return '<button class="reaction-btn' + (has?' has-reaction':'') + '" onclick="react(' + id + ',\\'' + e + '\\')">' + e + count + '</button>';
  }).join('');
}

function scrollBottom() {
  requestAnimationFrame(() => {
    msgsEl.scrollTop = msgsEl.scrollHeight;
  });
}

// 加载历史
async function loadHistory() {
  try {
    const res = await fetch('/api/history?limit=80');
    const msgs = await res.json();
    msgsEl.innerHTML = '';
    if (msgs.length === 0) {
      msgsEl.innerHTML = '<div class="empty-state"><div class="big">☯️</div><div class="label">通讯部就绪 — @太极 @黑丝 @白纱</div></div>';
      return;
    }
    msgs.forEach(m => msgsEl.appendChild(createMsgEl(m)));
    scrollBottom();
  } catch(e) {
    msgsEl.innerHTML = '<div class="sys-msg">加载失败: ' + e.message + '</div>';
  }
}

// 发送
function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;
  // 对线配置中 → 开始对线
  if (debateConfigMode) { startDebate(); return; }
  // 对线进行中 → 插话
  if (debateActive) { debateInterject(); return; }
  // 普通消息
  inputEl.value = '';
  inputEl.style.height = 'auto';
  const responder = allMode ? '__all__' : (activeRoles.length > 0 ? activeRoles[0] : '');
  const listeners = allMode ? [] : activeRoles.slice(1);
  socket.emit('send_message', {text, responder, listeners});
  const empty = msgsEl.querySelector('.empty-state');
  if (empty) empty.remove();
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoGrow(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// 参与者多选 toggle（按点亮顺序排列，第一个=回答者，其余=旁听者）
const activeRoles = [];  // 有序数组
let allMode = false;

function toggleAll() {
  const btn = document.getElementById('mbtn-All');
  allMode = !allMode;
  if (allMode) {
    // 全选
    activeRoles.length = 0;
    ['太极','黑丝','白纱'].forEach(r => {
      activeRoles.push(r);
      document.getElementById('mbtn-' + r).classList.add('active');
    });
    btn.classList.add('active');
    btn.textContent = '▶ @All';
  } else {
    // 全不选
    activeRoles.length = 0;
    ['太极','黑丝','白纱'].forEach(r => {
      document.getElementById('mbtn-' + r).classList.remove('active');
      document.getElementById('mbtn-' + r).textContent = '@' + r;
    });
    btn.classList.remove('active');
    btn.textContent = '@All';
  }
  inputEl.focus();
}

function toggleListener(name) {
  const btn = document.getElementById('mbtn-' + name);
  const idx = activeRoles.indexOf(name);
  if (idx >= 0) {
    activeRoles.splice(idx, 1);
    btn.classList.remove('active');
  } else {
    activeRoles.push(name);
    btn.classList.add('active');
  }
  // 更新按钮显示：第一个加下划线表示是回答者
  ['太极','黑丝','白纱'].forEach(r => {
    const b = document.getElementById('mbtn-' + r);
    b.textContent = (activeRoles[0] === r ? '▶ @' : '@') + r;
  });
  inputEl.focus();
}

function react(id, emoji) {
  socket.emit('reaction', {id, emoji});
}

// Socket 事件
socket.on('new_message', (msg) => {
  const empty = msgsEl.querySelector('.empty-state');
  if (empty) empty.remove();
  msgsEl.appendChild(createMsgEl(msg));
  scrollBottom();
});

socket.on('typing', (data) => {
  if (data.active) {
    typingBar.classList.add('active');
    typingText.textContent = data.role + ' 正在思考...';
    // 状态点变忙
    const dot = document.getElementById('dot-' + data.role);
    if (dot) dot.className = 'dot busy';
  } else {
    typingBar.classList.remove('active');
    const dot = document.getElementById('dot-' + data.role);
    if (dot) dot.className = 'dot online';
  }
});

socket.on('reaction_update', (data) => {
  const msgEl = document.querySelector('.msg[data-id="' + data.id + '"]');
  if (msgEl) {
    const reactionsEl = msgEl.querySelector('.msg-reactions');
    if (reactionsEl) reactionsEl.innerHTML = buildReactions(data.id, data.reactions);
  }
});

socket.on('listener_reaction', (data) => {
  const msgEl = document.querySelector('.msg[data-id="' + data.msg_id + '"]');
  if (msgEl) {
    let tagBar = msgEl.querySelector('.listener-tags');
    if (!tagBar) {
      tagBar = document.createElement('div');
      tagBar.className = 'listener-tags';
      tagBar.style.cssText = 'display:flex;gap:8px;margin-top:4px;flex-wrap:wrap;';
      msgEl.appendChild(tagBar);
    }
    const tag = document.createElement('span');
    const role = ROLES[data.listener] || {};
    const color = role.color || '#888';
    const emoji = role.emoji || '';
    tag.style.cssText = 'font-size:12px;padding:2px 8px;border-radius:10px;background:rgba(255,255,255,0.08);color:' + color + ';';
    tag.textContent = emoji + data.listener + ' ' + data.emoji + (data.comment ? ' ' + data.comment : '');
    tagBar.appendChild(tag);
    scrollBottom();
  }
});

socket.on('error', (data) => {
  const div = document.createElement('div');
  div.className = 'sys-msg';
  div.textContent = '⚠ ' + (data.msg || '未知错误');
  msgsEl.appendChild(div);
  scrollBottom();
});

socket.on('connect', () => {
  // 连接成功，所有角色标记在线
  Object.keys(ROLES).forEach(name => {
    const dot = document.getElementById('dot-' + name);
    if (dot) dot.className = 'dot online';
  });
});

socket.on('disconnect', () => {
  Object.keys(ROLES).forEach(name => {
    const dot = document.getElementById('dot-' + name);
    if (dot) dot.className = 'dot';
  });
});

// === 新话题 ===
function newSession() {
  socket.emit('new_session', {});
}
socket.on('new_session', (data) => {
  // 插入分割线
  const divider = document.createElement('div');
  divider.className = 'sys-msg';
  divider.style.cssText = 'border-top:1px solid var(--border);padding-top:12px;margin-top:16px;';
  divider.textContent = '──── 新话题 ────';
  msgsEl.appendChild(divider);
  scrollBottom();
});

// === Bypass 模式 ===
function toggleBypass() {
  socket.emit('toggle_bypass', {});
}
socket.on('bypass_status', (data) => {
  const btn = document.getElementById('bypass-btn');
  if (data.active) {
    btn.classList.add('active');
    btn.textContent = '🔓';
    btn.title = 'BYPASS 开启中 — AI 可执行操作（点击关闭）';
  } else {
    btn.classList.remove('active');
    btn.textContent = '🔒';
    btn.title = 'Bypass: 允许AI执行操作（点击开启）';
  }
});

// === 对线模式 ===
let debateConfigMode = false;  // 配置面板展开中
let debateActive = false;      // 对线进行中

function toggleDebatePanel() {
  debateConfigMode = !debateConfigMode;
  const panel = document.getElementById('debate-panel');
  const btn = document.getElementById('mbtn-debate');
  if (debateConfigMode) {
    panel.style.display = 'block';
    btn.classList.add('active');
    inputEl.placeholder = '输入辩论主题...';
    // 关闭@模式
    allMode = false;
    activeRoles.length = 0;
    ['太极','黑丝','白纱'].forEach(r => {
      document.getElementById('mbtn-' + r).classList.remove('active');
      document.getElementById('mbtn-' + r).textContent = '@' + r;
    });
    document.getElementById('mbtn-All').classList.remove('active');
    document.getElementById('mbtn-All').textContent = '@All';
  } else {
    panel.style.display = 'none';
    btn.classList.remove('active');
    inputEl.placeholder = '输入消息...';
  }
  inputEl.focus();
}

function startDebate() {
  const topic = inputEl.value.trim();
  if (!topic) return;
  const participants = [];
  ['太极','黑丝','白纱'].forEach(r => {
    if (document.getElementById('dp-' + r).checked) participants.push(r);
  });
  if (participants.length < 2) {
    alert('至少选两个参与者');
    return;
  }
  const maxRounds = parseInt(document.getElementById('debate-rounds-select').value);
  socket.emit('start_debate', {topic, participants, max_rounds: maxRounds});
  inputEl.value = '';
  // 关闭配置面板
  debateConfigMode = false;
  document.getElementById('debate-panel').style.display = 'none';
  document.getElementById('mbtn-debate').classList.remove('active');
}

function debateInterject() {
  const text = inputEl.value.trim();
  if (!text) return;
  socket.emit('debate_interject', {text});
  inputEl.value = '';
  inputEl.style.height = 'auto';
}

function stopDebate() {
  socket.emit('stop_debate', {});
}

socket.on('debate_status', (data) => {
  const bar = document.getElementById('debate-bar');
  const mentionBar = document.getElementById('mention-bar');
  if (data.active) {
    debateActive = true;
    bar.classList.add('active');
    document.getElementById('debate-round').textContent = data.round;
    document.getElementById('debate-max').textContent = data.max;
    inputEl.placeholder = '输入插话（可选）...';
    // 隐藏@按钮，只留对线按钮
    mentionBar.style.display = 'none';
  } else {
    debateActive = false;
    bar.classList.remove('active');
    inputEl.placeholder = '输入消息...';
    mentionBar.style.display = 'flex';
  }
});

// 初始化
loadHistory();
inputEl.focus();
</script>
</body>
</html>"""

# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    print(f"通讯部群聊系统启动中...")
    print(f"  数据库: {DB_PATH}")
    print(f"  端口: {PORT}")
    print(f"  角色: {', '.join(ROLES.keys())}")
    print()

    # 确保 reactions 字段存在
    ensure_reactions_column()

    # 启动 worker 线程
    worker = threading.Thread(target=message_worker, args=(socketio,), daemon=True)
    worker.start()
    print("  Worker 线程就绪（串行处理）")

    # 启动服务
    print(f"\n✅ 通讯部就绪: http://localhost:{PORT}")
    print(f"   Tailscale: http://echo:{PORT}")
    print()
    socketio.run(app, host=HOST, port=PORT, debug=False, allow_unsafe_werkzeug=True)
