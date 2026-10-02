#!/bin/bash
# One-time environment setup for HyperLIF_Learning on the HPC login node.
# Run from the project root:   bash hpc/setup_env.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
source "${HERE}/paths.sh"

# module load python/3.11 cuda/12.1      # <-- uncomment / edit for your cluster

echo "== creating scratch dirs =="
hll_mkdirs
echo "  cache:   $HLL_CACHE"
echo "  results: $HLL_RESULTS"
echo "  logs:    $HLL_LOGS"

echo "== creating venv at $HLL_VENV =="
python -m venv "$HLL_VENV"
source "${HLL_VENV}/bin/activate"
python -m pip install --upgrade pip

# GPU torch (match the cluster CUDA; cu121 shown). For a CPU-only login-node test use the cpu index.
python -m pip install torch --index-url https://download.pytorch.org/whl/cu121
python -m pip install snntorch tonic h5py numpy pyyaml

echo "== parity gate (must PASS before any benchmark) =="
PARITY_OK=1
for s in run_parity_snntorch.py run_parity.py; do
  if [ -f "${HLL_ROOT}/hpc/scripts/${s}" ]; then
    python "${HLL_ROOT}/hpc/scripts/${s}" || PARITY_OK=0
  else
    echo "WARN: ${HLL_ROOT}/hpc/scripts/${s} not found — vendor scripts/ under hpc/ to run the gate" >&2
    PARITY_OK=0
  fi
done

echo
if [ "$PARITY_OK" = "1" ]; then
  echo "Env ready and parity PASSED. Next: produce caches (see hpc/DATA.md), then hpc/preflight.sh"
else
  echo "Env ready but PARITY DID NOT RUN/PASS — resolve before trusting any results."
fi
