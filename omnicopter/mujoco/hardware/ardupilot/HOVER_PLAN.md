# Omnidrone: plan to the first tethered hover

Written 2026-11-04. Commands run from
`C:\Users\user\Desktop\Omnidrone\research-workspace\omnicopter\mujoco\hardware\ardupilot`.
The step-by-step details are in [RUNBOOK.md](RUNBOOK.md). This page is the hover-specific plan
and the flight card.

## 1. Where we are

| Item | Status |
|---|---|
| OptiTrack navigation parameters (stage 1) | ✅ written and verified |
| 6DoF frame, Lua mixer, DShot300 on MAIN 1–8 (stage 2) | ✅ boot shows `Frame: Omnidrone 6DoF` and `RCOut: DS300:1-8` |
| ESCs (2× HGLRC SPECTER 60A, BLHeli_32) reversible | ✅ all 8 reverse on DShot (motor test 16:06) |
| Motor map Motor1–8 = twin rotors 1–8 | ✅ identity |
| Board orientation | ✅ `AHRS_ORIENTATION 4` (Yaw180), residual 1.1° |
| Accelerometer and level calibration | ✅ successful (over USB) |
| Props: **normal (one-direction)**, mounted by hover sign | ⏳ step 7 |
| OptiTrack bridge streaming to the EKF | ⏳ steps 8–9 |
| RC receiver, E-stop switch, flight modes, failsafes | ⏳ step 10, **blocks arming** |
| Battery monitor | ⏳ step 10, strongly recommended |

**Arming is blocked until both of these are fixed:**
- `PreArm: RC not found`: there is no receiver.
- `PreArm: VisOdom: not healthy`: the OptiTrack pose is not being sent yet.

The pre-arm checks stay on (`ARMING_SKIPCHK 0`). Do not disable them to get around this.

## 2. Hover concept for the first flight

- **Attitude:** the twin's hover attitude, BOTTOM face down (rotors 5–8 down, TOP 1–4 up).
  This is the most efficient attitude: 5.36 N per rotor at 2.5 kg.
- **Props:** normal props, so every rotor must hover on its **strong** side.
  - Strong side along **+Z** (the blue axis in the twin viewer): rotors **1, 4, 5, 8**.
  - Strong side along **−Z**: rotors **2, 3, 6, 7**. These are pusher-mounted: the
    opposite-rotation prop, flipped.
- **Tilt limit 20°** (`ATC_ANGLE_MAX`). In the twin, rotor hover thrust stays on the strong
  side up to 35° of tilt on the worst axis, with ≥ 2 N margin up to 22.5°.
- **Mode: Stabilize, pilot on sticks.** The 6DoF mixer translates by tilting like a normal
  copter (forward/lateral thrust disabled in the `.lua`). Pure yaw changes nothing for the rotors.
- **The tether is the fence.** ArduPilot's circle fence needs ≥ 30 m radius and ≥ 10 m altitude,
  so it cannot be used in the cage.
- **Gains:** ArduPilot defaults (`ATC_RAT_RLL/PIT` P 0.135, I 0.135, D 0.0036). The twin
  predicts a rate-loop crossover of about 9 rad/s with them (assuming 10 N/rotor). Retune only
  from the first flight's log.

## 3. Before the flight day

### 3.1 Hardware

1. **RC transmitter and receiver**, bound and connected to the Cube's **RCIN** port.
   - Assign a 3-position switch on **channel 5** (flight modes).
   - Assign a 2-position switch for the **E-stop**.
2. **Battery monitor:** the power module on the Cube's POWER1 input.
3. **Props, by hover sign:** rotors 1, 4, 5, 8 strong toward +Z; rotors 2, 3, 6, 7 strong toward −Z.
4. **Tether rig:**
   - 3–4 lines from the frame's beam nodes to heavy floor anchors.
   - Lengths that allow **≤ 0.5 m height and ≤ 0.5 m drift**.
   - Route the lines so they can never reach a rotor. Props face every direction on this vehicle.
5. **Area:** net or cage closed, safety glasses, a fire-safe LiPo bag, nobody inside the cage.

### 3.2 Configuration and tests (props off unless stated)

| # | What | Command or action | ✔ Pass when |
|---|---|---|---|
| 7 | Thrust direction and strong side (**props ON, strapped down**) | `python motor_test_6dof.py --props-on --delta 50` | All 8 push along +Z on the plus pulse, the tool reports "All 8 props hover on their strong side", and nothing is flagged |
| 8 | OptiTrack calibration | `python mocap\omni_mocap_bridge.py --server <MOTIVE_PC_IP> --list`, then `--calibrate`, then `--check` | Hand checks: N, E, D and yaw all have the right signs |
| 9 | Bridge to the EKF | `python mocap\omni_mocap_bridge.py --server <MOTIVE_PC_IP> --stream --origin 0,0,0`, then Mission Planner **UDP 14551** | EKF-mocap < 3 cm, Cube-mocap roll/pitch/yaw within ±3°, ~30 Hz sent, `VisOdom` pre-arm gone |
| 10a | First-hover parameters | `python ap_param_load.py config\stage4_first_hover.param`. The bridge must be stopped and Mission Planner on USB, because the loader needs UDP 14550. | "Everything in this file is already set" |
| 10b | RC | Mission Planner (USB): SETUP → Radio Calibration. Flight Modes page shows Stabilize / AltHold / Loiter on the 3 positions. Full Parameter List → `RCx_OPTION` = 31 on the E-stop channel | `RC not found` gone, modes switch correctly |
| 10c | Battery | SETUP → Optional Hardware → Battery Monitor: Analog Voltage and Current + your module. Then `BATT_LOW_VOLT` = cells × 3.5, `BATT_FS_LOW_ACT` = 1 (Land) | The HUD voltage matches a multimeter |
| 10d | Audit | `python ap_param_audit.py` (bridge stopped, Mission Planner on USB or disconnected) | No TODO except ones you have accepted |
| 11 | Arming test (**props OFF**, bridge streaming, Mission Planner on 14551) | Stabilize, arm (throttle down + yaw right 2 s), raise the throttle a little, flip the E-stop, disarm (throttle down + yaw left 2 s) | Motors still at idle, spin with throttle, and stop on the E-stop |
| 12 | Push test (**props ON, strapped down**, ~30 % throttle) | Push and tilt the frame with a stick | Every push is resisted, with no oscillation |

## 4. Flight card: first tethered hover

**Roles.** Use three people. Nobody else enters the cage.

| Role | Responsibilities |
|---|---|
| **Pilot** | RC: throttle, mode switch, E-stop |
| **GCS operator** | Watches the bridge status line (EKF-mocap, Cube-mocap, Hz), Mission Planner Messages, battery voltage, and calls out warnings |
| **Safety officer** | Tether, people, calls **ABORT** |

**Pre-flight (every battery):**

1. Battery fully charged; voltage recorded.
2. Props tight. Their orientation matches the step-7 result (1, 4, 5, 8 strong +Z; 2, 3, 6, 7 strong −Z).
3. Tether lines attached and clear of every rotor. Vehicle BOTTOM down at the calibration spot,
   FORWARD toward room +x.
4. Start the bridge (Motive streaming), then connect Mission Planner on UDP 14551. On the status line:
   - ~30 Hz sent;
   - EKF-mocap < 3 cm;
   - Cube-mocap within ±3°;
   - `Cube disarmed Stabilize`.
5. Mission Planner Messages: no `PreArm` lines.
6. Mode switch at Stabilize, throttle down, E-stop off. Pilot and safety officer say "ready".

**Flight:**

1. Arm (throttle down + yaw right for 2 s). The motors stay at idle, stopped (1500 µs).
2. Raise the throttle **slowly**. Lift-off is expected around mid-stick or a little above
   (`MOT_THST_HOVER` 0.5, real thrust unknown).
3. Climb to **0.2–0.3 m**. Hold **10–20 s** with small corrections only.
4. Give gentle inputs: a little roll, pitch and yaw, one at a time. Each must respond in the
   right direction and settle.
5. Lower the throttle slowly to land. Throttle fully down, then disarm (throttle down + yaw left for 2 s).

**ABORT immediately: throttle down to land, or E-stop if it is out of control (the tether catches it) when:**
- the vehicle oscillates and the oscillation grows;
- it tilts more than about 15° without command;
- it drifts hard against a tether line;
- it yaws unexpectedly;
- a rotor makes an abnormal sound;
- the bridge shows `NOT TRACKED`, `NO CUBE HEARTBEAT` or large EKF-mocap differences;
- any failsafe message appears;
- the battery reaches the planned landing voltage.

**After each flight:**
1. Disarm and unplug the battery.
2. Download the log: Mission Planner → DATA → DataFlash Logs → **Download DataFlash Log Via Mavlink** → newest.
3. **Send me** the `.bin` and `mocap\logs\mocap_<date>_<time>.csv`. From them I check:
   - rate tracking (oscillation);
   - learned hover throttle (`MOT_THST_HOVER`);
   - vibration;
   - motor outputs, including whether any rotor approached its weak side;
   - EKF vs OptiTrack agreement;
   - Wi-Fi packet loss.

**Quick tuning only between flights:**
- **Oscillation:** land, lower `ATC_RAT_RLL_P`, `ATC_RAT_PIT_P` and `ATC_RAT_YAW_P` and the
  matching `_D` by 30 %.
- **Sluggish:** raise them by 20 %.

Change one thing per flight.

## 5. After the first good hover

1. AltHold, then Loiter, still tethered (runbook step 14).
2. SystemID sweeps (step 15). Those logs feed the twin identification: thrust gain per motor,
   strong/weak-side ratio, motor lag, delays.
3. Twin variant with asymmetric thrust (normal props), retune in simulation, then untethered flight.
