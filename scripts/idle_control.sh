#!/bin/bash
# Control the idle monitor
# Usage: ./idle_control.sh stop|start

CMD=$1
CONTROL_FILE="/Users/rrp/Documents/aicode/logs/idle_monitor_control"

case "$CMD" in
    stop|停止|idle|空闲)
        echo "$CMD" > "$CONTROL_FILE"
        echo "Sent stop command"
        ;;
    start|resume)
        rm -f "$CONTROL_FILE"
        echo "Sent start command"
        ;;
    *)
        echo "Usage: $0 stop|start"
        ;;
esac
