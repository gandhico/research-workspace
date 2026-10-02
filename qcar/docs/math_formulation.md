# QCar/QCar2 Mathematical Formulation

## Plant/system description

The offline campaign uses an image-lane abstraction:

```text
x = [e_lane, psi_error]
u = steering
```

`e_lane` is the normalized lookahead lane error computed from the yellow-lane
fit. `psi_error` is a heading/slope proxy. The hardware runner computes
`e_lane`, `d_lane_error`, and `slope_xy` directly from the front camera ROI.

## Baseline controller

The classical baseline is the image-space PID/SMC family already used in the
QCar hardware code. The shared offline runner uses the linearized equivalent:

```text
u_base = clip(-K x, -u_max, u_max)
```

with `u_max = 0.35 rad` for steering.

## HyperLIF residual augmentation

The residual module does not replace the baseline:

```text
z = clip(u_base / u_max, -1, 1)
I_pos = I0 + gI max(z, 0)
I_neg = I0 + gI max(-z, 0)
r = HyperLIFGate([I_pos, I_neg])
u_res = beta u_max (r_pos - r_neg)
u = clip(u_base + u_res, -u_max, u_max)
```

The same idea appears in the hardware runner as gated Adaptive HyperLIF residual
modes over PID, SMC, and image-state NMPC.

## Signals

Inputs to residual module:

- Baseline steering command.
- Lane error, derivative, slope, and valid-lane confidence in hardware modes.

Outputs:

- Bounded residual steering.
- Gate diagnostics and residual-gate confidence.

## Safety limits

- Steering command: `|steering| <= 0.35 rad` for offline and initial tests.
- Hardware throttle: start at `0.02` to `0.04`.
- Motion requires explicit `--armed`.
- Use `--steering-sign -1.0` unless a new steering sign test says otherwise.

