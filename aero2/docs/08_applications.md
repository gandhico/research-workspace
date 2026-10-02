# 08 - Applications

Applications are robot tasks that run through the shared closed-loop runner in
`aero2/applications/base.py`. They define references and disturbances; they do
not own plant I/O or controller logic.

## Implemented

| Application | Code | Purpose |
|---|---|---|
| `reference_tracking` | `aero2/applications/reference_tracking.py` | Square-wave pitch/yaw tracking for offline benchmarking and controller comparison. |
| `pitch_reference_tracking` | `aero2/applications/reference_tracking.py` | Pitch square-wave tracking with yaw reference held at zero. |
| `yaw_reference_tracking` | `aero2/applications/reference_tracking.py` | Yaw square-wave tracking with pitch reference held at zero. |

## Planned

| Application | Purpose |
|---|---|
| `regulation_disturbance` | Hold an equilibrium point while injecting repeatable disturbance schedules. |
| `calibration_check` | Verify encoder signs, zero offsets, gyro bias, and command directions before closed-loop tests. |
| `startup_shutdown` | Exercise safe hardware initialization and shutdown sequences without running a controller. |

## Desktop App

Aero 2 has its own desktop app:

```powershell
python .\app\aero2_app.py
```

The app delegates to:

```powershell
python .\runners\run_control.py --model helicopter_2dof --mode offline --controller pd --application reference_tracking
```

It exposes the same execution-mode names used by the backend contract:

| App label | Backend key | Status |
|---|---|---|
| Offline Simulation | `offline` | Implemented. |
| Digital Twin | `virtual_twin` | Pitch-only QLabs live validated; current scene keeps yaw locked. |
| Hardware Experiment | `hardware` | Scaffolded. |

Scaffolded modes are blocked by default so the interface remains honest about
what is implemented. Digital Twin is enabled with a confirmation prompt because
it depends on an external QLabs process. Once Direct HIL/PAL hardware is
validated, the app should enable hardware mode without changing controller code.

Axis-specific applications are available for staged validation:

| Application | Purpose |
|---|---|
| `pitch_reference_tracking` | Validate pitch control while holding yaw reference at zero. |
| `yaw_reference_tracking` | Diagnose yaw control while holding pitch reference at zero. |

The current QLabs asset was diagnosed with
`runners/run_virtual_twin_io_diagnostic.py --test all`: direct yaw and motor
pulses moved pitch but left yaw angle, yaw rate, and yaw encoder channel 3 fixed.
Use `yaw_reference_tracking` for software/offline tests until a true 2-DOF QLabs
scene is loaded.
