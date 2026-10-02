# QCar/QCar2 Experimental Design

## Offline today

Run:

```powershell
python .\runners\run_offline_benchmark.py --duration 20
```

This produces baseline and HyperLIF-residual CSV logs plus a summary JSON and
comparison figure. Offline dynamics model lane curvature and heading disturbance
only; they are a wiring/reproducibility check, not a hardware claim.

## Hardware tomorrow

Recommended sequence:

1. Perception only, no motion.
2. PID low-speed lane following.
3. SMC low-speed lane following.
4. PID + gated Adaptive HyperLIF residual.
5. SMC + gated Adaptive HyperLIF residual.
6. NMPC + gated Adaptive HyperLIF residual only after PID/SMC signs are stable.

## Metrics

- Lane-valid fraction.
- Mean absolute lane error.
- RMS lane error.
- Max lane error.
- Mean absolute steering.
- Steering saturation fraction.
- Residual mean/max magnitude.
- Gate mean/max.
- Battery voltage and watchdog status for hardware logs.

## Expected figures

- Baseline vs residual lane-error norm.
- Steering command comparison.
- Residual steering over time.
- Lane perception validity and yellow-pixel diagnostics for hardware logs.

## Interpretation

A useful residual should reduce lane-error RMS without unacceptable steering
saturation or lane-loss recovery problems. The legacy QCar benchmark already
shows a promising gate-state result: lower RMS lane error than PD/classical,
but with higher steering effort and saturation. The next evidence step is to
repeat that comparison with the hardware-safe runner and fixed perception.

