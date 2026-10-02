# Qube Servo/Pendulum Mathematical Formulation

## Plant/system description

The shared offline campaign uses a linearized rotary-pendulum state:

```text
x = [theta_arm, theta_dot, alpha_pendulum, alpha_dot]
u = motor_voltage
```

`theta_arm` is the servo arm angle error. `alpha_pendulum` is the pendulum angle
error relative to the upright target.

## Baseline controller

The baseline is a saturated PD/LQR-style motor-voltage law:

```text
u_base = clip(-K x, -V_max, V_max)
```

Initial validation uses `V_max = 5 V` to stay conservative.

## HyperLIF residual augmentation

The residual uses the same gate-state architecture as the other platforms:

```text
z = clip(u_base / V_max, -1, 1)
I_pos = I0 + gI max(z, 0)
I_neg = I0 + gI max(-z, 0)
r = HyperLIFGate([I_pos, I_neg])
u_res = beta V_max (r_pos - r_neg)
u = clip(u_base + u_res, -V_max, V_max)
```

The residual should add authority only when the baseline is already asking for a
directionally consistent correction.

## Signals

Inputs:

- Arm angle and angular rate.
- Pendulum angle and angular rate.
- Baseline motor voltage.

Outputs:

- Motor-voltage residual.
- Gate diagnostics.

## Safety limits

- Start with `|u| <= 5 V`.
- Keep arm angle within the lab-safe operating window before raising voltage.
- Do not run swing-up with residual augmentation until upright stabilization is
  stable and logged.

