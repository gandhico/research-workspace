#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12";cd "$ROOT";STAMP="$(date +%Y%m%d_%H%M%S)";OUT="logs/direct_deepc_${STAMP}.csv"
backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B deepc/run_deepc_direct_xp12.py --engage --disturbance --duration 30 --io-hz 35 --fallback-hz 10 --out "$OUT"
if [[ ! -s "$OUT" ]]; then
  echo "DeePC direct test ended before logging (normally a start-gate block); no analyzer run."
  exit 2
fi
backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B scripts/analyze_rich_r3_roll_deepc_pilot.py --require-engaged "$OUT"
