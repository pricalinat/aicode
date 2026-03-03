#!/bin/bash

# MiniMax API Key
API_KEY="sk-cp-mjBJmxDHEHvM8jYoUnpGfUS0bJLcS6Lc6lbIXseyS7j59dEEiy3iFV1R8SiwSuF23qS7H8_Ij8xKQuteDaNefFRlrPE4lhIUj5akR0RhUTcwDLH2DkEqQR0"

# Log file
LOG_FILE="/Users/rrp/.openclaw/workspace/monitoring/minimax_usage.log"

echo "Starting MiniMax quota monitoring..."
echo "Timestamp,Total,Used,Remaining,Usage%,RemainingTime" > "$LOG_FILE"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    RESPONSE=$(curl -s --location 'https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains' \
        --header "Authorization: Bearer $API_KEY" \
        --header 'Content-Type: application/json' 2>/dev/null)
    
    # Parse JSON
    TOTAL=$(echo "$RESPONSE" | grep -o '"current_interval_total_count":[0-9]*' | head -1 | grep -o '[0-9]*')
    USED=$(echo "$RESPONSE" | grep -o '"current_interval_usage_count":[0-9]*' | head -1 | grep -o '[0-9]*')
    REMAINS=$(echo "$RESPONSE" | grep -o '"remains":[0-9]*' | head -1 | grep -o '[0-9]*')
    REMAINS_TIME=$(echo "$RESPONSE" | grep -o '"remains_time":[0-9]*' | head -1 | grep -o '[0-9]*')
    
    # Calculate percentage
    if [ -n "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
        PERCENT=$((USED * 100 / TOTAL))
    else
        PERCENT=0
    fi
    
    # Format remaining time
    if [ -n "$REMAINS_TIME" ]; then
        MINS=$((REMAINS_TIME / 60))
    else
        MINS=0
    fi
    
    echo "$TIMESTAMP,$TOTAL,$USED,$((TOTAL - USED)),$PERCENT,$MINS mins" >> "$LOG_FILE"
    
    # Print current status
    echo "[$TIMESTAMP] MiniMax: ${USED}/${TOTAL} (${PERCENT}%) | Remaining: $((TOTAL - USED)) | Time left: ${MINS}m"
    
    # Sleep for 1 minute
    sleep 60
done
