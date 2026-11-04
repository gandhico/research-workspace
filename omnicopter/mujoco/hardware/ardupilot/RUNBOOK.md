# Omnidrone runbook: click-by-click, bench → tethered hover → OptiTrack flight

Do the steps in order. **✔ Pass when** is the gate: if it fails, stop and fix before going on.
Background is in [README.md](README.md). Step 1 was done on 2026-11-04
(`audits\audit_20261104_135526`).

---

## A. Things used in every step

### Folders and files

| What | Full path |
|---|---|
| Tools folder (run every command here) | `C:\Users\user\Desktop\Omnidrone\research-workspace\omnicopter\mujoco\hardware\ardupilot` |
| Stage 1 parameters | `...\ardupilot\config\stage1_optitrack_ekf.param` |
| Stage 2 parameters | `...\ardupilot\config\stage2_6dof_frame.param` |
| Stage 3 parameters (written by step 6) | `...\ardupilot\config\stage3_board_orientation.param` |
| 6DoF mixer script for the Cube | `...\ardupilot\generated\omnidrone_6dof_mixer.lua` |
| Bridge logs | `...\ardupilot\mocap\logs\` |
| Mission Planner | `C:\Program Files (x86)\Mission Planner\MissionPlanner.exe` (1.3.83) |

### Open a terminal

Windows Start → type **PowerShell** → open it, then run:

```powershell
cd C:\Users\user\Desktop\Omnidrone\research-workspace\omnicopter\mujoco\hardware\ardupilot
```

### Connect Mission Planner (three ways)

The connection controls are at the **top right**: a port drop-down, a baud drop-down and the
**CONNECT** button.

| Way | When | How |
|---|---|---|
| **USB** (preferred for configuration) | Steps 2–7 and 10 | 1. USB cable into the Cube's USB port. 2. Port drop-down → the COM port named like `COMx CubeOrange` / `ArduPilot`. 3. Baud → **115200**. 4. **CONNECT**. 5. Wait until the parameter download bar finishes. |
| **Wi-Fi through the Pico** | Only if USB is not reachable | Port drop-down → **UDP** → **CONNECT** → the port box shows 14550 → **OK**. Click **DISCONNECT** before running any Python tool (they need UDP 14550). |
| **Through the bridge** | Steps 9 and 11–15 | Start the bridge first (step 9). Then port drop-down → **UDP** → **CONNECT** → type **14551** → **OK**. |

The Python tools always use the Pico (UDP 14550), so they work while Mission Planner is on
**USB**, but not while it is on UDP 14550.

### Load a parameter file (steps 2, 4, 6)

**Preferred: the verified loader.** It writes through the Pico link and reads every value back.
Mission Planner must not be on UDP 14550 (USB is fine).

```powershell
python ap_param_load.py config\<file>.param
```

1. It shows current → new and asks you to type `WRITE`.
2. It reads every value back.
3. It offers the reboot.

Run the same command again after the reboot until it says
`Everything in this file is already set on the Cube.`

**Alternative, Mission Planner:** this only takes effect after **Write Params**. On
2026-11-04 a load without a completed write left the Cube unchanged.

1. Top menu **CONFIG** → left list **Full Parameter List**.
2. Right-hand buttons → **Load from file** → browse to the `.param` file → **Open**.
3. The changed rows are highlighted. If a message lists parameters that were "not found",
   click **OK**. That is expected on the first load of stage 1 and stage 3.
4. Click **Write Params**. Mission Planner confirms the parameters were saved.
5. Reboot the Cube (next section).

### Change a single parameter

**CONFIG** → **Full Parameter List** → type the name in the **Search** box (top) → click the
**Value** cell → type the value, or pick it from the drop-down → **Write Params**.

### Reboot the Cube

- **Most reliable:** unplug the battery and USB, wait 5 s, then plug them back.
- **Alternative:** **DATA** (top-left) → tab row under the HUD → **Actions** → in the action
  drop-down choose **PREFLIGHT_REBOOT_SHUTDOWN** → **Do Action**.

After a reboot Mission Planner loses the link: click **CONNECT** again.

### Read the Cube's messages

**DATA** → tab row under the HUD → **Messages**.

### Hard rule from step 4 on

**Do not use** Mission Planner's **SETUP → Optional Hardware → Motor Test** page.
Percent tests spin reversible motors in reverse. Only `motor_test_6dof.py` spins motors.
`motor_test_1.py` now refuses by itself on reversible outputs.

---

## Step 0: Label the frame (once, ~20 min)

1. In the terminal, open the twin with rotor labels:

   ```powershell
   python ..\..\review\review_models.py omni --view
   ```

2. Put a sticker with the **twin rotor number** (1–8) next to each physical motor, matching the viewer.
3. Label the six faces with tape:

   | Face | Twin axis | Rotors on that face |
   |---|---|---|
   | **BOTTOM** (down when hovering) | +x | 5, 6, 7, 8 |
   | **TOP** | −x | 1, 2, 3, 4 |
   | **FORWARD** (ArduPilot nose) | +z | 2, 4, 6, 8 |
   | **BACK** | −z | 1, 3, 5, 7 |
   | **RIGHT** | −y | 1, 2, 5, 6 |
   | **LEFT** | +y | 3, 4, 7, 8 |

✔ **Pass when** two people agree on every sticker and face.

## Step 1: Baseline audit (done)

```powershell
python ap_param_audit.py
```

✔ 1066/1066 parameters received.

## Step 2: Stage 1, OptiTrack navigation parameters (props OFF)

1. Mission Planner: **DISCONNECT** (or connect it by USB).
2. Write the file, then type `WRITE`. Ten values change; `VISO_POS_M_NSE` and `VISO_YAW_M_NSE`
   show as "not on the Cube yet". Answer `y` to reboot.

   ```powershell
   python ap_param_load.py config\stage1_optitrack_ekf.param
   ```

3. Wait about 20 s, then run the **same command** again → `WRITE` → `y`. This writes the two `VISO_*` values.
4. Run it a third time. It must say `Everything in this file is already set on the Cube.`
5. In the terminal:

   ```powershell
   python ap_param_audit.py
   ```

✔ **Pass when** the audit says **OK** for the EKF3 sources, `VISO_TYPE`, `COMPASS_USE` and `GPS1_TYPE`.

## Step 3: ESCs and 3D mode (nothing to run; done by stage 2)

The ESCs are **2× HGLRC SPECTER 60A 4-in-1, BLHeli_32** (stock firmware `SPECTER60_G_128`,
STM32G071). BLHeli_32 accepts the DShot commands **3D on** (10) and **reverse** (21).

Checked in the Copter-4.7.1 source (2026-11-04):
- **ArduPilot switches the ESCs to 3D itself.** While disarmed, it sends `DSHOT_3D_ON` once per
  second to every output in `SERVO_BLH_3DMASK`, and `DSHOT_REVERSE` to every output in
  `SERVO_BLH_RVMASK` (`RCOutput_serial.cpp`, `update_channel_masks`).
- **This only happens when `SERVO_DSHOT_ESC` is a BLHeli type.** Yours was 0. The stage 2 file
  sets **`SERVO_DSHOT_ESC 1`** (BLHeli32/Kiss/AM32) together with `SERVO_BLH_3DMASK 255`.
- **It reaches your MAIN 1–8 outputs.** They run DShot through the I/O coprocessor
  (`BRD_IO_DSHOT 1`), and the commands are forwarded there (`iomcu.send_dshot_command`).
- **No ESC tool or USB linker is needed.** BLHeli pass-through could not reach these outputs
  anyway: it is AUX-only when the I/O coprocessor is on.

✔ **Pass when** step 5 (props off) shows every motor spinning the **other way** at 1460 µs.
- On an ESC that did not switch to 3D, 1460 µs gives about 55 % **forward** instead: harmless
  without props, and the tool flags it.
- If any motor fails to reverse, **stop: this vehicle cannot hover without reversible thrust.**
- Keep the props off until step 5 passes.

## Step 4: Stage 2, 6DoF frame and mixer (props OFF)

1. Mission Planner → connect by **USB**.
2. **Upload the mixer:**
   1. **CONFIG** → left list **MAVFtp**.
   2. In the file tree, open **APM**. If there is no **scripts** folder, right-click inside APM →
      create a new folder named `scripts`.
   3. Open **scripts** → right-click in the file list → **Upload** → choose
      `C:\Users\user\Desktop\Omnidrone\research-workspace\omnicopter\mujoco\hardware\ardupilot\generated\omnidrone_6dof_mixer.lua`.
   4. Check that `omnidrone_6dof_mixer.lua` is now listed in `APM/scripts`.
3. Disconnect Mission Planner if it is on UDP, then write stage 2. It shows 4 changes
   (`SCR_ENABLE`, `FRAME_CLASS`, `SERVO_DSHOT_ESC`, `SERVO_BLH_3DMASK`) and asks for `PROPS OFF`,
   then `WRITE`; answer `y` to reboot. Run it again and it must say everything is set.

   ```powershell
   python ap_param_load.py config\stage2_6dof_frame.param
   ```
4. **DATA → Messages**: look for **`Omnidrone 6DoF mixer loaded`**.
5. In the terminal:

   ```powershell
   python ap_param_audit.py
   ```

If the motors do not respond in step 5: set `FRAME_CLASS` to **3** → Write → reboot → set it
back to **16** → Write → reboot (a known 6DoF quirk).

✔ **Pass when** the message appeared and the audit says **OK** for `FRAME_CLASS`, `SCR_ENABLE` and `SERVO_BLH_3DMASK`.

## Step 5: Motor map and reversal (props OFF, battery connected)

1. Mission Planner on USB, or disconnected; **not** on UDP 14550.
2. Run:

   ```powershell
   python motor_test_6dof.py
   ```

3. Type `YES` (props removed). For each motor:
   1. Type `r`.
   2. Watch which labelled motor spins at 1540 µs and type its twin number.
   3. Watch the 1460 µs pulse and answer `y` if it spun the other way.
4. At the end it prints `Motor map: --motor-map ...`. If that is **not** `1,2,3,4,5,6,7,8`:
   1. Regenerate the mixer:

      ```powershell
      python make_6dof_mixer.py --motor-map <the map it printed>
      ```

   2. Repeat step 4.2 (upload the `.lua` again; overwrite it).
   3. Reboot, then repeat step 5.

✔ **Pass when** all 8 motors reverse and the map matches.

## Step 6: Board orientation and accelerometer calibration (props OFF)

1. Mission Planner on USB, or disconnected; **not** on UDP 14550.
2. Run:

   ```powershell
   python board_orientation.py
   ```

   At each prompt rest the cube on the named face (**BOTTOM**, then **FORWARD**, then
   **RIGHT**), take your hands off, and press **Enter**.
3. If it says "keep AHRS_ORIENTATION 0", go to 6.5. If it wrote
   `...\ardupilot\config\stage3_board_orientation.param`:
   1. Write it, then `WRITE` → `y` (reboot):

      ```powershell
      python ap_param_load.py config\stage3_board_orientation.param
      ```

   2. Run it **again** after about 20 s. `CUST_ROT1_*` only exist after the first reboot, so
      they are written now. Then `y` to reboot.
4. Check the result:

   ```powershell
   python board_orientation.py
   ```

   It must print **CORRECT**.
5. **SETUP → Mandatory Hardware → Accel Calibration → Calibrate Accel.** For each prompt put
   the named face down, hold still, and click the button to continue:

   | Prompt | Face down |
   |---|---|
   | LEVEL | BOTTOM |
   | LEFT | LEFT |
   | RIGHT | RIGHT |
   | NOSE DOWN | FORWARD |
   | NOSE UP | BACK |
   | BACK | TOP |

6. Same page: BOTTOM down → **Calibrate Level**.
7. **DATA** HUD checks:
   - BOTTOM down → the horizon is level.
   - Tilt toward FORWARD → nose-down pitch.
   - Tilt toward RIGHT → right roll.

✔ **Pass when** the HUD behaves like that and `board_orientation.py` still says CORRECT.

## Step 7: Thrust direction (props ON, vehicle strapped down)

1. Strap the vehicle to a heavy base or fixture. Everyone stays ≥ 3 m away; one person stands at the battery plug.
2. Run:

   ```powershell
   python motor_test_6dof.py --props-on --delta 30
   ```

3. Type `PROPS ON RESTRAINED`.
4. For each motor, hold a tissue strip near the rotor. The air must **leave along −Z**, the
   opposite of the blue axis in the twin viewer, so the thrust pushes along +Z. Answer `y` or `n`.
5. If it prints a `SERVO_BLH_RVMASK` value: **Full Parameter List** → search
   `SERVO_BLH_RVMASK` → set that value → **Write Params** → reboot → repeat step 7.

✔ **Pass when** all 8 motors are answered **y**.

## Step 8: OptiTrack (props off)

1. **On the Motive PC:**
   - Rigid body **Aries_Omnidrone** is tracked, with its pivot at the cube centre.
   - **View → Data Streaming**: Broadcast Frame Data **ON**, Rigid Bodies **ON**,
     **Local Interface** = the Motive PC's lab-network IP (not loopback).
   - Find that IP: on the Motive PC run `ipconfig` and take the IPv4 address of the lab adapter.
   - If Motive runs on **this** PC, use this PC's IPv4 address (from `ipconfig` here).
2. In the terminal, replace `<MOTIVE_PC_IP>` and run:

   ```powershell
   python mocap\omni_mocap_bridge.py --server <MOTIVE_PC_IP> --list
   ```

   It must show `'Aries_Omnidrone' ... <== Omnidrone` at about 100 Hz or more. If no name is
   shown, add `--id N` with the id it lists to every bridge command.
3. Calibrate:

   ```powershell
   python mocap\omni_mocap_bridge.py --server <MOTIVE_PC_IP> --calibrate
   ```

   1. BOTTOM down at the take-off spot, with FORWARD facing your chosen room +x → **Enter**.
   2. Lift it straight up ~30 cm, put it back on the same spot → **Enter**.
   3. Slide it ~40 cm toward FORWARD and back → **Enter**.
4. Check:

   ```powershell
   python mocap\omni_mocap_bridge.py --server <MOTIVE_PC_IP> --check
   ```

   Move it by hand, then press **Ctrl+C**:
   - toward FORWARD → **N** increases;
   - toward RIGHT → **E** increases;
   - lift it → **D** decreases;
   - turn it right → **yaw** increases.

   At the calibration pose the twin quaternion reads (0.707, 0, 0.707, 0).

✔ **Pass when** all four hand checks are right and roll/pitch read about 0 with BOTTOM down.

## Step 9: Bridge, EKF and Mission Planner (props off)

1. **Unplug the Cube's USB cable.** From now on Mission Planner goes through the bridge.
2. Terminal (leave it running all session):

   ```powershell
   python mocap\omni_mocap_bridge.py --server <MOTIVE_PC_IP> --stream --origin 0,0,0
   ```

3. Mission Planner: **UDP** → **CONNECT** → **14551** → **OK**.
4. **DATA → Messages**: look for the EKF using external navigation (e.g.
   `EKF3 IMU0 is using external nav data`) and no EKF errors.
5. Move and tilt the vehicle by hand. Watch the bridge status line, the HUD and the map.
6. In Motive, pause streaming for a few seconds: the bridge shows `NOT TRACKED - nothing sent`.
   Resume streaming.

✔ **Pass when:**
- the status line shows ~30 Hz sent;
- **EKF-mocap < 3 cm**;
- **Cube-mocap roll/pitch/yaw within ±3°**;
- the HUD and map follow your hand.

## Step 10: Safety configuration (props off)

1. **RC receiver.** Plug it into the Cube's **RCIN** port and bind it to the transmitter (see
   the receiver manual).
2. **Radio:** **SETUP → Mandatory Hardware → Radio Calibration → Calibrate Radio**. Click
   **OK** on the prompts, move every stick and switch to both ends, then click **Click when Done**.
3. **Flight modes:** **SETUP → Mandatory Hardware → Flight Modes**. Set modes 1–6 to
   Stabilize, Stabilize, AltHold, AltHold, Loiter, Loiter → **Save Modes**. Flip the channel-5
   switch through its 3 positions: the highlighted mode must be Stabilize, then AltHold, then Loiter.
4. **E-stop:** choose a free 2-position switch channel, for example 7. **Full Parameter List**
   → `RC7_OPTION` → **Motor Emergency Stop** (31) → **Write Params**.
5. **Battery:** **SETUP → Optional Hardware → Battery Monitor**. Monitor = **Analog Voltage
   and Current**, Sensor = your power module → reboot. Check that the HUD voltage matches a
   multimeter. Then **SETUP → Mandatory Hardware → FailSafe**: battery low voltage = cells × 3.5 V,
   action **Land**.
6. **Fence and failsafes** (**Full Parameter List**, then **Write Params**, then reboot):

   | Parameter | Value |
   |---|---|
   | `FENCE_ENABLE` | 1 |
   | `FENCE_TYPE` | 3 (max altitude + circle) |
   | `FENCE_RADIUS` | your cage half-width − 0.5 m |
   | `FENCE_ALT_MAX` | your cage height − 0.5 m |
   | `FENCE_ACTION` | **Always Land** |
   | `FS_GCS_ENABLE` | **Enabled always Land** |
   | `MOT_HOVER_LEARN` | 2 |
   | `MOT_THST_HOVER` | 0.5 |

7. Run the audit. Stop the bridge first (**Ctrl+C**), because the audit needs UDP 14550:

   ```powershell
   python ap_param_audit.py
   ```

   Then start the bridge again (step 9.2) and reconnect Mission Planner on 14551.

✔ **Pass when** the audit shows **OK** for the RC receiver, the flight modes, the E-stop switch and `BATT_MONITOR`.

## Step 11: Arming test (props OFF, bridge running, Mission Planner on 14551)

1. Mode switch → **Stabilize**, throttle stick fully down.
2. **Arm:** throttle down + yaw stick fully **right** for 2 s.
   - Motors must stay **stopped**: the 6DoF mixer outputs 1500 µs at idle.
3. Raise the throttle a little: motors spin.
4. Flip the **E-stop** switch: everything stops. Flip it back.
5. Throttle down. **Disarm:** throttle down + yaw stick fully **left** for 2 s.

If it refuses to arm, **DATA → Messages** shows a `PreArm:` line. Send me that text.

✔ **Pass when** it arms, the E-stop stops everything, and it disarms.

## Step 12: Restrained push test (props ON, strapped down with a few cm of play)

1. Arm in **Stabilize** and raise the throttle to about 30 %, well below lift-off.
2. Push and tilt the frame gently with a stick or pole, not your hands, on all three axes.
3. Throttle down, disarm.

✔ **Pass when** every push is resisted and nothing oscillates or grows.

## Step 13: First tethered hover (Stabilize)

1. Tether: three lines from the frame to floor anchors, long enough for ≤ 0.5 m altitude and ≤ 0.5 m drift.
2. Bridge running, Mission Planner on 14551. Arm in **Stabilize**, raise the throttle slowly to
   lift-off, hover 10–20 s, land, disarm.
3. **Download the log:** **DATA** → tab row under the HUD → **DataFlash Logs** →
   **Download DataFlash Log Via Mavlink** → tick the newest log → download. Mission Planner
   saves it under `C:\Users\user\Documents\Mission Planner\logs\` (it shows the folder).
4. **Send me** the `.bin` log and the matching
   `...\ardupilot\mocap\logs\mocap_<date>_<time>.csv`.
5. Quick tuning, only if needed (in **Full Parameter List**):
   - **Oscillates:** lower `ATC_RAT_RLL_P`, `ATC_RAT_PIT_P`, `ATC_RAT_YAW_P` and the `_D`
     terms by 30 %.
   - **Sluggish:** raise them by 20 %.

✔ **Pass when** the hover is steady and `MOT_THST_HOVER` has changed from 0.5 (learned).

## Step 14: AltHold, then Loiter (tethered)

1. From a steady Stabilize hover, flip the mode switch to **AltHold**: the height must hold by itself.
2. Flip to **Loiter**: the position must hold by itself.
3. Flip back to **Stabilize** immediately if anything looks wrong.

✔ **Pass when** Loiter holds within ~10 cm and the bridge shows EKF-mocap < 5 cm in flight.

## Step 15: System-identification sweeps (tethered, land between sweeps)

1. On the ground, disarmed: **Full Parameter List** → set the sweep, then **Write Params**:

   | Parameter | Value |
   |---|---|
   | `SID_AXIS` | 10 (Mixer Roll) |
   | `SID_MAGNITUDE` | **0.05** (never the default 15 on mixer axes) |
   | `SID_F_START_HZ` | 0.5 |
   | `SID_F_STOP_HZ` | 15 |
   | `SID_T_FADE_IN` | 5 |
   | `SID_T_REC` | 40 |
   | `SID_T_FADE_OUT` | 2 |

2. Take off, and settle in a steady **Loiter** hover.
3. **DATA → Actions** → mode drop-down **SystemId** → **Set Mode**. The sweep lasts about 47 s.
   To abort, move the RC mode switch.
4. Land, disarm, then repeat with `SID_AXIS` **11** (pitch), **12** (yaw), and **13**
   (thrust, `SID_MAGNITUDE` **0.03**).
5. Download all logs (as in 13.3) and send them with the bridge CSVs.

✔ **Pass when** all four sweeps finish inside the tether and fence limits.

**Next, on my side:** fit the twin (thrust per motor, motor lag, delays), retune in simulation, then plan the untethered flight.
