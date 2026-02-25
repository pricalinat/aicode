#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/rrp/Documents/aicode"
cd "$REPO_DIR"

LOG="logs/iterate_supply_kg_100_$(date +%Y%m%d_%H%M%S).log"
PROMPT_FILE="/tmp/claude_supply_round_prompt.txt"

echo "[start] $(date)" | tee -a "$LOG"

START_ROUND="${START_ROUND:-1}"
END_ROUND="${END_ROUND:-100}"

for i in $(seq "$START_ROUND" "$END_ROUND"); do
  echo "[round $i] ===== $(date) =====" | tee -a "$LOG"

  cat > "$PROMPT_FILE" <<EOF
You are continuing iterative development on this repository toward the final goal: build a robust e-commerce + mini-program supply knowledge graph platform.

Round: $i / 100

Rules:
- Make one meaningful, production-oriented improvement this round.
- Prioritize runnable code and measurable progress over docs.
- If blocked on direction, consult and implement ideas inspired by strong papers/systems (e.g., AliCoCo/AliCoCo2 style concepts, industrial KG best practices), then convert them into concrete code or tests.
- Keep backward compatibility for existing arXiv features.
- After edits, run relevant tests (at least targeted ones).
- Output a concise summary: changed files, why it matters, run commands, test results, and next candidate step.

Focus areas (pick highest impact not yet done):
- KG schema quality & constraints
- ingestion for product/service/procedure/intent/slot
- entity normalization & dedup
- relation confidence scoring
- graph validation rules
- retrieval/query APIs over KG
- evaluation metrics and benchmark scripts
- adapter for mini-program structured inputs
- risk/policy tagging pipeline
- incremental update pipeline
- CI/test hardening for KG path
EOF

  set +e
  # YOLO mode enabled by user preference: always run with dangerously-skip-permissions.
  CLAUDE_OUT=$(claude -p --permission-mode dontAsk --dangerously-skip-permissions --output-format text "$(cat "$PROMPT_FILE")" 2>&1)
  CLAUDE_RC=$?
  echo "$CLAUDE_OUT" | tee -a "$LOG"
  set -e

  if [[ $CLAUDE_RC -ne 0 ]]; then
    echo "[round $i] claude exited with code $CLAUDE_RC" | tee -a "$LOG"
  fi

  # Ensure isolated test env with required deps
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
    git commit -m "iter: supply kg round $i"
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
