# Result and terminology audit

## Crazyflie torque authority

The Menagerie CF2 inertia is

`J = [2.3951e-5, 2.3951e-5, 3.2347e-5] kg m^2`.

With the project acceleration bounds `[12, 12, 10] rad/s^2`, the
inertia-derived torque bounds are

`[2.87412e-4, 2.87412e-4, 3.23470e-4] N m`.

The historical learned runner instead applies a floor
`[0.03, 0.03, 0.02] N m`. This is `[104.38, 104.38, 61.83]` times the
inertia-derived bound. The Menagerie XML moment actuators provide only
`1e-5 N m` per axis, so the learned floors are `[3000, 3000, 2000]` times
the model actuator authority.

These are different comparisons and both must be reported. The XML README
also says its virtual moment limits are arbitrary, so the model limit is not
claimed as a measured physical Crazyflie motor limit.

## Saved Skydio result

From `learned_gate_skydio.json`:

| Method | qerr mean | Score | qerr improvement | score improvement |
|---|---:|---:|---:|---:|
| Classical | 0.294079 | 0.299286 | — | — |
| Fixed gate | 0.275307 | 0.282060 | 6.38% | 5.76% |
| Online PES | 0.122051 | 0.129264 | 58.50% | 56.81% |
| E-prop anneal | 0.127526 | 0.134809 | 56.64% | 54.96% |

The 50%+ recollection is therefore correct. These runs use online decoder
adaptation, the legacy convex blend, and external wrench injection. They do
not yet demonstrate zero-shot transfer or rotor-actuator-faithful control.

## Naming rule

- `u = sat(u0 + beta*delta_u)` is **CMG residual augmentation** in the current paper.
- `u = (1-beta)u0 + beta*u_neural` is **gate-state neural blending**.
- The umbrella term for a paper containing both is **gate-state neural
  augmentation**.

The historical 50%+ result must be described as legacy online-adaptive gate-state
neural blending, independently of newer additive experiments.

## New corrected X2 rotor-actuator result (2026-08-27)

The clean runner exactly reproduced the classical 45 s Hard45 mean quaternion
error (`0.294082`) at `dt=0.0005 s`, then used the four X2 rotor actuators for
all compared commands.

| Additive controller | beta | qerr mean | improvement | rotor saturation |
|---|---:|---:|---:|---:|
| Classical | — | 0.294082 | — | 0% |
| Fixed residual | 0.5 | 0.263890 | 10.27% | 0% |
| Adaptive-conductance residual | 0.5 | 0.263890 | 10.27% | 0% |
| Online PES, fixed conductance | 0.5 | 0.138007 | 53.07% | 0% |
| Online PES, adaptive conductance | 0.5 | 0.138007 | 53.07% | 0% |

Using the established composite score formula, the online-PES additive result
improves approximately 52.04%. This is a genuine gate-state residual
augmentation result on the X2 actuator path. It is still deterministic and
adapts on the evaluation trajectory; disturbance, hold-out, sensitivity, and
initial-condition tests remain required before submission.

The fixed/adaptive-conductance pairs are numerically identical. Mean gate state
in the online run is approximately 0.963, so post-gate amplification pushes
most of the run into saturation and suppresses the conductance distinction.
