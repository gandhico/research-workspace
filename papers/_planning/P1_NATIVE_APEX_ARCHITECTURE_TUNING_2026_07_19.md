# P1 Native APEX Architecture Tuning Probe

Date: 2026-07-19

Purpose: continue auditing APEX-as-designed while APEX-v2 is being built. This report asks where the original Julia/CUDA APEX recurrent and delay architecture-family modes work, without changing them into the PyTorch-parity design.

## Native APEX Probe Script

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\run_apex_native_architecture_tuning_probe.ps1`

The probe tested HyperLIF/NSA only across recurrent and delay modes:

- 3 epochs
- 31 train batches
- 12 test batches
- batch size 64
- hidden size 128
- readout hidden size 64
- one seed for each setting

Manifest:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_native_architecture_tuning_probe_20260719_181027.csv`

## One-Seed Operating-Envelope Probe

| Config | beta | gamma | Delay test acc. | Recurrent test acc. | Interpretation |
|---|---:|---:|---:|---:|---|
| default | 0.10 | 0.50 | `0.1042` | `0.2721` | recurrent candidate |
| dense-best gate | 0.10 | 0.80 | `0.0768` | `0.1185` | not good for recurrent/delay |
| stronger gate | 0.10 | 1.20 | `0.0599` | `0.0690` | too strong |
| low conductance | 0.05 | 0.80 | `0.0677` | `0.1250` | weak |
| high conductance | 0.20 | 0.80 | `0.1042` | `0.1276` | delay recovers, recurrent modest |

Key observation:

The dense-best setting (`gamma=0.80`) is not the best architecture-transfer setting in native APEX. The native recurrent APEX path appears to prefer the older/default `gamma=0.50` setting.

## Three-Seed Confirmation of Best Candidate

Command:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
julia .\julia\apex_shd_ranking_smoke.jl --epochs=3 --max-train-batches=31 --max-test-batches=12 --batch-size=64 --hidden-dim=128 --readout-hidden=64 --seeds=3 --architectures=recurrent,delay --models=hyperlif --beta=0.10 --gamma=0.50 --max-delay=3
```

Summary CSV:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_182103_summary.csv`

Result:

| Architecture | Model | Seeds | Test accuracy | Test loss | Interpretation |
|---|---|---:|---:|---:|---|
| delay | HyperLIF/NSA | 3 | `0.0916 +/- 0.0146` | `2.9292` | below prior delay LIF control |
| recurrent | HyperLIF/NSA | 3 | `0.1441 +/- 0.1141` | `2.7434` | above prior recurrent LIF mean, but high variance |

Reference from the earlier three-seed native APEX recurrent/delay control run:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_161513_summary.csv`

| Architecture | LIF control test accuracy | HyperLIF/NSA at gamma=0.80 |
|---|---:|---:|
| delay | `0.1085 +/- 0.0131` | `0.0781 +/- 0.0306` |
| recurrent | `0.1176 +/- 0.0072` | `0.0955 +/- 0.0202` |

## Advisor Interpretation

The original APEX engine is not simply failing. It has at least three distinct behaviors:

1. Dense APEX works after calibration (`gamma=0.80`) and gives a small five-seed HyperLIF/NSA advantage.
2. Native recurrent APEX is architecture-sensitive. Its best tested setting so far is the default `gamma=0.50`, not the dense-best `gamma=0.80`; it beats the prior LIF mean in a three-seed probe but with high variance.
3. Native delay APEX remains limited. Its fixed `SpikingDelayLayer` is not equivalent to the PyTorch learnable temporal-current delay model and did not beat the prior delay LIF control.

## Claim Discipline

Safe claim:

APEX-as-designed is technically operational and informative. It supports a calibrated dense result and a recurrent candidate regime, but it is highly architecture-sensitive. Its fixed-delay implementation is currently the clearest limitation.

Unsafe claim:

Do not claim native APEX recurrent HyperLIF is paper-grade positive yet. The mean is promising but the variance is too high. Do not claim native APEX delay reproduces the PyTorch delay result.

## Next Gate

- Run a focused recurrent native APEX probe around `gamma=0.40,0.50,0.60` with 3 seeds if we want to sharpen the original-engine operating envelope.
- Keep native delay as a limitation unless a learnable temporal-current delay layer is added.
- In parallel, continue APEX-v2 as the portable architecture recipe.

## Readiness Effect

At the time of this native-APEX tuning note, P1 remained 94%. This was superseded later on 2026-07-19 by `P1_APEX_V2_SHARED_WEIGHT_PARITY_2026_07_19.md`, which completed the APEX-v2 shared-weight parity gate and moved the current P1 readiness to 95%.
