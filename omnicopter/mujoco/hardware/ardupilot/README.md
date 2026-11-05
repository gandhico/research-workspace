# Omnidrone: identification → twin update → gains → first flight

**Architecture chosen (2026-11-04):** ArduPilot on the Cube Orange runs the fast loops
(6DoF scripting frame, reversible motors). OptiTrack pose reaches the EKF over MAVLink
through the Pico W. The MuJoCo twin supplies the mixer and is used to choose and check gains.
**Identification resources:** OptiTrack, the vehicle's own logs, visual checks. There is no
thrust stand, scale or pendulum.

This folder implements the hardware side of
[TWIN_HARDWARE_VALIDATION_PROTOCOL.md](../../TWIN_HARDWARE_VALIDATION_PROTOCOL.md) and
[NEXT_WEEK_TEST_CARD.md](../NEXT_WEEK_TEST_CARD.md). Keep the canonical XML unchanged.
Put identified values in a new model variant.

**To run the tests and fly, follow [RUNBOOK.md](RUNBOOK.md)**: steps 0–15 with the exact command
lines and a go/no-go gate for each. This README explains the reasons behind them.

> **Safety: after the 6DoF frame change (stage 2), never use a percent motor test.** That
> includes Mission Planner's Motor Test tab and `motor_test_1.py`. ArduPilot 4.7.1 sends
> 1000 + 10×percent µs, and on reversible DShot-3D outputs 1500 µs is stop. So "10 %" is about
> 80 % reverse, and `motor_test_1.py`'s "0 %" emergency stop is full reverse.
> Use `motor_test_6dof.py`.

| File | Purpose |
|---|---|
| [HOVER_PLAN.md](HOVER_PLAN.md) | **Current plan: first tethered hover with the Python ground station only (no Mission Planner, no RC)** |
| [omni_gcs.py](omni_gcs.py) | Ground-station window: OptiTrack → EKF, pre-flight gates, ARM/TAKEOFF/nudge/LAND/DISARM, KILL (space), motor strong/weak display, logs |
| [gcs_core.py](gcs_core.py) | Its engine: Cube link, GUIDED commands with retries, safety monitor (auto LAND/KILL) ([test](test_gcs_core.py)) |
| [twin_view.py](twin_view.py) | MuJoCo window showing the twin at the real vehicle's OptiTrack pose |
| [config/stage5_gcs_only.param](config/stage5_gcs_only.param) | Cube settings for GCS-only flight (RC checks skipped, GCS-loss → Land) |
| [RUNBOOK.md](RUNBOOK.md) | Step-by-step commands and gates from bench to OptiTrack flight (RC version) |
| [ap_param_audit.py](ap_param_audit.py) | Read-only Cube audit: all parameters, firmware, RC receiver, readiness TODOs |
| [ap_param_load.py](ap_param_load.py) | Writes a `.param` file with read-back verification and an optional reboot. Stage-2 values need `ESC 3D CONFIRMED` ([test](test_ap_param_load.py)) |
| [motor_test_6dof.py](motor_test_6dof.py) | 6DoF motor map, reversal and thrust-direction test, PWM 1500±Δ only. Refuses to run on a non-6DoF frame ([test](test_motor_test_6dof.py)) |
| [board_orientation.py](board_orientation.py) | `AHRS_ORIENTATION` from gravity on three labelled faces, written as Custom 1 (`config/stage3_board_orientation.param`); also verifies an existing setting |
| [make_6dof_mixer.py](make_6dof_mixer.py) → [generated/omnidrone_6dof_mixer.lua](generated/omnidrone_6dof_mixer.lua) | ArduPilot 6DoF mixer from the twin's 6×8 matrix |
| [config/stage1_optitrack_ekf.param](config/stage1_optitrack_ekf.param) | EKF/sensor changes for OptiTrack (safe now) |
| [config/stage2_6dof_frame.param](config/stage2_6dof_frame.param) | 6DoF frame + reversible DShot (**only after ESC 3D is confirmed**) |
| [mocap/omni_mocap_bridge.py](mocap/omni_mocap_bridge.py) | OptiTrack → `VISION_POSITION_ESTIMATE`, and the MAVLink hub for Mission Planner |
| [mocap/test_omni_bridge.py](mocap/test_omni_bridge.py) | Loopback test with a fake Motive, a fake Cube and a fake Mission Planner |

## Where things stand

| Item | Status | Evidence |
|---|---|---|
| Twin on this PC (Python 3.11, MuJoCo 3.17) | Runs | `review/verify_rotor_frames.py` PASS; `control/validate_hover.py` 11/11 PASS |
| Hover attitude | Twin's choice (body −x up) is already the most efficient | 5.36 N/rotor at 2.5 kg. Worst attitude needs 9.36 N |
| Reversible thrust | Required | With forward-only thrust capped at 10 N, the best zero-torque lift is 22.9 N, below the 24.5 N weight (linear-program check over all attitudes) |
| 6DoF mixer | Generated; every column gives a pure wrench in MuJoCo (off-axis < 1e-14) | `make_6dof_mixer.py` |
| Cube (audit 2026-11-04) | ArduPilot **4.7.1**. Octa (`FRAME_CLASS 3`), `SCR_ENABLE 0`, DShot300 on SERVO1–8 = Motor1–8, `SERVO_BLH_3DMASK 0`. GPS and compass are the EKF sources. `BATT_MONITOR 0`. All modes Stabilize. No RC switches. SystemID available. `ARMING_SKIPCHK 0` (all checks on). Telemetry at 57600 baud | [audits/audit_20261104_131835](audits/audit_20261104_131835) |
| OptiTrack bridge | Loopback test passes | `mocap/test_omni_bridge_result.json` |
| Motor numbering vs twin rotors | **Unconfirmed** | Step 2 |
| ESC firmware supports DShot 3D | **Unknown** | Step 2 |
| Mass, inertia, thrust per motor, motor lag, delays | **Unidentified** | Step 4 |

## 0. Software (already installed on this PC)

- Git 2.56 and GitHub CLI 2.103.
- Python 3.11 with `mujoco` 3.17, `numpy`, `scipy`, `pandas`, `matplotlib`, `pymavlink`.
- Mission Planner, for MAVFTP script upload, calibrations, HUD and DataFlash logs.
  Parameters are written with `ap_param_load.py`.

## 1. Audit the Cube (read-only)

Close Mission Planner and any running bridge, then run:

```powershell
python ap_param_audit.py
```

It saves every parameter, and the RC receiver check, under `audits/`. Rerun it after each
configuration stage. Nothing is written to the Cube.

## 2. Configure (props OFF)

1. **Stage 1: OptiTrack navigation.** `python ap_param_load.py config\stage1_optitrack_ekf.param`.
   Done and verified on 2026-11-04.
2. **ESCs:** 2× HGLRC SPECTER 60A 4-in-1, BLHeli_32. 3D mode is switched on by ArduPilot itself.
   While disarmed it sends `DSHOT_3D_ON` to every output in `SERVO_BLH_3DMASK`, but only when
   `SERVO_DSHOT_ESC` is a BLHeli type (1). This also works through the I/O coprocessor on MAIN 1–8
   (Copter-4.7.1 `RCOutput_serial.cpp`). BLHeli pass-through cannot reach MAIN outputs, so no ESC
   tool is used.
3. **Upload the mixer.** In Mission Planner, go to Config → MAVFTP and copy
   `generated/omnidrone_6dof_mixer.lua` into `APM/scripts/`.
4. **Stage 2: 6DoF frame.** `python ap_param_load.py config\stage2_6dof_frame.param`
   (`SCR_ENABLE 1`, `FRAME_CLASS 16`, `SERVO_DSHOT_ESC 1`, `SERVO_BLH_3DMASK 255`,
   `SERVO_BLH_MASK 255`, `SERVO_BLH_OTYPE 5`), then reboot.
   - The boot messages must show `Frame: Omnidrone 6DoF…` and **`RCOut: DS300:1-8 …`**.
   - **Why the last two:** the 6DoF frame never puts its motor outputs into DShot. The boot
     banner read `RCOut: PWM:1-14` on 2026-11-04. `AP_MotorsMatrix::init(frame_class)` only
     configures motors that exist at boot, and the script-called
     `AP_MotorsMatrix_6DoF_Scripting::init()` skips `set_update_rate()`. `SERVO_BLH_OTYPE`
     forces the output type on the `SERVO_BLH_MASK` outputs at boot (`AP_BLHeli::init`).
5. **Motor map** (props off): run `python motor_test_6dof.py`. Each motor runs 1500+Δ, then
   1500−Δ µs; you name the labelled twin rotor that spun. The tool prints the `--motor-map`
   for `make_6dof_mixer.py` and flags any motor that does not reverse.
6. **Thrust direction** (props ON, vehicle restrained): run
   `python motor_test_6dof.py --props-on --delta 30`. Positive thrust must push along the
   site's **blue +Z** axis in the twin viewer; a tissue strip shows the airflow leaving along −Z.
   The tool prints the `SERVO_BLH_RVMASK` bits for wrong motors. Fix it there or in the ESC
   setting, never in the mixer.
7. **Flight-controller orientation.** At the hover attitude the mixer's ArduPilot frame is:
   - forward = twin body **+z**;
   - right = twin body **−y**;
   - down = twin body **+x**.

   Run `python board_orientation.py`: it solves the board→FRD rotation from gravity with the
   cube on its BOTTOM, FORWARD and RIGHT faces. Load the `stage3` file it writes and rerun the
   tool to verify. Then do the accelerometer calibration and Calibrate Level with BOTTOM down.
   During streaming, the bridge also shows Cube-minus-mocap roll/pitch/yaw as a live cross-check.
8. **Safety items still missing:**
   - an RC receiver with a Motor Emergency Stop switch (`RCx_OPTION 31`);
   - flight modes Stabilize / AltHold / Loiter / Land on `FLTMODE_CH 5`;
   - a battery monitor (`BATT_MONITOR`, e.g. 4 for an analog power module), then a battery failsafe;
   - `FENCE_ENABLE 1`.

## 3. OptiTrack → ArduPilot bridge

Motive settings:
- **Data Streaming:** Broadcast ON, Local Interface = the Motive PC's network IP, Rigid Bodies ON.
- **Rigid body:** `Aries_Omnidrone`. Put its pivot at the cube centre: the marker offsets in
  `MOTIVE/Aries_Omnidrone.motive` are roughly symmetric, so check the pivot sits there.

```powershell
cd mocap
python omni_mocap_bridge.py --server <MotivePC> --list          # finds 'Aries_Omnidrone' and its id/rate
python omni_mocap_bridge.py --server <MotivePC> --calibrate     # 3 prompts; see below
python omni_mocap_bridge.py --server <MotivePC> --check         # move by hand, check signs
python omni_mocap_bridge.py --server <MotivePC> --stream --origin 0,0,0
```

- **Calibrate:** place the vehicle in its hover attitude with ArduPilot-forward (twin body +z)
  pointing where room +x should be. Then lift it straight up ~30 cm, and slide it ~40 cm forward.
  - Up comes from Motive's ground-plane axis; the bridge refuses a lift more than 10° off it.
  - Forward comes from the slide.
- **Check:** forward → N+, right → E+, up → D−, turning right → yaw+. At the calibration pose,
  the twin quaternion must read (0.707, 0, 0.707, 0).
- **Stream:** the bridge owns UDP 14550, where the Pico sends Cube telemetry. It relays
  everything to **Mission Planner on UDP 14551**: in Mission Planner pick UDP, Connect, port
  14551. It sends the pose at 30 Hz, which fits the 57600-baud link. Each status line shows:
  - the mocap rate in and out;
  - the Cube's mode and arming state;
  - **EKF − mocap** position difference, and **Cube − mocap** roll, pitch and yaw. The EKF is
    using OptiTrack when position stays within a few cm. Roll/pitch within a few degrees confirms
    `AHRS_ORIENTATION` and the calibration pose.
- **What it never sends:** untracked frames, single-frame jumps (marker swaps), or anything
  before the first Cube packet. After a tracking gap longer than 0.5 s, `reset_counter`
  increments. `--origin 0,0,0` sets the EKF origin that Guided/Auto/RTL need indoors.
- **Logs:** `mocap/logs/mocap_*.csv` (twin-frame columns follow
  [COMMON_LOG_SCHEMA.md](../COMMON_LOG_SCHEMA.md)) and `vehicle_*.csv` (EKF echo).
- **Delay:** keep `VISO_DELAY_MS` at its default until ID-4 measures the real Motive→Wi-Fi→Cube delay.

Loopback test (no lab needed, about 2 min): `python mocap\test_omni_bridge.py`.

## 4. Identification with OptiTrack and onboard logs only

Without a load cell or scale, mass and thrust are not separately identifiable.
**Control does not need them separately.** It needs:
- acceleration per unit command (thrust/mass);
- angular acceleration per unit command (torque/inertia);
- the motor time constant;
- the delays.

Those come from flight data. A kitchen scale (≤5 kg) is the one cheap item that would
remove the ambiguity. Without it, keep 2.5 kg and treat identified gains as per-unit-mass.

| ID | Test | Data | Result → twin |
|---|---|---|---|
| ID-1 | Measure motor centres with a ruler | — | Confirms the 0.0973 m site cube. `START_HERE.md` flags it, because the STL frame is about 0.41 m |
| ID-2 | Tethered hover at the nominal attitude, later also arming in other resting orientations (6DoF roll/pitch offsets) | Motor outputs, `ATT`, `VISP`, battery voltage | Least squares over all attitudes gives per-motor thrust gain (relative to mass) and the thrust curve (`MOT_THST_EXPO`). `MOT_THST_HOVER` is learned directly |
| ID-3 | SystemID mode chirps on the rate roll/pitch/yaw axes, tethered then free | SystemID log messages, `RATE`, `IMU`, motor outputs | Motor time constant → MuJoCo `dyntype="filterexact"`; transport delay; torque/inertia per unit command |
| ID-4 | Waving by hand and steady hover | Bridge log vs `IMU`/`ATT` in the DataFlash log | Mocap latency → `VISO_DELAY_MS` and the twin sensor delay |
| ID-5 | Free-coast segments (later) | OptiTrack velocity | Body drag (optional indoors) |

Record every value in `physics/identification/parameter_measurements.csv` and
`physics/omnicopter_parameters.json`. Build `Omnidrone/omnidrone_identified.xml` with
normalized ±1 commands, per-motor gains and first-order motor dynamics. Rerun
`verify_rotor_frames.py`, `validate_hover.py` and the mission campaign. Check held-out logs
with `../validate_paired_logs.py`.

## 5. Gains (ArduPilot 4.7 names)

The twin PD targets position ω=2 rad/s and attitude ω=4 rad/s, both with ζ=0.9.
ArduPilot's structure is angle P → rate PID → mixer. The mixer gives **5.70 N·m per unit
roll/pitch/yaw command**. That is about **66 rad/s² per unit**, with the twin inertia
0.086 kg·m² and assuming 10 N per rotor (unverified).

Current Cube values are ArduPilot defaults:
- `ATC_RAT_RLL/PIT`: P 0.135, I 0.135, D 0.0036;
- `ATC_RAT_YAW`: P 0.18, I 0.018;
- `ATC_ANG_*_P` 4.5;
- `PSC_NE_POS_P` 1, `PSC_NE_VEL_P` 2;
- `PSC_D_POS_P` 1, `PSC_D_VEL_P` 5.

What the twin says about them:
- **Rate loop:** crossover is roughly `ATC_RAT_xxx_P × 66` rad/s, ignoring motor lag. 0.135
  gives about 9 rad/s, a plausible starting point. ID-3 replaces the 66 and adds the measured lag and delay.
- **Angle loop:** `ATC_ANG_*_P` 4.5 sits just under the twin's 4 rad/s attitude design, at
  about half the rate crossover.
- **Yaw:** yaw authority equals roll/pitch authority here (5.70 N·m, inertia nearly
  isotropic), unlike a normal copter. After ID-3, yaw can use roll-like rate gains.
- **Hover throttle:** start `MOT_THST_HOVER` near the twin estimate of 0.54 (at 10 N per rotor;
  0.35 is configured now) with `MOT_HOVER_LEARN=2`.
- **Next build step:** emulate ArduPilot's loops (400 Hz, its filters, this mixer) in the twin
  with identified motor lag and delay. Then choose gains by margin, not by trial in flight.

## 6. Flight progression

Follow [NEXT_WEEK_TEST_CARD.md](../NEXT_WEEK_TEST_CARD.md). Any unchecked item stops the armed test.

1. **Bench, props off.** The audit is clean, the mixer is loaded, arming works in 6DoF, and the
   motor map, signs and orientation are confirmed. The bridge shows a small EKF−mocap difference.
2. **Restrained wrench check.** Tethered or fixtured, Stabilize, low throttle. Push the vehicle
   and check that each correction opposes the push.
3. **Tethered hover in Stabilize** with a safety pilot on RC.
4. **AltHold** with OptiTrack Z, then **Loiter** with OptiTrack XY, then Guided waypoints.
5. **SystemID sweeps** (ID-3), then multi-attitude hovers (ID-2), then retune, then
   forward/lateral 6DoF translation (`set_forward_enable(true)`).

Before arming:
- an RC switch for Motor Emergency Stop (31) or Interlock (32);
- a fence;
- `FS_EKF_ACTION` 1 (Land; already set);
- a GCS failsafe;
- a battery failsafe;
- a tether;
- people outside the cage.

**Wi-Fi loss means OptiTrack loss.** The pilot must be ready to take over in Stabilize.
