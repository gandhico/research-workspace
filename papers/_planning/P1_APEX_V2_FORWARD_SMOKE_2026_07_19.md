# P1 APEX-v2 Forward Smoke

Date: 2026-07-19

Purpose: record the first validation gate for the new APEX-v2 PyTorch-parity layer.

## Implementation

New folder:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_v2`

Files:

- `APEXV2Parity.jl`
- `apex_v2_forward_smoke.jl`
- `README.md`

Launcher:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\run_apex_v2_forward_smoke.ps1`

## What APEX-v2 Implements So Far

This first scaffold implements forward-pass parity targets:

- Dense/feedforward architecture.
- RSNN-style recurrence: `fc_in(X_t) + fc_rec(prev_spk)`.
- Learnable-delay architecture shape: depthwise temporal-current kernel initialized as pass-through.
- PyTorch-style readout features:
  - `spike_count`
  - `membrane`
  - `gate`
  - `hybrid_gr`
  - `hybrid_vr`
  - `hybrid_vr_conductance`
- LIF, HyperLIF, and Adaptive HyperLIF forward states.
- Batch-normalized feature assembly followed by a random linear head for finite-logit validation.

This is a forward-trace gate only. It does not yet train or prove accuracy parity.

## Command

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
.\scripts\run_apex_v2_forward_smoke.ps1
```

Equivalent Julia call:

```powershell
julia .\julia\apex_v2\apex_v2_forward_smoke.jl --batch-size=32 --hidden-dim=64 --seeds=1 --architectures=dense,recurrent,delay --neurons=lif,hyperlif,adaptive --readouts=spike_count,membrane,gate,hybrid_gr,hybrid_vr,hybrid_vr_conductance --delay-kernel-size=7
```

## Result

The smoke passed:

`APEX_V2_FORWARD_SMOKE_OK`

Total combinations:

`3 architectures x 3 neurons x 6 readouts x 1 seed = 54`

Failures:

`0`

CSV:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex_v2\apex_v2_forward_smoke_20260719_174512.csv`

## Sanity Signals

Input batch:

- `x_fbt=[700,32,20]`
- SHD-wide cache: `shd_wide_T20.h5`
- classes: `20`

Feature dimensions matched readout design for hidden size 64:

| Readout | Feature dimension |
|---|---:|
| `spike_count` | 64 |
| `membrane` | 64 |
| `gate` | 64 |
| `hybrid_gr` | 128 |
| `hybrid_vr` | 128 |
| `hybrid_vr_conductance` | 192 |

Representative event/gate summaries:

| Architecture | Neuron | Events/sample | Gate mean |
|---|---|---:|---:|
| dense | LIF | `720.688` | `0.00000` |
| dense | HyperLIF | `583.938` | `0.41561` |
| dense | Adaptive HyperLIF | `262.531` | `0.26187` |
| recurrent | LIF | `721.469` | `0.00000` |
| recurrent | HyperLIF | `585.062` | `0.41622` |
| recurrent | Adaptive HyperLIF | `263.000` | `0.26213` |
| delay | LIF | `720.688` | `0.00000` |
| delay | HyperLIF | `583.938` | `0.41561` |
| delay | Adaptive HyperLIF | `262.531` | `0.26187` |

The delay architecture matches dense in this first smoke because the depthwise temporal-current kernel is initialized as a pass-through kernel, matching the PyTorch delay model initialization.

## Claim Discipline

Safe claim:

APEX-v2 now has a runnable Julia/CUDA forward-parity scaffold for dense, RSNN, and learnable-delay architecture families with PyTorch-style readout feature assembly. The first SHD-wide forward smoke passed 54/54 finite checks.

Unsafe claim:

Do not claim training parity, accuracy parity, or PyTorch trace parity yet. This is G1/G2 of the validation ladder, not G3-G6.

## Next Gate

- Export or compute trace-level PyTorch reference summaries for the same first SHD batch.
- Add one-batch gradient/training sanity for the APEX-v2 readout head.
- Add CSV comparison tooling for PyTorch vs APEX-v2 state summaries.
- Then run one-seed training smoke.

## Readiness Effect

At the time of this APEX-v2 forward-smoke note, P1 remained 94%. This was superseded later on 2026-07-19 by `P1_APEX_V2_SHARED_WEIGHT_PARITY_2026_07_19.md`, which completed the shared-weight parity gate and moved the current P1 readiness to 95%.
