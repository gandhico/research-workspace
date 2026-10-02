# P1 APEX-v2 Readout Training Smoke

Date: 2026-07-19

Purpose: record G3 of the APEX-v2 PyTorch-parity validation ladder.

## Scope

This smoke freezes the APEX-v2 recurrent HyperLIF forward features and trains only the linear readout head on one SHD-wide batch. It verifies that PyTorch-style assembled features can drive finite cross-entropy gradients and a decreasing loss.

This is not full trunk training and not an accuracy claim.

## Implementation

Runner:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_v2\apex_v2_readout_train_smoke.jl`

Launcher:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\run_apex_v2_readout_train_smoke.ps1`

Configuration:

- architecture: recurrent
- neuron: HyperLIF
- readout: `hybrid_vr`
- batch size: 64
- hidden size: 64
- seed: 1
- steps: 20
- learning rate: 0.05

## Command

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
.\scripts\run_apex_v2_readout_train_smoke.ps1
```

## Result

The smoke passed:

`APEX_V2_READOUT_TRAIN_SMOKE_OK`

Loss curve:

| Step | Loss |
|---:|---:|
| 0 | `4.083514` |
| 5 | `3.136462` |
| 10 | `2.517572` |
| 15 | `2.098402` |
| 20 | `1.792870` |

CSV:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex_v2\apex_v2_readout_train_smoke_20260719_174843.csv`

## Claim Discipline

Safe claim:

APEX-v2 now passes G1/G2 forward shape/finite validation and a G3 one-batch readout-head training sanity. The PyTorch-style recurrent HyperLIF `hybrid_vr` feature tensor is finite and can drive a decreasing cross-entropy readout update.

Unsafe claim:

Do not claim full APEX-v2 training parity yet. The recurrent/delay trunk weights are not being trained in this smoke.

## Next Gate

- Export PyTorch first-batch trace summaries for identical seed/config.
- Compare APEX-v2 and PyTorch summaries for events/sample, gate mean, voltage mean, conductance mean, feature dimension, and logits shape.
- Add one-seed full-head training smoke with frozen trunk.
- Then decide whether to add differentiable/manual trunk updates or keep APEX-v2 as a feature-parity and readout-parity validation layer first.

## Readiness Effect

At the time of this APEX-v2 readout-train smoke, P1 remained 94%. This was superseded later on 2026-07-19 by `P1_APEX_V2_SHARED_WEIGHT_PARITY_2026_07_19.md`, which completed the shared-weight parity gate and moved the current P1 readiness to 95%.
