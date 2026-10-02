#!/bin/bash

set -euo pipefail

: "${HLL_ROOT:?set HLL_ROOT to the uploaded project root}"
: "${HLL_CACHE:?set HLL_CACHE to the HDF5 cache directory}"

PROFILE="${1:-thursday}"
CAP="${HLL_ARRAY_CAP:-10}"
PROJECT="${HLL_ROOT}/code/julia/learning"
export HLL_PROFILE="$PROFILE"
export HLL_JULIA_RESULTS="${HLL_JULIA_RESULTS:-/fs1/scratch/gandhico/HyperLIF_Learning/results/julia_learning}"

cd "$PROJECT"
julia --project="$PROJECT" -e 'using Pkg; Pkg.instantiate(); Pkg.precompile()'
julia --project="$PROJECT" preflight.jl "$HLL_CACHE"
BUNDLES="$(julia --project="$PROJECT" grid.jl --profile="$PROFILE" \
  --cache-dir="$HLL_CACHE" --results-root="$HLL_JULIA_RESULTS" --bundle-count)"
test "$BUNDLES" -gt 0

echo "profile=$PROFILE bundles=$BUNDLES cap=$CAP results=$HLL_JULIA_RESULTS"
sbatch --array="0-$((BUNDLES - 1))%${CAP}" run_array.slurm

