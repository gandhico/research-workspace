#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12";cd "$ROOT";STAMP="$(date +%Y%m%d_%H%M%S)";OUT="logs/direct_lqr_${STAMP}.csv"
backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B lqr/run_lqr_direct_xp12.py --engage --controller lqr --disturbance --duration 30 --io-hz 35 --fallback-hz 10 --out "$OUT"
if [[ ! -s "$OUT" ]]; then
  echo "LQR direct test ended before logging (normally a start-gate block); no analyzer run."
  exit 2
fi
backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B scripts/analyze_rich_r3_roll_matched_run.py --mode lqr --require-engaged "$OUT"
