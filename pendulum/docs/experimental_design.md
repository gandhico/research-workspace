# Qube Servo/Pendulum Experimental Design

## Offline today

Run:

```powershell
python .\runners\run_offline_benchmark.py --duration 20
```

The offline model checks whether the residual wrapper, saturation, metrics, and
plotting behave consistently for a one-input underactuated plant. It is not a
substitute for Quanser's digital twin or hardware.

## Hardware tomorrow

Recommended sequence:

1. Run a read-only sensor check: arm encoder, pendulum encoder, sample time.
2. Command tiny open-loop voltages and verify sign conventions.
3. Run baseline servo position hold at low voltage.
4. Run baseline upright pendulum balance.
5. Add the HyperLIF residual with small blend.
6. Only after balance is reliable, consider swing-up plus residual near capture.

## Metrics

- RMS arm error.
- RMS pendulum angle error.
- Max pendulum angle error.
- Mean absolute motor voltage.
- Voltage saturation fraction.
- Residual mean/max magnitude.
- Gate mean/max.

## Expected figures

- Arm and pendulum error norm: baseline vs residual.
- Motor voltage: baseline vs residual.
- Residual voltage over time.

## Interpretation

A useful residual should reduce pendulum error or recovery time without raising
voltage saturation enough to endanger the rig. If the residual improves arm
tracking but worsens pendulum angle, it should be treated as a failed residual
allocation and redesigned around pendulum-specific features.

