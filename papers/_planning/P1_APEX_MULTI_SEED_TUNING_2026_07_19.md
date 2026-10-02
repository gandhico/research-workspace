# P1 APEX Multi-Seed Tuning Result

Date: 2026-07-19

Purpose: record the first useful Julia/APEX cross-framework reproduction result for P1 after the initial ranking smoke exposed an untuned HyperLIF/NSA schedule.

## Runner Updates

Updated:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_shd_ranking_smoke.jl`

The runner now writes:

- Final per-seed CSV.
- Per-epoch CSV for learning curves.
- Summary CSV with mean and standard deviation by model.

It also exposes HyperLIF/NSA dynamics as command-line knobs:

- `--g-base`
- `--beta`
- `--gamma`
- `--tau-r`
- `--tau-soma`
- `--num-micro`
- `--models=lif,hyperlif`, `--models=hyperlif`, or `--models=lif`

Added a compact tuning launcher:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\run_apex_hyperlif_tuning_grid.ps1`

Tuning manifest:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_hyperlif_tuning_grid_20260719_142329.csv`

## Finding 1: Default APEX HyperLIF Was Not Enough

The default APEX HyperLIF/NSA setting (`beta=0.10`, `gamma=0.50`) did not reproduce the PyTorch headline under the dense APEX cell.

Five-seed, three-epoch direct comparison:

| Model | Epochs | Seeds | Test accuracy | Test loss |
|---|---:|---:|---:|---:|
| LIF control | 3 | 5 | `0.1281 +/- 0.0477` | `2.6743` |
| HyperLIF/NSA default | 3 | 5 | `0.1206 +/- 0.0583` | `2.7421` |

This result is useful because it prevents an unsafe claim: the old APEX default is not automatically equivalent to the tuned PyTorch HyperLIF behavior.

## Finding 2: Stronger Gate Feedback Recovers the APEX Advantage

The compact HyperLIF-only grid showed that stronger gate feedback was the useful direction. The best grid point was:

`beta=0.10`, `gamma=0.80`

Three-seed grid result:

| HyperLIF/NSA setting | Seeds | Epochs | Test accuracy |
|---|---:|---:|---:|
| `beta=0.10`, `gamma=0.50` | 3 | 3 | `0.0829 +/- 0.0224` |
| `beta=0.05`, `gamma=0.50` | 3 | 3 | `0.0920 +/- 0.0112` |
| `beta=0.20`, `gamma=0.50` | 3 | 3 | `0.0981 +/- 0.0367` |
| `beta=0.10`, `gamma=0.30` | 3 | 3 | `0.0981 +/- 0.0229` |
| `beta=0.10`, `gamma=0.80` | 3 | 3 | `0.1332 +/- 0.0403` |

Five-seed confirmation for `beta=0.10`, `gamma=0.80`:

| Model | Epochs | Seeds | Test accuracy | Test loss |
|---|---:|---:|---:|---:|
| HyperLIF/NSA tuned | 3 | 5 | `0.1466 +/- 0.0385` | `2.6940` |

CSV:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_143421_summary.csv`

## Finding 3: Ten-Epoch Direct Comparison Closes the Cross-Framework Gate

Command:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
julia .\julia\apex_shd_ranking_smoke.jl --epochs=10 --max-train-batches=31 --max-test-batches=12 --batch-size=64 --hidden-dim=128 --readout-hidden=64 --seeds=5 --models=lif,hyperlif --beta=0.10 --gamma=0.80
```

Result:

| Model | HyperLIF setting | Epochs | Seeds | Test accuracy | Test loss |
|---|---|---:|---:|---:|---:|
| LIF control | `use_nsa=false` | 10 | 5 | `0.2411 +/- 0.0778` | `2.3359` |
| HyperLIF/NSA tuned | `beta=0.10`, `gamma=0.80` | 10 | 5 | `0.2490 +/- 0.0666` | `2.2768` |

CSV outputs:

- Raw: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_143719.csv`
- Epoch curve: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_143719_epochs.csv`
- Summary: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_143719_summary.csv`

Learning-curve aggregate:

| Epoch | LIF test acc. | Tuned HyperLIF/NSA test acc. |
|---:|---:|---:|
| 1 | `0.10 +/- 0.04` | `0.11 +/- 0.01` |
| 2 | `0.11 +/- 0.04` | `0.11 +/- 0.02` |
| 3 | `0.13 +/- 0.05` | `0.15 +/- 0.04` |
| 4 | `0.15 +/- 0.06` | `0.17 +/- 0.06` |
| 5 | `0.16 +/- 0.05` | `0.16 +/- 0.05` |
| 6 | `0.19 +/- 0.06` | `0.18 +/- 0.05` |
| 7 | `0.21 +/- 0.05` | `0.18 +/- 0.05` |
| 8 | `0.20 +/- 0.06` | `0.23 +/- 0.06` |
| 9 | `0.21 +/- 0.08` | `0.24 +/- 0.06` |
| 10 | `0.24 +/- 0.08` | `0.25 +/- 0.07` |

## Claim Discipline

Safe claim:

The Julia/APEX implementation now reproduces a small tuned HyperLIF/NSA advantage over a matched dense LIF control on the same SHD-wide HDF5 cache, with five seeds and full-batch one-pass epochs. The tuned gate feedback (`gamma=0.80`) is necessary; the older APEX default does not support the claim.

Unsafe claim:

Do not claim that all HyperLIF parameterizations dominate LIF in APEX. Do not claim this APEX dense result replaces the stronger PyTorch architecture/baseline tables. It is a cross-framework reproduction and mechanism check, not the main benchmark table.

## Next Gate

- Decide whether to extend the APEX run to 20 or 30 epochs for a smoother learning curve.
- Add this as a calibrated cross-framework table in P1 rather than a headline benchmark.
- Preserve the negative default-gamma result in limitations or supplementary material if space allows.
- Freeze the P1 final baseline table scope and begin the IEEEtran conversion.

## Readiness Effect

P1 moves from 91% to 93%. The APEX cross-framework gate is now closed at a reviewer-safe calibration level, but final P1 submission still needs the final baseline/statistics table and polished IEEEtran manuscript.
