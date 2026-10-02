# P1 APEX-v2 Multi-Batch Train/Eval Smoke

Date: 2026-07-19

## Purpose

This note records APEX-v2 G4: a bounded one-seed train/test smoke over real SHD train/test batches. The trunk is the PyTorch-parity APEX-v2 implementation validated by the shared-weight gate; only the readout head is trained. This is the correct next rung after one-batch readout training and shared-weight forward parity.

## New Runner

- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_v2\apex_v2_train_eval_smoke.jl`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\run_apex_v2_train_eval_smoke.ps1`

Run configuration:

- dataset: `shd_wide_T20`
- cache: `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5`
- architectures: `recurrent,delay`
- neurons: `hyperlif,adaptive`
- readout: `hybrid_vr`
- seed: `1`
- epochs: `2`
- batch size: `64`
- hidden: `64`
- train batches: `4`
- test batches: `2`
- learning rate: `0.05`

Result files:

- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex_v2\apex_v2_train_eval_smoke_20260719_185552_summary.csv`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex_v2\apex_v2_train_eval_smoke_20260719_185552_epochs.csv`

## Result Summary

All four cells were stable with `nan_batches=0`.

| Architecture | Neuron | Initial train loss | Final train loss | Final train acc. | Final test loss | Final test acc. | Events/sample | Gate mean | Stable |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| recurrent | HyperLIF | `3.9882` | `3.4730` | `0.0469` | `3.3515` | `0.0625` | `594.26` | `0.41650` | yes |
| recurrent | Adaptive HyperLIF | `3.9679` | `3.5511` | `0.0664` | `3.4920` | `0.0469` | `269.29` | `0.26732` | yes |
| delay | HyperLIF | `3.9185` | `3.4873` | `0.0781` | `3.2690` | `0.1250` | `593.76` | `0.41609` | yes |
| delay | Adaptive HyperLIF | `3.9760` | `3.5806` | `0.0469` | `3.4371` | `0.0625` | `269.27` | `0.26707` | yes |

## Interpretation

Safe claims:

- APEX-v2 G4 passed for recurrent and delay HyperLIF/Adaptive HyperLIF under the bounded smoke configuration.
- The readout-head loss decreases over multiple real SHD train batches for all four tested cells.
- APEX-v2 preserves the expected event/gate regime: HyperLIF is more event-rich than Adaptive HyperLIF, and Adaptive operates with lower gate mean.
- Delay HyperLIF was the strongest short smoke in this bounded configuration, reaching `0.1250` test accuracy over two held-out SHD batches.

Unsafe claims:

- Do not report these accuracies as paper-grade results.
- Do not claim full trunk training parity; this G4 keeps the APEX-v2 trunk fixed and trains the readout head only.
- Do not compare the bounded two-test-batch accuracies directly to the five-seed PyTorch or native APEX tables.

## Next Gate

G5 was completed later on 2026-07-19 and recorded in `P1_APEX_V2_THREE_SEED_PREFLIGHT_2026_07_19.md`.

Run G5 only if APEX-v2 will be included as a manuscript result rather than supplemental engineering evidence:

- three seeds
- more train/test batches
- same recurrent/delay x HyperLIF/Adaptive matrix
- paired with matching PyTorch fixed-trunk/readout-head smoke if needed

If the current paper remains focused on PyTorch tables plus calibrated native APEX dense validation, then this G4 result is sufficient as a traceability/supplementary APEX-v2 engineering note.
