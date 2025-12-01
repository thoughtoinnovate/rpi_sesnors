#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$ROOT_DIR/logs"
PID_FILE="$RUN_DIR/api.pid"
LOG_FILE="$LOG_DIR/api.log"
PORT="${PORT:-9000}"
HOST="${HOST:-0.0.0.0}"

mkdir -p "$RUN_DIR" "$LOG_DIR"

is_running() {
    local pid="$1"
    if [[ -z "$pid" ]]; then
        return 1
    fi
    kill -0 "$pid" >/dev/null 2>&1
}

stop_api() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid="$(cat "$PID_FILE")"
        if is_running "$pid"; then
            echo "Stopping API server (PID $pid)..."
            kill "$pid" >/dev/null 2>&1 || true
            wait "$pid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
}

stop_scheduler() {
    if command -v curl >/dev/null 2>&1; then
        curl -fs -X POST "http://127.0.0.1:${PORT}/api/scheduler/stop" >/dev/null 2>&1 || true
    fi
    pkill -f "aqi.scheduler" >/dev/null 2>&1 || true
}

start_api() {
    if [[ -f "$PID_FILE" ]]; then
        local old_pid
        old_pid="$(cat "$PID_FILE")"
        if is_running "$old_pid"; then
            echo "API already running (PID $old_pid); restarting..."
            stop_api
        fi
    fi

    if command -v lsof >/dev/null 2>&1; then
        local conflict
        conflict="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN || true)"
        if [[ -n "$conflict" ]]; then
            echo "Port $PORT is already in use by PID(s): $conflict" >&2
            echo "Stop the conflicting process or set PORT=xxxx make start" >&2
            exit 1
        fi
    fi

    echo "Starting API server on ${HOST}:${PORT}..."
    nohup python3 "$ROOT_DIR/apis/aqi/server.py" --host "$HOST" --port "$PORT" \
        >>"$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" >"$PID_FILE"
    sleep 1
    if ! is_running "$pid"; then
        echo "API server failed to start. Check $LOG_FILE for details." >&2
        rm -f "$PID_FILE"
        exit 1
    fi
    echo "API server running (PID $pid). Logs: $LOG_FILE"
}

case "${1:-}" in
    start)
        start_api
        ;;
    stop)
        stop_scheduler
        stop_api
        ;;
    restart)
        stop_scheduler
        stop_api
        start_api
        ;;
    status)
        if [[ -f "$PID_FILE" ]] && is_running "$(cat "$PID_FILE")"; then
            echo "API running (PID $(cat "$PID_FILE")), listening on ${HOST}:${PORT}"
        else
            echo "API not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}" >&2
        exit 1
        ;;
esac
