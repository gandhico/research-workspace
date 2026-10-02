#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12"; cd "$ROOT"
STAMP="$(date +%Y%m%d_%H%M%S)"
RUN_LABEL="${STAGE5_RUN_LABEL:-pitch_rate_pilot}"
DISTURBANCE_AMPLITUDE="${STAGE5_DISTURBANCE_AMPLITUDE:-0.0002}"
exec backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B lqr/run_stage5_rate_lqr_xp12.py --engage \
  --duration 30 --hz 10 --pulse-start-s 10 --pulse-duration-s 0.5 --pulse-amplitude-deg-s 0 \
  --disturbance-pulse-amplitude "$DISTURBANCE_AMPLITUDE" \
  --test-id "stage5_${RUN_LABEL}_${STAMP}" --out "logs/stage5_${RUN_LABEL}_${STAMP}.csv"
