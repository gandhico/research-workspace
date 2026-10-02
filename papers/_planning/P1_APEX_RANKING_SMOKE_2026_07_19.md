# P1 APEX Ranking Smoke

Date: 2026-07-19

Purpose: record the first bounded Julia/APEX training and evaluation run on the byte-identical SHD-wide cache used by the P1 PyTorch shortlist.

## New Runner

Added:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_shd_ranking_smoke.jl`

The runner:

- Activates the older APEX project at `C:\00_Research_\Neural_Networks_and_Learning\01_Adaptive_HyperLIF\03_Adaptive_HyperLIF_Apex_Engine\SNN_NSA_2`.
- Includes the local generic HDF5 adapter, which maps the Python-exported SHD cache to APEX `[F,N,T]`.
- Builds matched `DenseLIFLayer -> V11ReadoutLayer` models.
- Uses `DenseLIFLayer(...; use_nsa=false)` for the vanilla LIF control.
- Uses `DenseLIFLayer(...; use_nsa=true)` for the HyperLIF/NSA microstep cell.
- Runs a bounded manual loop around `train_batch!` and writes a CSV under `08_HyperLIF_Architectures\results\apex`.

## Smoke Command

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
julia .\julia\apex_shd_ranking_smoke.jl --epochs=1 --max-train-batches=2 --max-test-batches=2 --batch-size=64 --hidden-dim=128 --readout-hidden=64 --seeds=1
```

## First Smoke Result

The run completed successfully with `APEX_SHD_RANKING_SMOKE_OK`.

CSV generated:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_134401.csv`

Summary:

| Seed | Model | APEX neuron switch | Train batches | Test batches | Train acc. | Test acc. | Train loss | Test loss |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | dense_lif_control | `use_nsa=false` | 2 | 2 | 0.0391 | 0.0234 | 3.5252 | 3.4423 |
| 1 | dense_hyperlif_nsa | `use_nsa=true` | 2 | 2 | 0.0234 | 0.0234 | 3.4753 | 3.3428 |

## Synced-Path Calibration Smoke

After syncing the runner into the main research tree, a slightly larger calibration smoke was run directly from:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures`

Command:

```powershell
julia .\julia\apex_shd_ranking_smoke.jl --epochs=1 --max-train-batches=4 --max-test-batches=3 --batch-size=64 --hidden-dim=128 --readout-hidden=64 --seeds=1
```

Result:

- Completed with `APEX_SHD_RANKING_SMOKE_OK`.
- CSV: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_134923.csv`.

| Seed | Model | APEX neuron switch | Train batches | Test batches | Train acc. | Test acc. | Train loss | Test loss |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | dense_lif_control | `use_nsa=false` | 4 | 3 | 0.0547 | 0.0625 | 3.3595 | 3.3450 |
| 1 | dense_hyperlif_nsa | `use_nsa=true` | 4 | 3 | 0.0742 | 0.1042 | 3.3208 | 3.2413 |

This is still only a calibration smoke. It is encouraging that the HyperLIF/NSA cell leads the LIF control under the same tiny schedule, but this should not be cited as paper-grade ranking evidence.

## Interpretation

These are not paper-grade accuracy results. With only two-to-four training batches and two-to-three test batches, accuracy should be treated as CUDA/training-path and runtime sanity checks only.

What it does close:

- The byte-identical SHD cache can be loaded by APEX and trained end to end.
- The same APEX training path can evaluate a vanilla LIF control and a HyperLIF/NSA cell.
- `use_nsa` is now an executable, traceable cross-framework comparison knob for P1.
- The remaining Julia/APEX risk is now experimental scale and ranking reproduction, not data topology or engine integration.

## Next Gate

Follow-up multi-seed tuning is now recorded in:

`C:\00_Research_\Neural_Networks_and_Learning\10_IEEE_Paper_Proposals_2026_07_19\P1_APEX_MULTI_SEED_TUNING_2026_07_19.md`

That follow-up closes the APEX cross-framework gate at calibration level. Remaining paper work is no longer "can APEX reproduce anything?" but:

- Decide whether to extend APEX to 20 or 30 epochs.
- Integrate the tuned APEX table into P1.
- Preserve the default-gamma negative result as calibration discipline.
- Freeze final P1 baseline/statistical tables.

## Readiness Effect

P1 moved from 90% to 91% at this smoke stage. The APEX training/evaluation path was proven here. Historical note: the final cross-framework ranking claim still required larger multi-seed evidence at this point; this was superseded by `P1_APEX_MULTI_SEED_TUNING_2026_07_19.md`, which moved P1 to 93%.
