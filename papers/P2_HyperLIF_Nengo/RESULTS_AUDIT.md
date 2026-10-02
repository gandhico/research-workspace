# Results Audit

An honest classification of every result in the paper: what is **validated**
(directly measured/derived and cross-checked), what is **exploratory**
(illustrative, parameter-dependent, or single-instance), what is
**paper-ready**, and what is explicitly **future work**. Supporting data files
are named for each item.

Legend: ✅ validated · 🔬 exploratory/illustrative · 🔮 future work.

## Core validated results (paper-ready)

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | **Python `stable` stepping == Nengo port, exactly.** Voltage/gate RMSE `= 0`, max\|Δ\| `= 0`, event mismatch `= 0`, for HyperLIF and Adaptive, on step and stress protocols. | ✅ paper-ready | `07_parity_metrics.csv`, `07_python_vs_nengo.csv`; mechanism: shared kernel (`MATH_CODE_MAP.md`) |
| 2 | **DB onset is `J_DB = (v_thresh−γ)(1+τG_b) = 2.4`** for the reference parameters, matching the simulated firing collapse at `J≈2.3–2.4`. | ✅ paper-ready | `03_db_analysis.csv`, `03_current_sweep.csv` |
| 3 | **Fixed-gain latched voltage `v*=J/(1+τG_b)`**: predicted `1.3333` vs simulated `1.3333` at `J=4` (exact). | ✅ paper-ready | `03_db_analysis.csv` (`..._pred_at_I4`, `..._sim_at_I4`) |
| 4 | **Adaptive avoids the high-voltage latch**: asymptotic open-gate voltage `0.625 < 0.8` (gate knee), and `β=80 > 62.5 = 1/(τ(v_thresh−γ))`. | ✅ paper-ready | `03_db_analysis.csv`, `03_equilibria.csv` |
| 5 | **Adaptive widens the firing band and raises peak rate** (`[1.6,3.5]`, 151 Hz vs `[1.5,2.2]`, 73 Hz), with bounded mean voltage ≈0.9. | ✅ paper-ready | `03_current_sweep.csv`, `tab_sweep.tex` |
| 6 | **Both stepping schemes are first-order convergent** to the RK4 reference; gate error identical (shared update). | ✅ paper-ready | `06_integration_accuracy.csv` |
| 7 | **Exponential update is unconditionally stable; explicit Euler overshoots once `λΔt>2`.** | ✅ paper-ready | `06_stability.csv` |
| 8 | Continuous reset replaces the LIF hard reset; gate cycles can exceed event count (sub-threshold readiness). | ✅ paper-ready | `01_lif_vs_hyperlif.csv` |

## Honestly-qualified / exploratory results

| # | Claim | Status | Note |
|---|---|---|---|
| 9 | **Gate-state decoding** of a readiness target (test RMSE `0.287`), comparable to voltage→current (`0.258`) and better than filtered-events→current (`0.321`). | 🔬 paper-ready *as an illustrative single-neuron decoding study* | `05_decoding_metrics.csv`. Scalar least-squares, one neuron, fixed 70/30 split; the raw gate is spiky and its decode is noisy. Not an ensemble/NEF claim. |
| 10 | **Adaptive HyperLIF has its own finite-β operating ceiling** (`J≳3.6` here): spiking ceases at a *bounded sub-threshold* equilibrium (graceful self-silencing), unlike the fixed-gain high-voltage latch. | 🔬 reported honestly | `03_current_sweep.csv` (rate→0, mean V≈0.9), `03_equilibria.csv` (`v*≈0.86`, `r*≈0.7`). This is empirical; the exact ceiling is parameter-dependent. |
| 11 | The DB onset is derived from a **frozen-gate fixed-point** argument (sufficient condition), not a full bifurcation analysis. | 🔬 method caveat | Matches simulation but stated as such in the paper (Limitations). |
| 12 | Numerical accuracy: in the convergent regime the **explicit scheme had slightly lower trajectory RMSE** than the exponential scheme. | ✅ reported honestly | `06_integration_accuracy.csv`. The exponential scheme's advantage is *stability*, not accuracy — stated explicitly. |
| 13 | **Phase-A NEF app smoke**: LIF and Adaptive integrate/hold; base HyperLIF runs but holds weakly; all three show nonzero oscillator response. | 🔬 smoke-test result | `08_nef_app_smoke.csv`, `08_nef_app_smoke.txt`. This is a build/run qualitative check, not an optimized NEF benchmark. |
| 14 | **Static θ_event=0.95** widens the settled active current band and raises peak settled event rate (151.14 → 217.83 Hz) without changing continuous gate/reset dynamics. | 🔬 paper-ready as readout-adaptation evidence | `09_theta_static_event_threshold_summary.csv` copied from project `05`. Too-low θ_event=0.80 is a falsification case. |
| 15 | **Tuned adaptive θ_event** can improve event-only and combined-state decoding in the single-neuron protocol, but raw event count alone is not enough. | 🔬 exploratory | `09_theta_decoder_comparison.csv`, `09_theta_adaptive_rule_tuning_top.csv`. Needs ensemble/seed-matched validation. |
| 16 | **Core-Nengo app compatibility sweep**: communication, function representation, transform, working memory, oscillator, and PES-learning smoke models all build/run for LIF, HyperLIF θ=1.00/0.95, Adaptive θ=1.00/0.95, and static-origin variants (`v_reset=-0.6`, `min_voltage=-2.0`). | 🔬 calibration-smoke result | `10_core_nengo_capability_sweep.csv`, `10_core_nengo_capability_sweep.txt`. All 54 app×variant combinations ran. Uses approximate build-time rates for custom-neuron decoder solving; decoded RMSE values are not final optimized benchmarks. |
| 17 | **Static origin is a mixed Nengo calibration signal**, not yet a clean improvement: at θ=0.95 it improves HyperLIF communication RMSE (`0.346→0.217`) and PES late-error RMSE for HyperLIF/Adaptive (`0.631→0.549`, `0.546→0.497`), but worsens transform, working-memory, and oscillator smoke metrics. | 🔬 issue-finding result | `10_core_nengo_capability_sweep.csv`, `10_core_nengo_capability_sweep.txt`. In this fast sweep origin often raises event rates, suggesting the approximate build-time rate proxy is not origin-aware. Needs origin-aware gain/rate fitting and seed sweeps before any performance claim. |
| 18 | **Origin-aware calibration improves universality within the current priority set**: the best HyperLIF-family candidate is θ_event=`0.95`, static origin (`v_reset=-0.6`, `min_voltage=-2.0`), and `rate_to_current=140`, with no bad apps across communication, function, transform, memory, oscillator, and PES smoke tests. | 🔬 candidate-selection evidence | `12_origin_aware_calibration_sweep.csv`, `12_origin_aware_calibration_summary.csv`, `12_origin_aware_calibration_sweep.txt`, plus `fig_candidate_*`. All 126 priority app×candidate runs completed. Treat as a robust candidate, not a final universal Nengo guarantee; needs seed sweeps and final decoder calibration. |
| 19 | **Three-seed core capability preflight**: T001/T002/T023/T033 complete communication, function, transform, integrator, oscillator, working memory, and PES learning with 84/84 simulations and zero failures. T023 is the best low-rate HyperLIF candidate for NEF computation/dynamics; T033 is the better HyperLIF-family PES/memory candidate. | ✅ paper-ready as preflight evidence | `17_capability_seed_sweep.csv`, `17_capability_seed_sweep_summary.csv`, and `results/logs/17_capability_seed_sweep_preflight_20260719.log`. Use as seed-matched methods evidence; run `--paper` if the final venue requires five seeds. |
| 20 | **Backend portability wall**: the custom continuous-gate neuron runs in NengoCore but is not currently accepted by OpenCL, Loihi, or NengoDL without backend-specific engineering. | ✅ paper-ready as limitation evidence | `experiments/14_backend_portability_probe.py`; summarized in `NENGO_CAPABILITY_FINDINGS.md` and `tab:backend`. This is a framework portability result, not a claim about theoretical impossibility. |
| 21 | **Efficiency versus PES learning-speed trade**: calibrated HyperLIF is much sparser in representation tasks, but online PES convergence remains slower than LIF at matched time; rate tuning improves HyperLIF PES error but does not erase the ceiling in the current task. | 🔬 paper-ready as a bounded operating-point trade | `15_pes_rate_matched.csv`, `fig_nengo_capability`, and `tab:capability-calib`. Claim is limited to the matched-time PES channel-learning setup. |
| 22 | **Five-seed scalar NEF state-decoder ablation**: normal Nengo decoding is stable for LIF, calibrated HyperLIF T023, and Adaptive T033; at much lower firing rates, T023/T033 expose useful internal-state readouts. The reset-gate decoder reaches `0.1110 +/- 0.0064` for T023 and `0.1269 +/- 0.0073` for T033; combined-state readouts reach `0.1106 +/- 0.0212` for T023 and `0.1167 +/- 0.0141` for T033. | ✅ paper-ready as bounded scalar-NEF state-readout evidence | `18_nef_decoder_state_ablation.csv`, `18_nef_decoder_state_ablation_summary.csv`, and `results/logs/18_nef_decoder_state_ablation.txt`. Current paper run uses 5 seeds, 100 neurons, 1.2 s, ridge `0.01`, minimum feature scale `0.05`, and z-score clipping at `20`. Claim is limited to a scalar represented-signal channel, not closed-loop control or high-dimensional task decoding. |

## Future work (explicitly not claimed as results)

| # | Item | Status |
|---|---|---|
| 23 | Gate-state **residual decoding for quaternion attitude control** (the `error → J → (v,r,spikes) → residual → torque` pipeline). | 🔮 design + hypothesis only; **no closed-loop results** |
| 24 | Capability expansion beyond the current seven-app seeded core and nine-app matrix: controlled Lorenz dynamics, larger NengoSPA tasks, and control examples. | 🔮 |
| 25 | NEF **ensemble** experiments (tuning curves, multi-neuron decoding, noise robustness), including θ_event=0.95, tuned adaptive θ_event, and origin-aware calibration. | 🔮 |
| 26 | Decoder ablations beyond the current scalar channel: higher-dimensional channels, readiness targets, tuned adaptive thresholds, and residual-control targets. | 🔮 |
| 27 | Mapping `r(t)` to **local plasticity** as a low-memory alternative to BPTT; OpenCL/NengoDL/Loihi/FPGA backend sweeps and hardware metrics. | 🔮 |

## Scope notes carried into the paper

- The parameters (`tab_params.tex`) are a **normalized reference set** chosen for
  clean demonstration; they differ from the benchmark-scale training parameters
  of the theory manuscript. Specific numbers (`J_DB=2.4`, `β_crit=62.5`) are
  parameter-dependent instances of the general relations, not universal
  constants. Stated in the paper's Limitations.
- No N-MNIST / DVS / BPTT training results are claimed here — those belong to the
  theory manuscript. This paper's contribution is the validated reference
  implementation and its numerical/structural analysis.
