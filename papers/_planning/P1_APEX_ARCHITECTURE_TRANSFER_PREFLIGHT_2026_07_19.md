# P1 APEX Architecture-Transfer Preflight

Date: 2026-07-19

Purpose: answer whether the APEX bridge has implemented the PyTorch-successful recurrent and delay architecture families, and record the current evidence boundary.

## Implementation

Updated:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_shd_ranking_smoke.jl`

New runner support:

- `--architectures=dense,recurrent,delay`
- aliases: `ff` -> `dense`, `rsnn` -> `recurrent`
- `--max-delay` for APEX fixed causal axonal-delay length
- CSV columns now include `architecture`

Reproducible launcher:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\run_apex_architecture_transfer_preflight.ps1`

## Relation to the PyTorch Architectures

What is implemented:

- Dense: matched APEX dense LIF/HyperLIF-NSA cell plus V11 readout.
- Recurrent: APEX-native `EPropHyperLIFLayer` with `use_nsa=false` control and `use_nsa=true` HyperLIF/NSA, plus V11 readout.
- Delay: APEX-native `DenseLIFLayer -> SpikingDelayLayer -> V11ReadoutLayer`.

What is not yet identical to PyTorch:

- The PyTorch RSNN uses `fc_in + fc_rec(prev_spk)` and a batch-normalized classifier over selectable readout features.
- The PyTorch delay model uses a learnable depthwise temporal-current convolution initialized as a pass-through kernel.
- APEX delay currently uses fixed causal axonal delays after the hidden neuron, not a learnable current-delay kernel.
- APEX V11 readout does not yet reproduce the PyTorch `hybrid_vr` / `hybrid_vr_conductance` feature assembler exactly.

Therefore this is an APEX architecture-family transfer preflight, not yet a byte-identical PyTorch architecture port.

## Compile Smoke

Command:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
julia .\julia\apex_shd_ranking_smoke.jl --epochs=1 --max-train-batches=1 --max-test-batches=1 --batch-size=64 --hidden-dim=64 --readout-hidden=32 --seeds=1 --architectures=dense,recurrent,delay --models=lif,hyperlif --beta=0.10 --gamma=0.80 --max-delay=3
```

Result: passed with `APEX_SHD_RANKING_SMOKE_OK`.

CSV outputs:

- Raw: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_161335.csv`
- Epoch curve: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_161335_epochs.csv`
- Summary: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_161335_summary.csv`

## Three-Seed Preflight

Command:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
julia .\julia\apex_shd_ranking_smoke.jl --epochs=3 --max-train-batches=31 --max-test-batches=12 --batch-size=64 --hidden-dim=128 --readout-hidden=64 --seeds=3 --architectures=recurrent,delay --models=lif,hyperlif --beta=0.10 --gamma=0.80 --max-delay=3
```

Result: passed with `APEX_SHD_RANKING_SMOKE_OK`.

Summary:

| Architecture | Model | Seeds | Epochs | Test accuracy | Test loss |
|---|---|---:|---:|---:|---:|
| delay | LIF control | 3 | 3 | `0.1085 +/- 0.0131` | `2.8326` |
| delay | HyperLIF/NSA | 3 | 3 | `0.0781 +/- 0.0306` | `2.9265` |
| recurrent | LIF control | 3 | 3 | `0.1176 +/- 0.0072` | `2.8432` |
| recurrent | HyperLIF/NSA | 3 | 3 | `0.0955 +/- 0.0202` | `2.8578` |

CSV outputs:

- Raw: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_161513.csv`
- Epoch curve: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_161513_epochs.csv`
- Summary: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex\apex_shd_ranking_smoke_20260719_161513_summary.csv`

## Claim Discipline

Safe claim:

APEX now contains runnable dense, recurrent, and delay architecture-family modes for SHD-wide HDF5 caches. The recurrent and delay modes instantiate, train, evaluate, and log without CUDA/runtime failure.

Unsafe claim:

Do not claim that the successful PyTorch RSNN/delay recipe has been fully ported to APEX. Do not claim APEX recurrent/delay reproduce the PyTorch HyperLIF advantage yet. The current short preflight is negative for HyperLIF under the APEX recurrent/delay approximations.

## Next Gate

- Add or approximate PyTorch-style readout feature assembly in APEX: spike count, membrane mean, gate mean, and hybrid `[v,r]`.
- Decide whether to implement a learnable causal temporal-current delay layer in APEX, or keep delay as a separate fixed-axonal-delay control.
- Run a small recurrent/delay tuning grid before any longer 10/20/30 epoch architecture claim.
- Keep the P1 main-text APEX claim dense-only for now; move recurrent/delay APEX preflight to limitations/supplementary traceability until it becomes positive.

## Readiness Effect

At the time of this architecture-transfer preflight, P1 remained 94%. This was superseded later on 2026-07-19 by `P1_APEX_V2_SHARED_WEIGHT_PARITY_2026_07_19.md`, which completed the APEX-v2 shared-weight parity gate and moved the current P1 readiness to 95%.
