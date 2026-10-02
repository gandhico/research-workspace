#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12";cd "$ROOT";STAMP="$(date +%Y%m%d_%H%M%S)"
exec backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B scripts/diagnose_rich_mission_datarefs.py --duration 10 --hz 10 --out "logs/rich_dataref_observe_${STAMP}.csv"
