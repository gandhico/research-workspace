# P5 — Dual neuromorphic control: CMG self-tuning PID + CMG–PES residual

Started 2026-09-12. A follow-on to the ACC 2027 CMG–PES paper
(`C:\Research\papers\ACC2027_Gate_Residual_Control`).

The project fuses two lines of work:
- **Self-tuning neuromorphic PID** (PES-adapted gains; Olivares et al., IFAC-PapersOnLine 2025 and
  Neural Computing and Applications 2026, with Garcia Carrillo, Espinoza and Garcia Alcantara).
- **The bounded additive CMG–PES residual** from the ACC 2027 paper.

In both learning paths the spiking/LIF basis is replaced by the continuous coupled membrane–gate (CMG) unit.

| | |
|---|---|
| Base controller | Quaternion PID; the ACC 2027 PD gains plus integral action |
| Platforms | Crazyflie 2 (1.5× rotor design), Skydio X2, Omnicopter (`C:\Research\omnicopter`) |
| Phase 1 | Attitude (quaternion) tracking, same missions as ACC 2027 |
| Phase 2 | 6-DOF, once the architecture and its mathematics are settled |
| Parallel track | High-fidelity MuJoCo models: motors, propellers, dynamics, animation, virtual twin |

## Layout

| Path | What |
|---|---|
| `docs/PLAN.md` | Phases, hypotheses, pre-declared evaluation rules, milestones |
| `docs/ARCHITECTURE_MATH.md` | Dual architecture, bounded gains, stability facts, open questions |
| `docs/HIGH_FIDELITY_MUJOCO_PROPOSAL.md` | Motor/propeller/aero/sensor/animation plan for CF2, X2 and Omnicopter |
| `docs/DUAL_HARDWARE_STABILITY_PROOF_2026-10-06.md` | Audit of the dual stability claims, narrow common-Lyapunov certificate, and proposed robust sampled-data hardware theorem |
| `docs/QUAD_TWINS_QDRONE2_STABILITY_2026-10-06.md` | Active quadrotor route: X2/CF2 MuJoCo twin completion, racing stress tests, and QDrone2 hardware proof gates |
| `docs/TWIN_L0_AUDIT_2026-10-06.json` | Compiled X2/CF2 L0 model inventory with source hashes, rotor geometry, inertia and authority assumptions |
| `hifi/rotor_response.py` | Opt-in normalized rotor-speed lag model; zero-lag mode preserves ideal commanded force exactly |
| `experiments/quat_dual_v0/` | First quaternion-tracking experiment (PID, PID+residual, self-tuned PID, dual) |
| `results/` | Run outputs; never overwritten, one dated folder per campaign |

## Rules carried over from ACC 2027

- Never edit the canonical runners in the ACC 2027 repository. Import `gra_control` read-only.
- Selection rules are declared before results. Report nominal, disturbance, and mismatch results separately.
- At most 4 parallel CMG/Nengo runs on this machine.
- Build LaTeX with pdflatex + bibtex; latexmk has no Perl here.

## Status

**2026-10-06 direction:** QDrone2 is the intended hardware endpoint, after X2/CF2 MuJoCo variants and a quadrotor-specific stability filter are validated. The earlier Aero2 Phase 5 text is historical. See `docs/QUAD_TWINS_QDRONE2_STABILITY_2026-10-06.md`.

- **v0 (2026-09-12).** All gates pass. On X2, dual is best (geometric mean 0.540 vs PID; residual alone 0.585).
  On CF2 Hardstep the target-scheduled tuner winds up and diverges. See `results/quat_dual_v0_2026-09-12/REPORT.md`.
- **Olivares et al. (NCA 2026).** The PDF is in this folder and has been read. The published law (an MIT-rule
  gradient with a PES-learned sensitivity, unbounded) is written up in `docs/ARCHITECTURE_MATH.md` §6a. The
  CMG mapping and bounded version are in §6b. The closed-loop sign bias of the learned sensitivity is derived
  in §6c.
- **v1 (done).**
  - The faithful CMG STN-PID-PES is inadmissible: the learned closed-loop sensitivity has the wrong sign.
  - Bounding it makes it safe but still worse than PID.
  - On CF2 step missions, gain-raising tuners crash, because they steal collective thrust.
  - Report: `results/quat_v1_2026-09-12/REPORT_v1.md`.
- **v2 (done).**
  - Authority gating, validity gating and a damping floor: 0 crashes in 56 cells.
  - dual_v2 beats the ACC 2027 residual over all 7 missions on both vehicles (0.976 X2, 0.963 CF2), but only by
    2–5%; safety cost most of the tuner's benefit.
  - The X2 PD baseline (and the ACC 2027 paper cell) grazes the floor for 1 ms on Hardstep.
  - Report: `results/quat_v2_2026-09-12/REPORT_v2.md`; v3 directions are listed there.
- **v3 (done).**
  - Allocation: pure thrust priority failed (it zeroed the attitude torque); attitude priority (`apa`) was selected
    by the declared screen. It fixes the ungated single tuner on CF2 at no cost to the baselines, but not the
    ungated dual.
  - The dither-identified sensitivity has the right sign everywhere and recovers the X2 axis-inertia mismatch
    (1.66 / 1.43 / 0.42), but gives only small gains.
  - The gated dual v2 generalizes to the new held-out pair (0.975 X2, 0.969 CF2 vs the residual).
  - Report: `results/quat_v3_2026-09-12/REPORT_v3.md`; v4 directions are listed there.
- **v4 (done).**
  - A body-axis (physically scaled) PID is only 3% better than the ACC j_tune PID on X2.
  - The residual's gain survives correct scaling (0.641 vs 0.613), so the ACC 2027 result is not a gain-scaling
    artifact.
  - The identification-based gain correction is right in mean but fails as a law: instantaneous inversion plus
    asymmetric gating makes the gains drift down, and the residual corrupts the estimate. The dual even crashes once
    on CF2.
  - Report and figure: `results/quat_v4_2026-09-12/`.
- **6-DOF pilot (done, exploratory).**
  - The cascade reproduces ACC FF6 bit-for-bit.
  - On the tuned cascade, attitude-level residual/dual change position error by ≤ 1%; the FF6 gain likely lives in
    the position channels.
  - The predicted closed-loop bias of the dither estimate is confirmed and self-reinforcing.
  - The known-controller estimate is correct on CF2 and X2 yaw; it fails on X2 roll/pitch, and its consistency check
    flags the failure.
  - Report and figure: `results/six_dof_pilot_2026-09-12/`. Math: `docs/ARCHITECTURE_MATH.md` §7.3.
- **FROZEN 2026-09-12: `P5-QUAT-6DOF-2026-09-12-R1`.**
  - See `results/FREEZE_P5-QUAT-6DOF-2026-09-12-R1/FROZEN_RESULTS.md` and `MANIFEST_SHA256.txt`.
  - Do not modify frozen result folders. New work goes in new dated folders.
- **ACC 2027 update + v5 declared (2026-09-25).** Two ACC 2027 amendments closed: A4 re-confirms CMG as the best
  residual basis (and confirms P5's own `SelfTuner`, which also uses CMG, was never at risk from the neuron-basis
  bug that hit the comparison families); A5 certifies the residual R generalizes to LQR/PID/SMC/MPC/NMPC with no
  exceptions. **v5 is declared** (not yet run): generalize S the same way, reusing `AdvancedBaseline`'s k1/k2/K0
  structure. A new Phase 5 also connects this project to `C:\Research\aero2\` — Gandhi's existing Quanser Aero2
  project, which already has hardware runs on file for PD/LQR/backstepping/SMC/NMPC and its own (simpler, non-
  learning) neuromorphic residual that the validated CMG-PES architecture is a natural upgrade to. See
  `docs/PLAN.md`'s "ACC 2027 update", "v5 declaration", and "Phase 5" sections.
- **v5 run (2026-09-25): 128/128 cells, 0 failures.** LQR/backstepping/MPC full grid + an 8-cell NMPC pilot
  (SMC deferred). **E1/E2 both fail honestly**: self-tuning S is essentially a no-op on these four families
  (st vs base and dual vs res both sit at 0.1-0.6%, noise level); the large dual-vs-base numbers are almost
  entirely R restated. Diagnosed and quantitatively confirmed: S's fixed `e_ref=0.1` target scale was
  implicitly calibrated for PID's (feedforward-free, ~10x larger) baseline error and under-drives the tuner
  once rate feedforward already shrinks the error. R generalizes cleanly (reconfirms A5 under a second
  allocation scheme, apa); S's benefit was PID-specific, not yet shown family-general. See `docs/PLAN.md`'s
  "v5 outcomes" and `results/v5_2026-09-25/V5_RESULTS.md`.
