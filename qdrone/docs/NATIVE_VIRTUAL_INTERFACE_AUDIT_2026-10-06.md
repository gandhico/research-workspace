# QDrone2 native virtual/command-interface audit — 2026-10-06

Read-only inspection only: no QUARC model launched, no QLabs actor created, no ESC/flight command sent.

## Verified locally

- `C:/Users/gandhico/Documents/Quanser/0_libraries/resources/rt_models/QDrone2/QDrone2_Workspace.rt-win64` exists (1,101,312 bytes; modified 2026-08-27; SHA-256 `579eea48063ce7a235390b39e5f0a0e83b0cf4839220e6950bfa0fc493cd0284`). Presence does not prove the runtime launches or exposes the required attitude-torque channel.
- `RTMODELS_DIR` points to the containing `rt_models` directory. The QDrone `.venv` imports `qvl` and `pal` successfully.
- `pal.resources.rtmodels.QDRONE2` resolves to the present workspace path (without the `.rt-win64` suffix); this confirms path wiring, not native-model execution.
- QUARC target manager and timing service processes were present, but no QLabs process was running during this check.
- The installed `pal.products.qdrone2.QDrone2StreamStack` exposes `read`, `status_check`, and `terminate`; it is a telemetry stream, not a command interface.
- Read-only source inspection of the installed `qvl.multi_agent.MultiAgent._createQD2` identifies the native launch path: it copies `QDrone2_Workspace.rt-win64` into the `MultiAgent` model directory, allocates HIL/video/pose localhost ports, then calls `QLabsRealTime().start_real_time_model(...)`. This is a specific launcher candidate; it has not been executed here.
- The installed `pal.products.qdrone2.QDrone2StreamStack` receives a 47-double packet. Indices 40:44 are exposed as `motorCmd`, 44 as `battVoltage`, 45 as `lowBattery`, and 46 as `timestampREC`; indices 12:39 contain state vectors. This offers a concrete virtual/hardware telemetry schema once a model is running, but does not establish what unit or control layer `motorCmd` uses.
- `qvl.qdrone2.QLabsQDrone2.set_velocity_and_request_state` sends body velocity, Euler orientation and a motor-enable flag to the QLabs actor. It is a high-level virtual command, not the four-ESC/body-torque injection sought for the ACC residual.
- The `virtual/position_control` vendor source folder described in older notes is absent in the current local tree; `python_to_simulink/virtual` contains an `rtmodels` directory but not the former tutorial sources. The compiled workspace file may have arrived independently.
- The current `runners/twin_acc2027_cmg_residual.py` remains a kinematic pose mirror using X2 physical parameters. No QDrone2 dynamic-validation result follows from it.

## Interface distinction

Quanser's official QUARC board documentation identifies four ESC output channels and sensor inputs on QDrone2 (https://docs.quanser.com/quarc/documentation/qdrone2.html). The current local Python telemetry/waypoint route does not yet expose this inner-loop command path. The P5 ACC residual acts on body torque **before** allocation; a waypoint correction is a different intervention. Before claiming QDrone2 validation of the ACC or dual controller, establish a reproducible interface that records proposed body torque, allocated four-motor command, realized/estimated motor response, state, and deadline/failsafe status.

## Next read-only and virtual actions

1. Use the identified `qvl.multi_agent` launch path in an available QLabs/QUARC session, first recording model hash, versions, ports and process ownership. The installed code establishes the call path, not successful execution.
2. Launch native virtual QDrone2 with the vendor baseline, log hover/step telemetry including the 47-field stream packet, and determine the units and provenance of `motorCmd`. Then determine whether body torque or four ESC commands can be injected without bypassing required vendor safeguards.
3. Compare native virtual hover and step responses against Quanser's local thrust parametrization and against a separately parameterized QDrone2 MuJoCo variant. Do not substitute X2/CF2 parameters.
4. Keep physical hardware in telemetry/shadow mode until the applied-control path, timing, fallback, and geofence are verified in the native virtual environment.

This audit closes file-presence and Python-import questions, but **native dynamic execution and command injection remain unverified**.
