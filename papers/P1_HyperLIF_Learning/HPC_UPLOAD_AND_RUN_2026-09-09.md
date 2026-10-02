# Julia HyperLIF HPC upload and run

## Current status

The code, 100-test suite, data contract, preflight, experiment grids, result schema, checkpoints,
aggregation, and SLURM scripts are ready locally. CPU and CUDA mechanism preflights pass all three
learning modes on this workstation. The cluster has **not** been contacted or submitted from this
machine: no SSH host/alias is configured, and the existing notes use the placeholder `<cluster>`.
Do not describe the experiments as running until `sbatch` returns a job ID.

## Build the code-only upload

From PowerShell:

```powershell
& 'C:\Research\papers\P1_HyperLIF_Learning\code\julia\learning\package_hpc.ps1'
```

This creates `C:\Research\papers\P1_HyperLIF_Learning\hyperlif_julia_hpc_20260909.zip`. It excludes
datasets, local results, and Julia package artifacts.

## Upload

Upload the ZIP to `/fs1/home/gandhico/HyperLIF_Learning/` through Open OnDemand, or replace
`<cluster>` with the real SSH host:

```bash
scp hyperlif_julia_hpc_20260909.zip gandhico@<cluster>:/fs1/home/gandhico/HyperLIF_Learning/
```

On the login node:

```bash
cd /fs1/home/gandhico/HyperLIF_Learning
unzip -o hyperlif_julia_hpc_20260909.zip
module avail julia
module load julia
export HLL_ROOT=/fs1/home/gandhico/HyperLIF_Learning
export HLL_CACHE=/fs1/scratch/gandhico/HyperLIF_Learning/cache
export HLL_JULIA_RESULTS=/fs1/scratch/gandhico/HyperLIF_Learning/results/julia_learning
mkdir -p "$HLL_CACHE" "$HLL_JULIA_RESULTS" /fs1/scratch/gandhico/HyperLIF_Learning/logs
```

The cluster Julia must be 1.11 or 1.12. If only another version is available, update compatibility
only after running the full unit suite; do not edit the manifest blindly.

## Convert every existing portable cache

The existing Python workflow primarily uses `.pt`. Julia uses the corresponding `.h5` files in the
same cache directory:

```bash
source hpc/paths.sh
python code/hpc/export_hdf5.py --all
ls -lh "$HLL_CACHE"/*.h5
```

The grid discovers every `.h5` present. Missing datasets are omitted rather than silently replaced.
Before the Friday presentation, record the exact discovered names and sizes.

## Preflight and Thursday screen

On a GPU allocation:

```bash
cd "$HLL_ROOT/code/julia/learning"
julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.test()'
julia --project=. preflight.jl "$HLL_CACHE"
bash submit.sh thursday
```

`submit.sh` prints the number of bundles and `sbatch` should print `Submitted batch job <ID>`. Add that
ID and timestamp to `THREE_STAGE_DEVELOPMENT_REPORT_2026-09-09.md`.

For `D` discovered datasets, Thursday contains `27D` experiments in `9D` bundles. It is a one-seed,
three-epoch screen and must not be called a benchmark.

Useful checks:

```bash
squeue -u gandhico
sacct -j <JOB_ID> --format=JobID,State,Elapsed,ExitCode,MaxRSS
find "$HLL_JULIA_RESULTS" -name summary.json | wc -l
julia --project=. aggregate_results.jl "$HLL_JULIA_RESULTS"
```

## Serious matrix

Only after the Thursday screen has no systematic CUDA, NaN, no-event, or data-layout failures:

```bash
export HLL_PROFILE=serious
bash submit.sh serious
```

For each dataset, this profile has 300 experiments in 60 bundles: three cells, five seeds, dense,
recurrent, causal-delay, and a labelled noncausal centered-delay upper-bound; it includes pure and
hybrid surrogate/event-time readouts. With six datasets this is 1,800 experiments/360 bundles. Check
the allocation and storage budget before submission.

This is a within-family mechanism matrix. It is not sufficient for a superiority claim until matched
LIF/ALIF/PLIF and continuous-state baselines are produced under the same split/event/compute contract.

## Honest presentation language

Before submission: “The full Julia HPC matrices are prepared and locally preflighted; cluster
submission awaits access.”

After receiving a job ID: “A one-seed screening matrix is running on the cluster; no performance
conclusion will be drawn until completion.”

After Thursday aggregation: report completed/failed counts, not only successful cells. Keep
upcrossings, occupancy, no-event fraction, crossing-speed conditioning, wall time, and accuracy
separate. Do not call activity an energy measurement.
