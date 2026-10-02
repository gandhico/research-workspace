# QArm — Runners & Launchers Index

**Full bring-up story (defaults -> both arms moving, 2026-09-27): `BRINGUP_LOG_2026-09-27_QArm_and_QArm_Mini.md`**

**Hardware bench tools exist (2026-09-27); there is no controller runner yet.**
The environment and results are below. A non-actuating position-servo
identification screen and DILISIC bench runbook now live at
`C:\Research\dilisic\tools\qarm_identify_position_servo.py` and
`C:\Research\dilisic\docs\QARM_RUNBOOK_2026-09-09.md`. These authorize
recorded-data/shadow work only, not direct DILISIC actuation.

## Project environment (installed 2026-09-27)

```
C:\Research\qarm\.venv\Scripts\python.exe <script>
```

- `.venv`: Python 3.13, all QUARC 2026 Quanser wheels, Quanser's `requirements.txt`
  (numpy 2.3.5 < 2.4 as Quanser pins; scipy, opencv, pytransform3d, PyQt6, ...), pytest,
  pyrealsense2 2.58.4, and `dilisic` installed editable (its 11 tests pass on this venv).
  Exact versions: `requirements.lock.txt`.
- `vendor\quanser_libraries\python\{hal,pal,pit,qvl}`: a copy of Quanser Academic Resources
  (release 2026-07-31), on the path via `quanser_libraries.pth` in the venv, so
  `import pal.products.qarm` works. Source: `Documents\Quanser_Academic_Resources_tmp`
  (`Documents\Quanser\0_libraries` is an incomplete 16-file copy; do not use it).
- `quanser_resources\`: user manual plus kinematics/dynamics notes (`user_manual\ancillaryMaterial`),
  quick-start guides and models, research examples (basic IO, RGBD, dynamics, gain scheduling,
  IK, HD2 teleop, ROS1/ROS2 sources without build outputs), the teaching lab `play_qarm`,
  `rt_models\QArm*`, and community QArm projects (links only).
- The QArm itself stores no files: over USB it appears only as the `qarm_usb` HIL board.

## Hardware connection check (2026-09-27)

`tools\qarm_readonly_probe.py` opens the `qarm_usb` board and **only reads**
(identity, joint pos/vel/temp/PWM, motor currents; it makes no write/set calls). Result:
`hw_logs\2026-09-27_readonly_probe.json`. Needs the Quanser Python wheels from
`C:\Program Files\Quanser\QUARC\python\` (install *all* of them together;
`quanser_api` depends on `quanser_multimedia`). QUARC 2026 (26.0.5256).

- Board: QArm model 2021, serial QF0009012b11142b07, firmware 3.3 / "QFLEX 2 USB v1.3",
  USB VID 0x21DF PID 0x0020, Cypress CYUSB3 driver, status OK.
- Rest pose read: yaw -0.682, shoulder -1.558, elbow **+1.404**, wrist 0.076 rad;
  gripper 0.088. Joint velocity 0, holding current ~0 A, temps 28-35 degC.
- **Elbow rests 0.014 rad past the documented +1.39 command limit.** Any first
  command must be clamped *and* rate-limited; never echo the raw reading back.
- Position noise std ~0.0007 rad (about 1/2 count at 4096 counts/rev); the velocity
  channel reads exactly 0 at rest, so its resolution is still unknown.
- The RealSense end-effector camera is not enumerated (second USB cable not connected).

## First actuated bench test (2026-09-27)

`tools\qarm_wrist_step_test.py {hold|steps}`: position mode, profiles 0.5 rad/s and
0.5 rad/s^2 (wrist 1.0/1.0), 100 Hz, with abort monitors. Logs are in `hw_logs\20260927_19*`.
The driver **rejects `gripper_profile_velocity/_acceleration`**, although the doc lists them.

- **Hold:** no abort, 0 overruns. When torque engages, the shoulder moves +0.049 rad and
  the elbow -0.051 rad *away* from their hold commands within 1 s, then stay dead steady
  (holding current 1.27 A and 0.81 A). Starting off the rest pose, the offset is only
  0.008 and 0.014 rad. Cause not yet known (rest-pose stops? P-only servo under gravity?
  backlash?); **investigate before any shoulder or elbow work.** Closing the board does
  not drop the arm: it stayed near the held pose.
- **Wrist steps** (+/-0.10 rad, 17 levels): no abort. Measured steady-state gain 0.972,
  |ss error| <= 0.0033 rad, rise 240-570 ms (the profile dominates), ~150 ms until motion starts.
- **ID gate** (`dilisic\tools\qarm_identify_position_servo.py`) -> `hw_logs\20260927_wrist_contract.json`:
  R^2 0.9997 and stable, **but `shadow_ready=false`**, because max sample jitter was 5.54%
  (limit 5%; 2 of 2749 samples >10.5 ms). The ARX DC gain of 1.56 is unreliable (pole 0.990).
  The tool only searches delays 0-5 samples, which is too short for this ~15-sample delay.

## Resolved: Quanser gains + hardware clock (2026-09-27, later the same day)

Reading Quanser PAL `pal/products/qarm.py` explained the problems above:
- PAL writes servo PID gains on every open (P 8.89, I 0.012, D 10.23; properties
  128-141). Without them the servos have no integral term. `--gains quanser` (default) now sets them.
- **The servo firmware enforces PAL's joint limits** (shoulder +/-17pi/36, elbow
  [-19pi/36, 15pi/36], yaw +/-17pi/18, wrist +/-8pi/9). The rest pose is outside them,
  so enabling torque **lifts the arm ~4-5 deg** to shoulder -1.4835 / elbow +1.3090,
  which is PAL's `SLEEP_POSE`. That was the "offset". The encoders show the motion, but it
  is small and slow enough to go unnoticed. The tools now clamp to these limits (gripper 0.1-0.9).
- `--clock hw` (default) samples on HARDWARE_CLOCK_0 through a reader task, as PAL does.
  Sample jitter is now exactly 0. Command writes are still host-timed (worst 3.1 ms late at 100 Hz).

Results with both defaults (`hw_logs\20260927_1918*`, `..._1919*`):
- Hold: shoulder/elbow error 0.0006 / 0.0021 rad (was ~0.05).
- Wrist steps: no abort; gain 1.017; |ss error| <= 0.0022 rad; rise 270-560 ms.
  (A first attempt aborted on a monitor false positive, since a 0.20 rad step equals the old
  0.20 error limit. Replaced by an envelope of hold +/-0.15 rad plus settle < 0.03 rad
  1 s after each step.)
- ID gate, `--max-delay 30` -> `hw_logs\20260927_wrist_contract_hw_quanser.json`:
  **all checks true, `shadow_ready=true`** (delay 16 samples = 160 ms, R^2 0.9996,
  poles 0.982/0.40). `direct_dilisic_actuation_ready=false`, by design. The ARX DC gain of
  1.235 is still biased by the slow pole; use the measured 1.017.
- **First full-motion demo** `tools\qarm_hello_demo.py`: sleep -> home -> base +/-0.5 ->
  wrist +/-0.8 -> gripper 0.7/0.1 -> sleep, at 0.6 rad/s and 0.6 rad/s^2, with base LEDs.
  30.3 s, no fault; every waypoint reached within 0.03 rad in <= 3.9 s. Max current:
  shoulder 1.38 A, elbow 0.87 A, gripper 0.76 A. Max temperature 41 degC (gripper).
  Log: `hw_logs\20260927_192230_hello_demo*`.

## DILISIC shadow mode on the wrist (runbook step 5, 2026-09-27)

`tools\dilisic_shadow.py` (library, no hardware), `tools\qarm_dilisic_shadow.py {replay LOG | hw}`,
`tests\test_dilisic_shadow.py` (2 tests). **The servo only ever receives the baseline;**
DILISIC's request is logged, never sent.

Design, and the reasons it deviates from a naive wrap of the scaffold:
- 4th-order state from a steady-state Kalman filter on a quadruple integrator
  (sigma_q 7e-4, sigma_snap 2 -> about 2.1 Hz). On quantized synthetic data the worst-case
  errors are qd 3%, qdd 21%, **qddd 72%**. Jerk is noise-dominated (a runbook no-go for
  actuation). A 4.6 Hz setting gave qdd errors 4x the signal.
- **Reference model anchored:** u_DI = PD of the *reference-model* state toward the baseline
  (kp 50, kd 14.1, the scaffold's gains). With the scaffold's measured-state form, the
  open-loop DI reference drifted 2 rad in 20 s, because nothing pulls the plant onto it in shadow.
- **Weights frozen for the primary readout;** the paper-adaptive copy runs alongside.
  Adaptation assumes u reaches the plant; in shadow mode h_hat drifts 1.2 -> 8 in 30 s.
- The streamed wrist runs with **no firmware profile** (0 = no limit) plus a **0.8 rad/s
  software rate limit**. With a firmware profile, setpoints streamed every 10 ms made the wrist
  crawl, because the profile restarts on each new target (aborted run `_193148`).
- The baseline is a 0.3 rad, 0.25 Hz sine with 2 s raised-cosine ramps and *exact*
  derivatives. Run `_193307` omitted the ramp-derivative terms, which knocked the reference 0.06 rad off
  and made adaptation run away (h_hat 267, 73% saturation). **Do not use `_193307` as a result.**

Result, live `hw_logs\20260927_193556_shadow_hw*` (30 s, no abort):
- Wrist vs baseline <= 0.015 rad; reference model vs baseline <= 0.003 rad after 2 s.
- **Frozen DILISIC request |u|: median 169, p95 444, max 803, 0% saturation.** DILISIC's own
  validated sim (`dilisic\reference\..._20260908`, t>2 s excluding the disturbance) gives
  median 296 and p95 417 (disturbance ~7,500, cap 5e4). On real wrist data it asks for the same
  order as in its paper setting.
- Adaptive copy: median 374, p95 2,173, h_hat 1.23 -> 8.19 (open-loop drift).
- s-term RMS: acc 2.37 > vel 1.56 > pos 1.09 > jerk 0.86, so the jerk noise is not what dominates.
- The replay of the same log offline (`--frozen`) reproduces this (median 168, p95 445).

**Still not established** (`direct_dilisic_actuation_ready` stays false): a mapping from
DILISIC's q^(4)-input units to a position-servo setpoint; the true g for the wrist
(h_hat is seeded with the paper arm's 1/g = 1.2257); independent review (runbook step 6). Send baseline commands only
  and log the DILISIC correction.

Pulled forward from
`D:\NMSU_backups\Backup\00_Research_\Neuromorphic_Embodied_AI\14_Qarm\`
on 2026-08-21. Sole content: `paper_math\qarm_models_control_ieee.tex`
(+ compiled `.pdf`) — "Quanser QArm 4-DOF Manipulator: Hardware Physics,
Identification, Modelling, and the Complete Controller Suite" (Gandhi
Contreras). Covers the physics/identification/modelling derivation and a
full controller suite (PID/LQR/LQG/backstepping/SMC/NMPC) **on paper only**.

Not to be confused with `qarm_mini\` — a separate platform with its own
paper, see that folder's `RUNNERS.md`.

## Next step, when ready to build

Follow the same shape as `pendulum\` or `qdrone\`: `runners\run_offline_benchmark.py`
using the shared `_shared\quanser_residual_campaign` module (see
`qdrone\RUNNERS.md` §3 for how that dependency resolves), then a digital-twin
runner, then a hardware runner behind explicit arming.
