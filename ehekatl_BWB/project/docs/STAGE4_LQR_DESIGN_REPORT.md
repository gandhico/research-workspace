# Stage 4 delay-aware LQR design — intermediate report

Date: 2026-07-12 (America/Denver)

Status: PASS. Separate inner-rate gains and exact runtime replay are frozen.

## Design choices

- Exact numerical continuous-to-discrete conversion at 10 Hz using RK4 matrix
  exponential integration with 100 substeps.
- State is `[angle, rate, u(k-1), u(k-2), u(k-3)]`.
- The measured three-sample input delay is part of the synthesized plant.
- Bryson scaling uses 2 deg angle, 2 deg/s rate, and 0.003 normalized command.
- Command magnitude is limited to 0.003 and slew to 0.0005 per 0.1-second
  sample.
- The design uses measured X-Plane total-control sign conventions.

Machine-readable matrices, gains, poles, replays, and all robustness cases are
in `configs/stage4_lqr_design.json`.

## Nominal attitude-state candidate gains

The command law is `u_perturbation = -K x`.

```text
K_roll = [
  +0.0008744492, -0.0015549728,
  +0.0485960530, +0.0475990244, +0.0457516334
]

K_pitch = [
  +0.0013164881, -0.0006435013,
  +0.0189824485, +0.0173657542, +0.0149767632
]
```

Nominal spectral radii are 0.97358 roll and 0.98010 pitch.

## Robustness audit

For each axis, all combinations of `-2, 0, +2` coefficient standard errors
were combined with plant delays of 2, 3, and 4 samples: 81 cases per axis.
The controller retained its nominal three-command history while the plant delay
changed inside a common four-command state representation.

```text
Roll worst spectral radius   0.98577; unstable cases 0/81
Pitch worst spectral radius  0.98938; unstable cases 0/81
```

Matched 20-second disturbances of +/-1 deg, +/-1 deg/s, and their combinations
converged with zero saturation. Peak commands were 0.00218 roll and 0.00196
pitch. The final-five-second angle/rate maxima stayed below 0.023 deg / 0.030
deg/s for roll and 0.045 deg / 0.112 deg/s for pitch.

Offline command replay over all eight Stage-2 training/validation logs produced
zero saturation. Peak replay commands were below 0.000299 roll and 0.000183
pitch.

## Architectural hold

These candidates use angle and rate feedback together. They are therefore
attitude-controller candidates for the later Stage 6 gate, not authorization
to skip Stage 5. Before Stage 4 can pass, synthesize and audit separate
delay-aware inner-rate laws, freeze their runtime state/history initialization,
trim feed-forward, sign, magnitude/slew limits, and safety supervision, and
replay the exact implementation offline. No X-Plane LQR command is authorized
yet.

## Frozen inner-rate controllers

The inner controllers have zero angle feedback by construction. Their state is
`[rate_error, u(k-1), u(k-2), u(k-3)]`, and the perturbation law is `u=-Kx`.

```text
K_roll_rate = [-0.0027262310, 0.0788174356, 0.0785343024, 0.0782521863]
K_pitch_rate = [-0.0019913193, 0.0441278087, 0.0432419710, 0.0423739160]
```

After the first held-out Stage-5 confirmation exposed inadequate live damping,
Stage 4 was reopened and the inner-rate Bryson scale changed from 2.0 to 1.0
deg/s without changing command or slew limits. When mapped onto the full plant,
nominal spectral radii are 0.96259 roll and 0.97361 pitch. Across the same 81
uncertainty/delay cases per axis, worst radii are 0.97925 and 0.98728, with zero
unstable cases. The deliberately combined +/-1-deg, +/-1-deg/s stress cases
touch the fixed limit for at most 2.5% roll / 2.0% pitch samples; saved-log
replays have zero saturation.

The exact runtime implementation is `lqr/delay_aware_lqr.py`. It initializes
the perturbation history to zero around captured trim, applies the frozen
0.0005/sample slew and 0.003 magnitude limits, and updates three-command
history deterministically. `scripts/replay_stage4_runtime.py` exercised that
exact object over all eight accepted Stage-2 logs. Peak perturbations were
0.000473 roll and 0.000411 pitch; saturation was zero.

Stage 4 passes offline synthesis and replay. This authorizes Stage-5 software
preparation and observe-only/live-gated inner-rate experiments, not an
unrestricted or combined LQR flight.
