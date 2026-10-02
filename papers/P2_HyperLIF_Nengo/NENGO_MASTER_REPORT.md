# HyperLIF in Nengo — Master Report (for advisors)

*This folder — `04_Adaptive_HyperLIF_Nengo/05_Adaptive_HyperLIF_Nengo_Paper/` — is the **integrated home**
for the HyperLIF Nengo implementation. Everything below lives here or is indexed here. Nothing from the
older exploratory folders is authoritative except where explicitly imported. Date: 2026-07-04.*

## 0. One-paragraph summary
We built an equation-faithful, numerically-validated, **exactly Nengo-parity** reference implementation
of the continuous-reset HyperLIF / Adaptive HyperLIF neurons, and characterized them across the *entire*
Nengo capability spectrum and every simulation backend. The neuron runs as a first-class NengoCore
`NeuronType` on all nine canonical capabilities (representation, dynamics, memory, online learning,
cognition); once **calibrated** (θ_event, origin, rate-to-current) it matches or beats LIF on dynamics
and memory at ~3.5× fewer spikes; its one honest weakness is online-learning speed (a tunable firing-rate
trade); and it is **confined to the reference simulator** — the accelerated/hardware/DL backends reject a
custom continuous-gate neuron. The continuous gate is a decodable readiness signal, motivating a future
gate-state residual controller.

## 1. Complete contribution list (all results)
| # | Result | Evidence | Status |
|---|--------|----------|--------|
| 1 | Exact Python↔Nengo parity (voltage/gate/gain RMSE = 0, shared kernel) | `07_python_vs_nengo.csv`, `fig_parity` | core ✅ |
| 2 | DB fixed-point: onset `J_DB=2.4`, latched `J/(1+τG_b)`, β-bound | `03_db_analysis.csv`, `fig_db`, `fig_fi` | core ✅ |
| 3 | Numerical schemes: exponential (stable) vs Euler (cond.) | `06_stability.csv`, `fig_integration` | core ✅ |
| 4 | Continuous vs hard reset; fixed vs adaptive conductance | `01/02_*.csv`, `fig_step`, `fig_stress` | core ✅ |
| 5 | Gate-state decoding (readiness): gate/voltage/event/combined | `05_gate_state_decoding.csv`, `fig_decode` | ✅ (single-neuron) |
| 6 | θ_event readout adaptation (151→218 Hz; static + tuned adaptive) | `09_theta_*.csv`; `05_Adaptive_Threshold/` figs | ✅ |
| 7 | **Operating-point calibration → useful across apps (T023)** | `12_origin_aware_calibration_summary.csv`, `fig_candidate_*` | ✅ NEW |
| 8 | **Capability matrix — all 9 blocks run; calibration beats LIF on dyn/memory** | `13_*.csv`, `fig_nengo_capability`a | ✅ NEW |
| 9 | **Backend portability wall (OCL/Loihi reject; DL version-locked)** | `14_backend_portability_probe.py` | ✅ NEW |
| 10 | **Efficiency ↔ learning-speed trade (PES rate curve)** | `15_pes_rate_matched.csv`, `fig_nengo_capability`b | ✅ NEW |
| 11 | Control bridge: gate-state residual → attitude | `PAPER_BRIDGE.md` | hypothesis / future |

## 2. Asset inventory
- **Manuscript:** `paper/main.tex` (13 sections + 3 appendices) — the drafted paper. Tables in
  `paper/tables/`, figures in `paper/figures/`.
- **Experiments (self-contained, reproducible):** `experiments/01…16` — from parity/DB/numerics up to
  the capability matrix (13), backend probe (14), PES rate curve (15), NengoDL probe (16).
- **Results:** `results/csv/01…15` (every number regenerable).
- **Figures (paper set):** `fig_step, fig_stress, fig_fi, fig_db, fig_integration, fig_parity, fig_decode,
  fig_candidate_{robustness_heatmap,score_events,rate_calibration}, fig_nengo_capability`.
- **Findings docs:** `NENGO_CAPABILITY_FINDINGS.md` (today's matrix + limits), `CANDIDATE_RESULTS.md`
  (T023 selection), `PAPER_NOTES.md`, `PAPER3_WORKPLAN.md`, `MATH_CODE_MAP.md`, `REPRODUCIBILITY.md`.
- **Imported/related (indexed, not moved):** base reference figures in
  `04_Adaptive_HyperLIF_Nengo/results/figures/`; θ_event sweeps + GUI in
  `05_Adaptive_Threshold_HyperLIF_Nengo/`; Nengo-transfer notes + decoder ablation precursors in
  `01_Adaptive_HyperLIF/.../Adaptive_HyperLIF_Audit_Repair/`.

## 3. Publication strategy — honest recommendation
**Bottom line: one focused paper, not a dense everything-paper and not 2–3 spin-offs.** The Nengo work
is a single coherent story; fragmenting it thins each piece, and over-densifying dilutes the contribution
and confuses reviewers. θ_event and calibration are *sections*, not papers.

**On "high-impact journal," honestly:** as it stands this is a **strong specialized-venue paper**
(Neuromorphic Computing & Engineering [IOP], Neural Computation, IEEE TNNLS, or Frontiers in
Neuroscience: Neuromorphic Engineering) — a rigorous, honest reference implementation + full
characterization. That is genuinely valuable and very publishable. But a *flagship high-impact* venue
usually needs a surprising capability or a demonstrated new ability — and two of our headline results are
honest *limitations* (backend wall, learning-speed trade), which are scientifically excellent but temper
the "wow." The missing high-impact hook is the **gate-state residual controller** (currently future work):
a closed-loop demonstration where the continuous gate does something LIF's discarded sub-threshold state
cannot. That is the differentiator that lifts this from "solid reference" to "high-impact."

**Two viable paths (pick by timeline vs ceiling):**
- **Path A — submit soon (recommended if you want a strong publication now):** the current single paper
  (parity + DB + numerics + gate decoding + θ_event + calibration + capability + portability) to a strong
  specialized venue. It is ~one focused editing pass from submittable, and the honesty is a strength there.
- **Path B — swing for high-impact:** hold the same single paper, **add the gate-state closed-loop control
  demonstration** (the `PAPER_BRIDGE` experiment with real, seed-matched results), and target a
  higher-impact venue. Higher ceiling, longer timeline.

**On "report everything to advisors":** do it via *this master report + the reproducible repo*, and keep
the *paper* focused. Advisors see the full body of work here and decide scope; the manuscript stays crisp.
That satisfies both goals without a bloated draft. My recommendation: give advisors this report + the
current `main.tex`, and ask them to choose Path A vs Path B — framed by the one question that decides it:
*is there appetite/time to add a control demonstration?* If yes → Path B, one high-impact paper. If no →
Path A, one strong paper now. Either way it stays a **single** paper.
