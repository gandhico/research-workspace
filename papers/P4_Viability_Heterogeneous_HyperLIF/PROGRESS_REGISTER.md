# Progress register

Updated: 2026-09-10 (second session)

| Workstream | Status | Evidence | Next gate |
|---|---|---|---|
| Literature/novelty | Initial primary-source map complete | `RESEARCH_PROGRAM.md` | Formal Scopus/WoS/GS query before priority language |
| Canonical equations | Reuses tested P1 package | local Julia path dependency | ODE/discrete/GPU parity audit |
| Viability geometry | Implemented | `code/src/ViabilityHyperLIF.jl`, tests | generalized nonlinear barriers |
| Heterogeneous populations | Forward and gradients implemented | Julia tests | see regime instantiation below |
| Constant-current atlas | Implemented | `code/results/regime_atlas.csv` | pulse/ramp/chirp and release tests |
| **Regime instantiation on real data** | **Negative result: per-regime input gain does not set the regime** | `reachable_rate_envelope.csv` | superseded by shared-gain profile |
| **Shared-gain regime profile** | **Implemented and measured** | `shared_gain_sweep.csv`, tests | confirm regimes survive training |
| SHD label-free activity calibration | Superseded; retained as record | `dataset_activity_calibration.csv` | — |
| Matched model families | Implemented and run | `matched_triple_aggregate.txt` | joint-readout variant (F6) |
| SHD train/validation/test | **Matched triple complete: heterogeneity loses** | 9 runs, 3 seeds | remove the late-fusion confound |
| Population homeostasis | **Prior paired pilot was vacuous; runner now detects this** | `homeostasis_effective` flag | non-vacuous gain-drift experiment |
| CBF reference shield | Implemented and tested | CBF tests | production QP, model error, deadline tests |
| Dynamic vision | Blocked on missing exact cache | workspace audit | recover N-MNIST/DVS HDF5/PT and verify hashes |
| Robot simulation | Not started | — | recognition gate and P3 interface design |
| Hardware | Not authorized by evidence | — | simulator safety gate |

## Verified local data

- SHD HDF5: `C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5`
- SHA-256: `6e5eb592c7530184daf83ecdff54ef4db34a42a45551195898a1e1a557c74738`
- Shape: 700 features × 20 bins × 2,000 train; 800 native test; 20 classes.
- Input statistics: 22.7% of entries nonzero, mean 0.580, std 1.338, max 13.0.
- Exact N-MNIST, DVS-Gesture-32/48, and SSC cache binaries: absent locally.

## Findings that change the program

### F1 — Per-regime input gain does not set the firing regime on this cache

Sweeping `input_scale` from 0.5 to 512 on training-only SHD input moves every regime to the
*same* ceiling of 0.049–0.061 upcrossings per neuron-step, that is, about one crossing per
neuron per 20-step sequence (`code/results/reachable_rate_envelope.csv`). At the previously
calibrated gains `(2, 4, 32, 32)` the burst population receives drive with standard deviation
52.9 against a threshold of 1.05, and 46.8% of its neuron-time steps already sit above
threshold, while its crossing count stays pinned at the ceiling. That is saturation, not
high-rate firing. The existing block screen misses it because occupancy (0.38–0.49) stays
below the 0.50 trigger while events are non-zero.

Two of the four calibrated gains, `regular=32` and `burst=32`, were the **maximum of the
search grid** rather than interior optima; the score in `dataset_activity_calibration.csv`
decreases monotonically to the grid edge for both.

### F2 — The 20-bin horizon is not the cause

Under synthetic constant current at the same 20-step horizon the burst regime still reaches
an event rate of 0.40, that is, 8 crossings per neuron. The horizon permits repeated
crossings; the SHD input statistics do not sustain them. Drive is approximately zero-mean
with variance dominated by the 700-channel random fan-in, so raising the gain scales a
symmetric noise distribution rather than moving neurons into a different regime: the fraction
of above-threshold neuron-time steps only moves from 0.468 to 0.502 between gains 32 and 512.

### F3 — A single shared gain restores separated regimes

At a shared gain of 1.4 the four regimes measure 0.0024 / 0.0057 / 0.0116 / 0.0221
upcrossings per neuron-step, in the intended order, with 9.1× separation and burst occupancy
0.037 (`code/results/shared_gain_sweep.csv`). A shared gain also removes an input
signal-to-noise confound: under per-regime gains any population difference conflates
intrinsic dynamics with input scale. `shd_shared_gain_regimes` implements this and re-derives
the target rate bands from the measured envelope so that they are reachable.

### F4 — The 2026-09-10 paired homeostasis pilot compared a model to itself

Both runs selected epoch 1, and threshold offsets were applied only *after* each epoch's
validation evaluation, so the selected configurations were the untouched reference
configurations in both cases. The two `test` dictionaries are byte-identical. The rate-band
penalty difference quoted previously (3.21e-5 versus 3.43e-5) compares epoch-3 *training*
values from checkpoints that were never selected; under homeostasis the penalty in fact rose
from 2.86e-5 at epoch 1, moving away from the bands. Separately, the burst threshold offset
reached -0.30 of a -0.40 clamp within two epochs because its target band midpoint of 0.17 is
unreachable on this cache. The runner now computes `homeostasis_effective` and warns when a
homeostasis run is numerically identical to its control.

### F5 — Event count is a diagnostic, not a computed signal, under the current readout

`readout=:hybrid_vr` builds features from time-averaged voltage and gate only; upward
crossings never enter the readout or the loss. The research question's "using less event
communication" is therefore not measurable under the current contract, because reducing
events costs the objective nothing. Testing that clause requires an event-carrying readout
(`:hybrid_zr`, or `learning_mode=:surrogate` with `:spike_count`).

### F6 — At matched budget on SHD, heterogeneity loses to both controls

Nine runs, three families, three seeds, equal total hidden state (64), effective parameter
spread 63 out of 47,445, shared-gain profile, homeostasis off, 720 training examples,
12 epochs, `results/matched_triple_aggregate.txt`:

| family | test mean | min | max | test loss range |
|---|---:|---:|---:|---|
| homogeneous (1 population, 64 units) | 0.4000 | 0.3925 | 0.4100 | 1.70-1.80 |
| ensemble (4 identical populations) | 0.3650 | 0.3400 | 0.3775 | 1.88-1.98 |
| heterogeneous (4 distinct regimes) | 0.3208 | 0.2675 | 0.3850 | 1.88-2.49 |

Seed-paired: heterogeneous minus ensemble -0.044 (wins 1/3); heterogeneous minus homogeneous
-0.079 (wins 0/3); ensemble minus homogeneous -0.035 (wins 0/3). Chance is 0.05. Three paired
seeds support no significance test, and none is reported.

The ordering is monotone and opposite to the hypothesis. Splitting the hidden budget into four
populations costs accuracy, and making those populations heterogeneous costs more on top.
Heterogeneous runs also carry the highest test loss and by far the widest seed spread.

Regime ordering was preserved in only 3/7, 4/11, and 7/12 epochs across the three seeds, so the
heterogeneity itself is unstable during training even though the separation ratio grows.

**This is not yet a clean test of heterogeneity, and the confound favours the conclusion.**
All three families fuse at the logit level: each population runs its own readout over its own
16 units and the four logit vectors are averaged. The homogeneous model instead runs one
readout jointly over all 64 units. So the comparison conflates *heterogeneous intrinsic
parameters* with *late fusion of four narrow classifiers*, and the monotone ordering
(1 wide > 4 identical > 4 distinct) is consistent with the partition being the dominant cost.
`RESEARCH_PROGRAM.md` already lists cross-population communication as a required ablation and
none is implemented. Before H2 is called falsified, the heterogeneous bank needs a joint
readout over all 64 units so the only difference from the homogeneous control is the intrinsic
parameters.

## Session evidence

1. All 44 package tests pass, including new budget-matching and shared-gain tests.
2. Reachable-rate envelope measured over 4 regimes × 18 gains × 3 seeds.
3. Shared-gain sweep measured over 18 shared gains × 4 regimes × 3 seeds; verdict gain 1.4.
4. Constant-current horizon probe at 20/50/100/500 steps isolating F2.
5. Three budget-matched families implemented and smoke-tested; effective parameter counts
   8976 (heterogeneous), 8976 (ensemble), 8913 (homogeneous) at total hidden 12.
6. Matched triple over three seeds at total hidden 64, 720 training examples: running.

## Next action

Add a joint readout over the concatenated population features and re-run the triple. That
removes the late-fusion confound and makes heterogeneous-versus-homogeneous a test of the
intrinsic parameters alone. If heterogeneity still loses under joint fusion, H2 is falsified on
this cache and the program should move to a longer-horizon cache or narrow to the mechanisms
that survive.
