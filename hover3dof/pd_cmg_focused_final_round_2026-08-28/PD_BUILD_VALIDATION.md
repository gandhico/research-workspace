# PD/CMG build validation record

Validation date: 2026-08-28. Hardware was not opened, armed, or commanded.

## Two baselines are deliberately separated

1. `mujoco` is the default experiment: quaternion PD, body rate, three torque
   channels, six CMG units, PES, and 0.5 ms neural integration from `drone.py`.
2. `lqr-equivalent` is an offline-validated bridge: the vendor LQR is exposed as
   Euler axis PD. It remains useful as an ablation but is not the MuJoCo
   reproduction and cannot be paired with `pd-cmg` in the new runner.

## MuJoCo conformance checks

- MuJoCo gains and inertia-policy torque limits are computed from the canonical
  formulas and reordered from xyz to yaw/pitch/roll.
- A synthetic-state unit test proves that the Hover torque and PES equations
  equal `drone.py` after the declared order/sign transformation.
- ZYX Euler-rate to body-rate conversion is tested at the level orientation.
- The baseline torque is bounded by the model/inertia limits.
- The Q8 loop uses ten 0.5 ms CMG/PES substeps inside each 5 ms control sample.
- Full neuron state and all 18 decoder weights are written to every 200 Hz trace
  row, synchronized with all plant/control signals.

## LQR-equivalent bridge validation

The explicit bridge

\[
\tau=K_pe-K_d\omega,\qquad
u=\operatorname{clip}(V_b\mathbf 1+G^\dagger\tau,0,24)
\]

was compared sample by sample with frozen motor voltages from the original LQR
runner. This validates only the optional `lqr-equivalent` profile.

| Mission/source run | Samples | Maximum absolute difference | RMS difference |
|---|---:|---:|---:|
| hard45 / classical_armed_20260828_123415 | 5000 | 3.20e-14 V | 5.37e-15 V |
| full3 / classical_armed_20260827_232303 | 5000 | 2.22e-14 V | 4.34e-15 V |
| yaw360 / classical_armed_20260828_123653 | 6000 | 1.03e-13 V | 2.43e-14 V |

All pass the predeclared 1e-9 V tolerance.

## MuJoCo-PD/CMG frozen-trace safety replay

This replay checks the new controller signals and hardware bounds on measured
states. It does not predict the closed-loop trajectory.

| Mission | Motor residual max | Slew max | Command range | Requested residual torque RMS | Realized residual torque RMS | Gate mean |
|---|---:|---:|---:|---:|---:|---:|
| hard45 | 1.2 V | 4.0 V/s | 0-24 V | 0.232920 N m | 0.010485 N m | 0.9600 |
| full3 | 1.2 V | 4.0 V/s | 0-24 V | 0.231420 N m | 0.011247 N m | 0.8217 |
| yaw360 | 1.2 V | 4.0 V/s | 0-24 V | 0.146264 N m | 0.008979 N m | 0.0991 |

All three report `all_bounds_pass=true` and `neural_dt_s=0.0005`.
The requested/realized gap is expected from the conservative motor residual cap
and positive-voltage actuator projection. It is a reported hardware adaptation,
not evidence of identical authority.

## Software checks

- Controller, transform, mixer, allocator, and bounds unit tests pass.
- Runner, replay tool, and plotters compile under the project environment.
- Neuron plotter smoke test passes.
- `--help` completes without opening hardware.
- `--armed` without `--confirm-pd-review` exits before Q8 initialization.
- Existing LQR runner SHA-256 remained
  `a20dbb24a6da87ae3a4332cde5e8c9b5e2cb4ada022c0a3f1875f55de93a6446`.

See `MUJOCO_HOVER_CONFORMANCE.md` for equations, signal architecture, logged
channels, and the exact-versus-adapted boundary.
