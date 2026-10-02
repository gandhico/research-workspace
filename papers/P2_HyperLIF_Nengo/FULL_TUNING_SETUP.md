# Full Tuning Setup: HyperLIF / Adaptive HyperLIF in Nengo

This is the broad tuning program for the next Paper 3 push. It is intentionally
not conservative: the goal is to explore every plausible control lever around
`theta_event=0.95`, origin, calibration, adaptive gain, gate timing, and
state-aware decoding, while keeping each option tied to a hypothesis and a
decision rule.

Executable matrix:

```powershell
python experiments\10_full_tuning_setup.py
```

Outputs:

- `results/csv/11_full_tuning_candidate_matrix.csv`
- `results/logs/11_full_tuning_setup.txt`

## Core Principle

Do not optimize raw event count. Optimize useful events and stable decoded
dynamics.

A candidate is interesting only if it improves decoded task metrics without
hiding failure through longer synapses, runaway oscillator amplitude, or
overfit state decoders.

## Stage 0: Anchors

Keep these fixed as the comparison floor:

- Native LIF.
- HyperLIF with `theta_event=1.00`.
- HyperLIF with `theta_event=0.95`.
- Adaptive HyperLIF with `theta_event=1.00`.
- Adaptive HyperLIF with `theta_event=0.95`.
- Current static-origin rows:
  - `theta_event=0.95`
  - `v_reset=-0.6`
  - `min_voltage=-2.0`

Known result: static origin helps HyperLIF communication and PES late error, but
hurts transform, working memory, and oscillator metrics. Treat this as a
calibration clue, not as a solved knob.

## Stage 1: Origin + Threshold

First real sweep:

- `theta_event in {0.98, 0.95, 0.92, 0.90}`
- static origin:
  - mild: `v_reset=-0.3`
  - medium: `v_reset=-0.6`
  - deep: `v_reset=-0.9`
  - `min_voltage=-2.0`
- families:
  - HyperLIF
  - Adaptive HyperLIF

Logic:

- `theta_event=0.95` gives event availability.
- Origin should reshape reset/reference dynamics.
- The question is whether mild or medium origin recovers useful sparsity without
breaking recurrent state.

Decision rule:

- Keep only rows that improve communication/PES while keeping transform and
working-memory degradation small.
- Reject rows that only increase events.

## Stage 2: Origin-Aware Calibration

This is probably the most important practical stage.

Sweep:

- `rate_to_current in {40, 60, 80, 100, 140}`
- ensemble max-rate bands:
  - `20..80`
  - `40..120`
  - `40..160`
  - `80..200`
- intercept bands:
  - `-0.8..0.2`
  - `-0.7..0.3`
  - `-0.5..0.5`
  - `-0.3..0.7`
- synapse probes:
  - `0.01`
  - `0.02`
  - `0.05`
  - `0.10`

Logic:

The origin result may be bad because the approximate build-time rate proxy is
not origin-aware. Before blaming the neuron dynamics, fit the NEF calibration to
the shifted tuning curves.

Decision rule:

Pick by a multi-app score:

```text
score = mean(normalized decoded errors)
      + memory_error_penalty
      + oscillator_runaway_penalty
      - PES_improvement_bonus
```

Do not use a single-app win as the final choice.

## Stage 3: Adaptive Gain Placement

Sweep Adaptive HyperLIF:

- `base_gain, gain_scaling`:
  - `10, 40`
  - `20, 40`
  - `20, 80`
  - `20, 120`
  - `40, 80`
  - `40, 120`
- with and without static origin.

Logic:

The theory value `gain_scaling=80` is good for the fixed-point demonstration,
but Nengo recurrent apps may prefer a different reset-energy placement.

Decision rule:

Keep a gain row only if it improves memory or oscillator behavior without
killing communication and PES.

## Stage 4: Gate Shape

Core gate parameters to try:

- soft slow gate:
  - `alpha=60`, `tau_r=0.003`, `gamma=0.15`
- wide hysteresis slow gate:
  - `alpha=80`, `tau_r=0.004`, `gamma=0.25`
- sharp fast gate:
  - `alpha=150`, `tau_r=0.001`, `gamma=0.20`
- strong hysteresis:
  - `alpha=100`, `tau_r=0.002`, `gamma=0.30`
- weak hysteresis:
  - `alpha=100`, `tau_r=0.002`, `gamma=0.10`

Logic:

If the failure is gate timing, not threshold or origin, reshape the gate. This
may help recurrent state because memory and oscillators are sensitive to phase,
not only event rate.

Decision rule:

Before app claims, run single-neuron F-I sanity:

- active current band
- peak settled rate
- mean voltage
- gate saturation fraction
- boundedness under stress current

## Stage 5: Out-of-the-Box Candidates

These are intentionally adventurous and should live in experiment-local
subclasses or new decoder scripts until they earn promotion.

### Gate-Coupled Origin

Use an effective reset reference:

```text
v_reset_eff = v_reset - delta_reset * reset_gate
```

Try:

- `delta_reset=0.15`
- `delta_reset=0.30`
- `delta_reset=0.60`
- `min_voltage=-2.0`
- `theta_event=0.95`

Why:

Static origin shifts the neuron all the time. Gate-coupled origin adds
after-hyperpolarization only when the gate opens, so it may preserve encoding
while adding sparse recovery dynamics.

### Mixed Dense/Sparse Populations

Use two sub-populations:

- dense half: `theta_event=0.95`, no origin
- sparse half: `theta_event=0.95`, origin `v_reset=-0.6`

Why:

Do not force one operating point to do all jobs. Let the decoder combine a dense
communication channel with a sparse readiness channel.

### State-Aware Decoders

Compare decoders:

- spike-only
- voltage-only
- gate-only
- voltage + gate
- voltage + gate + dynamic_gain
- spikes + voltage + gate + dynamic_gain

Why:

Paper 2 already shows the gate is a real decodable learning signal. Paper 3
should test whether it is also useful inside NEF apps.

### Tuned Adaptive Threshold

Import the best candidate from project 05:

```text
theta_base = 0.99
target_rate_hz = 60.0
theta_error_gain = 0.002
theta_spike = 0.0005
tau_theta = 0.20
theta_min = 0.90
theta_max = 1.00
```

Why:

Static `theta_event=0.95` makes more events. The tuned adaptive rule makes more
useful events in the single-neuron decoder tests.

### Origin Annealing

Start dense, end sparse:

```text
v_reset(t): 0.0 -> -0.6
```

Why:

Bootstrap recurrent state with dense communication, then settle into sparse
origin dynamics.

### Gate-Modulated PES

Use `reset_gate` or `dynamic_gain` as an eligibility/readiness factor in PES-like
learning.

Why:

PES is already one of the apps where origin helps. Gate-state learning may turn
that smoke result into a real mechanism.

### Readiness Residual Output

Decode a residual from:

```text
[voltage, reset_gate, dynamic_gain]
```

and add it to the standard NEF decoded output.

Why:

This is the direct bridge to the control story: standard NEF output plus a
gate-state residual for hidden readiness/error state.

## Recommended Execution Order

1. Run `experiments\10_full_tuning_setup.py`.
2. Take priority-1 rows from stages 0-2.
3. Run those rows on communication, transform, memory, oscillator, and PES.
4. Score with multi-app metrics, not one favorite task.
5. Add Stage 3 adaptive-gain rows if recurrent apps remain weak.
6. Add Stage 4 gate-shape rows only after F-I sanity checks.
7. Prototype Stage 5 ideas one at a time in local subclasses/decoders.

## Non-Negotiable Claim Discipline

- Do not merge gate-coupled origin into the core Nengo neuron before parity and
  single-neuron validation.
- Do not claim origin is a performance win unless seed-matched app sweeps show
  it across multiple apps.
- Do not treat raw event rate as success.
- Do not compare state-aware decoder rows against spike-only rows without
  labeling the decoder change.
- Do preserve the current exact parity and fixed-point claims as the reference
  substrate.
