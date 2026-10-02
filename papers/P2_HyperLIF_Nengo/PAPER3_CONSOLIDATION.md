# Paper 3 — Consolidation plan (merge `04` base + `05` θ_event + the app sweep)

> Paper 3 is closest to done: `04` has the manuscript draft (`paper/main.tex`), parity + gate-decoding
> experiments, and notes; `05` has the θ_event sweeps + GUI. This is the plan to consolidate them into
> one manuscript in the assembly order — most sections are **write-now** (data/figures exist).

Active Codex lane: see `PAPER3_WORKPLAN.md` for the current Paper 3-only workplan,
next experiments, claim boundary, and coordination boundary with Paper 2.

**Thesis (from `PAPER_NOTES.md`):** *the continuous-reset HyperLIF can be implemented as a clean,
equation-faithful, numerically-validated, Nengo-compatible component whose continuous gate is a
decodable readiness signal → a path to gate-state residual decoding for control.*
**Scope boundary:** owns the *implemented* dynamics, numerics, exact Nengo parity, gate decoding;
cites the theory manuscript for NSA/DB/flux-balance; control is future work.

## Unified structure → assets → status

| § | Section | Source | Status |
|---|---|---|---|
| 1 | Introduction | `04/paper/main.tex` | drafted; polish |
| 2 | Models (as implemented) | `04/MATH_CODE_MAP.md` | **write-now** ✅ |
| 3 | Fixed-point structure (DB onset `J_DB`, β-bound) | `04` | **write-now** ✅ |
| 4 | Numerical schemes (2 steppers vs RK4; stability/accuracy CSVs) | `04/results` | **write-now** ✅ |
| 5 | Nengo implementation & exact parity (**RMSE = 0**, shared kernel) | `04/experiments/05_python_vs_nengo` | **write-now** ✅ |
| 6 | Gate-state decoding (spike/voltage/gate/combined) | `04/experiments/04_gate_state_decoding` + `05` decoder | **write-now** ✅ |
| **6b** | **NEF app sweep (NEW)** — HyperLIF runs in the canonical models | `04/apps/smoke_integrator_oscillator.py` | **write-now** ✅ (extend) |
| 7 | θ_event (readout adaptation) — 0.95 → 217 vs 151 Hz; static + adaptive | `05` (sweeps, phase results, GUI) | **write-now** ✅ |
| 8 | Toward control (gate-state residual → attitude) | `04/PAPER_BRIDGE.md` + `Neuromorphic_Embodied_AI` | write-only (hypothesis) |
| 9 | *(optional)* ecosystem/backends (NengoDL/OpenCL/Loihi) | — | defer |
| 10 | Conclusion | — | write-only |

## Two consolidation actions

**(A) Fold `05` (θ_event) in as §7.** It is a separate project today but the same neuron and the same
"readout adaptation, not core-dynamics change" thesis. Its evidence (event rate 151→217 Hz at
θ_event 0.95; static + adaptive/homeostatic sweeps; NengoGUI visualizers) becomes §7. This also
resolves a tension surfaced by the new app sweep (below): base HyperLIF fires too sparsely for some
NEF loops, and θ_event is the principled fix.

**(B) Add the NEF app sweep as §6b (new evidence, Phase-A result).**
`04/apps/smoke_integrator_oscillator.py` drops HyperLIF/Adaptive into a Nengo **integrator** and
**oscillator** and compares to `nengo.LIF`. Result (proof-of-life that HyperLIF runs *inside the NEF*,
not just as a standalone neuron):

| neuron | integrator (value held) | oscillator (amplitude) |
|---|---:|---:|
| LIF | 0.29 | 0.60 |
| HyperLIF | 0.03 (weak) | 0.56 |
| Adaptive | 0.33 | 0.25 |

All three **build, run, and oscillate**; LIF and Adaptive integrate-and-hold; **base HyperLIF holds
weakly** because at `v_thresh = 1.0` it emits too few events for the integrator's recurrent rate loop
— exactly what §7's θ_event = 0.95 addresses. This is an honest, self-consistent finding that *links*
§6b ↔ §7 and motivates the full app sweep (memory · SPA cognition · online-learning · control) as the
paper's forward experimental program.

## Write order (all write-now first)
§2 → §3 → §4 → §5 → §6 → §6b → §7 (fold `05`) → §1 polish → §8 → §10. Then extend §6b (memory/SPA/
control apps) and, if pursued, §9 (backends/hardware).

**Net:** §2–§7 are write-now from existing `04`/`05` data + figures. Consolidation = merge `05` into
`04`'s manuscript, add §6b from the new app smoke, and write intro/control/conclusion.

## Consolidation status — 2026-07-04

Completed in `paper/main.tex`:

- added §6b / `sec:results-nef` from the canonical NEF integrator/oscillator
  smoke;
- generated `results/csv/08_nef_app_smoke.csv` and
  `results/logs/08_nef_app_smoke.txt`;
- folded the `05_Adaptive_Threshold_HyperLIF_Nengo` θ_event results into a new
  readout-adaptation section, `sec:thetaevent`;
- copied the key θ_event evidence into the Paper 3 project as
  `results/csv/09_theta_*`;
- updated `MATH_CODE_MAP.md`, `FIGURE_TABLE_MAP.md`, `RUNNERS.md`,
  `REPRODUCIBILITY.md`, and `RESULTS_AUDIT.md`.
- added `experiments/09_core_nengo_capability_sweep.py`, which runs a fast
  Core-Nengo smoke survey over communication, function representation, 2D
  transform, working memory, oscillator, and PES learning for LIF, HyperLIF
  θ=1.00/0.95, and Adaptive θ=1.00/0.95.

Current claim discipline:

- NEF app smoke is a Phase-A build/run result, not an optimized NEF benchmark.
- Static `theta_event=0.95` is the recommended immediate Nengo-channel baseline.
- Tuned adaptive θ_event is promising but remains exploratory until ensemble and
  seed-matched validation.
- The Core-Nengo capability sweep is a compatibility/calibration smoke because
  it uses approximate build-time rates for decoder solving. It proves the apps
  build/run and exposes calibration targets; it is not yet an optimized NEF
  benchmark.
