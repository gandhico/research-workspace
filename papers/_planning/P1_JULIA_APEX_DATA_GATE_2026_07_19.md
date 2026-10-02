# P1 Julia/APEX Data Gate

Date: 2026-07-19

Purpose: verify that the PyTorch-exported SHD-wide HDF5 cache is readable from Julia and lands in the topology expected by the APEX data loader.

## Source Cache

HDF5:

`C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5`

Original PyTorch cache:

`C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.pt`

Exporter:

`C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\export_hdf5.py`

Julia checks:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\load_cache.jl`

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\test_load_cache_h5.jl`

## Commands

```powershell
julia C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\load_cache.jl C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5
```

```powershell
julia C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\test_load_cache_h5.jl C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5
```

## Results

Raw Julia ingestion:

```text
X_train (700, 20, 2000)   y_train (2000,)   (Julia F,T,N = Python N,T,F)
X_test  (700, 20, 800)   y_test  (800,)
sum(X_train) = 1.551635e7
n_classes = 20   T = 20   F = 700
INGESTION OK
```

APEX topology check:

```text
X_train [F,N,T] = (700, 2000, 20)   X_test = (700, 800, 20)
y_train (2000,)   classes = 20
sum(X_train) = 1.551635e7
APEX topology OK: [F=700, N=2000, T=20]
```

## Interpretation

Safe claim:

- The SHD-wide PyTorch cache is readable by Julia and can be permuted into the APEX `[F,N,T]` data layout with an invariant checksum.

Still pending:

- APEX GPU training/reproduction of the PyTorch ranking.
- Cross-framework accuracy comparison using matched neuron, readout, seed, and cache settings.

Readiness effect:

- Historical readiness note: P1 remained at 89% at this data-gate stage. This was superseded on 2026-07-19 by `P1_APEX_MULTI_SEED_TUNING_2026_07_19.md`, which closed the APEX cross-framework gate at calibration level and moved P1 to 93%.
