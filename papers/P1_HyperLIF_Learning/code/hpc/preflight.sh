#!/bin/bash
# Cheap end-to-end sanity check BEFORE submitting the full array. Run interactively (ideally on a
# GPU node: `srun --gres=gpu:1 --pty bash hpc/preflight.sh`).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
source "${HERE}/paths.sh"
cd "$HLL_ROOT"
hll_activate

echo "== paths =="
printf '  %s\n' "ROOT=$HLL_ROOT" "CACHE=$HLL_CACHE" "RESULTS=$HLL_RESULTS" "LOGS=$HLL_LOGS" "DATA=$HLL_DATA"
hll_mkdirs

echo "== read-only source HDF5 =="
ls -lh "$HLL_DATA"/*.h5 2>/dev/null || echo "  (none found in $HLL_DATA)"

echo "== discovered caches + job count =="
python hpc/grid.py --list
N=$(python hpc/grid.py --count)
if [ "$N" -eq 0 ]; then
  echo "NO caches in $HLL_CACHE — produce them first (see hpc/DATA.md). Aborting preflight."
  exit 1
fi

echo "== parity gate =="
for s in run_parity_snntorch.py run_parity.py; do
  [ -f "hpc/scripts/${s}" ] && python "hpc/scripts/${s}" || echo "WARN: hpc/scripts/${s} skipped"
done

echo "== one real job (index 0, 2 epochs) — validates the full pipeline on a GPU =="
python hpc/train_hpc.py $(python hpc/grid.py --index 0) --epochs 2

echo
echo "Preflight OK. Submit the full array with:  sbatch --array=0-$((N-1))%16 hpc/run_array.slurm"
