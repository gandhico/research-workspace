# 07 — Execution Modes (the offline / virtual-twin / hardware contract)

The whole project rests on one idea: a controller never knows where it runs.
`offline → virtual_twin → hardware` is a single config field, never an `if`
inside a controller (brief §5, §17).

## The `Backend` contract (`aero2/execution/backend.py`)
```python
reset(x0) -> Measurement      # set plant state, return first measurement
apply(u) -> None              # send virtual command u=[u_p,u_y] (or mapped motor V)
read() -> Measurement         # angles, rates, currents, imu, timestamp
dt_actual() -> float          # MEASURED loop period — controllers update on this
close() -> None
```
`Measurement` carries `theta, psi, theta_dot, psi_dot, gyro, accel, currents, t, raw`.

## Implementations
| Backend | Plant source | Status |
|---|---|---|
| `OfflineBackend(model, dt, quantize, measurement_noise)` | integrates a `Model` | ✅ functional |
| `VirtualTwinBackend` | PAL `Aero2(hardware=0)` / QLabs at `localhost:18950` | ✅ pitch-only QLabs live validated; current scene keeps yaw locked |
| `HardwareBackend` | Direct HIL `DirectHilAero2IO` | 🚧 stub (P6) |

Selection: `aero2.execution.BACKENDS["offline"|"virtual_twin"|"hardware"]`.

## Capability matrix (controller × backend × variant)

Status language is centralized in `aero2/config/capabilities.py` so the runner,
desktop app, docs, and paper tables can stay consistent.

`T` = tested offline through the direct runner path used by the desktop app.
`E` = experimental/offline only; not hardware-validated. `S` = scaffolded backend.
`V` = validated in previous hardware work and still needs to be reconnected to
this backend contract. `NV` = NotValidated by design.

| Controller \ Backend | offline | virtual_twin | hardware |
|---|---|---|---|
| PD | T, primary baseline | Pitch-only QLabs live validated; yaw/2-DOF requires a true 2-DOF virtual asset | V in previous work; backend reconnect pending |
| LQR / LQG / MPC | T, linear controllers | Backend implemented; controller-specific live validation pending | V in previous work; backend reconnect pending |
| Backstepping / SMC / NMPC | T, nonlinear controllers | Backend implemented; controller-specific live validation pending | V in previous work; backend reconnect pending |
| HyperLIF residual | T, E | Backend implemented; live validation pending | E; no Aero 2 hardware result yet |

Variants:

- `helicopter_2dof`: primary coupled pitch-yaw model; all registered controllers
  are direct-runner smoke tested offline.
- `linear_2dof`: offline-supported linearized model.
- `pitch_only`: offline-supported pitch-axis model.
- `yaw_only`: offline-supported yaw-axis model with stiction approximation.
- `half_rotor`: exploratory offline model, hardware **NV**.

Stage 2 validation added `tests/test_runner_cli.py`, which verifies:

- Direct script execution works without editable install.
- Every app-listed controller runs offline on `helicopter_2dof`.
- Every app-listed model runs offline with the PD baseline.

Stage 3 validation added `tests/test_virtual_twin_backend.py`, which verifies:

- Virtual-twin command mapping (`direct`, `mixed`, `mixed-reversed`) and PAL
  voltage clipping.
- `VirtualTwinBackend` uses PAL's virtual flag `hardware=0`.
- Backend reset/read/apply/close behavior, including zero-voltage safe shutdown,
  using a fake PAL object.
- LED state convention: red while PAL/QLabs is connected but idle, green once
  control commands are being sent, and red again on shutdown.
- The installed PAL `Aero2` module is importable when the project helper adds
  `C:\Quanser\0_libraries\python` and the Quanser API site-packages directory.

Stage 3b live QLabs validation completed:

- `reference_tracking`: connected and ran at 200.1 Hz for 3 s, but yaw stayed
  fixed (`psi_range=[0, 0]`) and yaw saturated (`yaw_sat_frac=1.0`).
- `pitch_reference_tracking`: connected and ran at 199.9 Hz for 3 s with
  pitch RMS 0.1572 rad, yaw RMS 0, and yaw saturation 0.
- `yaw_reference_tracking`: connected and ran at 199.9 Hz for 2 s, but yaw
  stayed fixed (`psi_range=[0, 0]`) and yaw saturated (`yaw_sat_frac=1.0`).

Stage 3c live QLabs I/O diagnostics added
`runners/run_virtual_twin_io_diagnostic.py`, which sends open-loop pitch, yaw,
direct motor-0, direct motor-1, and direct-both pulses while saving angles,
rates, motor voltages, and encoder counts.

Final all-probe artifact:
`results/virtual_twin_io_all_20260712_011105.json`.

Observed at 200 Hz, 3 V pulses, task-based PAL read mode:

- Overall: `theta_range=0.3011` rad, `psi_range=0.0000` rad,
  `psi_dot_peak=0.0000` rad/s, yaw encoder channel-3 range `0`.
- Per-test yaw range stayed `0.0000` and encoder-3 range stayed `0` for
  `pitch`, `yaw`, `direct0`, `direct1`, and `direct_both`.

Conclusion: PAL/QLabs connection, timing, logging, pitch-axis control, and
direct motor writes are live validated. The currently loaded QLabs asset behaves
as pitch-only: yaw is mechanically/configurationally locked or the scene is not
the 2-DOF Aero2 variant. Yaw/2-DOF digital-twin claims require loading/spawning a
true 2-DOF QLabs configuration before controller tuning.

## Why this matters
The original project's headline lesson is that the controller equation and the
real-time implementation are inseparable: PD only became the strongest controller
once derivative filters used the *measured* Δt from `dt_actual()`, not the nominal
0.002 s. The contract makes that Δt the same object everywhere, so offline tuning
and hardware behavior stay honest about timing.
