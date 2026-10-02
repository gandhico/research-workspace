#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12"; cd "$ROOT"
STAGE5_RUN_LABEL="pitch_rate_zero_excitation_baseline" STAGE5_DISTURBANCE_AMPLITUDE=0 \
  bash scripts/run_stage5_pitch_rate_pilot.sh
