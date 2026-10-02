# Aero2 Cross-Platform Validation Bridge

The Aero2 folder already contains the most mature package structure in this
campaign: models, backends, controllers, applications, benchmarking, tests, and
HyperLIF residual code. This document connects that existing work to the shared
Quanser validation campaign used by QCar, Qube Servo/Pendulum, and QDrone.

## Plant/system description

Aero2 is treated as a two-axis pitch/yaw plant with strong coupling and known
yaw-axis difficulty. The mature local implementation lives under `aero2/` and
the first-class runner is `runners/run_benchmark.py`.

The shared campaign uses a lighter abstraction:

```text
x = [pitch_error, pitch_rate, yaw_error, yaw_rate]
u = [pitch_voltage, yaw_voltage]
```

## Baseline controller

The local baseline of record remains the existing PD/LQR/SMC/NMPC benchmark
stack. For cross-platform consistency, the shared runner uses a two-axis
PD-style baseline:

```text
u_base = clip(-K x, -V_max, V_max)
```

## HyperLIF residual augmentation

The local implementation of record is:

```text
aero2/control/neuromorphic/hyperlif_residual.py
```

The shared campaign mirrors the same architecture:

```text
u = clip(u_base + beta V_max (r_pos - r_neg), -V_max, V_max)
```

with one positive/negative gate pair per command channel.

## Offline today

Native Aero2 benchmark:

```powershell
python .\runners\run_benchmark.py
```

Shared-campaign benchmark:

```powershell
python .\runners\run_cross_platform_offline_benchmark.py --duration 20
python .\runners\plot_cross_platform_results.py
```

## Hardware tomorrow

Use the existing Aero2 execution abstraction and hardware backend notes. The
shared campaign is only a cross-platform sanity check; paper-quality Aero2
numbers should come from the native Aero2 benchmark runners and real logs.

## Metrics

- Pitch/yaw RMS tracking error.
- Max pitch/yaw tracking error.
- Mean absolute motor voltage.
- Voltage saturation fraction.
- Residual mean/max magnitude.
- Gate mean/max.

## Interpretation

The existing Aero2 results are honest and important: fixed-weight HyperLIF
residuals did not yet improve the ideal offline plant. The next useful Aero2
hypothesis is not "fixed gates always help", but "trained gate-state residuals
may help in harder regimes such as yaw breakaway, sensor noise, and hardware
disturbances."

