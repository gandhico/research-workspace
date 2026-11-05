# Omnidrone: plan to the first tethered hover, with the Python ground station only

No Mission Planner and no RC link: `omni_gcs.py` (Python, OptiTrack, MuJoCo twin view) does everything.
Run every command from
`C:\Users\user\Desktop\Omnidrone\research-workspace\omnicopter\mujoco\hardware\ardupilot`.

## 1. Where we are

| Item | Status |
|---|---|
| OptiTrack navigation parameters (stage 1) | ✅ written and verified on the Cube |
| 6DoF frame, Lua mixer, DShot300 on MAIN 1–8 (stage 2) | ✅ boot shows `Frame: Omnidrone 6DoF` and `RCOut: DS300:1-8` |
| ESCs (2× HGLRC SPECTER 60A, BLHeli_32) reversible on DShot | ✅ all 8 reverse (motor test 16:06) |
| Motor map Motor1–8 = twin rotors 1–8 | ✅ |
| Board orientation (`AHRS_ORIENTATION 4`, Yaw180) and accelerometer/level calibration | ✅ |
| Ground station `omni_gcs.py` + `gcs_core.py` + `twin_view.py` | ✅ built; tested against fake Motive and a fake Cube with 10 % packet loss (`test_gcs_core.py`) |
| GCS-only Cube parameters (stage 5) | ⏳ step A |
| Props mounted by hover sign (normal props) | ⏳ step B |
| OptiTrack room calibration on the real vehicle | ⏳ step C |
| Real-vehicle checks with the app (props off, then strapped) | ⏳ steps D–E |
| Battery monitor | ⏳ recommended (audit TODO) |

## 2. How flying works without RC

- **Mode:** ArduPilot **GUIDED** only. The app does SET GUIDED → ARM → TAKEOFF (0.05–0.4 m) →
  position nudges → LAND.
- **KILL** = force disarm (`MAV_CMD_COMPONENT_ARM_DISARM`, 21196): the motors stop **immediately**
  and the vehicle drops onto its tether. The app sends a burst and repeats every 0.1 s until the
  Cube reports disarmed (the link loses about 1 packet in 8). Use the **SPACE** key or the red
  button. Use LAND (**L**) for anything that is not out of control.
- **Automatic actions by the app** (once per flight):
  - **LAND** when the vehicle is more than **0.35 m** from the arming spot, more than **0.45 m**
    high, has lost OptiTrack for 0.5 s, or tilts more than 30°;
  - **KILL** when it tilts more than 60° (out of control).
- **The Cube on its own:**
  - lands if the app's heartbeat stops for 3 s (app closed, PC or Wi-Fi down; `FS_GCS_ENABLE 5`);
  - lands if the OptiTrack pose stops (`FS_EKF_ACTION 1`);
  - keeps all of its other pre-arm checks. Only the RC checks are skipped (`ARMING_SKIPCHK 64`).
- **The honest risk.** Every command, KILL included, travels over the Pico W Wi-Fi link, which lost
  about 1 command reply in 8 today. That is why a **physical kill is required**: a person holding a
  pull-cord or quick disconnect on the battery lead (for example an XT60 loop on a lanyard). Also:
  - a tether that keeps the vehicle ≤ 0.5 m high and ≤ 0.5 m from the spot;
  - nobody inside the cage.

## 3. Before the flight day

### Hardware

1. **Tether rig:**
   - 3–4 lines from the frame's beam nodes to heavy floor anchors;
   - ≤ 0.5 m height and ≤ 0.5 m drift;
   - lines routed so they can never reach a rotor (the rotors face every direction).
2. **Physical kill:** a battery lead with an inline disconnect on a pull cord, held by the safety officer.
3. **Props, by hover sign:**

   | Rotors | Strongest thrust along | Mounting |
   |---|---|---|
   | 1, 4, 5, 8 | +Z (the blue axis in the twin viewer) | normal |
   | 2, 3, 6, 7 | −Z | pusher: the opposite-rotation prop, flipped |

4. **Battery monitor** (recommended): the power module on POWER1. Tell me the module and I'll give
   the `BATT_*` values.

### OptiTrack on this PC (verified 2026-11-04)

Motive:Tracker **3.3.2** runs on this PC. The cameras use the 169.254.199.60 adapter.
Edit → Settings → Streaming → NatNet:
- **Enable** on;
- **Local Interface 192.168.2.2** (the wired adapter, never the Wi-Fi). Loopback did not work
  here, and a blank interface means no streaming at all;
- **Transmission Type Unicast**;
- Rigid Bodies on.

Result: `Aries_Omnidrone` = rigid body **id 2**, about **360 Hz**, NatNet 4.2. Every OptiTrack
command takes the same three options:

`--server 192.168.2.2 --local-ip 192.168.2.2 --unicast`

### Steps

Mission Planner is not needed for any of these. Close it and every other tool that uses UDP 14550.

| Step | What | Command | ✔ Pass when |
|---|---|---|---|
| A | GCS-only parameters (props off) | `python ap_param_load.py config\stage5_gcs_only.param` → `WRITE` → `y` (reboot). Run again, then `python ap_param_audit.py` | Audit: everything OK except `BATT_MONITOR`; `ARMING_SKIPCHK = 64: GCS-only setup` |
| B | Thrust direction and strong side (**props ON, strapped down**) | `python motor_test_6dof.py --props-on --delta 50` | All 8 push along +Z on plus, and "All 8 props hover on their strong side" |
| C | OptiTrack room frame (props off) | `python mocap\omni_mocap_bridge.py --server 192.168.2.2 --local-ip 192.168.2.2 --unicast --list`, then `--calibrate`, then `--check` | Hand checks: forward → N+, right → E+, up → D−, turn right → yaw+ |
| D | App check (**props OFF**) | `python omni_gcs.py --server 192.168.2.2 --local-ip 192.168.2.2 --unicast`, then click **Twin view** | See below |
| E | Restrained spool-up (**props ON, strapped to the floor**) | In the app: ARM → TAKEOFF **0.10 m** → watch 3 s → **SPACE** (KILL) | See below |

**Step D passes when:**
1. Every pre-flight gate is green except the operator box: Cube link, OptiTrack to EKF ≥ 20 Hz,
   EKF = OptiTrack < 5 cm, Cube attitude = OptiTrack < 5°, link loss < 25 %, no PreArm, at the spot.
2. Moving and tilting the vehicle by hand moves the app's numbers and the twin view the same way.
3. Tick the box, **ARM**: armed, with motors still stopped (the 6DoF mixer outputs 1500 µs at idle).
4. **SPACE**: disarmed within a fraction of a second.
5. ARM again, then **DISARM**: disarmed.

**Step E passes when:**
1. All 8 motor boxes turn **green** (strong side). None is amber.
2. The vehicle pushes up evenly against the straps, with no twisting or tipping.
3. KILL stops everything at once.

If any motor box turns amber or the vehicle twists, **stop** and send me the app's
`flight_logs\telemetry_*.csv`.

## 4. Flight card: first tethered hover

**Roles:**
- **App operator:** the keyboard. SPACE = KILL, L = LAND.
- **Safety officer:** tether lines, the physical battery kill, calls ABORT.
- **Observer:** watches the vehicle and the twin view.

**Pre-flight (every battery):**
1. Battery charged; voltage noted.
2. Props tight and as in step B.
3. Tether attached and clear of every rotor.
4. Vehicle BOTTOM down at the calibration spot, FORWARD toward room +x.
5. `python omni_gcs.py --server 192.168.2.2 --local-ip 192.168.2.2 --unicast`: every gate green. Tick the box only when the
   tether is attached, the area is clear and the kill person is ready.

**Flight:**
1. **ARM.** The app sets GUIDED itself. The motors stay stopped.
2. **TAKEOFF 0.25 m** and confirm. The vehicle climbs and holds. Watch:
   - the motor boxes stay green;
   - "From arming spot" stays small;
   - EKF − OptiTrack stays under about 5 cm.
3. **Hold 20 s.** Then single small nudges, waiting about 5 s after each:
   - Yaw+ / Yaw− (10°);
   - N / S / E / W (5 cm);
   - Up / Down (5 cm).
4. **LAND** (button or L). The Cube descends and disarms by itself about 10 s after touchdown
   (`DISARM_DELAY`), or press DISARM once it is down.

**ABORT:**
- **SPACE (KILL)** if it is out of control: growing oscillation, flipping, hitting a tether line hard.
- **L (LAND)** for slow drift, battery low, odd sounds, or any warning in the log.
- The **safety officer pulls the battery kill** if the app or the link does not respond.

**After each flight, send me:**
- `flight_logs\telemetry_<time>.csv` and `flight_logs\mocap_<time>.csv` (written by the app);
- the Cube's DataFlash log. Without Mission Planner, take the SD card out of the Cube and copy the
  newest file from `APM\LOGS`.

From them I check:
- rate tracking and oscillation;
- the learned hover throttle;
- vibration;
- which side each rotor ran on;
- EKF vs OptiTrack agreement;
- link loss.

## 5. After the first good hover

1. Longer hovers and small square patterns with the nudge pad.
2. SystemID sweeps (needs SystemID mode from the app; I will add it), which feed the twin
   identification: thrust per motor, strong/weak ratio, motor lag, delays.
3. Twin variant with asymmetric thrust (normal props), retune in simulation, then untethered flight.
