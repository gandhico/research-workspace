#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12";cd "$ROOT";STAMP="$(date +%Y%m%d_%H%M%S)";RUN="${RICH_ROLL_RUN:-training_01}"
exec backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B backstepping/run_backstepping_baseline_xp12.py \
  --engage --override-roll-axis --override-pitch-axis --trim-relative-controls --duration 60 --hz 10 --rate-units deg_s --routing legacy --pitch-sp 1.3 --roll-sp 0 \
  --K-roll 0.001 --K-pitch 0.001 --Ku-roll 33 --Ku-pitch 39 --tau-roll 0.03 --tau-pitch 0.03 --clip 0 --throttle -998 \
  --target-altitude-m 1700 --altitude-tolerance-m 100 --target-ias-kts 39 --ias-tolerance-kts 2 --max-start-pitch-error-deg 3.7 --max-start-roll-error-deg 5 --max-start-rate-deg-s 2 --target-throttle 0.0235 --throttle-tolerance 0.02 \
  --recovery-max-abs-pitch-deg 10 --recovery-max-abs-roll-deg 10 --recovery-max-abs-rate-deg-s 20 --recovery-total-command-limit 0.5 \
  --recovery-axis none --identification-axis roll --identification-start-s 10 --identification-duration-s 40 --identification-ramp-s 2 --identification-amplitude 0.0002 \
  --identification-frequencies-hz 0.10,0.20,0.35,0.55,0.80,1.10 --identification-phases-rad 0.0,1.256637,2.513274,3.769911,5.026548,0.628319 \
  --aircraft-config EHEKATL_BWB_G33_acf_v1_XP12.4.3-r2_scale_14lb --payload no_payload_stations --fuel 0.0lb_intentional_scale_model --weather manual_clear_47F_29.92inHg_no_layers --failures none \
  --test-id "rich_R3_roll_${RUN}_${STAMP}" --out "logs/rich_R3_roll_${RUN}_${STAMP}.csv"
