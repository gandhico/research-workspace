# QDrone2 QLabs twin — fidelity boundary

`runners\twin_acc2027_cmg_residual.py` is a **kinematic-mirror virtual twin**,
not a QLabs-native physics twin. Read this before citing or screen-recording
its output.

## What it is

- The exact canonical controller from the ACC2027 repository, imported
  unmodified: `gra_control.gate.CMGResidualAugmentor` and
  `gra_control.math3d`, installed editable
  (`pip install -e C:\Research\papers\ACC2027_Gate_Residual_Control`) into
  `C:\Research\qdrone\.venv` so there is exactly one CMG implementation, not a
  second divergent copy.
- Rigid-body quadrotor dynamics (6-DOF, quaternion attitude + translational)
  integrated in this process with the same quaternion-PD baseline, torque
  limits, and altitude-PD collective-thrust law as
  `gra_control.platforms.drone.run_drone` for the `x2` platform — reimplemented
  without MuJoCo so it can run standalone against a live QLabs connection.
- Mass, inertia, and gravity are read directly from the same Skydio X2 MuJoCo
  model the ACC2027 paper uses (`third_party/mujoco_menagerie/skydio_x2`), at
  load time, not hardcoded — so the plant parameters cannot silently drift
  from the paper's own numbers.
- The resulting pose (position + Euler orientation) is pushed every
  `--viz-every` control steps into the QDrone2 actor already spawned in the
  running Quanser Interactive Labs instance, via
  `qvl.qdrone2.QLabsQDrone2.set_transform_and_dynamics(..., enableDynamics=False)`
  — i.e. QLabs is a **visualization sink**: it renders the pose this process
  computed, it does not compute or contribute any physics of its own.

## What it is not

- **Not mass/inertia-identified to the physical QDrone2.** The X2 numbers are
  a MuJoCo Menagerie model, not a measured QDrone2 parametrization. See
  `3_user_manuals/qdrone2/qdrone2_parametrization/qdrone2_thrust_parametrization.pdf`
  for the one piece of real QDrone2 parametrization pulled onto this machine
  so far.
- **Not the QLabs-native physics path.** Quanser's own virtual QDrone2 pipeline
  (`Documents\Quanser\5_research\autonomous_vehicles\qdrone2\python_to_simulink\virtual`
  and `...\virtual\position_control`) runs real flight dynamics inside a
  compiled QUARC real-time model (`DroneStack`/stabilizer), driven over a
  Mission Server socket. That path was investigated 2026-08-27: `qvl` and
  `pal` are installed (`C:\Research\qdrone\.venv`), `QAL_DIR`/`RTMODELS_DIR`
  are correctly set, but the compiled airframe model
  `RTMODELS_DIR\QDrone2\QDrone2_Workspace` does not exist on this machine yet
  — it has to be built once from
  `virtual\position_control\virtual_QD2_DroneStack_PID_2024a.slx` via
  MATLAB R2025a + QUARC's win64 real-time target. That build is tracked as a
  separate follow-on, not required for this script.
- **No position/velocity feedback.** Exactly like the paper's own MuJoCo `x2`
  runs, only attitude (roll/pitch/yaw) and altitude (`z`) are controlled;
  `x`/`y` are free. Under `hard45`'s large attitude excursions the simulated
  drone will translate tens of meters within seconds — this is correct
  physics given the paper's architecture, not a bug, but it means `hard45`
  will fly the QLabs actor out of the visible scene quickly. Use `--mission
  hover` or `--mission roll` for an in-view demo, or a short `--duration` with
  `hard45`.
- **Not the QLabs-native attitude/torque channel.** Even the QLabs-native
  path above only exposes a Mission-Server-level `[x, y, z, yaw]`
  waypoint/arm/takeoff/land API in Python (`commander.py` read in full,
  2026-08-27) — the inner attitude/rate/motor-mixing loop is opaque, compiled
  into the Simulink stabilizer. Neither this script nor the QLabs-native path
  currently injects the CMG residual at true rotor-torque level outside
  MuJoCo.

## Verified 2026-08-27

`--controller online-pes-adaptive --mission hover --duration 6
--initial-angle-deg 15`: final simulated pose `(x, y, z) =
(-2.3191, -4.8663, 1.0)` at `t=5.9995s` in `trace.csv`; live QLabs actor
readback via `get_world_transform_degrees()` immediately after:
`(-2.316, -4.858, 1.0)` — matches within the `--viz-every` update cadence.
No NaN/Inf in a 6000-row `hard45` dry run; `qerr` magnitudes consistent with
`docs\AGENT_HANDOFF_2026-08-27.md`'s recorded X2 MuJoCo results.
