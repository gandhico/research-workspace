# QArm Mini — Runners & Launchers Index

**Full bring-up story (defaults -> both arms moving, 2026-09-27): `BRINGUP_LOG_2026-09-27_QArm_and_QArm_Mini.md`**

**No control or hardware runner exists yet.** A non-actuating position-servo
identification screen and DILISIC bench runbook now live at
`C:\Research\dilisic\tools\qarm_identify_position_servo.py` and
`C:\Research\dilisic\docs\QARM_RUNBOOK_2026-09-09.md`. QArm Mini PWM must be
treated as a separate, explicitly verified plant contract; these materials
authorize recorded-data/shadow work only.

Pulled forward from
`D:\NMSU_backups\Backup\00_Research_\Neuromorphic_Embodied_AI\15_Qarm_mini\`
on 2026-08-21. Sole content: `paper_math\qarm_mini_models_control_ieee.tex`
(+ compiled `.pdf`) — "Quanser QArm Mini 4-DOF Manipulator: Hardware Physics,
Identification, Modelling, and the Complete Controller Suite" (Gandhi
Contreras). Covers the physics/identification/modelling derivation and a
full controller suite (PID/LQR/LQG/backstepping/SMC/NMPC) **on paper only**.

Not to be confused with `qarm\` — a separate platform with its own paper,
see that folder's `RUNNERS.md`.

## Project environment (installed 2026-09-27; hardware not yet connected)

```
C:\Research\qarm_mini\.venv\Scripts\python.exe tools\qarm_mini_readonly_probe.py
```

- `.venv` is set up the same way as `qarm\` (Quanser QUARC 2026 wheels, Quanser requirements with numpy 2.3.5,
  pytest, `dilisic` editable); `vendor\quanser_libraries` is on the path, so `import pal.products.qarm_mini`
  works. `requirements.lock.txt` has the exact versions.
- `quanser_resources\`: user manual, Python/Simulink quick start, research (basic IO, PWM IO,
  pick-and-place, face detect), and the teaching lab `play`.
- `tools\qarm_mini_readonly_probe.py`: **no write calls**. It reads identity, raw and PAL-frame joint angles,
  load/current, temperature, and the 25 servo error flags. With the arm unplugged it exits 2 with
  "Could not open the Dynamixel device" (verified 2026-09-27).

## First connection (2026-09-27): read-only probe PASSED

```
C:\Research\qarm_mini\.venv\Scripts\python.exe tools\qarm_mini_readonly_probe.py --id 6
```
- USB: FTDI FT232H "USB Serial Converter" (VID 0403 PID 6014, serial FTAA0AZ3), driver 2.12.36.20
  (installed by Windows Update on first plug-in) -> **COM6**. **Board id = the COM number** (`--id 6`), not 0.
- **FTDI Latency Timer must be 2 ms** (Device Manager > Ports > USB Serial Port (COM6) > Port Settings >
  Advanced > Latency Timer; the Windows default is 16). At 16 ms each small Dynamixel status packet waits in
  the FTDI buffer longer than the driver's reply timeout, so late replies were matched to the next request:
  channel-shifted positions, all-zero reads, and HIL error -1376 `DYNAMIXEL_COMMUNICATION_ERROR` (including
  on close, leaving a hung process). Fix: set 2 ms, power-cycle the arm at rest, replug the USB.
  Registry check: `HKLM\SYSTEM\CurrentControlSet\Enum\FTDIBUS\VID_0403+PID_6014+FTAA0AZ3A\0000\Device Parameters\LatencyTimer`.
- Read only the **15 documented other inputs**; PWM 11000-11004 returned out-of-range values (e.g. 23.1).
- **Load/current need the combined `card.read(...)`** as PAL uses; a standalone `read_analog` leaves the
  buffer untouched on this driver.
- String and integer identity properties are not supported by this driver.
- Result at 2 ms (`hw_logs\2026-09-27_readonly_probe_final.json`): consistent (0% deviating samples,
  position noise <= 0.0006 rad), jitter 0.47%, temps 27-29 degC, 0 error flags, load/current 0 (torque off).
  Rest pose in PAL joint frame: yaw -9.1, shoulder +191.6, elbow -139.8, wrist +7.6 deg, all inside PAL
  limits (shoulder is 3.4 deg from its max 195 deg, elbow 10 deg from its min -150 deg).
  Gripper raw 4.028: PAL maps give -0.99 and +1.06, both outside [0, 1], which confirms the map inconsistency.
- **Rest configuration confirmed by eye** (matches Quanser's photo), so PAL's joint bias map is correct for this unit.
- **Gripper calibrated by hand** (torque off): open raw 1.6659, closed raw 4.0819 (span 2.416 rad; raw
  increases while closing). `tools\qarm_mini_calibration.py` is the single source for the joint and gripper maps
  (commands clamped to PAL joint limits and gripper 0.05-0.95); `tests\test_calibration.py` has 4 passing tests.
  **Do not use PAL's `write_gripper_position` on this unit: it drives the wrong direction.**

## First motion (2026-09-27): it moves, but the bus is not yet reliable

`tools\qarm_mini_hello_demo.py --id 6`, `tools\qarm_mini_gripper_sweep.py --id 6`, logs `hw_logs\20260927_20*`.
- **Driver options:** the Mini REJECTS `jX_profile_config` and `gripper_profile_config` and ACCEPTS
  `gripper_profile_velocity/_acceleration` (the QArm is the opposite). The profile is speed-based: requested
  0.6, and the joints actually ran at <= 0.31 rad/s (checked at rest before any large move).
- **It moved:** rest -> home (9.6 s) -> base +/-0.5 -> wrist +/-0.5, every waypoint within 0.04 rad, current <= 0.5 A.
- **Gripper firmware limit:** open commands beyond raw about 2.24-2.27 are silently rejected (no motion, zero
  load). Commandable range is 0.27-0.95 of the hand-measured span (`qarm_mini_calibration.py`).
- **Closing the board drops torque: the arm falls under gravity** (a run frozen at home was found sagged to
  shoulder 37 deg / elbow -131 deg). The QArm did not do this. **Never close the Mini away from rest; the
  "freeze then close" fault handling is unsafe here.**
- **Intermittent bus glitches, about 1 per 30-60 s at 50 Hz:** all five error flags on one servo, or an all-zero
  read, each clearing by itself (real Dynamixel hardware errors latch until reboot). They were seen once at 1
  sample, once as an impossible all-joint jump, and once for 3 samples (60 ms) on the elbow while holding the
  sagged pose under load (elbow 1.75 A, wrist 1.28 A). The cause is not established: the USB/FTDI path, supply dips
  under load (24 V 2.71 A adapter), or bus traffic (each cycle reads 10 other + 5 analog + 25 digital channels).

**Final run of the day (`hw_logs\20260927_204210_mini_hello_demo*`), with the fixes below in place:** the full
sequence ran (rest -> home -> base +/-0.5 -> wrist +/-0.5 -> gripper 0.27/0.70/0.27) in 76 s: current <= 0.38 A,
temperature <= 36 degC. A 3-sample glitch (all flags on yaw and gripper, t = 55 s) was dropped and motion continued.
**The last move failed:** the rest target put the elbow at exactly -150.0 deg (PAL min), which the firmware rejected,
so the elbow stayed at -90 deg and the 25 s safe return could not move it either. The arm was left at shoulder
191.8 / elbow -90 deg with torque off (stable). Fix: `JOINT_CMD_MARGIN` = 0.02 rad clamps all commands inside
the PAL limits (-149.6 deg was accepted in the same run). Not yet re-run on hardware.

Fixes now in `qarm_mini_hello_demo.py`: start gate (shoulder/elbow/wrist within 10 deg of `REST_POSE`; yaw free,
and the return keeps the starting yaw); bad-sample dropping with a fault only after 10 consecutive (200 ms);
on any fault, drive back to rest under torque before closing.

**Before the next motion:** (1) start only if the arm is within ~10 deg of `REST_POSE`; (2) on a *read* glitch keep
commanding the waypoint and resume; on a persistent fault, slowly return to REST under torque *before*
closing, never close mid-air; (3) localize the glitches (glitch counter at rest vs. under load; 25 Hz; fewer
channels per cycle; another USB port without a hub).

## Mini contract: differences from the QArm (read before the first motion)

Source: QUARC doc `quarc/doc/qarm_mini.html` + PAL `pal/products/qarm_mini.py` (release 2026-07-31).
- Board `qarm_mini`. Other channels 1000-1004 are **raw servo angles**. PAL's joint frame is
  `joint = raw - thetaBias - actuatorBias`, with thetaBias [0, -pi/2, pi/2, -pi/2] and actuatorBias
  [pi-1.178, pi+0.1834, pi-0.1834+0.07, pi]. **Never send a QArm-style joint angle to a raw channel.**
- PAL limits (joint frame): min [-10pi/18, -pi/6, -5pi/6, -pi/10], max [4pi/3, 13pi/12, pi/6, 8pi/9].
  HOME [0, pi/2, -pi/2, pi/2], SLEEP [0, 0, 0, pi/2]. Unlike the QArm, it is not yet known
  whether the firmware enforces these limits.
- Analog 0 and 4 are **load %** (yaw, gripper); 1-3 are current A (+/-3.21). Digital 0-24 are servo
  error flags (voltage, overheating, encoder, shock, overload per joint): use them as abort monitors.
- PAL defaults are aggressive: profiles 6.28 rad/s and 6.28 rad/s^2 (QArm tools use 0.5-1.0), and PAL
  `terminate()` **writes HOME on exit**, so closing a PAL session moves the arm.
- **PAL's gripper map is inconsistent:** x(-1.8) in `write_gripper_position`, x(+1.68) in `read_write_std`,
  and `read_outputs` inverts with the wrong sign on the 0.9 offset. The probe prints both candidates;
  settle the direction by moving the gripper by hand with the power off, before any gripper command.
- PWM mode exists (channels 11000-11004). Per the runbook, it is **not** to be used without an identified
  plant contract.

First session, once connected: (1) run the probe with the arm resting; (2) check that the PAL-frame angles
look right against the physical pose (and the gripper direction); (3) then port `qarm\tools\qarm_wrist_step_test.py`
and `qarm_hello_demo.py` through the bias map, with profiles <= 1 rad/s and the error flags as monitors.

## Next step, when ready to build

Follow the same shape as `pendulum\` or `qdrone\`: `runners\run_offline_benchmark.py`
using the shared `_shared\quanser_residual_campaign` module (see
`qdrone\RUNNERS.md` §3 for how that dependency resolves), then a digital-twin
runner, then a hardware runner behind explicit arming.
