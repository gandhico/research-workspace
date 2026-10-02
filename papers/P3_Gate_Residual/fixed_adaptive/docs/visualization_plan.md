# Real-Time Visualization Plan

## Dashboard Architecture

The dashboard is implemented in `src/viz/dashboard.py` using matplotlib with
interactive mode (`plt.ion()`). It runs in the same process as the simulation
and updates every N steps (default: 100 steps = 50ms at dt=0.0005).

## Panel Layout

```
Row 0: Quaternion q0..q3 (measured + reference)
Row 1: Euler angles roll/pitch/yaw (deg) (measured + reference)
Row 2: Body angular velocity wx, wy, wz [rad/s]
Row 3: Body torques τx, τy, τz [Nm] + collective thrust T [N]
Row 4: Motor commands u1..u4 [N] (rotor-level only)
Row 5: Tracking metrics: qerr_angle [rad], altitude z [m]
Row 6: Neural state: gate[0..2], voltage_mean, event_count, |residual|
```

Row 4 is shown only for rotor-level (X2) controllers.

## Usage

```python
dash = Dashboard(enabled=True, update_every=100, max_t_shown=10.0)
dash.setup(has_rotors=True, title="My Run")

for step in simulation:
    ds = DashState(t=t, q=q, q_ref=q_ref, ...)
    dash.update(ds)

dash.save_figures(Path("results/figures"), stem="run_001")
dash.close()
```

## CLI Flags

| Flag                        | Effect                                |
|-----------------------------|---------------------------------------|
| --dashboard                 | Enable dashboard                      |
| --dashboard-update-every N  | Redraw every N simulation steps       |
| --dashboard-window T        | Show last T seconds (default: 10)     |
| --viewer                    | MuJoCo 3D viewer (separate window)    |
| --realtime                  | Add sleep to match real time          |

## Backend Note

On Windows, the TkAgg backend is used by default. If TkAgg is unavailable,
matplotlib falls back to the default backend. For headless runs (save only),
use `matplotlib.use("Agg")` which is set automatically when --no-save is off
and --dashboard is off.

## Offline Plot Generation

Even without --dashboard, plots are generated and saved when --save-figures is used.
Standard output plots:
- `*_euler.png`       Euler angle tracking with references
- `*_tracking.png`    qerr_angle + altitude over time
- `*_motors.png`      Motor commands (if rotor-level)
- `*_neural.png`      Gate state, voltage, events over time
- `*_dashboard.png`   Full dashboard screenshot (if dashboard was active)
