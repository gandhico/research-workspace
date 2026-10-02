# Mathematics-to-code map

| Mathematical object | Julia implementation | Verification |
|---|---|---|
| Normalized lower/upper viability slack | `normalized_slacks` | center/boundary/outside tests |
| Scalar health margin and nested regions | `viability_health`, `viability_region` | exact region tests |
| Population regime priors | `RegimeSpec`, `default_regimes` | ordering/config tests |
| SHD training-only input gains (superseded) | `shd_calibrated_regimes` | frozen scale test + calibration CSV |
| SHD shared input gain and measured bands | `shd_shared_gain_regimes` | shared-gain sweep + ordering/band tests |
| Parameter-mean null regime | `mean_regime`, `matched_homogeneous_regime` | averaging and budget-matching tests |
| Budget-matched model families | `model_family` in `train_h5.jl` | equal hidden state; effective counts within 63 |
| Parameters the architecture reads | `effective_parameter_count` in `train_h5.jl` | budget-matching test |
| Risk-dependent population weights | `regime_weights` | normalization and endpoint argmax tests |
| Canonical HyperLIF step | P1 `HyperLIFLearning.neuron_step` | P1 100-assertion suite; P4 reuses package |
| Heterogeneous parameter blocks | `init_heterogeneous_parameters` | forward shape/finite tests |
| Learned/prior evidence fusion | `heterogeneous_forward` | normalized weights and gradient test |
| Cross-entropy through mixed populations | `heterogeneous_classification_loss` | finite Zygote gradient test |
| True event/occupancy rates | `population_activity` | depends on P1 upcrossing diagnostics |
| Slow threshold homeostasis | `update_homeostasis` | sign, bound, and frozen-gate tests |
| Threshold application | `apply_threshold_offsets` | implicit in runner; add dedicated drift test |
| Viability-gated plasticity | `plasticity_gate` | safe/boundary endpoint tests |
| Rate-band violation | `rate_band_penalty` | positive violation test |
| Box CBF inequalities | `cbf_constraints` | integrator-near-boundary test |
| Reference safety projection | `project_halfspaces`, `shield_action` | feasible and infeasible tests |
| Constant-current atlas | `experiments/regime_probe.jl` | `results/regime_atlas.csv` |
| Synthetic high-rate search | `calibrate_high_reactivity.jl` | ranked calibration CSV |
| Training-only activity calibration | `calibrate_dataset_activity.jl` | SHD calibration CSV |
| Exact-cache train/validation/test | `experiments/train_h5.jl` | timestamped JSON and checkpoint |
| Reachable crossing envelope | `experiments/reachable_rate_envelope.jl` | `results/reachable_rate_envelope.csv` |
| Shared-gain regime separation | `experiments/shared_gain_sweep.jl` | `results/shared_gain_sweep.csv` |
| Horizon versus input-statistics limiter | `experiments/horizon_probe.jl` | `results/horizon_probe.csv` |
| Matched triple driver | `experiments/run_matched_triple.sh` | `results/matched_triple/*/summary.json` |
| Matched-triple aggregation | `experiments/aggregate_matched.jl` | budget check, paired deltas, separation trace |

## Resolved by measurement

- Input gain is not a regime-setting lever on SHD; the crossing rate saturates near one event
  per neuron per sequence for every regime (F1 in `PROGRESS_REGISTER.md`).
- The saturation is caused by the input's zero-mean, high-variance fan-in, not by the 20-bin
  horizon: the same regimes separate under constant current at the same horizon (F2).

## Open mathematical checks

- ODE versus frozen-substep discrete parity under four current families.
- Gate release and depolarization-block inequalities over the empirical current envelope.
- Local Jacobian spectra and recurrence sensitivity; no global contraction claim yet.
- Monotonicity of high-reactivity arbitration weight over the chosen viability coordinate.
- Robust CBF margins for bounded model error and sampled-data effects.
- Feasibility and deadline analysis for the production QP.

