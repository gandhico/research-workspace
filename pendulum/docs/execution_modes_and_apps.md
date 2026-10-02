# QUBE-Servo Pendulum Execution Modes and App

The pendulum project uses one robot-specific desktop app:

```powershell
python .\app\qube_pendulum_app.py
```

The app is a launcher and monitor for the existing backend runners. It must not
contain a separate control implementation.

## Modes

| Mode | Runner mapping | Purpose |
|---|---|---|
| Offline Simulation | `python .\runners\run_offline_benchmark.py --duration <s>` | Software-only benchmark for baseline and HyperLIF residual behavior. |
| Digital Twin | `python .\runners\run_online_qube.py --hardware 0 ...` | Quanser virtual/digital-twin execution using the online runner. |
| Hardware Experiment | `python .\runners\run_online_qube.py --hardware 1 ...` | Physical QUBE-Servo execution after sensor checks and safety confirmation. |

## Current App Controls

- Execution mode.
- Controller mode: sensor check, balance, or HyperLIF residual balance.
- Duration.
- Sample rate.
- Voltage limit.
- Capture angle.
- Motor-output arming.
- Stop and emergency-stop process termination.
- Live runner output.

## Safety Rules

- Sensor check commands zero voltage.
- Closed-loop commands are zeroed by the runner unless `--armed` is present.
- The hardware mode asks for confirmation before an armed closed-loop run.
- Emergency stop terminates the runner process; the runner's `finally` block is
  responsible for zero-voltage shutdown through `safe_stop_qube`.

## Planned Additions

- Nonlinear energy-based swing-up mode.
- Capture-transition state display.
- Balance-state display.
- Saturation and fault indicators.
- Red/green Quanser status indicator mapping after official or experimental
  confirmation.
- Shared configuration loading and saving.
- Plot/export shortcuts for the latest run.
