# P1 APEX-v2 Shared-Weight PyTorch Parity

Date: 2026-07-19

## Purpose

This note records the first value-level APEX-v2 parity gate. The previous trace comparison proved structural parity only: matching architecture/neuron/readout rows, feature dimensions, finite states, and qualitative event/gate hierarchy. This new gate exports exact PyTorch-initialized weights, expected features, and expected logits, then injects the same weights into Julia/APEX-v2.

## New Scripts

- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\export_pytorch_apex_v2_fixture.py`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_v2\apex_v2_shared_weight_trace_compare.jl`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\run_apex_v2_shared_weight_trace_compare.ps1`

The PyTorch exporter writes HDF5 fixtures with:

- SHD-wide first-batch metadata
- exact PyTorch `fc_in`, recurrent, delay, and readout-head weights
- expected readout features
- expected logits

The Julia comparator loads the same SHD-wide HDF5 first batch, injects the PyTorch weights into APEX-v2, and compares feature and logit arrays.

## Passing Shared-Weight Gates

Dataset/cache:

`C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5`

Batch/hidden/readout:

`batch=32`, `hidden=64`, `readout=hybrid_vr`, `seed=1`.

| Architecture | Neuron | Feature max abs | Feature mean abs | Logit max abs | Tolerance | Result CSV |
|---|---|---:|---:|---:|---|---|
| dense | HyperLIF | `8.5831e-06` | `5.0175e-07` | `6.6608e-06` | feature `1e-4`, logit `1e-3` | `apex_v2_shared_weight_trace_compare_20260719_183400.csv` |
| recurrent | HyperLIF | `8.5831e-06` | `4.9969e-07` | `5.0068e-06` | feature `1e-4`, logit `1e-3` | `apex_v2_shared_weight_trace_compare_20260719_183254.csv` |
| delay | HyperLIF | `1.0490e-05` | `5.0446e-07` | `7.3314e-06` | feature `1e-4`, logit `1e-3` | `apex_v2_shared_weight_trace_compare_20260719_183441.csv` |
| dense | Adaptive HyperLIF | `1.9792e-04` | `6.8891e-07` | `1.8263e-04` | feature `5e-4`, logit `1e-3` | `apex_v2_shared_weight_trace_compare_20260719_183651.csv` |
| recurrent | Adaptive HyperLIF | `5.0840e-04` | `7.8672e-07` | `4.3511e-04` | feature `1e-3`, logit `1e-3` | `apex_v2_shared_weight_trace_compare_20260719_183826.csv` |
| delay | Adaptive HyperLIF | `3.5203e-04` | `7.2987e-07` | `1.4955e-04` | feature `1e-3`, logit `1e-3` | `apex_v2_shared_weight_trace_compare_20260719_183913.csv` |

Diagnostic failed-tolerance files were also produced while tightening the Adaptive envelope:

- `apex_v2_shared_weight_trace_compare_20260719_183550.csv`: dense Adaptive at feature tolerance `1e-4`
- `apex_v2_shared_weight_trace_compare_20260719_183742.csv`: recurrent Adaptive at feature tolerance `5e-4`

These are useful diagnostics, not architecture failures. The maximum errors remain small and logits pass the `1e-3` envelope.

## Interpretation

Safe claims:

- APEX-v2 has value-level shared-weight parity with the validated PyTorch implementation for the portable dense, recurrent, and delay HyperLIF cores.
- APEX-v2 also has value-level shared-weight parity for Adaptive HyperLIF under a `1e-3` Float32 tolerance envelope.
- The APEX-v2 delay implementation is a PyTorch-style temporal-current depthwise delay, not the older native APEX fixed spike-delay approximation.
- This separates the current story into two honest parts:
  - original APEX-as-designed: useful native-engine audit, dense calibrated-positive, recurrent/delay limited
  - APEX-v2: direct PyTorch architecture port with verified cross-language forward values

Unsafe claims:

- Do not claim APEX-v2 paper-grade accuracy until G4-G6 training runs are complete.
- Do not claim original APEX recurrent/delay reproduces PyTorch architecture wins.
- Do not merge the native APEX and APEX-v2 results into one table without labeling the implementation difference.

## Next Gate

This next gate was completed later on 2026-07-19 and recorded in `P1_APEX_V2_TRAIN_EVAL_SMOKE_2026_07_19.md`.

Run an APEX-v2 one-seed training smoke over real train/test batches for the most relevant cells:

1. recurrent HyperLIF, `hybrid_vr`
2. recurrent Adaptive HyperLIF, `hybrid_vr`
3. delay HyperLIF, `hybrid_vr`
4. delay Adaptive HyperLIF, `hybrid_vr`

This should use the same result schema as PyTorch and report accuracy, loss, events/sample, gate mean, stability, and provenance.
