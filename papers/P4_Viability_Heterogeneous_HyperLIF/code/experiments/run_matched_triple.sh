#!/usr/bin/env bash
# P4-005 / R01-R03: budget-matched heterogeneous vs ensemble vs homogeneous.
#
# Equal total hidden state, effective parameter counts within 63 of each other,
# identical split rule, optimizer, epoch budget, and early-stopping rule.
# Homeostasis is OFF: this experiment isolates heterogeneity from ensembling and
# from a single wide population. Homeostasis is a separate factor (R05).
set -u
CACHE="C:/Research/papers/P1_HyperLIF_Learning/code/hpc/upload_data/shd_wide_T20.h5"
ROOT="results/matched_triple"
for seed in 1 2 3; do
  for model in heterogeneous ensemble homogeneous; do
    echo "=== model=$model seed=$seed ==="
    julia --project=. experiments/train_h5.jl \
      --cache="$CACHE" --model="$model" --seed="$seed" \
      --regime-profile=shd_shared_gain \
      --epochs=12 --hidden-per-population=16 --batch-size=32 \
      --max-train=800 --max-test=400 --patience=4 \
      --homeostasis=false --results-root="$ROOT" 2>&1 | tail -4
  done
done
echo "ALL RUNS COMPLETE"
