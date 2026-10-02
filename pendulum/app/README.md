# QUBE-Servo Pendulum App

This folder contains the robot-specific desktop control panel for the QUBE-Servo
pendulum project.

Launch it from the project root:

```powershell
cd C:\00_Research_\Neuromorphic_Embodied_AI\07_ServoPendulum_SNNs
python .\app\qube_pendulum_app.py
```

The app is intentionally a launcher and monitor for the validated backend
runners. It does not contain a separate controller implementation.

## Execution Modes

| App mode | Runner | Meaning |
|---|---|---|
| Offline Simulation | `runners\run_offline_benchmark.py` | Software-only benchmark of the pendulum residual-control campaign. |
| Digital Twin | `runners\run_online_qube.py --hardware 0` | Quanser virtual/digital-twin path using the same online runner as hardware. |
| Hardware Experiment | `runners\run_online_qube.py --hardware 1` | Physical QUBE-Servo path. Closed-loop motor output requires the app's arm checkbox and the runner's `--armed` flag. |

## Current Controller Choices

- `Sensor check`: reads and logs state while commanding zero voltage.
- `Balance`: upright balance controller with capture-angle protection.
- `HyperLIF residual`: bounded Adaptive HyperLIF residual around the balance controller.

Swing-up should be added only after the nonlinear energy controller, capture
logic, and transition tests are implemented in the shared backend runner.
