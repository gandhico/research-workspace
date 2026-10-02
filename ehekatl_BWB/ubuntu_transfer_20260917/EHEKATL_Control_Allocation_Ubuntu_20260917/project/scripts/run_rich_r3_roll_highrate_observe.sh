#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12";cd "$ROOT";STAMP="$(date +%Y%m%d_%H%M%S)"
exec backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B scripts/run_rich_r3_roll_highrate_observe_xp12.py --duration 30 --hz 35 --design configs/rich_R3_roll_highrate_design.json --out "logs/rich_R3_roll_highrate_waveform_observe_${STAMP}.csv"
