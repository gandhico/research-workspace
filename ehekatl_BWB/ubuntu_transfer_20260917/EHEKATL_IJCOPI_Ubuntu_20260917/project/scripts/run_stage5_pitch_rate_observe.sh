#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12"; cd "$ROOT"
STAMP="$(date +%Y%m%d_%H%M%S)"
exec backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B lqr/run_stage5_rate_lqr_xp12.py \
  --duration 30 --hz 10 --pulse-start-s 10 --pulse-duration-s 0.5 --pulse-amplitude-deg-s 0 \
  --disturbance-pulse-amplitude 0.0002 \
  --test-id "stage5_pitch_rate_observe_${STAMP}" --out "logs/stage5_pitch_rate_observe_${STAMP}.csv"
