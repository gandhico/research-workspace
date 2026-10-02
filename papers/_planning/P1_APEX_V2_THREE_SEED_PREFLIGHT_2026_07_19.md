# P1 APEX-v2 Three-Seed Train/Eval Preflight

Date: 2026-07-19

## Purpose

This note records APEX-v2 G5: a bounded three-seed preflight over the portable recurrent/delay HyperLIF and Adaptive HyperLIF cores. It uses the same fixed-trunk/readout-head setting as G4, but repeats the smoke across seeds to test stability and ordering.

## Runner

- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_v2\apex_v2_train_eval_smoke.jl`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\run_apex_v2_train_eval_preflight.ps1`

The runner now supports `--seeds`.

Run configuration:

- dataset: `shd_wide_T20`
- architectures: `recurrent,delay`
- neurons: `hyperlif,adaptive`
- readout: `hybrid_vr`
- seeds: `1,2,3`
- epochs: `2`
- batch size: `64`
- hidden: `64`
- train batches: `4`
- test batches: `2`
- learning rate: `0.05`

Result files:

- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex_v2\apex_v2_train_eval_smoke_20260719_190105_summary.csv`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex_v2\apex_v2_train_eval_smoke_20260719_190105_epochs.csv`

## Aggregate Results

All four cells passed stability checks across all three seeds:

- `stable_all=true`
- `nan_total=0`
- train loss decreased for every seed/cell

| Architecture | Neuron | Seeds | Mean train-loss drop | Test accuracy mean | Test accuracy std | Events/sample mean | Gate mean |
|---|---|---:|---:|---:|---:|---:|---:|
| recurrent | HyperLIF | 3 | `0.481039` | `0.080729` | `0.019661` | `545.109` | `0.38224` |
| recurrent | Adaptive HyperLIF | 3 | `0.434455` | `0.075521` | `0.043028` | `248.841` | `0.24604` |
| delay | HyperLIF | 3 | `0.433798` | `0.072917` | `0.045105` | `545.167` | `0.38216` |
| delay | Adaptive HyperLIF | 3 | `0.402579` | `0.059896` | `0.011934` | `248.810` | `0.24599` |

## Interpretation

Safe claims:

- APEX-v2 G5 passes as an engineering preflight: stable across three seeds with no NaN batches.
- The fixed-trunk/readout-head learner consistently reduces training loss across recurrent and delay HyperLIF/Adaptive HyperLIF cells.
- HyperLIF remains more event-rich than Adaptive HyperLIF in APEX-v2, matching the expected operating regimes.
- Recurrent HyperLIF is the best mean short-smoke cell in this bounded preflight, but only slightly.

Unsafe claims:

- Do not claim a paper-grade APEX-v2 accuracy advantage from this bounded preflight.
- Do not use this table as the final architecture-transfer evidence; the PyTorch architecture table remains the main evidence unless a larger APEX-v2 G6 run is executed.
- Do not overinterpret delay vs recurrent ordering because only two test batches were used.

## Decision

Recommended manuscript handling:

- Include APEX-v2 as traceability/supplementary evidence if space allows.
- Do not move APEX-v2 into the main result table unless we run a larger G6-style experiment with more batches, more epochs, and paired statistics.
- For advisor discussion, this result is strong enough to say the APEX-v2 port is stable and faithful, but not yet strong enough to say it reproduces PyTorch architecture-transfer accuracy at paper grade.
