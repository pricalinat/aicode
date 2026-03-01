#!/bin/bash
# Monitor MiniMax API usage

API_URL="https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains"
AUTH_TOKEN="sk-cp-mjBJmxDHEHvM8jYoUnpGfUS0bJLcS6Lc6lbIXseyS7j59dEEiy3iFV1R8SiwSuF23qS7H8_Ij8xKQuteDaNefFRlrPE4lhIUj5akR0RhUTcwDLH2DkEqQR0"

LOG_FILE="/Users/rrp/Documents/aicode/logs/api_usage.log"
STATE_FILE="/Users/rrp/Documents/aicode/logs/api_usage_state.json"

mkdir -p "$(dirname "$LOG_FILE")"

# Get current usage
response=$(curl -s --location "$API_URL" \
  --header "Authorization: Bearer $AUTH_TOKEN" \
  --header 'Content-Type: application/json')

echo "$(date '+%Y-%m-%d %H:%M:%S') - $response" >> "$LOG_FILE"

# Extract usage count for M2.5 (3rd model in the list)
usage=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['model_remains'][2]['current_interval_usage_count'])" 2>/dev/null)

if [ -z "$usage" ]; then
    echo "Failed to parse usage"
    exit 1
fi

echo "Current M2.5 usage: $usage"

# Load previous state
if [ -f "$STATE_FILE" ]; then
    prev_usage=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['usage'])" 2>/dev/null)
    prev_time=$(python3 -c "import json; print(json.load(open('$STATE_FILE'))['time'])" 2>/dev/null)
    echo "Previous usage: $prev_usage at $prev_time"
else
    prev_usage=""
fi

# Save current state
echo "{\"usage\":$usage,\"time\":\"$(date '+%Y-%m-%d %H:%M:%S')\"}" > "$STATE_FILE"

# Check if we need to trigger iteration
if [ -n "$prev_usage" ]; then
    increase=$((usage - prev_usage))
    echo "Usage increase since last check: $increase"
fi
