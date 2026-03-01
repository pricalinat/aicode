#!/bin/bash
# Background monitor for idle state and API usage

CHECK_INTERVAL=300  # 5 minutes
IDLE_THRESHOLD=100  # <100 increase in 2 hours = 24 checks * <100 = trigger

LOG_FILE="/Users/rrp/Documents/aicode/logs/idle_monitor.log"
API_LOG="/Users/rrp/Documents/aicode/logs/api_usage.log"
STATE_FILE="/Users/rrp/Documents/aicode/logs/idle_state.json"

# Control file
CONTROL_FILE="/Users/rrp/Documents/aicode/logs/idle_monitor_control"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

check_control() {
    if [ -f "$CONTROL_FILE" ]; then
        cmd=$(cat "$CONTROL_FILE")
        if [ "$cmd" = "stop" ] || [ "$cmd" = "停止" ] || [ "$cmd" = "idle" ] || [ "$cmd" = "空闲" ]; then
            log "STOP command received - entering wait mode"
            rm "$CONTROL_FILE"
            return 1
        fi
    fi
    return 0
}

log "Starting idle monitor..."

while true; do
    # Check for stop command
    if ! check_control; then
        log "Waiting for next command..."
        sleep 60
        continue
    fi
    
    # Check API usage
    /Users/rrp/Documents/aicode/scripts/monitor_api_usage.sh
    
    sleep $CHECK_INTERVAL
done
