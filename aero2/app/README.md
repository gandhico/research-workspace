# Quanser Aero 2 App

This folder contains the robot-specific desktop control panel for Aero 2
experiments.

Launch it from the project root:

```powershell
cd C:\00_Research_\Neuromorphic_Embodied_AI\04_Aero2_SNNs
python .\app\aero2_app.py
```

The app delegates experiment execution to `runners\run_control.py`, which uses
the existing `model x backend x controller x application` interfaces. The GUI is
only a configuration, launch, stop, and monitoring surface.

## Execution Modes

| App mode | Backend key | Current status |
|---|---|---|
| Offline Simulation | `offline` | Implemented. |
| Digital Twin | `virtual_twin` | Pitch-only QLabs live validated; the current scene keeps yaw locked. |
| Hardware Experiment | `hardware` | Scaffolded; Direct HIL/PAL backend still needs implementation. |

By default, the app blocks scaffolded modes so that a user does not mistake them
for validated paths. Digital Twin is no longer scaffolded, but it asks for
confirmation because it expects QLabs to be open at `localhost:18950`.
When the PAL/QLabs backend is connected, the Aero2 LED convention is red while
idle or shutting down, and green while runner commands are actively being sent.

## Current Choices

- Models: `helicopter_2dof`, `linear_2dof`, `pitch_only`, `yaw_only`, `half_rotor`.
- Controllers: `pd`, `lqr`, `lqg`, `mpc`, `backstepping`, `smc`, `nmpc`, `hyperlif`.
- Applications: `reference_tracking`, `pitch_reference_tracking`, `yaw_reference_tracking`.

The dropdown choices are loaded from `aero2\config\capabilities.py`, and the app
shows the selected capability status before launch. Stage 2 smoke tests verify
that every listed controller runs offline on `helicopter_2dof`, and every listed
model runs offline with the PD baseline through the same direct runner path used
by the app. Stage 3 unit tests verify the digital-twin PAL adapter with a fake
PAL object. Stage 3b live QLabs smoke tests validate pitch-axis execution and
show that yaw remains fixed in the current virtual scene/configuration. Stage
3c open-loop diagnostics confirm the loaded QLabs asset behaves as pitch-only:
direct yaw and direct motor pulses move pitch but leave yaw angle, yaw rate, and
yaw encoder channel 3 at zero.

Additional regulation, disturbance, calibration, hardware startup, and shutdown
workflows should be added through the shared backend/application layer first,
then exposed here.
