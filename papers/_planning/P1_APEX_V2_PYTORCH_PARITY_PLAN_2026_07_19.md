# P1 APEX-v2 PyTorch-Parity Plan

Date: 2026-07-19

Purpose: define the next engineering stage after reporting the current APEX-as-designed audit.

## Goal

Build a new APEX implementation that follows the successful PyTorch architecture harness closely enough that results can be compared as true cross-framework architecture validation.

The current APEX engine should be preserved as APEX-as-designed. APEX-v2 should be treated as a PyTorch-parity validation layer, not a replacement for the original engine.

## Target Architectures

### 1. Dense / Feedforward

Reference PyTorch behavior:

- one hidden spiking layer
- same neuron variants
- same readout assembly
- batch-normalized classifier

APEX-v2 requirement:

- preserve current dense result
- add PyTorch-style readout feature assembler
- compare LIF, PLIF if available, ALIF if available, HyperLIF, Adaptive HyperLIF

### 2. RSNN

Reference PyTorch behavior:

```text
cur_t = fc_in(X_t) + fc_rec(prev_spk)
spk_t, state_t = neuron(cur_t, state_{t-1})
prev_spk = spk_t
readout = assemble(vbar, rbar, gbar, spk_sum)
```

APEX-v2 requirement:

- implement an explicit `RSNNParityLayer`
- keep `prev_spk` recurrence separate from APEX e-prop assumptions at first
- expose exact HyperLIF/LIF toggle
- log membrane, gate, conductance, and spike-count traces

### 3. Learnable Delay

Reference PyTorch behavior:

```text
cur = fc_in(X)                         # [B,T,H]
cur = depthwise_temporal_conv(cur)     # learnable per-hidden-channel delay kernel
spk_t, state_t = neuron(cur_t, state)
readout = assemble(vbar, rbar, gbar, spk_sum)
```

APEX-v2 requirement:

- implement a learnable temporal-current delay kernel, not only fixed axonal spike delays
- initialize the kernel as pass-through
- support kernel size 7 first
- record learned delay kernels as a figure/table candidate

## Required Readouts

The strongest PyTorch evidence depends on readout parity. APEX-v2 must implement:

- `spike_count`
- `membrane`
- `gate`
- `hybrid_gr`
- `hybrid_vr`
- `hybrid_vr_conductance`

The readout table must use the same feature definitions as PyTorch:

- `vbar`: time-average membrane
- `rbar`: time-average gate or adaptive state
- `gbar`: time-average conductance proxy
- `spk_sum`: spike count over time

## Validation Ladder

Do not jump directly to paper-grade experiments. Use this ladder:

| Gate | Scope | Pass criterion |
|---|---|---|
| G1 | shape/import smoke | model builds, CUDA functional, no allocation mismatch |
| G2 | one-batch forward trace | finite logits, finite states, expected feature dimensions |
| G3 | one-batch train | finite loss and gradients |
| G4 | one-seed smoke | improving or stable training curve |
| G5 | three-seed preflight | no NaNs, credible ordering or clear diagnostic |
| G6 | five-seed paper run | mean/std and paired tests ready for manuscript |

## Result Schema

Use one CSV schema across PyTorch and APEX-v2:

```text
framework,dataset,architecture,neuron,readout,seed,epochs,
test_accuracy,test_loss,events_per_sample,gate_mean,
stable,nan_batches,provenance,raw_csv,summary_json
```

## Decisions Needed

- Whether ALIF/PLIF should be implemented natively in APEX-v2 or kept as PyTorch-only reviewer baselines.
- Whether APEX-v2 should preserve V11 as an optional readout or use PyTorch-style readouts as the main validation surface.
- Whether APEX-v2 lives inside `08_HyperLIF_Architectures\julia\apex_v2` or as a new sibling project.

Recommended initial location:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_v2`

## First Implementation Sprint

1. [x] Create `apex_v2` folder and a minimal Julia module.
2. [x] Implement `ReadoutFeatureAccumulator` for `vbar`, `rbar`, `gbar`, and `spk_sum`.
3. [x] Implement dense parity forward runner first.
4. [x] Add RSNN parity forward path.
5. [x] Add learnable-delay forward path with pass-through initialization.
6. [x] Run G1/G2 on SHD-wide HDF5 cache: 54/54 finite forward checks passed on 2026-07-19.
7. [x] Run PyTorch-vs-APEX-v2 trace summary comparison on the same first batch: 54 matched rows, 0 structural failures.
8. [x] Run G3 one-batch readout-head training sanity: recurrent HyperLIF `hybrid_vr` loss decreased from `4.083514` to `1.792870` over 20 frozen-feature readout updates.
9. [x] Export PyTorch first-batch trace summaries for direct APEX-v2 comparison: 54/54 finite PyTorch rows on the same SHD-wide HDF5 first batch.
10. [x] Run structural PyTorch-vs-APEX-v2 trace comparison: 54 matched rows, 0 missing rows, 0 structural failures.
11. [x] Run value-level/shared-weight trace comparison. Completed for dense/recurrent/delay HyperLIF and Adaptive HyperLIF with `hybrid_vr` on the SHD-wide first batch.
12. [x] Run one-seed APEX-v2 train/test smoke for recurrent and delay HyperLIF/Adaptive HyperLIF. G4 passed on 2026-07-19 with stable fixed-trunk/readout-head training over real SHD batches.
13. [x] Run G5 three-seed APEX-v2 preflight for the same bounded fixed-trunk/readout-head setting.
14. [ ] Run a larger G6 APEX-v2 experiment only if APEX-v2 is promoted from supplementary traceability to a main manuscript result.

## Shared-Weight Parity Result

Added:

- `scripts\export_pytorch_apex_v2_fixture.py`
- `julia\apex_v2\apex_v2_shared_weight_trace_compare.jl`
- `scripts\run_apex_v2_shared_weight_trace_compare.ps1`

Passing result surface:

- HyperLIF dense/recurrent/delay: feature max abs `8.6e-06` to `1.05e-05`; logits `5.0e-06` to `7.3e-06`.
- Adaptive HyperLIF dense/recurrent/delay: feature max abs `1.98e-04` to `5.08e-04`; logits `1.50e-04` to `4.35e-04`.

Conclusion: APEX-v2 now reproduces the PyTorch portable architecture cores at shared-weight forward-value level. Training parity remains the next gate.

## G4 Train/Eval Smoke Result

Added:

- `julia\apex_v2\apex_v2_train_eval_smoke.jl`
- `scripts\run_apex_v2_train_eval_smoke.ps1`

Configuration:

- `recurrent,delay x hyperlif,adaptive`
- `hybrid_vr`
- seed `1`
- epochs `2`
- train batches `4`
- test batches `2`
- batch size `64`
- hidden `64`

Result:

- all four cells stable
- `nan_batches=0`
- train loss decreased for every cell
- final bounded test accuracies: recurrent HyperLIF `0.0625`, recurrent Adaptive `0.0469`, delay HyperLIF `0.1250`, delay Adaptive `0.0625`

This is a fixed-trunk/readout-head G4 smoke. It supports APEX-v2 engineering readiness but is not a paper-grade accuracy table.

## G5 Three-Seed Preflight Result

Added:

- `scripts\run_apex_v2_train_eval_preflight.ps1`
- `--seeds` support in `julia\apex_v2\apex_v2_train_eval_smoke.jl`

Result:

- all four cells stable across three seeds
- `nan_total=0`
- train loss decreased for every seed/cell
- mean test accuracies: recurrent HyperLIF `0.0807 +/- 0.0197`, recurrent Adaptive `0.0755 +/- 0.0430`, delay HyperLIF `0.0729 +/- 0.0451`, delay Adaptive `0.0599 +/- 0.0119`

Decision: APEX-v2 should stay supplementary/traceability evidence unless a larger G6 run is requested.

## IEEE Manuscript Integration

APEX-v2 was integrated into the IEEEtran package on 2026-07-19 as traceability evidence:

- added `tab:apex-v2-traceability`
- updated Discussion and Limitations
- updated `FIGURE_TABLE_MAP.md` and `README_OVERLEAF.md`
- rebuilt `main.pdf` successfully

This does not change the main accuracy claim surface; it strengthens reproducibility and implementation traceability.

## Paper Strategy

Current P1 remains submittable with the existing dense APEX calibration and PyTorch architecture tables. APEX-v2 is the next strengthening step. If APEX-v2 reproduces RSNN/delay advantages, it can become:

- a stronger revision package for P1,
- a supplementary cross-framework section,
- or a separate short methods/engineering contribution on PyTorch-to-Julia SNN parity.
