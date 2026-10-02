# QDrone/QDrone2 Experimental Design

## Offline today

Run:

```powershell
python .\runners\run_offline_benchmark.py --duration 20
```

The offline model injects wind-like attitude and altitude disturbances. It tests
whether the residual wrapper can improve hover error while respecting command
limits.

## Hardware tomorrow

Recommended sequence:

1. Confirm QDrone/QDrone2 software stack and communication.
2. Run a sensor/telemetry-only logger.
3. Run baseline hover with no residual.
4. Replay logged baseline signals offline and evaluate residual commands.
5. Test residual on roll/pitch only.
6. Add yaw, then altitude/thrust residuals only after stability is clear.

## Metrics

- RMS attitude error.
- RMS altitude error.
- Max attitude error.
- Max altitude error.
- Mean absolute command.
- Saturation fraction.
- Residual mean/max magnitude.
- Gate mean/max.

## Expected figures

- Attitude/altitude error norm: baseline vs residual.
- Command channels: baseline vs residual.
- Residual command channels.
- Gate activations per command channel.

## Interpretation

A useful residual should reduce hover error under disturbance while keeping
command effort and saturation bounded. If residual thrust increases altitude
oscillation, keep the residual limited to attitude channels until trained
weights or a better vertical feature set is available.

