# QDrone/QDrone2 Mathematical Formulation

## Plant/system description

The shared offline campaign starts with a hover abstraction:

```text
x = [phi, phi_dot, theta, theta_dot, psi, psi_dot, z, z_dot]
u = [roll_cmd, pitch_cmd, yaw_cmd, thrust_delta]
```

The state is expressed as tracking error around hover or waypoint hold.

## Baseline controller

The baseline is a cascaded PD-style attitude/altitude controller represented in
linear form:

```text
u_base = clip(-K x, -u_max, u_max)
```

The command limits are attitude command limits for roll/pitch/yaw and thrust
delta for altitude.

## HyperLIF residual augmentation

Each command channel receives a pair-coded HyperLIF gate residual:

```text
z_i = clip(u_base_i / u_max_i, -1, 1)
I_i+ = I0 + gI max(z_i, 0)
I_i- = I0 + gI max(-z_i, 0)
r_i = HyperLIFGate(I_i+, I_i-)
u_res_i = beta u_max_i (r_i+ - r_i-)
u_i = clip(u_base_i + u_res_i, -u_max_i, u_max_i)
```

The residual should be evaluated first in simulation/virtual hover and only then
in hardware.

## Signals

Inputs:

- Attitude error and angular rates.
- Altitude error and vertical rate.
- Baseline command vector.

Outputs:

- Roll/pitch/yaw/thrust residual corrections.
- Gate diagnostics per command channel.

## Safety limits

- Keep altitude tests in a netted/clear area.
- Start with virtual/digital-twin tests before hardware.
- Hardware scripts should require explicit arming and a kill switch.
- Do not enable residual thrust correction until attitude residuals are stable.

