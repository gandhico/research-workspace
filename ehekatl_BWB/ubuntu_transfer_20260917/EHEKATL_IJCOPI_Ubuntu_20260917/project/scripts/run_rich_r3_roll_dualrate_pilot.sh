#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12";cd "$ROOT";STAMP="$(date +%Y%m%d_%H%M%S)"
exec backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B scripts/run_rich_r3_roll_dualrate_xp12.py --engage --duration 30 --io-hz 35 --controller-hz 10 --out "logs/rich_R3_roll_dualrate_pilot_${STAMP}.csv"
