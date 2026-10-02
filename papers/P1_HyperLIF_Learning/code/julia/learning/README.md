# HyperLIFLearning.jl

Julia reference and experiment package for three distinct learning contracts:

- `continuous`: AD through the discretized piecewise-smooth state path; events are diagnostics.
- `surrogate`: hard upward crossings forward, fast-sigmoid pseudo-gradient backward.
- `event_time`: interpolated first-crossing time, conditional on fixed event topology.

Cells are `hyperlif`, `adaptive`, and exploratory `next`; architectures are `dense`, `recurrent`,
and `delay`. Delay mode defaults to causal. Centered delay is available only as a labelled offline
upper-bound ablation.

## Local verification

```bash
julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.test()'
julia --project=. preflight.jl /path/to/hdf5/cache/directory
```

HDF5 files require `X_train`, `y_train`, `X_test`, and `y_test`. Either samples × time × features or
features × time × samples is accepted and normalized to features × time × samples. Labels may be
zero- or one-based.

One real-data experiment:

```bash
julia --project=. train_hpc.jl \
  --cache=/path/to/shd_wide_T20.h5 \
  --architecture=dense --cell=hyperlif \
  --learning-mode=continuous --readout=hybrid_vr \
  --device=cpu --epochs=3
```

Every completed experiment produces `summary.json` and `checkpoint.jls`. Checkpoint selection uses
a class-stratified held-out validation subset; capped train/test subsets are also stratified and
seeded. Test is evaluated once afterward.

## Experiment profiles

```bash
julia --project=. grid.jl --profile=thursday --cache-dir="$HLL_CACHE" --count
julia --project=. grid.jl --profile=thursday --cache-dir="$HLL_CACHE" --bundle-count
bash submit.sh thursday
```

`thursday` is screening only (all caches, 3 architectures, 3 cells, 3 modes, one seed, three epochs,
capped data). `serious` uses full data, five seeds, 40 epochs, pure/hybrid event readouts, and a
noncausal centered-delay ablation.

Each SLURM array element is a bundle rather than a single experiment. Keeping several modes in one
Julia process amortizes the substantial first reverse-mode compilation. `submit.sh` instantiates the
environment, runs preflight, calculates the array bounds, and submits `run_array.slurm`.

Aggregate completed runs with:

```bash
julia --project=. aggregate_results.jl "$HLL_JULIA_RESULTS"
```

## Reporting discipline

`upcrossings_per_sample` and `occupancy_per_sample` are different. Neither is hardware energy.
Event-time derivatives are not valid claims across event creation/deletion or grazing crossings.
The `next` cell is a computational hypothesis, not a demonstrated biological model. See the project
root `AGENTS.md` and mathematical report before interpreting results.
