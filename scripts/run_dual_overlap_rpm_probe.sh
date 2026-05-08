#!/usr/bin/env bash
# Run two parallel rpm_minute_window_probe (overlap) against NEWAPI_BASE_URL.
# Usage (on host with repo + .venv):
#   export NEWAPI_BASE_URL="https://api.mixroute.ai/v1"
#   export NEWAPI_API_KEY="..."
#   ./scripts/run_dual_overlap_rpm_probe.sh claude-sonnet-4-6
#
# Logs: /tmp/rpm_dual_<model_slug>_<UTC_TS>_{A,B}.out
# Merge: python scripts/merge_dual_rpm_probe_window.py --log-a ... --log-b ...

set -euo pipefail

MODEL="${1:?usage: $0 <model_id>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${NEWAPI_API_KEY:-}" && -z "${OPENAI_API_KEY:-}" ]]; then
  echo "error: set NEWAPI_API_KEY or OPENAI_API_KEY" >&2
  exit 2
fi

slug="$(echo "$MODEL" | tr '/.' '__')"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUTA="/tmp/rpm_dual_${slug}_${TS}_A.out"
OUTB="/tmp/rpm_dual_${slug}_${TS}_B.out"

export PYTHONUNBUFFERED=1

echo "MODEL=$MODEL TS=$TS"
echo "OUTA=$OUTA"
echo "OUTB=$OUTB"

run_one() {
  local out="$1"
  nohup .venv/bin/python scripts/rpm_minute_window_probe.py \
    --scheduler overlap \
    --payload minimal \
    --model "$MODEL" \
    --scale double \
    --start-concurrency 2048 \
    --max-concurrency 12000 \
    --ramp-interval-sec 1 \
    --max-requests 2048 \
    >"$out" 2>&1 &
  echo "pid=$! -> $out"
}

run_one "$OUTA"
run_one "$OUTB"
wait
echo "done. merge with (use --log-a = file that contains anchor_t_start from FIRST failure summary):"
echo "  .venv/bin/python scripts/merge_dual_rpm_probe_window.py --log-a $OUTA --log-b $OUTB"
echo "  # swap A/B if only the other process printed first_failure / anchor_t_start"
