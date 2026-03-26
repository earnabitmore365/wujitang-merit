#!/bin/bash
# 通讯部 — Claude Code 多实例 Web 终端
# 用法：
#   bash ~/.claude/scripts/comm_hub.sh start   # 启动所有实例
#   bash ~/.claude/scripts/comm_hub.sh stop    # 停止所有实例
#   bash ~/.claude/scripts/comm_hub.sh status  # 查看状态

TAILSCALE_IP="100.108.158.57"
DASHBOARD_PORT=8080
PIDFILE="/tmp/comm_hub.pids"
COMM_PASS_FILE="$HOME/.claude/.comm_pass"

# 读取认证密码
if [ -f "$COMM_PASS_FILE" ]; then
    COMM_PASS=$(cat "$COMM_PASS_FILE")
    CRED_ARG="-c boss:$COMM_PASS"
else
    echo "⚠️  密码文件不存在: $COMM_PASS_FILE（无认证启动）"
    CRED_ARG=""
fi

# 实例配置：名称 | 端口 | 工作目录 | 模型参数
declare -a INSTANCES=(
    "太极|8081|$HOME|--model opus"
    "黑丝|8082|$HOME/project/auto-trading|--model opus"
    "白纱|8083|$HOME/project/auto-trading|--model sonnet"
)

start_instance() {
    local name="$1" port="$2" workdir="$3" model_arg="$4"

    if lsof -i :"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "⏭️  $name (端口 $port) 已在运行"
        return
    fi

    # ttyd 启动 claude code，-W 允许写入，-t 设置标题，-c 认证
    nohup ttyd -p "$port" -W \
        $CRED_ARG \
        -t titleFixed="$name" \
        -t fontSize=14 \
        bash -c "cd '$workdir' && claude $model_arg" \
        > "/tmp/comm_hub_${name}.log" 2>&1 &

    local pid=$!
    echo "$name:$pid:$port" >> "$PIDFILE"
    echo "✅ $name 已启动 → http://$TAILSCALE_IP:$port (PID $pid)"
}

start_dashboard() {
    if lsof -i :"$DASHBOARD_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "⏭️  看板 (端口 $DASHBOARD_PORT) 已在运行"
        return
    fi

    local html_dir="/tmp/comm_hub_dashboard"
    mkdir -p "$html_dir"

    cat > "$html_dir/index.html" << 'HTMLEOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>通讯部</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0d1117; color: #c9d1d9; font-family: -apple-system, system-ui, sans-serif; height: 100vh; display: flex; flex-direction: column; }
        .header { background: #161b22; padding: 8px 16px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #30363d; flex-shrink: 0; }
        .header h1 { font-size: 16px; font-weight: 600; }
        .tabs { display: flex; gap: 4px; }
        .tab { padding: 6px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; background: #21262d; border: 1px solid #30363d; color: #8b949e; transition: all 0.2s; }
        .tab.active { background: #1f6feb; border-color: #1f6feb; color: #fff; }
        .tab:hover:not(.active) { background: #30363d; color: #c9d1d9; }
        .status { margin-left: auto; font-size: 12px; color: #8b949e; }
        .container { flex: 1; display: flex; position: relative; }
        .panel { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: none; }
        .panel.active { display: block; }
        .split-view { display: flex; width: 100%; height: 100%; }
        .split-view iframe { flex: 1; border: none; border-right: 1px solid #30363d; }
        .split-view iframe:last-child { border-right: none; }
        iframe { width: 100%; height: 100%; border: none; }
        .status-bar { display: flex; gap: 12px; align-items: center; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
        .status-dot.online { background: #3fb950; }
        .status-dot.offline { background: #f85149; }
        .status-item { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #8b949e; }
        @media (max-width: 768px) {
            .split-view { flex-direction: column; }
            .split-view iframe { border-right: none; border-bottom: 1px solid #30363d; min-height: 33%; }
            .split-view iframe:last-child { border-bottom: none; }
            .header { flex-wrap: wrap; }
            .tabs { flex-wrap: wrap; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>通讯部</h1>
        <div class="tabs">
            <div class="tab active" onclick="show('taiji')">太极</div>
            <div class="tab" onclick="show('heisi')">黑丝</div>
            <div class="tab" onclick="show('baisha')">白纱</div>
            <div class="tab" onclick="show('all')">全部</div>
        </div>
        <div class="status-bar" id="status-bar">
            <div class="status-item"><span class="status-dot" id="dot-taiji"></span>太极</div>
            <div class="status-item"><span class="status-dot" id="dot-heisi"></span>黑丝</div>
            <div class="status-item"><span class="status-dot" id="dot-baisha"></span>白纱</div>
        </div>
    </div>
    <div class="container">
        <div class="panel active" id="panel-taiji">
            <iframe src="PROTO://HOST:8081"></iframe>
        </div>
        <div class="panel" id="panel-heisi">
            <iframe src="PROTO://HOST:8082"></iframe>
        </div>
        <div class="panel" id="panel-baisha">
            <iframe src="PROTO://HOST:8083"></iframe>
        </div>
        <div class="panel" id="panel-all">
            <div class="split-view">
                <iframe src="PROTO://HOST:8081"></iframe>
                <iframe src="PROTO://HOST:8082"></iframe>
                <iframe src="PROTO://HOST:8083"></iframe>
            </div>
        </div>
    </div>
    <script>
        // 动态替换HOST为当前访问的hostname
        document.querySelectorAll('iframe').forEach(f => {
            f.src = f.src.replace(/PROTO:\/\/HOST/g, location.protocol + '//' + location.hostname);
        });

        function show(id) {
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById('panel-' + id).classList.add('active');
            event.target.classList.add('active');
        }

        // 状态检测
        const ports = { taiji: 8081, heisi: 8082, baisha: 8083 };
        function checkStatus() {
            Object.entries(ports).forEach(([name, port]) => {
                const dot = document.getElementById('dot-' + name);
                fetch(location.protocol + '//' + location.hostname + ':' + port, { mode: 'no-cors' })
                    .then(() => { dot.className = 'status-dot online'; })
                    .catch(() => { dot.className = 'status-dot offline'; });
            });
        }
        checkStatus();
        setInterval(checkStatus, 30000);
    </script>
</body>
</html>
HTMLEOF

    # 用python http server托管看板页面
    nohup python3 -m http.server "$DASHBOARD_PORT" -d "$html_dir" \
        > /tmp/comm_hub_dashboard.log 2>&1 &
    local pid=$!
    echo "dashboard:$pid:$DASHBOARD_PORT" >> "$PIDFILE"
    echo "✅ 看板已启动 → http://$TAILSCALE_IP:$DASHBOARD_PORT (PID $pid)"
}

stop_all() {
    if [ -f "$PIDFILE" ]; then
        while IFS=: read -r name pid port; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null
                echo "🛑 $name (PID $pid, 端口 $port) 已停止"
            fi
        done < "$PIDFILE"
        rm -f "$PIDFILE"
    fi
    # 兜底清理
    pkill -f "ttyd.*claude" 2>/dev/null
    pkill -f "http.server.*$DASHBOARD_PORT" 2>/dev/null
    echo "✅ 全部停止"
}

show_status() {
    echo "=== 通讯部状态 ==="
    for inst in "${INSTANCES[@]}"; do
        IFS='|' read -r name port workdir model <<< "$inst"
        if lsof -i :"$port" -sTCP:LISTEN >/dev/null 2>&1; then
            local pid=$(lsof -i :"$port" -sTCP:LISTEN -t 2>/dev/null | head -1)
            echo "✅ $name | 端口 $port | PID $pid | http://$TAILSCALE_IP:$port"
        else
            echo "❌ $name | 端口 $port | 未运行"
        fi
    done
    if lsof -i :"$DASHBOARD_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "✅ 看板 | 端口 $DASHBOARD_PORT | http://$TAILSCALE_IP:$DASHBOARD_PORT"
    else
        echo "❌ 看板 | 端口 $DASHBOARD_PORT | 未运行"
    fi
}

case "${1:-status}" in
    start)
        echo "🚀 启动通讯部..."
        for inst in "${INSTANCES[@]}"; do
            IFS='|' read -r name port workdir model <<< "$inst"
            start_instance "$name" "$port" "$workdir" "$model"
        done
        start_dashboard
        echo ""
        echo "📱 手机访问: http://$TAILSCALE_IP:$DASHBOARD_PORT"
        ;;
    stop)
        stop_all
        ;;
    status)
        show_status
        ;;
    *)
        echo "用法: $0 {start|stop|status}"
        ;;
esac
