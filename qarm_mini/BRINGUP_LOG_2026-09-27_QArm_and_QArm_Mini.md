# QArm + QArm Mini bring-up log — 2026-09-27

From Quanser's out-of-the-box defaults to both arms moving safely under our own Python
tools. Every problem below was hit on the real hardware and fixed that day. Details and the
per-run numbers are in `C:\Research\qarm\RUNNERS.md` and `C:\Research\qarm_mini\RUNNERS.md`;
raw logs are in each project's `hw_logs\`. A copy of this file is in `C:\Research\qarm_mini\`.

---

## 0. Starting point (Quanser defaults on this laptop)

| Item | State at start |
|---|---|
| Software | QUARC 2026 (26.0.5256) + Quanser SDK installed 2026-08-17/18; services running (License Manager, Target Manager, Timing Services); MATLAB R2025a |
| Quanser Python API | Wheels shipped in `C:\Program Files\Quanser\QUARC\python\`, **not installed in any project venv** |
| Quanser Python libs (PAL/HAL) | Two copies in `Documents`: `Documents\Quanser\0_libraries` (**incomplete, 16 files**) and `Documents\Quanser_Academic_Resources_tmp` (complete, release 2026-07-31, 117 files) |
| Project code | `qarm\` and `qarm_mini\`: only the theory papers; no hardware runner. DILISIC runbook (2026-09-09): shadow mode first, no direct actuation |
| QArm | USB, Cypress `CYUSB3` driver, "Quanser QArm USB" (VID 21DF PID 0020), board `qarm_usb`, id `0` |
| QArm Mini | USB-C, FTDI FT232H (VID 0403 PID 6014), driver installed by Windows Update on first plug-in, **COM6**, board `qarm_mini` |
| Quanser PAL defaults | QArm: profiles 1.5708 rad/s and 1.0472 rad/s^2, PID gains set on open. Mini: profiles **6.28 rad/s**, `terminate()` **commands HOME on exit** |

---

## 1. Environment we built

| | `C:\Research\qarm` | `C:\Research\qarm_mini` |
|---|---|---|
| venv | `.venv` (Python 3.13) | `.venv` (Python 3.13) |
| Quanser API | **all** QUARC wheels (installed together; `quanser_api` requires `quanser_multimedia`) | same |
| Quanser requirements | `requirements.txt` from the Academic Resources (numpy **2.3.5**, below 2.4 as Quanser pins) | same |
| PAL/HAL/PIT/QVL | vendored copy in `vendor\quanser_libraries\python`, added to the path by `quanser_libraries.pth` | same |
| Extra | pyrealsense2, pytest, `dilisic` installed editable (its 11 tests pass on numpy 2.3.5) | pytest, `dilisic` editable |
| Resources | manuals, kinematics/dynamics notes, quick starts, research (+ROS), teaching labs, RT models | manual, quick start, research, teaching lab |
| Lock | `requirements.lock.txt` | `requirements.lock.txt` |

---

## 2. QArm: from defaults to moving

| # | Symptom / question | Cause | Fix |
|---|---|---|---|
| 1 | Is the arm there? | — | Read-only probe `tools\qarm_readonly_probe.py`: model 2021, fw 3.3 "QFLEX 2 USB v1.3", serial QF0009012b11142b07; all channels finite |
| 2 | The QArm stores no files | It is a HIL DAQ, not a drive | Installed Quanser's software locally instead (section 1) |
| 3 | Elbow rests at +1.404 rad, past the doc limit of +1.39 | The rest pose sits on mechanical rests | Never echo a raw reading back as a command; clamp and rate-limit |
| 4 | Driver rejects `gripper_profile_velocity/_acceleration` | Listed in the doc, not supported by the fw 3.3 driver | Removed them. The QArm *accepts* `jX_profile_config` |
| 5 | On torque-on, shoulder/elbow moved ~0.05 rad **away** from the hold command | **The servo firmware enforces PAL's joint limits**; the rest pose is outside them, so the servos drive to -17pi/36 / +15pi/36 (= PAL `SLEEP_POSE`). Without PAL's PID gains (no integral term) they stopped short | Set PAL's gains (P 8.89, I 0.012, D 10.23; properties 128-141); clamp all commands to PAL limits. Expect a 4-5 deg lift at every power-on |
| 6 | ID gate failed on timing (5.54% > 5%) | Host busy-wait loop | Hardware-clocked reader task on `HARDWARE_CLOCK_0` (as PAL does): sample jitter 0 |
| 7 | ID tool found no good delay | Only searched 0-5 samples; the real delay is ~16 (160 ms) | `--max-delay 30` -> wrist gate **passed** (`shadow_ready=true`, R^2 0.9996, measured gain 1.017) |
| 8 | Step-test abort at exactly the step size | Instantaneous tracking-error limit = step size | Replaced with an envelope plus a settle-within-1 s check |
| 9 | Streamed wrist setpoints: the wrist crawled | Firmware profile restarts on every 10 ms setpoint | For streamed joints: firmware profile off (0) + **0.8 rad/s software slew limit** |
| 10 | **Motion demo** `tools\qarm_hello_demo.py` | — | sleep -> home -> base +/-0.5 -> wrist +/-0.8 -> gripper -> sleep, 0.6 rad/s: 30 s, no fault, **ran twice, confirmed by eye** |
| 11 | DILISIC shadow mode (runbook step 5) | Open-loop reference drift; adaptation without a closed loop; noisy jerk | Reference model anchored to the baseline; frozen weights as the primary readout; Kalman bandwidth 2.1 Hz. Result: frozen request median 169 / p95 444, the same order as the sim (296 / 417). Only the baseline was ever sent |

Closing the QArm board does **not** drop the arm (it stayed at its held pose).

---

## 3. QArm Mini: from defaults to moving

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | "Could not open the Dynamixel device" | Board id is the **COM port number**, not 0 (Quanser quick start) | `--id 6` |
| 2 | "USB Serial Port" in Error | Windows Update was still installing the FTDI driver (2.12.36.20) | Resolved itself; the port became COM6 |
| 3 | Positions channel-shifted, zeros, 1e-312 velocities, PWM 17.9; later a hang and HIL error **-1376 `DYNAMIXEL_COMMUNICATION_ERROR`** | **FTDI latency timer 16 ms** (Windows default): the small Dynamixel reply packets wait in the FTDI buffer past the driver timeout, so late replies are matched to the wrong request | **Device Manager > Ports > USB Serial Port (COM6) > Port Settings > Advanced > Latency Timer = 2 ms**, power-cycle the arm at rest, replug the USB. Readings consistent after that (noise <= 0.0006 rad) |
| 4 | PWM channels 11000-11004 out of range | Not among the 15 documented inputs | Read only the 15 documented other inputs |
| 5 | Load/current read NaN | A standalone `read_analog` does not fill the buffer on this driver | One combined `card.read(...)`, as PAL does |
| 6 | Joint frame | Raw channels are servo angles | PAL bias map, **verified against the physical rest configuration** (yaw -9, shoulder +191.6, elbow -139.8, wrist +7.6 deg) |
| 7 | Gripper: PAL maps give -0.99 / +1.06 | PAL is internally inconsistent (x-1.8 vs x+1.68, and wrong offset signs); **`write_gripper_position` drives the wrong direction** | **Hand calibration** (torque off): open raw 1.6659, closed raw 4.0819 -> `tools\qarm_mini_calibration.py` |
| 8 | Driver rejects `jX_profile_config`, `gripper_profile_config` | Mini driver differs from the QArm's (it *accepts* the gripper profile values) | Removed; the profile is speed-based (0.6 requested -> ~0.3 rad/s measured, checked at rest first) |
| 9 | Gripper would not open past ~0.25 (no motion, zero load) | **Servo firmware rejects goals beyond its limit** (raw ~2.24-2.27 = PAL's pi-0.9) | Measured by a gripper sweep; commandable range 0.27-0.95 |
| 10 | Arm found collapsed after a stopped run | **Closing the Mini board drops torque; the arm falls** (unlike the QArm) | Never close mid-air: **on any fault, return to rest under torque, then close**; the demo ends at rest |
| 11 | Occasional one- to three-sample glitches (all five error flags on one servo, or an all-zero read), ~1 per 30-60 s | Bus/USB/supply transient (cause open); real Dynamixel errors latch until reboot, these cleared by themselves | Drop a bad sample (the commands are fixed waypoints); fault only after **10 consecutive** (200 ms); glitches are counted in the log |
| 12 | Start from an unexpected pose | A prior run left the arm sagged | **Start gate**: shoulder/elbow/wrist within 10 deg of the measured rest (yaw free) |
| 13 | Elbow stuck at -90 deg on the final return to rest | Rest target elbow = exactly -150 deg (PAL min); the firmware rejects goals at the limit (-149.6 accepted) | `JOINT_CMD_MARGIN` = 0.02 rad: all commands clamped just inside the PAL limits (to re-verify on the next run) |
| 14 | **Motion demo** `tools\qarm_mini_hello_demo.py --id 6` | — | rest -> home -> base +/-0.5 -> wrist +/-0.5 -> gripper 0.27/0.70/0.27 -> rest: **full sequence in 76 s**, current <= 0.38 A, <= 36 degC, glitch absorbed. Confirmed by the user |

---

## 4. How to run (current state)

```powershell
# QArm (USB, board id 0)
C:\Research\qarm\.venv\Scripts\python.exe C:\Research\qarm\tools\qarm_readonly_probe.py
C:\Research\qarm\.venv\Scripts\python.exe C:\Research\qarm\tools\qarm_hello_demo.py
C:\Research\qarm\.venv\Scripts\python.exe C:\Research\qarm\tools\qarm_wrist_step_test.py {hold|steps}
C:\Research\qarm\.venv\Scripts\python.exe C:\Research\qarm\tools\qarm_dilisic_shadow.py {hw | replay LOG}

# QArm Mini (COM6 -> --id 6; the FTDI latency timer MUST be 2 ms; start with the arm at rest)
C:\Research\qarm_mini\.venv\Scripts\python.exe C:\Research\qarm_mini\tools\qarm_mini_readonly_probe.py --id 6
C:\Research\qarm_mini\.venv\Scripts\python.exe C:\Research\qarm_mini\tools\qarm_mini_hello_demo.py --id 6
```

Safety discipline used throughout: read-only probe first; operator at the power/E-stop; slow profiles;
per-sample monitors; PAL limits (with margin on the Mini); stop to a safe pose on any fault.

---

## 5. Open items

- Mini: re-run the demo once to confirm the elbow now returns fully to rest with `JOINT_CMD_MARGIN`.
- Mini: localize the bus glitches (rate at rest vs. under load, 25 Hz, fewer channels, direct USB port, supply).
- QArm: the RealSense wrist camera (second USB 3 cable) is not connected yet.
- DILISIC: a mapping from its q^(4) input to a position-servo setpoint, the wrist's true g, and independent review
  before any actuation (runbook step 6). `direct_dilisic_actuation_ready` stays false.
