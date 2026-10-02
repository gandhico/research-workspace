# Advisor Report: Current APEX Status for HyperLIF Learning

Date: 2026-07-19

## Executive Summary

The current APEX engine works as a native Julia/CUDA implementation and is useful for cross-framework validation. It successfully loads the same SHD-wide HDF5 cache used by the PyTorch experiments, trains LIF and HyperLIF/NSA cells end-to-end, and produces reproducible CSV summaries.

Scientifically, the result is mixed but useful:

- Positive: APEX reproduces a small calibrated dense-cell HyperLIF/NSA advantage over matched dense LIF on SHD-wide.
- Negative/limited: The current APEX recurrent and delay modes do not reproduce the stronger PyTorch RSNN/delay HyperLIF advantage.
- Interpretation: this is not evidence against HyperLIF; it shows that the older APEX architecture/readout design is not yet equivalent to the successful PyTorch recipes.

Recommended next step: report the current APEX result as an honest native-engine audit, then create an APEX-v2/PyTorch-parity implementation that ports the successful PyTorch architectures directly into Julia/APEX.

Update after the first APEX-v2 pass: APEX-v2 now passes forward/readout sanity, structural PyTorch trace comparison, and shared-weight PyTorch-to-Julia/APEX-v2 value comparison on the same SHD-wide first batch. Separately, a native APEX recurrent/delay tuning probe shows that original APEX is architecture-sensitive: recurrent HyperLIF has a promising but high-variance default-gamma regime, while fixed-delay APEX remains limited.

## What Was Validated

Implemented and tested in:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_shd_ranking_smoke.jl`

The runner now supports:

- `--architectures=dense,recurrent,delay`
- `--models=lif,hyperlif`
- HyperLIF/NSA tuning knobs: `--beta`, `--gamma`, `--g-base`, `--tau-r`, `--tau-soma`, `--num-micro`
- APEX-native HDF5 loading from `shd_wide_T20.h5`
- Raw, epoch, and summary CSV outputs

The APEX project imports successfully, CUDA is functional, the SHD cache is read correctly as `[F,N,T] = [700,2000,20]`, and all tested modes run without CUDA/runtime failure.

## Dense APEX Result

The default APEX HyperLIF/NSA parameters were not enough:

| Model | Epochs | Seeds | Test accuracy | Test loss |
|---|---:|---:|---:|---:|
| LIF control | 3 | 5 | `0.1281 +/- 0.0477` | `2.6743` |
| HyperLIF/NSA default | 3 | 5 | `0.1206 +/- 0.0583` | `2.7421` |

After calibration, stronger gate feedback recovered the expected direction:

| Model | HyperLIF setting | Epochs | Seeds | Test accuracy | Test loss |
|---|---|---:|---:|---:|---:|
| LIF control | `use_nsa=false` | 10 | 5 | `0.2411 +/- 0.0778` | `2.3359` |
| Tuned HyperLIF/NSA | `beta=0.10`, `gamma=0.80` | 10 | 5 | `0.2490 +/- 0.0666` | `2.2768` |

Advisor-facing claim:

The current APEX implementation supports a calibrated dense HyperLIF/NSA advantage over matched dense LIF on the same SHD-wide cache. The result is small, but it is valuable because it is cross-framework and uses APEX's native GPU kernel.

## Recurrent and Delay APEX Result

A one-batch compile smoke passed for dense, recurrent, and delay. A larger bounded recurrent/delay preflight also passed:

| Architecture | Model | Seeds | Epochs | Test accuracy | Test loss |
|---|---|---:|---:|---:|---:|
| delay | LIF control | 3 | 3 | `0.1085 +/- 0.0131` | `2.8326` |
| delay | HyperLIF/NSA | 3 | 3 | `0.0781 +/- 0.0306` | `2.9265` |
| recurrent | LIF control | 3 | 3 | `0.1176 +/- 0.0072` | `2.8432` |
| recurrent | HyperLIF/NSA | 3 | 3 | `0.0955 +/- 0.0202` | `2.8578` |

Advisor-facing claim:

APEX recurrent and delay modes now run end-to-end, but the current APEX design does not yet reproduce the PyTorch recurrent/delay advantage. This should be treated as an architecture-portability gap, not as a negative result for HyperLIF.

## Why APEX Differs From the Successful PyTorch Runs

The PyTorch RSNN result used:

- `fc_in(X_t) + fc_rec(prev_spk)` recurrence
- the parity-validated HyperLIF PyTorch cell
- batch-normalized readout features
- selectable readouts including spike count, membrane mean, gate mean, `[v,r]`, and `[v,r,G]`

The PyTorch delay result used:

- a learnable depthwise temporal-current convolution
- pass-through initialization
- the same readout assembly used across the PyTorch architecture zoo

The current APEX recurrent/delay paths use:

- APEX-native `EPropHyperLIFLayer`
- APEX-native V11 readout
- fixed causal `SpikingDelayLayer` after the hidden neuron
- no exact PyTorch-style hybrid readout feature assembler yet

Therefore the APEX recurrent/delay tests are architecture-family approximations, not direct ports.

## APEX-v2 PyTorch-Parity Result

APEX-v2 is the direct architecture port. It now implements:

- dense/feedforward current projection
- recurrent/RSNN current update: `fc_in(X_t) + fc_rec(prev_spk)`
- PyTorch-style temporal-current delay kernel with pass-through initialization
- PyTorch-style readout features: spike count, membrane mean, gate mean, `[r,G]`, `[v,r]`, and `[v,r,G]`

Shared-weight first-batch comparison passed for `hybrid_vr`:

| Architecture | Neuron | Feature max abs | Logit max abs | Status |
|---|---|---:|---:|---|
| dense | HyperLIF | `8.58e-06` | `6.66e-06` | passed |
| recurrent | HyperLIF | `8.58e-06` | `5.01e-06` | passed |
| delay | HyperLIF | `1.05e-05` | `7.33e-06` | passed |
| dense | Adaptive HyperLIF | `1.98e-04` | `1.83e-04` | passed under Float32 envelope |
| recurrent | Adaptive HyperLIF | `5.08e-04` | `4.35e-04` | passed under Float32 envelope |
| delay | Adaptive HyperLIF | `3.52e-04` | `1.50e-04` | passed under Float32 envelope |

Advisor-facing interpretation:

APEX-v2 is no longer just structurally similar to PyTorch. With shared weights, it reproduces the PyTorch dense, recurrent, and delay forward values for HyperLIF and Adaptive HyperLIF. The remaining question is training behavior, not forward implementation fidelity.

APEX-v2 also passed the first bounded train/eval smoke with fixed trunk and trained readout head:

| Architecture | Neuron | Initial train loss | Final train loss | Final test accuracy | Stable |
|---|---|---:|---:|---:|---|
| recurrent | HyperLIF | `3.9882` | `3.4730` | `0.0625` | yes |
| recurrent | Adaptive HyperLIF | `3.9679` | `3.5511` | `0.0469` | yes |
| delay | HyperLIF | `3.9185` | `3.4873` | `0.1250` | yes |
| delay | Adaptive HyperLIF | `3.9760` | `3.5806` | `0.0625` | yes |

This result should be framed as G4 engineering evidence. It proves stable multi-batch learning of the readout head over APEX-v2 features, but it is not yet a full trunk-training or multi-seed accuracy claim.

A three-seed bounded preflight also passed:

| Architecture | Neuron | Mean train-loss drop | Test accuracy mean/std | Stable |
|---|---|---:|---:|---|
| recurrent | HyperLIF | `0.4810` | `0.0807 +/- 0.0197` | yes |
| recurrent | Adaptive HyperLIF | `0.4345` | `0.0755 +/- 0.0430` | yes |
| delay | HyperLIF | `0.4338` | `0.0729 +/- 0.0451` | yes |
| delay | Adaptive HyperLIF | `0.4026` | `0.0599 +/- 0.0119` | yes |

Advisor-facing interpretation:

APEX-v2 is stable across seeds and trains the readout head over the transferred PyTorch-style features. However, the bounded accuracy ordering is not strong enough to promote APEX-v2 into the main result table without a larger G6 run. I recommend using APEX-v2 as supplementary traceability for now while keeping the main P1 evidence on the stronger PyTorch architecture tables plus calibrated native APEX dense validation.

## Recommended Message to Advisors

The current APEX engine is technically operational and scientifically informative. It validates that HyperLIF/NSA can run in the native Julia/CUDA stack and gives a small positive dense-cell reproduction after gate-feedback calibration. However, the older APEX design does not yet reproduce the strongest PyTorch architecture results in recurrent and delay networks. The next step should be a new APEX-v2 implementation that ports the successful PyTorch architectures directly, rather than continuing to tune the old APEX recurrent/delay approximations.

## Recommended Next Step

Create an APEX-v2/PyTorch-parity branch or folder with:

1. PyTorch-equivalent RSNN layer: `fc_in + fc_rec(prev_spk)`.
2. PyTorch-equivalent learnable delay layer: depthwise temporal-current kernel with pass-through initialization.
3. PyTorch-equivalent readout assembler: spike count, membrane mean, gate mean, `[v,r]`, and `[v,r,G]`.
4. Shared result schema across PyTorch and Julia: same seeds, same cache, same split, same readout names, same tables.
5. A short parity ladder: forward trace parity, one-batch gradient sanity, one-seed training smoke, three-seed preflight, five-seed paper-grade run.

## Paper Impact

P1 should keep the current native APEX result as a calibrated dense cross-framework validation and report original APEX recurrent/delay limitations honestly. APEX-v2 can now be introduced as the direct PyTorch-parity implementation layer, but it should not be used for paper-grade recurrent/delay accuracy claims until one-seed and multi-seed APEX-v2 training runs are complete.

Readiness after the APEX-v2 G5 preflight was 96%. After integrating APEX-v2 into the IEEEtran manuscript as traceability evidence, verifying the bibliography metadata, generating the final-statistics audit, updating the main quantitative tables with five-seed sample standard deviations and zero-failure framing, and rebuilding the package successfully, current P1 readiness is 98%. The remaining gates are author/funding/repository metadata, final copyedit, and advisor approval.
