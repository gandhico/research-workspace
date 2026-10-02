# Math ↔ Code Map

Every equation in `paper/main.tex` is realized in `src/`. Equation numbers below
refer to the compiled manuscript. Line numbers refer to the files in this
project's `src/` (the neuron files are verbatim copies of the
`04_Adaptive_HyperLIF_Nengo` baseline, so the equations are identical to the
validated baseline). Functions are named explicitly; line ranges are accurate to
the current files and marked "approx." where a function spans a range.

## LIF baseline — `src/neurons/lif.py`

| Eq. | Statement | Code |
|---|---|---|
| (1) | `dv/dt = (-(v−v_rest)+J)/τ` | docstring of `_lif_voltage_update` (L28–29); the closed form is L31–32 |
| (2) | `v_{k+1} = (v_rest+J) + (v_k−v_rest−J)e^{−Δt/τ}` | `_lif_voltage_update`: `target = v_rest + current` (L31), `return target + (v−target)·exp(−dt/τ)` (L32) |
| — | threshold crossing → event `A/Δt`, reset to `v_reset`, refractory `τ_ref` | `simulate_lif` L66–69; refractory hold L58–60; `v = max(v, v_min)` L64 |

## HyperLIF — `src/neurons/hyperlif.py`

| Eq. | Statement | Code |
|---|---|---|
| (3) | `θ_eff = v_thresh − γ·r` | `gate_target`: `effective_thresh = v_thresh − gamma·gate` (L43) |
| (4) | `r_∞ = σ(α(v−θ_eff))`, `σ(x)=1/(1+e^{−x})` | `gate_target` return (L44); `sigmoid_switch` (L33–37) |
| (5) | `dr/dt = (r_∞ − r)/τ_r` | `hyperlif_derivatives`: `dr = (target − gate)/tau_r` (L56) |
| (6) | `dv/dt = (−(v−v_rest)+J)/τ − G(r)(v−v_reset)`, `G=G_b r²` | `hyperlif_derivatives`: `drift` (L57), `conductance = reset_gain·gate²` (L58), `reset_force` (L59), `dv` (L60) |
| (13) | exact gate update `clip(r_∞+(r−r_∞)e^{−Δt/τ_r},0,1)` | `exact_gate_update` (L64–74): target L72, decay L73, return L74 |
| (14) | `λ = 1/τ + G`, `d = v_rest/τ + J/τ + G·v_reset` | `stable_voltage_update`: `lam` (L93), `drive` (L94) |
| (15) | exponential update `v e^{−λΔt}+(d/λ)(1−e^{−λΔt})` | `stable_voltage_update` (L95–100); used in `HyperLIFNeuron.step` L132–142 |
| (16) | explicit-Euler update | `HyperLIFNeuron.step` "julia" branch (L143–146) |
| — | event = upward crossing of `v_event`, no reset | `HyperLIFNeuron.step` L152 |

## Adaptive HyperLIF — `src/neurons/adaptive_hyperlif.py`

| Eq. | Statement | Code |
|---|---|---|
| (9) | `G_dyn = G_base + β|J|`, `G(r,J) = G_dyn·r²` | params `base_gain`,`gain_scaling` (L27–29); `adaptive_hyperlif_derivatives` `dyn_gain` (L43), `conductance` (L44) |
| (10) | adaptive `dv/dt` | `AdaptiveHyperLIFNeuron.step`: `dyn_gain` (L72), `conductance = dyn_gain·r²` (L73); shares `stable_voltage_update`/Euler with HyperLIF |

## Nengo port — `src/neurons/nengo_hyperlif.py`

The `step` methods implement Algorithm 1 of the paper using the **same**
`sigmoid_switch` and `stable_voltage_update` kernel as the standalone model. This
shared kernel is why the parity in `07_parity_metrics.csv` is exact.

| Item | Code |
|---|---|
| effective threshold, detector, gate exact update (3,4,13) | `HyperLIFNengo.step` L124–131 |
| conductance `G_b r²` and exponential membrane update (6,15) | L133–142 |
| event crossing | L147–150 |
| adaptive `G_dyn`, `G(r,J)` (9,10) | `AdaptiveHyperLIFNengo.step` L251–252; membrane L253–261 |
| state declaration + probes | `state = {...}` / `probeable = (...)` (HyperLIF L59–64, Adaptive L157–169) |
| NEF gain/bias calibration | `_CurrentCalibrationMixin.gain_bias` / `max_rates_intercepts` (L23–39) |

## Event readout threshold — base project and adaptive-threshold project

The manuscript separates the dynamical threshold `v_thresh` from the readout
event threshold `theta_event`. In the base Paper 3 project this appears as the
`event_threshold` parameter in `src/neurons/nengo_hyperlif.py` and in the
standalone parameter dataclasses. It affects only the upward-crossing condition
that emits `output = amplitude / dt`; it does not change `gate_target`,
`exact_gate_update`, `stable_voltage_update`, or the reset conductance.

The dedicated adaptive-threshold code lives in:

```text
C:\00_Research_\Neural_Networks_and_Learning\05_Adaptive_Threshold_HyperLIF_Nengo
```

Relevant files:

- `src/neurons/static_threshold_nengo.py`
- `src/neurons/adaptive_threshold_hyperlif.py`
- `src/neurons/adaptive_threshold_nengo.py`
- `experiments/01_static_event_threshold_sweep.py`
- `experiments/05_decoder_comparison.py`
- `experiments/06_adaptive_rule_tuning.py`

The Paper 3 project carries copied CSV evidence as `results/csv/09_theta_*`.

## Fixed-point analysis — `src/analysis/depolarization_block.py`

| Eq. | Statement | Code |
|---|---|---|
| (7) | `v* = (v_rest+J+τG·v_reset)/(1+τG)` | `latched_voltage` |
| (8) | `J_DB = (v_thresh−γ)(1+τG_b) − v_rest − τG_b·v_reset` | `db_onset_current` |
| (11) | `v*_∞ = (1+τβ·v_reset)/(τβ)` | `adaptive_asymptotic_voltage` |
| (12) | `β > 1/(τ(v_thresh−γ))` | `adaptive_is_db_free` (`gain_scaling_critical`, `db_free`) |
| — | self-consistent `(v*,r*)` equilibria | `coupled_equilibria` |

These analytical functions are exercised and cross-checked against simulation in
`experiments/03_current_sweep.py` (writes `03_db_analysis.csv` and
`03_equilibria.csv`). The validated agreement (`J_DB=2.4`; latched voltage at
`J=4`: predicted `1.3333` vs simulated `1.3333`) is recorded in
`results/logs/03_current_sweep.txt`.

## Numerical-integration claims — `src/simulation/ode_integrators.py`

The RK4 reference used to verify convergence (paper Sec. "Numerical accuracy and
stability") is `rk4_integrate`; the explicit reference is `euler_integrate`.
`experiments/06_numerical_integration.py` integrates the continuous ODE
(`hyperlif_derivatives`) with `rk4_integrate` and compares both discrete schemes
against it.
