# Real-Time Gain Methodology for EHEKATL XP12

This document records the controller-development method now being used for the
EHEKATL BWB X-Plane 12 experiments. The goal is to move from trial-and-error
attitude tuning to an identifiable, repeatable, paper-ready process.

## Current Status

The initial fixed-gain LQR and damped attitude experiments proved the bridge,
routing, trim biasing, logging, and runtime supervision. The runner now:

1. Uses current X-Plane controls as trim bias.
2. Can isolate pitch or roll axes.
3. Waits instead of exiting when the aircraft is outside the engagement
   envelope.
4. Pauses corrections when attitude/rate/divergence guards are active.
5. Applies actuator magnitude and rate limits.

The newest pitch-only logs still show limit-cycle behavior. The important
finding is that the elevator command is saturated for most or all samples, so
the log is not yet a clean linear identification experiment. The next step is
therefore system identification with deliberately small elevator excitation
around a manually trimmed condition.

## Continuous-Time Pitch Model

Start with the short-period/pitch-rate approximation:

```text
q_dot = a q + b u_e
theta_dot = q
```

where:

```text
theta  pitch attitude [deg]
q      pitch rate [deg/s]
u_e    X-Plane elevator stick command around trim [-1, 1]
a      pitch-rate damping derivative [1/s]
b      elevator effectiveness [deg/s^2/stick]
```

For CSV samples at time `t_k`, estimate:

```text
q_dot_k = (q_{k+1} - q_k) / (t_{k+1} - t_k)
```

and fit:

```text
q_dot_k = a q_k + b u_{e,k} + epsilon_k
```

using least squares:

```text
[a b]^T = (X^T X)^-1 X^T y

X = [q_k  u_{e,k}]
y = q_dot_k
```

This is the first identification layer. After it is stable and repeatable, the
model can be expanded to include angle of attack, velocity perturbations,
actuator lag, and delay.

## Inner Pitch-Rate Controller

The first controller should damp pitch rate before closing the pitch-attitude
loop:

```text
u_e = -k_q (q - q_cmd)
```

For `q_cmd = 0`, the closed-loop rate dynamics become:

```text
q_dot = (a - b k_q) q
```

Choose a desired first-order pole:

```text
p_q = -1 / tau_q
```

Then:

```text
k_q = (a - p_q) / b
```

The selected `tau_q` must be slow enough for X-Plane sample rate, sensor noise,
and actuator rate limits. In these experiments, start around `tau_q = 1.0` to
`2.0 s`, then reduce only after the response is non-oscillatory.

## Outer Pitch-Attitude Loop

After pitch-rate damping is stable, add a slower attitude loop:

```text
e_theta = theta - theta_ref
q_cmd = -k_theta e_theta
u_e = -k_q (q - q_cmd)
```

Substitution gives:

```text
u_e = -k_q q - k_q k_theta e_theta
```

The attitude loop must be much slower than the rate loop. A practical starting
point is:

```text
tau_theta >= 3 tau_q
k_theta = 1 / tau_theta
```

Only after this pitch loop is quiet should lateral-directional identification
start.

## Lateral-Directional Extension

Use the same process after pitch is stable:

```text
p_dot = a_p p + b_a u_a + c_r r
r_dot = a_r r + b_r u_r + c_p p
phi_dot = p
```

where `p` is roll rate, `r` is yaw rate, `u_a` is aileron stick, and `u_r` is
rudder stick. Begin with roll-only identification:

```text
p_dot = a_p p + b_a u_a
```

Then add yaw coupling and rudder once roll damping is repeatable. The control
architecture should mirror pitch:

```text
u_a = -k_p (p - p_cmd)
p_cmd = -k_phi (phi - phi_ref)
```

## Real-Time Platform Rule

The real-time controller should not solve new gains every frame. A practical
flight controller:

1. Identifies or linearizes models offline around trim points.
2. Designs and validates discrete-time gains offline.
3. Stores gain tables by airspeed, altitude, CG, and configuration.
4. Interpolates validated gains online.
5. Applies actuator magnitude/rate limits and safety supervision online.

The online loop should be deterministic: read sensors, filter states, select
gains, compute commands, apply limiters, send actuators, and log.

## Commands

Analyze a pitch log:

```bash
python lqr/identify_pitch_model.py \
  logs/lqr_pitch_lqr_YYYYMMDD_HHMMSS.csv
```

Use the result only if the excitation is small and not mostly saturated.
