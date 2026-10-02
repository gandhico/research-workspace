# Paper Notes

Working notes on the manuscript (`paper/main.tex`): the intended story, the
scope boundary with the theory manuscript, and the scientific-honesty decisions
made while writing.

## One-line thesis

*The continuous-reset HyperLIF neuron can be implemented as a clean,
equation-faithful, numerically validated, Nengo-compatible component — and its
continuous gate is a decodable readiness signal that opens a path to gate-state
residual decoding for control.*

## Story arc

1. **Problem.** The LIF hard reset breaks differentiability and discards
   sub-threshold state.
2. **Models.** Restate HyperLIF / Adaptive HyperLIF *exactly as implemented*
   (Secs. 3): two-state ODE, quadratic gate conductance, input-modulated
   adaptive gain.
3. **Structure.** A fixed-point analysis explains the depolarization block
   (onset `J_DB`, latched voltage `J/(1+τG_b)`) and shows when the adaptive law
   keeps the high-drive equilibrium bounded (`β > 1/(τ(v_thresh−γ))`).
4. **Numerics.** Two stepping schemes; convergence + stability vs an RK4
   reference; this motivates the exponential update used by Nengo.
5. **Validation.** The Nengo port reproduces the standalone model *exactly*
   (RMSE = 0) because they share one kernel — the strongest possible "port is the
   model" evidence.
6. **Meaning.** The gate is a readiness signal (decoding study), which motivates
   the **future** controller bridge.

## Scope boundary with the theory manuscript

- The theory manuscript owns: the NSA derivation, the DB-as-Zeno argument, the
  flux-balance condition, differentiability/BPTT, and the N-MNIST/DVS benchmarks.
- **This paper owns**: the reference implementation, the fixed-point
  characterization for the *implemented* dynamics, the numerical-scheme analysis,
  the exact Nengo parity, and the gate-decoding interpretation.
- We cite the theory manuscript as `\cite{hyperlif_theory}` and never re-claim
  its results. The flux-balance condition there and the fixed-point condition
  here are presented as two views of the same stabilization principle.

## Notation alignment (code ↔ theory manuscript)

| This project (code) | Theory manuscript | Meaning |
|---|---|---|
| `reset_gain` (`G_b`) | `G_base` (fixed model) | baseline reset gain |
| `base_gain` (`G_base`) | `G_base` (adaptive) | adaptive baseline gain |
| `gain_scaling` (`β`) | `β` | adaptive feedforward scaling |
| `tau`, `tau_r` | `τ`, `τ_r` | membrane / gate time constants |
| `alpha`, `gamma` | `α`, `γ` | detector steepness / hysteresis |

> Note the deliberate name choice in the paper: the *fixed-gain* HyperLIF baseline
> gain is written `G_b` (code `reset_gain`) to avoid clashing with the adaptive
> `G_base` (code `base_gain`). Both equal 100 vs 20 respectively in the reference
> parameter set, which is why the two models differ even at small input.

## Scientific-honesty decisions

- **Adaptive is not "DB-proof."** The fixed-point function reports `db_free=True`
  in the specific sense that the *open-gate, high-voltage* latch is never reached
  (asymptotic voltage stays below the knee). But the adaptive model has its own
  higher operating ceiling (`J≳3.6` here) where spiking ceases at a *bounded
  sub-threshold* equilibrium. The paper states both, and frames the high-drive
  cessation as graceful self-silencing rather than "no block ever."
- **"Stable" ≠ "more accurate."** `06_integration_accuracy.csv` shows the
  explicit scheme can have slightly lower trajectory RMSE in the convergent
  regime. The paper says so plainly and attributes the exponential scheme's value
  to unconditional stability (demonstrated in `06_stability.csv`).
- **Parameters are a normalized reference set**, not the benchmark-scale theory
  values. The specific constants (2.4, 62.5, …) are labeled as parameter-specific
  instances of general relations.
- **Attitude control is future work.** Sec. 9 is explicitly a design + hypothesis
  with no closed-loop results; the validated port is presented as the
  *prerequisite* that makes such a study trustworthy.
- **Decoding is a single-neuron illustration**, not an ensemble/NEF claim; the
  gate decode is noisy and we say so.

## Things a reviewer might ask (and where we address them)

- *Why is parity exactly zero?* Shared numerical kernel — Sec. "Nengo
  Implementation" and `MATH_CODE_MAP.md`.
- *Is `J_DB` just the theory's `I > G_base(v_thresh−v_reset)`?* No — that is a
  cruder sufficient bound; our `(v_thresh−γ)(1+τG_b)` accounts for the leak and
  the hysteresis knee and matches the observed onset. Discussed in Sec. 3.2.
- *Does the explicit scheme ever blow up?* It develops growing overshoot for
  `λΔt>2`; the lower clamp prevents `NaN`, but the trajectory is spurious. Shown
  in Fig. 6(b).
