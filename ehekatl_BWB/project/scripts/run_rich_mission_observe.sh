#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12"
cd "$ROOT"
REGIME="${RICH_REGIME:-R3}"
STAMP="$(date +%Y%m%d_%H%M%S)"
exec backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B scripts/run_rich_mission_observe_xp12.py \
  --regime "$REGIME" \
  --test-id "rich_${REGIME}_observe_01" \
  --aircraft-config EHEKATL_BWB_G33_acf_v1_XP12.4.3-r2_scale_14lb \
  --payload no_payload_stations \
  --fuel 0.0lb_intentional_scale_model \
  --weather manual_clear_47F_29.92inHg_no_layers \
  --failures none \
  --out "logs/rich_${REGIME}_observe_01_${STAMP}.csv"
