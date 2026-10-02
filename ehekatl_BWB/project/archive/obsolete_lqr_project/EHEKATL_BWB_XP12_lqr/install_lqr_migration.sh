#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12}"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$ROOT/lqr" "$ROOT/logs" "$ROOT/configs"

cp "$SRC_DIR/lqr/LQR.py" "$ROOT/lqr/LQR.py"
cp "$SRC_DIR/lqr/run_lqr_xp12.py" "$ROOT/lqr/run_lqr_xp12.py"
cp "$SRC_DIR/lqr/health_check_xpc.py" "$ROOT/lqr/health_check_xpc.py"
cp "$SRC_DIR/lqr/README.md" "$ROOT/lqr/README.md"
chmod +x "$ROOT/lqr/run_lqr_xp12.py" "$ROOT/lqr/health_check_xpc.py"

RUNNERS="$ROOT/configs/EHEKATL_XP12_RUNNERS.txt"
touch "$RUNNERS"
if grep -q "EHEKATL BWB LQR X-Plane 12 runners" "$RUNNERS"; then
  echo "Runner lines already present in $RUNNERS"
else
  cat "$SRC_DIR/configs/EHEKATL_XP12_RUNNERS_LQR_APPEND.txt" >> "$RUNNERS"
  echo "Appended LQR runner lines to $RUNNERS"
fi

echo "Installed LQR files into $ROOT/lqr"
echo "Backstepping/PID files were not modified."
