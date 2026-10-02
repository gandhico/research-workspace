# Paper 3 Workplan — Nengo Reference, Readiness Decoding, and Control Bridge

This is the active lane for Codex. Claude is handling Paper 2; Paper 3 should
stay focused on the Nengo/reference/control story and should not duplicate the
learning-benchmark narrative.

## Core Thesis

HyperLIF and Adaptive HyperLIF can be implemented as equation-faithful,
numerically validated Nengo `NeuronType` components. Their continuous reset
gate is probeable and decodable, which opens a principled path toward
gate-state residual decoding for NEF control.

## Scope Boundary

Paper 3 owns:

- implemented equations and numerical stepping;
- fixed-point DB analysis for the implemented reference parameters;
- exact standalone Python vs Nengo parity;
- gate/readiness decoding;
- NEF/Nengo app compatibility;
- `theta_event` as readout adaptation;
- origin and calibration as Nengo operating-point tools;
- future bridge to quaternion/control residuals.

Paper 3 does not own:

- N-MNIST/DVS/SHD/SSC training benchmarks;
- SOTA accuracy comparisons;
- PyTorch/APEX architecture transfer;
- Paper 2 local-learning claims except as short context/citation.

## Current Paper-Ready Results

These are safe, central claims:

- Python stable stepping equals the Nengo port exactly: voltage/gate RMSE `0`,
  max difference `0`, event mismatch `0`.
- DB onset for fixed HyperLIF is predicted by
  `J_DB=(v_thresh-gamma)(1+tau G_b)=2.4` and matches simulation.
- Fixed-gain latched voltage `v*=J/(1+tau G_b)` matches simulation exactly
  at `J=4`: `1.3333` predicted and observed.
- Adaptive conductance bounds the high-drive equilibrium:
  `beta=80 > beta_crit=62.5`, with asymptotic open-gate voltage `0.625 < 0.8`.
- Exponential update is the stable Nengo update; explicit Euler overshoots once
  `lambda dt > 2`.
- Gate-state decoding works as an illustrative single-neuron readiness result:
  gate-readiness RMSE `0.287`; voltage-current RMSE `0.258`; filtered-event
  current RMSE `0.321`.
- Static `theta_event=0.95` widens the active band and raises peak settled rate
  from `151.14` to `217.83` Hz without changing continuous gate/reset dynamics.

## Current Exploratory Results

These are useful but must remain qualified:

- NEF integrator/oscillator smoke:
  - LIF holds `0.287`, oscillator std `0.598`;
  - HyperLIF holds weakly `0.034`, oscillator std `0.561`;
  - Adaptive holds `0.334`, oscillator std `0.247`.
- Core-Nengo capability sweep:
  - all `54/54` app x variant combinations build and run;
  - LIF remains the best representation/memory reference;
  - HyperLIF/Adaptive work, but accuracy depends on calibration.
- Static origin:
  - improves HyperLIF communication RMSE `0.346 -> 0.217`;
  - improves PES late error for HyperLIF `0.631 -> 0.549`;
  - improves PES late error for Adaptive `0.546 -> 0.497`;
  - worsens transform, memory, and oscillator metrics.

Interpretation: origin is a Nengo calibration clue, not yet a performance win.

## Immediate Technical Next Steps

### 1. Origin-Aware Calibration Sweep

Use `FULL_TUNING_SETUP.md` and
`results/csv/11_full_tuning_candidate_matrix.csv`.

First target rows:

- Stage `0_anchor`;
- Stage `1_origin_threshold`, priority `1`;
- Stage `2_origin_aware_calibration`, priority `1`.

Measure:

- communication RMSE;
- function RMSE;
- transform RMSE;
- working-memory hold error;
- oscillator amplitude and boundedness;
- PES early/late error;
- event rate;
- optional gate mean/saturation.

Decision rule:

Keep a candidate only if it improves a multi-app score, not merely one app or
raw event count.

### 2. Gate/State Decoder Ablation

Add a multi-neuron Nengo decoder experiment comparing:

- spike-only;
- voltage-only;
- gate-only;
- voltage + gate;
- voltage + gate + dynamic_gain;
- spikes + voltage + gate + dynamic_gain.

Purpose:

Move the readiness result from single-neuron illustration toward a real NEF
ensemble claim.

### 3. Gate-Coupled Origin Prototype

Implement only as an experiment-local subclass first:

```text
v_reset_eff = v_reset - delta_reset * reset_gate
```

Try:

- `delta_reset=0.15`;
- `delta_reset=0.30`;
- `delta_reset=0.60`;
- `theta_event=0.95`;
- `min_voltage=-2.0`.

Do not change `src/neurons/nengo_hyperlif.py` until parity and F-I sanity checks
are complete.

### 4. Tuned Adaptive Threshold Ensemble Test

Import the best project-05 candidate:

```text
theta_base = 0.99
target_rate_hz = 60.0
theta_error_gain = 0.002
theta_spike = 0.0005
tau_theta = 0.20
theta_min = 0.90
theta_max = 1.00
```

Goal:

Test whether "better-timed events" improves multi-neuron Nengo decoding better
than static `theta_event=0.95`.

## Immediate Writing Next Steps

### Manuscript Polish

Current manuscript:

```text
paper/main.tex
paper/main.pdf
```

Needed:

- tighten title and abstract around the Nengo/control contribution;
- move some exploratory app-sweep details into a cleaner "calibration and
  operating-point study" framing;
- make limitations and future work crisp but not apologetic;
- ensure `theta_event`, origin, and tuned adaptive threshold are introduced as
  readout/operating-point tools, not new core dynamics;
- add a short paragraph explaining why Paper 3 is complementary to Paper 2.

### Figures/Tables To Consider

Already present:

- step response;
- stress response;
- F-I curve / DB;
- integration stability;
- Nengo parity;
- gate-state decoding.

Potential additions:

- compact Nengo app-sweep heatmap;
- origin/threshold calibration Pareto;
- gate/state decoder ablation figure;
- pipeline schematic for readiness residual control.

## Claim Discipline

Safe claims:

- exact Nengo parity;
- equation-faithful implementation;
- fixed-point DB prediction;
- stable exponential stepping;
- `theta_event=0.95` increases readout availability;
- gate carries decodable readiness information;
- Nengo apps build and run.

Qualified claims:

- Core-Nengo app performance;
- origin as a calibration knob;
- tuned adaptive threshold;
- ensemble gate decoding.

Do not claim yet:

- closed-loop control improvement;
- origin improves Nengo generally;
- tuned adaptive threshold is validated in ensembles;
- Nengo app sweep is an optimized benchmark;
- hardware or backend speed/energy results.

## Recommended Next Work Session

1. Build `experiments/11_origin_aware_calibration_sweep.py`.
2. Consume priority-1 candidates from
   `results/csv/11_full_tuning_candidate_matrix.csv`.
3. Run the six existing Nengo apps over those candidates.
4. Write:
   - `results/csv/12_origin_aware_calibration_sweep.csv`;
   - `results/logs/12_origin_aware_calibration_sweep.txt`.
5. Update `RESULTS_AUDIT.md` and manuscript only after the result is clear.
