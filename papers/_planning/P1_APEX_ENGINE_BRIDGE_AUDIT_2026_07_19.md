# P1 APEX Engine Bridge Audit

Date: 2026-07-19

Purpose: record what is actually present for the Julia/APEX cross-framework ranking gate and define the next executable step for P1.

## Current Status

The P1 architecture folder already validates the HDF5 data bridge, but it does not contain the full APEX training engine. The APEX engine was located under the older Adaptive HyperLIF tree:

`C:\00_Research_\Neural_Networks_and_Learning\01_Adaptive_HyperLIF\03_Adaptive_HyperLIF_Apex_Engine\SNN_NSA_2`

The current P1 SHD-wide HDF5 cache was located at:

`C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5`

Existing P1 bridge checks:

- `julia\load_cache.jl` confirms Julia can read the HDF5 cache and preserves the checksum.
- `julia\test_load_cache_h5.jl` confirms the strict APEX topology `[F,N,T] = [700,2000,20]`.

## Engine Findings

- APEX engine module file exists: `SNN_NSA_2\src\APEXEngine.jl`.
- APEX engine data loader exists: `SNN_NSA_2\src\data.jl`.
- Existing `load_dvs_h5` is hardcoded for 32x32x2 DVS tensors and reshapes to 2048 features.
- P1 SHD cache is already flat with 700 features, so using `load_dvs_h5` directly would be wrong.
- APEX classification labels are 0-based at the loader boundary; `learning.jl` adds `+1` inside the CUDA one-hot kernel. Therefore the PyTorch-exported labels should pass through unchanged.

## Local Environment Check

Command attempted:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\01_Adaptive_HyperLIF\03_Adaptive_HyperLIF_Apex_Engine\SNN_NSA_2
julia --project=. -e 'include("src/APEXEngine.jl"); using .APEXEngine; println("APEX_INCLUDE_OK")'
```

Initial result:

- The first engine import did not complete because the Julia project needed dependency instantiation and CUDA precompilation.

Follow-up result:

- A clean include/import now passes: `APEX_INCLUDE_OK`.
- CUDA is functional: `CUDA_FUNCTIONAL=true`.
- CUDA devices: `CUDA_DEVICES=1`.
- Dependency setup is no longer the blocker. Do not run the full P1 APEX ranking until the ranking runner itself is created and scoped to the selected P1 shortlist cells.

## New Adapter Scaffold

Added:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_load_cache_h5_adapter.jl`

Purpose:

- Reads P1 HDF5 caches written by `07_AdHyperLIF_Triage\hpc\export_hdf5.py`.
- Converts HDF5.jl layout `[F,T,N]` to strict APEX `[F,N,T]`.
- Preserves 0-based labels for APEX's internal one-hot kernel.
- Provides `inspect_cache_h5(path)` for CPU-only adapter inspection.
- Provides `load_cache_h5(path, batch_size)` for use from an instantiated APEXEngine session.

CPU-only adapter inspection command:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
julia .\julia\apex_load_cache_h5_adapter.jl "C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5"
```

Inspection result:

- `X_train raw(HDF5.jl) = (700, 20, 2000) -> APEX [F,N,T] = (700, 2000, 20)`.
- `X_test raw(HDF5.jl) = (700, 20, 800) -> APEX [F,N,T] = (700, 800, 20)`.
- Labels are 0-based: train `0/19`, test `0/19`.
- `sum(X_train) = 1.551635e7`.
- Adapter inspection completed successfully without requiring CUDA.

APEX-backed loader smoke:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
julia .\julia\apex_loader_smoke.jl 64
```

Result:

- `TRAIN_BATCHES=31`, `TEST_BATCHES=12`.
- First GPU batch: `FIRST_BATCH_X=(700, 64, 20)`, `FIRST_BATCH_Y=(64,)`.
- First-batch label range: `0/19`.
- `APEX_LOADER_SMOKE_OK`.

## Next Executable Step

1. Re-check engine and CUDA if the environment changes:

```powershell
julia --project=. -e 'using CUDA; println(CUDA.functional())'
julia --project=. -e 'include("src/APEXEngine.jl"); using .APEXEngine; println("APEX_INCLUDE_OK")'
```

2. From an APEX script, include the adapter and construct loaders:

```julia
include("src/APEXEngine.jl")
using .APEXEngine
include(raw"C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_load_cache_h5_adapter.jl")
train_loader, test_loader = load_cache_h5(raw"C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5", 64)
```

3. Scale the new bounded ranking runner from smoke-grade to paper-grade multi-seed evidence.

Bounded runner now added:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_shd_ranking_smoke.jl`

First smoke result is recorded in:

`C:\00_Research_\Neural_Networks_and_Learning\10_IEEE_Paper_Proposals_2026_07_19\P1_APEX_RANKING_SMOKE_2026_07_19.md`

## Readiness Effect

P1 moved from 89% to 90% at this bridge stage. This closed the "where is APEX?", loader-design, cache-path, topology, label-convention, CUDA, and APEX-loader-smoke uncertainties. The follow-up bounded train/eval smoke then moved P1 to 91%. Historical note: at this stage the paper-grade Julia/APEX ranking reproduction was still pending; this was superseded by `P1_APEX_MULTI_SEED_TUNING_2026_07_19.md`, which moved P1 to 93%.
