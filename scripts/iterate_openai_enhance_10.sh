#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/rrp/Documents/aicode"
cd "$REPO_DIR"
mkdir -p logs scripts

LOG="logs/iterate_openai_enhance_10_$(date +%Y%m%d_%H%M%S).log"
PROMPT_FILE="/tmp/openai_enhance_round_prompt.txt"
START_ROUND="${START_ROUND:-1}"
END_ROUND="${END_ROUND:-10}"

echo "[start] $(date)" | tee -a "$LOG"

for i in $(seq "$START_ROUND" "$END_ROUND"); do
  echo "[round $i] ===== $(date) =====" | tee -a "$LOG"

  cat > "$PROMPT_FILE" <<EOF
You are implementing V2 capabilities in /Users/rrp/Documents/aicode.
Round: $i / 10

Assumption: OpenAI API large models are available.
Goal: fully implement and iterate capabilities for an AI-native supply KG + test analysis platform.

Must prioritize these tracks (ship real code each round):
1) Multimodal true parsing layer (replace stubs): image/table/doc parsing adapters; normalize into unified chunks with source spans + confidence.
2) Repo/doc understanding agents: requirement->code trace, system analysis->test trace, change impact mapping.
3) Dual matching upgrade: recall + LLM rerank + explanation output; include safety/policy constraints.
4) Feedback loop upgrade: LLM feature distillation from behavior logs into structured features.
5) Evaluation upgrade: add LLM-judge-compatible rubric outputs + calibration hooks.
6) Cost/safety controls: model routing, caching, audit logs.

Engineering constraints:
- Keep existing functionality passing.
- Add/extend CLI commands for new capabilities where needed.
- Add/extend tests each round (target >= 8 meaningful tests per round or equivalent net increase over rounds).
- Update README succinctly for runnable commands.
- Commit + push every round if there are changes.
- If blocked, implement degraded but runnable fallback and clearly mark TODO boundaries.

Deliver in round summary:
- changed files
- why this round matters
- commands run
- test results
- next round target
EOF

  set +e
  OUT=$(claude -p --permission-mode dontAsk --dangerously-skip-permissions --output-format text "$(cat "$PROMPT_FILE")" 2>&1)
  RC=$?
  set -e
  echo "$OUT" | tee -a "$LOG"

  if [[ $RC -ne 0 ]]; then
    echo "[round $i] claude_rc=$RC" | tee -a "$LOG"
  fi

  if [[ ! -d .venv ]]; then
    python3 -m venv .venv
  fi

  set +e
  .venv/bin/python -m pip install -q -U pip loguru >/dev/null 2>&1
  PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v 2>&1 | tee -a "$LOG"
  TEST_RC=${PIPESTATUS[0]}
  set -e
  echo "[round $i] test_rc=$TEST_RC" | tee -a "$LOG"

  if [[ -n "$(git status --porcelain)" ]]; then
    git add -A
    git commit -m "iter: openai capability enhancement round $i"
    set +e
    git push origin main 2>&1 | tee -a "$LOG"
    PUSH_RC=${PIPESTATUS[0]}
    set -e
    echo "[round $i] push_rc=$PUSH_RC" | tee -a "$LOG"
  else
    echo "[round $i] no file changes; skip commit/push" | tee -a "$LOG"
  fi
done

echo "[done] $(date)" | tee -a "$LOG"
