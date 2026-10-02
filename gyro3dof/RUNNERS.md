# 3-DOF Gyroscope — Runners & Launchers Index

Theory paper: `paper_math\gyroscope3dof_models_control_ieee.tex` (pulled forward from
`D:\NMSU_backups\...\11_3DOF_Gyroscope\` on 2026-08-21). Hardware is **not connected**
(it opens through a Q8-USB DAQ; see `julia_bridge\README.md`, where it is `daq_mediated`).
Vendor curriculum: `Documents\Quanser\Gyroscope\` (LQR and reaction-torque Simulink models,
plus the `.mlx` live scripts that are the parameter source below).

## Hardware connection (2026-09-27, in progress) — read-only so far, nothing written to the board

- **Q8-USB connected and on:** Quanser Q8_USB, model 2010, serial **QM67494** (USB VID 21DF PID 0001), board
  `q8_usb` id `0`. The AMPAQ-L4 amplifier was switched on by the operator.
  `tools\gyro_q8_readonly_probe.py` -> `hw_logs\2026-09-27_q8_readonly_probe.json`. Analog inputs 0-7 all read
  ~1.83 V (+/-0.2 mV), i.e. unconnected; the amplifier state is not visible from the Q8 inputs.
- **Quanser's model contract** (`q_3dgyro_lqr.mdl`, HIL Initialize): encoders read 0:3; encoder gains
  `[60/4096, 2pi/4000, 2pi/4000, -2pi/4000]` (enc0 = disc 4096/rev as rpm; enc1-3 gimbals 4000/rev, enc3
  sign-flipped); analog outputs 0:2(3) = motor current commands via 1/Kt; **digital outputs 0-3 = active-low
  amplifier enables**: initial [0 0 0 0 1] while running, final/watchdog [1 1 1 1 0] = disabled.
  **Any future write must replicate the final/watchdog = disabled states.**
- **Encoder map, first attempt** (`tools\gyro_q8_encoder_map.py`, `hw_logs\20260927_205520_q8_encoder_map.*`;
  operator moved gray, red, blue, disc in order, but motion started at 28 s of a 40 s window): enc0 moved first
  (405 counts), then enc2 (82 counts, small: a locked red gimbal?), then enc1 (1337 counts); enc3 was never
  reached. At least enc0/1/2 are wired and counting. **The mapping is ambiguous** (enc0 moved first, but Quanser's
  model calls enc0 the disc): repeat with a longer window, one axis at a time.
- **Second map attempt** (90 s, `hw_logs\2026-09-27 20:5x *_q8_encoder_map.*`): **enc0 = disc confirmed.** It rotated
  continuously one way ~4 rev and coasted to a stop at 29 s after a hand spin (nothing was written, so it was not
  motor-driven), matching Quanser's enc0 = disc at 4096/rev. The gimbals moved only *between* the two recordings
  (enc1 720 -> 38, enc2 10 -> 19), so the gimbal mapping is still open: likely enc1 = blue (large moves),
  enc2 = red (small, maybe locked), enc3 = gray (never moved yet; Quanser flips its sign). **Confirm one axis per recording.**
- **Connector labels on this unit (reported by Gandhi):** blue gimbal = **M1-E1**, red gimbal = **M2**(-E2), gray frame
  = no label (unactuated, encoder only). Together with the recordings: **enc0 = disc (M0?), enc1 = blue, enc2 = red,
  enc3 = gray (to confirm; Quanser flips its sign)**. Naming trap: Quanser's lab text numbers motors from 1
  (motor 1 = disc, motor 2 = blue), but the connector labels count Q8 channels from 0 (M1 = blue). **Use Q8 channel
  numbers in code.** Still to check: the disc's label, gray = enc3, and each axis's sign vs. `mjcf.py`.
- **Unit configuration as found (Gandhi, 2026-09-27):** 4 motors + 4 encoders physically, **only 3 connected**
  (disc, blue, red). **The gray frame is locked** (very limited travel) and its motor and encoder are not wired:
  the gray recording (`*_q8_encoder_map_gray.*`) showed enc3-7 = 0. Red turns freely (moved ~3 rev between recordings).
  Consequences: the reaction-torque lab (yaw psi via blue torque), the one the MuJoCo twin was validated on, **needs gray
  unlocked + its encoder on Encoder 3 (+ motor if used)**. With gray locked, blue-red gyroscopic coupling is zero
  at the nominal pose (red axis parallel to spin) and appears only as blue tilts (the cos(theta) geometry of the paper).
  Gray-locked is the safe setting for the first powered steps: **E1** (disc spin-up/coast-down near 750 rpm) and
  **E2** (blue, then red, identification with Omega = 0).
- **Rewired and unlocked (later on 2026-09-27):** Gandhi connected the 4th motor/encoder and unlocked the gray frame.
  (The Q8-USB dropped off USB during rewiring and came back as the same QM67494; counters reset to 0.)
  Gray recording `*_q8_encoder_map_gray.*` (latest): **enc3 = gray confirmed**, 1316 counts (118 deg) with blue 0 /
  red 7 counts. **Sign:** counterclockwise seen from above -> raw enc3 *decreases*; Quanser's gain -2pi/4000 therefore
  gives **+psi = CCW = MuJoCo +z**, so no correction is needed. The disc encoder (disc relative to its gimbal) also read 596 counts
  as the frame turned (disc inertia; friction drags part of it along).
- **Encoder map (final):** enc0 = disc (4096/rev), enc1 = blue (M1-E1), enc2 = red (M2), enc3 = gray (sign -1).
  Blue/red signs vs. `mjcf.py` are still to be checked (a direction reference is needed; alternatively take the sign from the
  first powered gyroscopic-coupling test).
- **First powered test (`tools\gyro_blue_first_motion.py`, `hw_logs\*_blue_first_motion.*`): NO MOTION, UNRESOLVED.**
  Command chain from Quanser's model (HIL Interfacing): AO V = 2 x amps (AMPAQ-L4 0.5 A/V); AO0 disc, AO1 blue,
  AO2 red (x -1 in Quanser), AO3 gray (always 0); DO0-3 active-low enables + DO4 = 1 while running; safe = [1 1 1 1 0].
  Blue current pulses of 0.15-0.6 A (0.3 s each) moved nothing on any axis (0 counts), and the script ended safely.
  The loop ran far slower than 200 Hz (2-24 samples per 0.3 s pulse), so the **100 ms Q8 hardware watchdog most likely
  expired and locked the outputs in the safe (disabled) state**, which is the leading hypothesis. But a later benchmark
  (amps disabled, 0 V) showed every Q8 call takes < 0.1 ms, so the slowness is in my loop (Windows sleep granularity?
  the stage loops?), not the Q8. **Next agent:** (1) log `watchdog_is_expired()` each step and time the loop;
  (2) retry with the watchdog at 0.5 s and a busy-wait loop; (3) if there is still no motion, check the AMPAQ-L4 enable
  LEDs and the amp/motor cabling (does DO k map to amp channel k?); (4) only then the PD moves. Keep the disc still.
- **E1 preliminary (hand-spin coast-down, 15 rpm -> 0):** a near-linear decay, i.e. **Coulomb-dominated:
  tau_c ~ 3.5e-4 N m** (0.064 rad/s^2 with J_d 5.54e-3); the viscous term is ~0 at this speed. Needs a powered
  coast-down near 750 rpm (viscous/slip-ring losses) before use in the twin.
- Next: finish the encoder map and directions vs. the MuJoCo twin (`mjcf.py` axes) -> read the disc
  speed/encoder (Quanser: 4096/rev) -> only then any motor current, with the enables handled as above,
  starting with a gimbal-locked spin-up per the paper's safety section.

## Environment (2026-09-27)

```
C:\Research\gyro3dof\.venv\Scripts\python.exe -m pytest tests -q          # 4 validation tests
C:\Research\gyro3dof\.venv\Scripts\python.exe runners\run_reaction_torque_demo.py
```
Python 3.13, mujoco 3.11.0, numpy, scipy, matplotlib, imageio[ffmpeg]; `gyro3dof` is installed editable
(`src\gyro3dof`). Exact versions: `requirements.lock.txt`. Basilisk is not in this venv yet; the
working Basilisk 2.11.1 + MJScene example is `C:\Research\spacecraft_twin`.

## G0/G1 — reference model + MuJoCo twin (done 2026-09-27)

- `params.py`: vendor values from `quanser_3dof_gyro_reaction_torque.mlx`: m_d 1.907 kg,
  r_d 0.0762 m (J_d 5.536e-3), Jx 3.8855e-3, Jy 2.3446e-2, Jz 6.6321e-2, kt 0.115 (gimbal) / 0.0704
  (disc) N m/A, Imax 3 A (tau_max 0.345 N m), w_ss 750 rpm (h 0.4348 N m s), lab gains kv 0.2,
  kp -1.09, kd -0.000238. **Assumed:** the per-body split of the composite inertias (only the
  composites are published). The split reproduces all three composites exactly at the nominal pose.
- `mjcf.py`: gray (psi, z, free) -> red (theta, y, optional lock) -> blue (phi, x, torque motor) ->
  disc (spin +y, torque-limited velocity servo). Spin about +y reproduces Quanser's signs
  Jx phi'' = tau2 + h psi', Jz psi'' = -h phi'.
- `reference_model.py`: Quanser's linear red-locked model; `controllers.py`: the lab's successive-loop
  controller; `sim.py`: controller-in-the-loop runner (`ctrl_dt` must be a multiple of the timestep).
- `tests\test_mujoco_vs_quanser.py` (all pass): composite inertias from `mj_fullM` are exact;
  nutation frequency within 1% of h/sqrt(JxJz) = 4.311 Hz; momentum exchange
  psi' = -(h/Jz)dphi within 1%; under the lab controller, MuJoCo vs the linear model within 2% of the step.
- `runners\run_reaction_torque_demo.py` -> `results\reaction_torque_{plot.png, video.mp4, trace.csv,
  summary.json}`: psi steps +15 -> -15 -> 0 deg driven only by the blue-gimbal torque. psi = 14.9999 deg
  at 4 s; MuJoCo vs linear max 0.15 deg (psi) / 0.31 deg (phi); disc 750 +/- 0.23 rpm; tau2 saturates
  1.4% of the time, during the 30 deg swing.
- **Open gap:** the vendor text says phi goes to about -3.5 deg for the 15 deg step, but these gains give a
  **-4.9 deg peak** in both models. The .mlx designs with `pidtune(...,'PD2')` (2-DOF PD); its setpoint
  weights are not saved. A proportional setpoint weight b of about 0.72 would explain it. This is not tuned away.
  Also: in Quanser's own model phi returns to 0 once psi stops (psi' = -(h/Jz)phi), so -3.5 deg can only be a
  peak, unless the hardware's gray-axis friction is involved.

## Plan (agreed order: G2 Basilisk, then G3 neuromorphic)

- **G2 Basilisk:** carry this gimbal+rotor as a single-gimbal CMG on a spacecraft bus in Basilisk
  `MJScene` (the `spacecraft_twin` pattern), where the lab's "yaw psi via gimbal torque" is spacecraft
  attitude control by momentum exchange. Gates: momentum conservation, and the psi/phi transfer function vs G1.
- **G3 neuromorphic:** (a) perception: event-based encoding of the encoder/visual signals (the DVS emulator
  from `neuromorphic_drone_racing`) and a spiking state estimator vs the Kalman baseline; (b) control:
  a Nengo SNN as a *bounded residual* on the lab/LQR baseline, with a gimbal-lock guard |theta_i| < 90 deg.
  Evaluation follows `spacecraft_twin\PROPOSAL.md` claim discipline (no energy claims without measured power).
- Hardware later: identification E1-E4 from the paper, hat-h vs J_r*Omega as the validation gate.
