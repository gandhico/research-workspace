# Controller-family extension after the neuron-basis decision

## Decision

Use **CMG-PES as the primary residual**, tuned LIFRate as the conventional
challenger, and the static paired PES basis as the non-neural mechanism
control. Do not repeat all eight bases over every controller: that would create
a large factorial sweep with little value for the ACC paper.

The existing controller campaign already tested additive CMG-PES on tuned
PD+feedforward, LQR, backstepping, SMC, unconstrained MPC, and grid NMPC. Its
main result was coherent: the residual helped model-free PD+feedforward and X2
SMC, did not improve accurate LQR/backstepping/MPC/NMPC, and recovered modest
5--8% gains beside backstepping only under unmodeled disturbance. These are
valid exploratory findings, but that campaign predates the final
saturation-opposition gate and the corrected basis benchmark.

## Why a blind rerun is not the right next experiment

An additive residual after every controller tests interface portability, not
whether the residual is integrated correctly:

- LQR, backstepping, and unconstrained MPC are nearly equivalent for the
  decoupled double-integrator model used here.
- With exact inertia and feedforward, their tracking error is already near the
  numerical floor; any active residual can only add a floor.
- An output residual after MPC/NMPC is an unmodeled input to the optimizer. A
  learned disturbance/model term inside prediction is the principled design.
- SMC already rejects matched disturbances; a large residual can leave its
  boundary layer and reintroduce switching.
- PID requires rotor-level anti-windup accounting; torque-box clipping alone
  is insufficient.

## Recommended staged experiment

### Stage A — interface portability (small, common experiment)

For each baseline controller, run baseline and baseline+CMG on X2 and CF2 for
Roll, Full3, Hard45, Hardstep, and Yaw360. Use the final output gate and log the
same allocation/neural schema as the present study. Purpose: verify bounded
attachment and exact baseline recovery, not claim universal improvement.

One controller-specific bandwidth and one residual beta must be selected on a
development split, then frozen. Never select beta independently per mission.

### Stage B — meaningful uncertainty experiment

Use Full3 and Hard45 as tracking missions, plus intermittent matched torque
bursts and one disclosed inertia mismatch. Compare

1. baseline;
2. baseline + CMG-PES;
3. baseline + tuned LIFRate-PES;
4. baseline + static paired PES.

This is the experiment that can distinguish a useful learned residual from a
floor when the nominal model is already accurate.

### Stage C — controller-native integration

| Controller | Baseline output | Primary residual placement | Teacher/learning target | Required check |
|---|---|---|---|---|
| PD | body torque | additive after PD | bounded error-proportional target | final gate and allocation |
| PID | body torque | additive after PID | error-proportional; integral remains baseline state | rotor-level anti-windup with and without residual |
| LQR | body torque | additive matched input | start with error target; later estimate model mismatch | same reference-rate convention and state scaling |
| Backstepping | computed body torque | additive matched uncertainty after computed torque | preferably estimated disturbance/model error | exact-model and mismatched-model cases separated |
| SMC | equivalent/reaching torque | additive inside declared term or bounded outside it | matched-disturbance target | residual authority below reaching margin; switching metric |
| MPC | optimized torque | learned disturbance in prediction model; post-optimizer residual only as ablation | prediction-error/disturbance target | actual constrained QP, not unconstrained LQR-like gain plus clip |
| NMPC | optimized torque at slow clock | learned dynamics/disturbance in rollout; optional high-rate residual between updates | one-step model error | declare optimizer, hold, plant, and neural clocks separately |

## Metrics

Tracking error alone is insufficient. Report, per mission and controller:

- mean, RMS, maximum, and mission-phase quaternion error;
- normalized baseline, requested residual, gated residual, and realized
  actuator effort;
- torque-box and individual-rotor saturation duty;
- output-gate duty and residual/baseline opposition fraction;
- decoder rail duty, activity occupancy, and decoder-weight norm;
- PID integral freeze duty, SMC switching/total variation, and MPC/NMPC solve
  time/prediction error where applicable.

## ACC scope recommendation

Do not add this full controller study to the 6--7 page ACC manuscript. The
corrected basis study is the stronger mechanism result and directly protects
the central contribution. Use at most one sentence noting that the bounded
interface is controller-agnostic. Treat controller-native integration as the
next paper or a journal extension, where the teacher and residual location can
be redesigned rather than appended mechanically.

## Existing implementation references

- Controller laws and old common-interface runner:
  `../nengo_nef_replication_2026-08-29/run_mujoco_nef_baselines.py`
- Existing controller campaign:
  `../nengo_nef_replication_2026-08-29/results/baselines_2026-09-10/`
- Existing detailed design cautions:
  `../nengo_nef_replication_2026-08-29/results/baselines_2026-09-10/CONSIDERATIONS.md`
- Final output-gate/allocation telemetry contract:
  `../final_robustness_gating_2026-09-20/run_izh_robustness.py`

The next implementation should merge the controller laws from the first file
into the final gate/telemetry contract; it should not modify either frozen
runner in place.
