# Omnidrone runbook: bench → tethered hover → OptiTrack flight

Run the steps in order. Each step ends with a **GATE**: if the gate fails, stop and fix before
continuing. Background and reasons are in [README.md](README.md).

## Rules that apply to every step

1. **Props OFF until step 7.**
2. **After step 4, never run a percent motor test.** That includes Mission Planner's Motor Test
   tab and `Desktop\Omnidrone\motor_tests\motor_test_1.py`.
   - On reversible outputs ArduPilot 4.7.1 turns "10 %" into 1100 µs, which is about
     **80 % reverse**. "0 %" (`motor_test_1.py`'s emergency stop) is 1000 µs, which is **full reverse**.
   - Use `motor_test_6dof.py` only. Since 2026-11-04, `motor_test_1.py` checks `FRAME_CLASS`
     and `SERVO_BLH_3DMASK` itself and refuses, sending nothing, on reversible outputs or when
     it cannot read them.
3. **One program on UDP 14550 at a time.** The Python tools talk to the Cube through the Pico W
   on UDP 14550, and so does the bridge.
   - For configuration, connect Mission Planner over **USB** (COM port), so it never competes for UDP 14550.
   - During flights, the bridge owns 14550 and Mission Planner connects to it on **UDP 14551**.
4. **Same terminal setup every time:**

   ```powershell
   cd C:\Users\user\Desktop\Omnidrone\research-workspace\omnicopter\mujoco\hardware\ardupilot
   ```

## Step 0: Label the frame (once)

Open the twin with rotor labels: `python ..\..\review\review_models.py omni --view`.

1. Put a sticker with the **twin rotor number** (1–8) next to each physical motor.
2. Label the six faces with tape:

   | Face | Twin axis | Rotors on that face |
   |---|---|---|
   | **BOTTOM** (down when hovering) | +x | 5, 6, 7, 8 |
   | **TOP** | −x | 1, 2, 3, 4 |
   | **FORWARD** (ArduPilot nose) | +z | 2, 4, 6, 8 |
   | **BACK** | −z | 1, 3, 5, 7 |
   | **RIGHT** | −y | 1, 2, 5, 6 |
   | **LEFT** | +y | 3, 4, 7, 8 |

**GATE:** every motor and face is labelled, and two people agree on it.

## Step 1: Baseline audit (props off)

```powershell
python ap_param_audit.py
```

**GATE:** 1066/1066 parameters received. The first audit is saved in `audits\audit_20261104_131835`.

## Step 2: Stage 1, OptiTrack navigation parameters (props off)

1. In Mission Planner (USB): CONFIG → Full Parameter List → **Load from file** →
   `config\stage1_optitrack_ekf.param` → Write Params → reboot.
2. Load the same file a second time, write and reboot. `VISO_*_M_NSE` only appears after the first reboot.
3. Close Mission Planner's connection (or unplug USB), then run:

   ```powershell
   python ap_param_audit.py
   ```

**GATE:** the audit shows **OK** for the EKF3 sources, `VISO_TYPE`, `COMPASS_USE` and `GPS1_TYPE`.

## Step 3: ESC check, the hard gate for everything after

Read the ESC firmware through ArduPilot pass-through (`SERVO_BLH_AUTO=1` is already set),
using BLHeliSuite32 or the web ESC Configurator, with Mission Planner disconnected.
- The firmware must support **DShot 3D / bidirectional** rotation: BLHeli_32, BLHeli_S/Bluejay or AM32.
- Enable 3D/bidirectional mode in the ESC settings if that firmware requires it.

**GATE:** all 8 ESCs are confirmed 3D-capable. Otherwise **stop: this vehicle cannot hover
without reversible thrust.**

## Step 4: 6DoF frame and mixer (props OFF)

1. In Mission Planner (USB): CONFIG → **MAVFTP** → open `APM/scripts` (create it if missing).
   Upload `generated\omnidrone_6dof_mixer.lua`.
2. Load `config\stage2_6dof_frame.param` → Write → reboot.
3. In the Messages tab, look for `Omnidrone 6DoF mixer loaded`.
   If motors do not respond later, set `FRAME_CLASS` to 3, reboot, set it back to 16, and reboot again.
4. Disconnect Mission Planner, then run:

   ```powershell
   python ap_param_audit.py
   ```

**GATE:** **OK** for `FRAME_CLASS` 16, `SCR_ENABLE` and `SERVO_BLH_3DMASK`, and the message appeared.

## Step 5: Motor map and reversal (props OFF)

```powershell
python motor_test_6dof.py
```

Each motor runs 1540 µs and then 1460 µs. Answer which labelled rotor spun, and whether it
reversed. The tool prints `--motor-map`.

- If the map is not `1,2,3,4,5,6,7,8`, regenerate the mixer, upload the new `.lua`
  (step 4.1), reboot, and rerun this step:

  ```powershell
  python make_6dof_mixer.py --motor-map <map printed by the tool>
  ```

**GATE:** all 8 motors reverse, and the map is the identity (or the mixer has been regenerated with it).

## Step 6: Board orientation and accelerometer calibration (props off)

```powershell
python board_orientation.py
```

Rest the cube on its BOTTOM, then its FORWARD, then its RIGHT face when asked.

1. If it writes `config\stage3_board_orientation.param`, load it in Mission Planner, reboot,
   load it again (`CUST_ROT1_*` appear after the first reboot), and reboot again.
2. Run the check:

   ```powershell
   python board_orientation.py
   ```

   It must print **CORRECT** (residual under 3°).
3. In Mission Planner: SETUP → Mandatory Hardware → **Accel Calibration**.
   - Do the 6-pose calibration using the labelled faces: "level" = BOTTOM down,
     "nose down" = FORWARD down, "left" = LEFT down, and so on.
   - Then **Calibrate Level** with BOTTOM down.

**GATE:** `board_orientation.py` says CORRECT after the accelerometer calibration, and the HUD
is level with BOTTOM down. Tilting the FORWARD face down must give negative pitch (nose down).

## Step 7: Thrust direction (props ON, vehicle RESTRAINED)

Strap the vehicle to a heavy base or fixture. Everyone stays clear, with the E-stop in hand.

```powershell
python motor_test_6dof.py --props-on --delta 30
```

For each motor, a tissue strip must show the air leaving along that rotor's **−Z**, so the
thrust is along the blue +Z axis in the twin viewer.
- The tool prints a `SERVO_BLH_RVMASK` value for any wrong motors. Set it, reboot, and repeat this step.

**GATE:** all 8 motors answer **y**.

## Step 8: OptiTrack

Motive settings:
- Rigid body `Aries_Omnidrone`, pivot at the cube centre.
- Data Streaming ON, Local Interface = the Motive PC's network IP.

```powershell
cd mocap
python omni_mocap_bridge.py --server <MOTIVE_PC_IP> --list
python omni_mocap_bridge.py --server <MOTIVE_PC_IP> --calibrate
python omni_mocap_bridge.py --server <MOTIVE_PC_IP> --check
```

- `--list` must show `Aries_Omnidrone` at ≥100 Hz. If the name is missing, add `--id N`.
- **Calibrate:**
  1. BOTTOM down at the take-off spot, with FORWARD facing the direction you want as room +x.
  2. Lift it straight up about 30 cm, then put it back.
  3. Slide it about 40 cm toward FORWARD, then back.
- **Check:** move FORWARD → N increases; move RIGHT → E increases; lift → D decreases;
  turn right → yaw increases. At the calibration pose the twin quaternion must read
  (0.707, 0, 0.707, 0).

**GATE:** all four hand checks pass, and roll and pitch read about 0 with BOTTOM down.

## Step 9: Bridge, EKF and Mission Planner (props off)

```powershell
python omni_mocap_bridge.py --server <MOTIVE_PC_IP> --stream --origin 0,0,0
```

Then in Mission Planner: choose **UDP** at the top right → Connect → port **14551**.

**GATE, all of these with the vehicle moved and tilted by hand:**
- The status line shows about 30 Hz sent and **EKF-mocap < 3 cm**.
- It also shows **Cube-mocap roll, pitch and yaw within ±3°**.
- Mission Planner Messages show the EKF using external navigation (e.g. `EKF3 IMU0 is using
  external nav data`), with no EKF errors.
- The Mission Planner map and HUD follow the hand motion.
- Pausing Motive streaming: the bridge shows `NOT TRACKED - nothing sent`, and Mission
  Planner's EKF status degrades within a few seconds. Resuming restores both.

## Step 10: Safety configuration (Mission Planner, props off)

- **RC:** bind the receiver and run Radio Calibration. Then rerun `python ap_param_audit.py`;
  it must say **OK** for "RC receiver".
- **Flight modes** (`FLTMODE_CH 5`, 3-position switch = modes 1, 4 and 6): Stabilize, AltHold, Loiter.
  Put Land on another switch or mode slot.
- **E-stop:** on a 2-position switch, set `RCx_OPTION = 31` (Motor Emergency Stop) for that
  channel. Test it in step 11.
- **Battery:** set `BATT_MONITOR` to match the power module (e.g. Analog Voltage and Current),
  set the cell voltages, and battery failsafe = Land.
- **Fence:** `FENCE_ENABLE 1`, type = altitude + circle, radius and altitude smaller than the
  cage, action = Land.
- **GCS failsafe:** `FS_GCS_ENABLE` = Land. `FS_EKF_ACTION` is already 1 (Land).
- **Learning:** `MOT_HOVER_LEARN 2`, and start `MOT_THST_HOVER` at 0.5.

**GATE:** the audit has no TODO except items you have consciously accepted.

## Step 11: Arming test (props OFF, bridge streaming)

Arm in **Stabilize** with the RC.
1. At zero throttle the motors stay stopped; the 6DoF mixer outputs 1500 µs at ground idle.
2. Raise the throttle slightly: the motors spin.
3. Flip the **E-stop**: everything stops.
4. Disarm.

**GATE:** arming, E-stop and disarm all behave exactly like that, with no pre-arm errors left.

## Step 12: Restrained wrench check (props ON, strapped down with a few cm of play)

In Stabilize, bring the throttle to about 30 %, below lift-off. Push and tilt the frame by hand
(gloves, from the side): every push must be resisted, with no growing oscillation. Then disarm.

**GATE:** stable, and corrections oppose the pushes on all three axes.

## Step 13: First tethered hover (Stabilize)

Use a three-point tether that keeps altitude ≤ 0.5 m and drift ≤ 0.5 m. Keep the bridge
streaming for the logs. The pilot raises the throttle slowly until lift-off, holds 10–20 s,
then lands and disarms.
- **If it oscillates:** land and lower `ATC_RAT_RLL/PIT/YAW_P` and `_D` by 30 %.
- **If it is sluggish:** land and raise them by 20 %.

Download the DataFlash log: Mission Planner → DataFlash Logs → Download via MAVLink.
Keep it together with `mocap\logs\mocap_*.csv`.

**GATE:** a steady hover, `MOT_THST_HOVER` learned (check the parameter), and vibration
(`VIBE`) under 30 m/s².

## Step 14: AltHold, then Loiter (tethered)

From a Stabilize hover, switch to AltHold (height held from OptiTrack). Then switch to Loiter
(position held). Be ready to switch back to Stabilize at any time.

**GATE:** Loiter holds within about 10 cm, and the bridge keeps EKF-mocap under 5 cm in flight.

## Step 15: System identification sweeps (hover, Loiter → SystemID)

Put SystemID (mode 25) on a mode slot.

| Sweep | `SID_AXIS` | `SID_MAGNITUDE` | Notes |
|---|---|---|---|
| Roll | 10 (Mixer Roll) | 0.05 | |
| Pitch | 11 (Mixer Pitch) | 0.05 | |
| Yaw | 12 (Mixer Yaw) | 0.05 | |
| Thrust | 13 (Mixer Thrust) | 0.03 | |

- For mixer axes the magnitude is a 0–1 fraction. **Never** use the default 15 on these axes.
- Common settings: `SID_F_START_HZ 0.5`, `SID_F_STOP_HZ 15`, `SID_T_FADE_IN 5`,
  `SID_T_REC 40`, `SID_T_FADE_OUT 2`.
- Start each sweep from a steady Loiter hover. Raise the magnitude in small steps only if the
  response is barely visible.

Download the logs and keep the bridge CSVs: they are the identification data (README §4).

**GATE:** all four sweeps complete without leaving the fence or tether limits.

After step 15: fit the twin (thrust gains, motor lag, delays), retune in simulation, then go
untethered. That is the next build.
