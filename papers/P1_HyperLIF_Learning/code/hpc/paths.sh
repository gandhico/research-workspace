#!/usr/bin/env bash
# Canonical paths for the HyperLIF_Learning HPC workflow.
# Source from the other scripts:   source "$(dirname "$0")/paths.sh"
# Every value is overridable from the environment; defaults are the cluster layout.

: "${HLL_ROOT:=/fs1/home/gandhico/HyperLIF_Learning}"            # code/project root (this repo)
: "${HLL_SCRATCH:=/fs1/scratch/gandhico/HyperLIF_Learning}"      # scratch base
: "${HLL_CACHE:=${HLL_SCRATCH}/cache}"                           # portable {Xtr,ytr,Xte,yte}.pt caches
: "${HLL_RESULTS:=${HLL_SCRATCH}/results}"                       # _registry.csv, summaries, HPC_RESULTS.md
: "${HLL_LOGS:=${HLL_SCRATCH}/logs}"                             # SLURM stdout/err
: "${HLL_DATA:=/fs1/scratch/gandhico/HyperLIF_replication/data}" # read-only source HDF5 (do not write here)
: "${HLL_PKG:=${HLL_ROOT}/hpc}"                                  # where the adhyperlif_triage python pkg is vendored
: "${HLL_VENV:=${HLL_ROOT}/.venv}"                               # python venv

export HLL_ROOT HLL_SCRATCH HLL_CACHE HLL_RESULTS HLL_LOGS HLL_DATA HLL_PKG HLL_VENV
export PYTHONPATH="${HLL_PKG}:${PYTHONPATH:-}"

hll_mkdirs() { mkdir -p "$HLL_CACHE" "$HLL_RESULTS" "$HLL_LOGS"; }

hll_activate() {
  if [ -f "${HLL_VENV}/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${HLL_VENV}/bin/activate"
  else
    echo "WARN: venv not found at ${HLL_VENV} (run hpc/setup_env.sh first)" >&2
  fi
}

# Auto-activate the project venv when it exists, so `source hpc/paths.sh` fully prepares an
# interactive shell (torch/snntorch/tonic on PATH). Skipped on the first setup run (no venv yet)
# and when already inside a venv.
if [ -f "${HLL_VENV}/bin/activate" ] && [ -z "${VIRTUAL_ENV:-}" ]; then
  # shellcheck disable=SC1091
  source "${HLL_VENV}/bin/activate"
fi
