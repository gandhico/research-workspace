# IEEE ToE paper — §VI.A "Aero2 semester-long design project": analysis & improvements

Source: `C:\Users\gandhico\Downloads\2026___IEEE_ToE.pdf` (13 pp). The paper is a
**control-systems-education** paper (course EE 475/551, digital-twin + Quanser
hardware pedagogy). §VI.A is the Aero2 design-project exemplar.

## What §VI.A currently says (qualitative)
- Aero 2 in **2-DOF** config; coupled pitch–yaw; actuator saturation + encoder
  quantization "difficult to represent in an ideal nominal model."
- Progression: **offline → QLabs digital twin → hardware** (hardware taken "at the
  students' own initiative").
- ID: axis-specific excitation (Lec 2–7); multiplicative-uncertainty weight →
  robust design (Lec 8–9).
- **MATLAB/Simulink twin @ 500 Hz**; **Python (Quanser API) @ ~380 Hz**;
  algorithms "updated using the measured sample interval."
- Hardware step "revealed practical limitations (modeling accuracy, actuator
  dynamics, timing, tuning)."

**Gap:** the subsection is a *narrative*. It states the workflow and the timing
difference but gives **no quantitative controller results**, no figure of the
twin-vs-hardware or Python-vs-MATLAB comparison, and no concrete "practical
limitation" numbers. That is exactly what our digital-twin campaign already
produced, and what hardware will close.

## Concrete improvements (each backed by data we already have — see `WORKFLOW.md`)

1. **Add a quantitative controller table (twin, then hardware).** PD/LQR/LQG/MPC/
   BS/SMC/NMPC on the 2-DOF twin (WORKFLOW §5.1). Headline: **PD pitch RMS 0.150
   on the twin ≈ 0.154 hardware benchmark** → the twin is faithful. **Yaw is the
   hardest axis for every model-based controller** (0.43 → 6.0). Turns "revealed
   limitations" into evidence.

2. **Quantify timing → performance (the 500 vs 380 Hz remark).** Our rate sweep:
   same PD, same 2-DOF twin — **200 Hz → pitch RMS 0.150 (sat 0.04); 91 Hz → 0.248
   (sat 0.44); 69 Hz (MATLAB↔Python bridge) → 0.449 (sat 0.83)**. This is a
   teachable figure: loop rate/latency *monotonically* degrades control and drives
   saturation — a direct, measured illustration of "update on the measured sample
   interval." (WORKFLOW insight #8.)

3. **Twin-config fidelity as a reproducibility lesson.** PD on the *correct* 2-DOF
   twin reproduces hardware (0.150), but the **half-rotor config mismatch inflated
   it to 0.60**. Teaching point: *the digital twin is faithful only when its
   configuration matches the model* — pin the twin config, not just the code
   (WORKFLOW insight #6/#1).

4. **Plant characterization = the motor map.** Document the identified 2-DOF map
   (collective→pitch, differential→yaw, with measured pitch↔yaw coupling) on twin
   and hardware — concrete "plant characterization" content.

5. **Add a robustness dimension.** Regulation-under-disturbance table (WORKFLOW
   §5.3): PD/LQR reject best; yaw again discriminates. Complements the
   tracking-only story with disturbance rejection.

6. **Cross-platform (Python↔MATLAB) validation, quantified.** We reproduced the
   Python controllers natively in MATLAB against the *same* twin (bridge). Report
   the parity + the honest bridge-latency cost — strengthens "reproduced the
   real-time interface in Python/MATLAB."

7. **(Optional, advanced-extension / research bridge) Neuromorphic augmentation.**
   The gate-state residual (HyperLIF) architecture ported from the MuJoCo
   quadrotor gives **−72% yaw / −29% pitch disturbance rejection** on the twin —
   a candidate "advanced project extension" showing where a neuromorphic residual
   *does* help (robustness, the unsolved yaw axis). Likely a separate research
   paper, but a strong forward-pointer for the ToE project subsection.

## Figures/tables worth adding to §VI.A
- **T1** controller comparison (twin vs hardware; pitch/yaw RMS, sat, loop rate).
- **F1** loop-rate sweep: pitch RMS & saturation vs realized Hz (200/91/69).
- **F2** twin-vs-hardware trace overlay for the PD baseline (once hardware runs).

## Blocking dependency for the hardware half
Physical Aero 2 needs the **full QUARC install** (HIL board drivers;
`C:\Quanser_Setup\02_quarc\install_quarc.exe`) — QUARC *Runtime* alone (from the
QLabs bundle) does not enumerate the physical device (`board type not installed`).
Once installed: run `campaigns/run_motor_id.py hardware`, then the controller
benchmark with `--mode hardware` for the twin-vs-hardware table.
