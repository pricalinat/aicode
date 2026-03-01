#!/bin/bash
set -euo pipefail

# 调度策略：优先 Claude，失败切 Codex；每30分钟探测 Claude 恢复后立即切回
ROOT="/Users/rrp/Documents/aicode"
LOG_DIR="$ROOT/logs"
STATE_FILE="$LOG_DIR/auto_scheduler_state.json"
CONTROL_FILE="$LOG_DIR/idle_monitor_control"
SCHED_LOG="$LOG_DIR/auto_scheduler.log"
ITER_LOG="$ROOT/iteration_log.md"

API_URL="https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains"
AUTH_TOKEN="${MINIMAX_TOKEN:-sk-cp-mjBJmxDHEHvM8jYoUnpGfUS0bJLcS6Lc6lbIXseyS7j59dEEiy3iFV1R8SiwSuF23qS7H8_Ij8xKQuteDaNefFRlrPE4lhIUj5akR0RhUTcwDLH2DkEqQR0}"

CHECK_INTERVAL_SEC=300      # 每5分钟
CLAUDE_RECHECK_SEC=1800     # 每30分钟
WINDOW_SAMPLES=24           # 2小时窗口（24*5min）
LOW_USAGE_THRESHOLD=100     # 2小时增量 < 100 触发

mkdir -p "$LOG_DIR"

log() {
  echo "$(date '+%F %T') $*" | tee -a "$SCHED_LOG"
}

ensure_state() {
  if [ ! -f "$STATE_FILE" ]; then
    cat > "$STATE_FILE" <<JSON
{"engine":"claude","last_claude_check":0,"samples":[],"status":"running"}
JSON
  fi
}

get_state() {
  python3 - <<PY
import json
s=json.load(open('$STATE_FILE'))
print(s.get('$1'))
PY
}

set_state_py() {
  python3 - <<PY
import json
p='$STATE_FILE'
s=json.load(open(p))
$1
json.dump(s, open(p,'w'))
PY
}

is_paused() {
  if [ -f "$CONTROL_FILE" ]; then
    cmd=$(cat "$CONTROL_FILE" 2>/dev/null || true)
    case "$cmd" in
      stop|停止|idle|空闲)
        set_state_py "s['status']='paused'"
        log "进入等待状态（收到控制命令: $cmd）"
        return 0
        ;;
      start|resume|继续)
        set_state_py "s['status']='running'"
        rm -f "$CONTROL_FILE"
        log "恢复运行（收到控制命令: $cmd）"
        return 1
        ;;
    esac
  fi
  [ "$(get_state status)" = "paused" ]
}

fetch_usage() {
  local resp
  resp=$(curl -s --location "$API_URL" \
    --header "Authorization: Bearer $AUTH_TOKEN" \
    --header 'Content-Type: application/json')
  python3 - <<PY
import json,sys
try:
  d=json.loads('''$resp''')
  # 取 M2.5 使用量（第三项）
  print(d['model_remains'][2]['current_interval_usage_count'])
except Exception:
  print('-1')
PY
}

append_sample() {
  local usage="$1"
  local ts
  ts=$(date +%s)
  python3 - <<PY
import json
p='$STATE_FILE'
s=json.load(open(p))
a=s.get('samples',[])
a.append({'ts':$ts,'usage':$usage})
s['samples']=a[-$WINDOW_SAMPLES:]
json.dump(s, open(p,'w'))
PY
}

usage_increase_2h() {
  python3 - <<PY
import json
s=json.load(open('$STATE_FILE'))
a=s.get('samples',[])
if len(a)<2:
  print('999999')
else:
  # 处理区间重置：负增量按0计
  inc=0
  for i in range(1,len(a)):
    d=a[i]['usage']-a[i-1]['usage']
    inc += d if d>0 else 0
  print(inc)
PY
}

check_claude_available() {
  # 轻量探活：可调用即视为可用，配额耗尽/限流会返回非0或错误文本
  local out rc
  set +e
  out=$(timeout 45 claude -p "Reply exactly: OK" --output-format text 2>&1)
  rc=$?
  set -e
  if [ $rc -ne 0 ]; then
    return 1
  fi
  echo "$out" | grep -Eqi "quota|rate limit|overloaded|insufficient|exhaust" && return 1
  echo "$out" | grep -q "OK"
}

run_iteration() {
  local engine="$1"
  local ts
  ts=$(date '+%F %T')
  log "触发增量迭代，执行引擎: $engine"

  local prompt
  prompt="你在仓库 $ROOT。请做一个明确的小增量（功能/修复/测试/文档其一），要求：1) 修改代码或文档；2) 运行相关测试；3) git add/commit；4) 输出提交hash和变更摘要。"

  if [ "$engine" = "claude" ]; then
    set +e
    claude -p "$prompt" --output-format text >> "$SCHED_LOG" 2>&1
    local rc=$?
    set -e
    if [ $rc -ne 0 ]; then
      log "Claude 执行失败，切换到 Codex"
      set_state_py "s['engine']='codex'"
      return 1
    fi
  else
    set +e
    codex exec "$prompt" >> "$SCHED_LOG" 2>&1
    local rc=$?
    set -e
    if [ $rc -ne 0 ]; then
      log "Codex 执行失败（保留 Codex，下一轮重试）"
      return 1
    fi
  fi

  echo "- [$ts] auto-iteration via $engine" >> "$ITER_LOG"
  log "增量迭代完成: $engine"
  return 0
}

main_loop() {
  ensure_state
  log "自动调度器启动（优先 Claude，失败切 Codex，30 分钟回切检查）"

  while true; do
    if is_paused; then
      sleep 60
      continue
    fi

    usage=$(fetch_usage)
    if [ "$usage" = "-1" ]; then
      log "API 使用量获取失败，5分钟后重试"
      sleep "$CHECK_INTERVAL_SEC"
      continue
    fi

    append_sample "$usage"
    inc=$(usage_increase_2h)
    log "2小时累计使用增量: $inc（阈值<$LOW_USAGE_THRESHOLD 触发）"

    if [ "$inc" -lt "$LOW_USAGE_THRESHOLD" ]; then
      engine=$(get_state engine)

      if [ "$engine" = "claude" ]; then
        if check_claude_available; then
          run_iteration claude || true
        else
          log "Claude 不可用/配额不足，切换 Codex"
          set_state_py "s['engine']='codex'; s['last_claude_check']=0"
          run_iteration codex || true
        fi
      else
        now=$(date +%s)
        last=$(get_state last_claude_check)
        delta=$((now-last))
        if [ "$delta" -ge "$CLAUDE_RECHECK_SEC" ]; then
          set_state_py "s['last_claude_check']=$now"
          if check_claude_available; then
            log "Claude 已恢复，立即切回 Claude"
            set_state_py "s['engine']='claude'"
            run_iteration claude || true
          else
            log "Claude 仍不可用，继续 Codex"
            run_iteration codex || true
          fi
        else
          run_iteration codex || true
        fi
      fi
    fi

    sleep "$CHECK_INTERVAL_SEC"
  done
}

main_loop
