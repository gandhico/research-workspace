# FROZEN RESULTS: P5-QUAT-6DOF-2026-09-12-R1

Frozen 2026-09-12 (UTC 2026-09-13T05:37:05), at Gandhi's request: "once you have tests and idea how it behaves
in 6DOF stop, froze".

**Manifest.** `MANIFEST_SHA256.txt`: 1086 files (P5 code, docs, all v0–v4 and 6-DOF pilot results including traces, plus the five
ACC 2027 dependency files imported read-only).
Manifest SHA256: `7d170a0ced667050474efb66dd62867b25e82c9ed18dcf2bb0471a59db114ae8`.

## Rules for this freeze

- Do not edit anything listed in the manifest. New work goes in new dated folders and new declarations in `docs/PLAN.md`.
- Nothing in the ACC 2027 repository was modified. The five dependency hashes are recorded.
- Verify with `sha256sum` or `Get-FileHash` against `MANIFEST_SHA256.txt`.

## What is frozen

| campaign | folder | cells | gates |
|---|---|---|---|
| v0 target-scheduled dual | `results/quat_dual_v0_2026-09-12` | 2 platforms × 5 missions × 4 controllers | G1, G2 pass |
| v1 STN-PID-PES (Olivares et al. 2026, CMG) | `results/quat_v1_2026-09-12` | + held-out pair | pass |
| v2 gated dual | `results/quat_v2_2026-09-12` | 56 | pass |
| v3 allocation + dither ID | `results/quat_v3_2026-09-12` | 162 + allocation screen | G4, G5 pass |
| v4 body-axis PID + ID gain correction | `results/quat_v4_2026-09-12` | 72 new + G6 | G6, G7 pass |
| 6-DOF pilot (exploratory) | `results/six_dof_pilot_2026-09-12` | 2 platforms × 4 missions × 5 controllers | G8 pass (bit-identical to ACC FF6) |

## Headline findings (state at freeze)

1. **The published STN-PID-PES does not transfer as written.**
   - In closed loop, the PES-learned sensitivity Δθ/Δu ≈ −2/k_q has the wrong sign (§6c).
   - Bounded, known-sign and gated variants are our contribution.
2. **Gated dual v2 is safe and modestly better than the ACC 2027 residual.**
   - All 9 quaternion missions, apa allocation, vs pid: X2 0.599 vs 0.613; CF2 0.578 vs 0.600.
   - It holds on both held-out pairs.
3. **ACC 2027 relevance.**
   - The X2 j_tune gains are mis-scaled per axis (×1.66 / ×1.44 / ×0.42), but physically scaled gains improve PID by
     only 3%.
   - The residual's improvement survives correct scaling (0.641 vs 0.613).
   - Separately: the X2 PD Hardstep cell grazes the floor for 1 ms (v2 note).
4. **Dither identification.**
   - It gets the sign right everywhere and the magnitude right in mean at the quaternion bandwidth.
   - As a gain-correction law, v4 fails: instantaneous inversion plus asymmetric gating makes gains drift down, and
     the residual corrupts the estimate.
5. **6-DOF.**
   - On the ACC tuned cascade the attitude loop has no room left: attitude-level residual/dual change position error
     by ≤ 1%.
   - The quadrature estimate is closed-loop biased at the tuned bandwidth, as predicted before the runs, and the bias
     is self-reinforcing (CF2 roll m → 1.97).
   - The known-controller estimate is correct on CF2 and X2 yaw. It fails on X2 roll/pitch, and its consistency
     check c flags the failure.

## Disclosures

- **Hash drift in older summaries.**
  - v0–v3 `summary.json` files record `run_dual.py` / `dual_controller.py` hashes from before the v4 additions.
  - G6 shows the edited code reproduces a v3 cell bit-for-bit.
  - The v4 edits only add controllers and summary fields.
- **Pilot runner edited after the runs.**
  - 6-DOF pilot summaries record a `pilot_6dof.py` hash from before one post-run edit: a zero-division guard in
    `compile_report` for CF2 hover, where classical error is exactly 0.
  - `run()` was not changed.
- **Post-hoc material.** Every interpretation section in the reports was written after its results and is labelled as such. The v2
  crash classification (z_min < 0.05 m) and the 6-DOF consistency-gate reading are post hoc.
- **Scope.** All results are noise-free and deterministic, one run per cell. The quaternion runs are 45 s and the
  6-DOF runs 15 s.

## Open at freeze (next session candidates, not declared)

- **v5 identification law.**
  - Estimate first, then invert: slow second-stage average of H.
  - Symmetric log-m update.
  - Consistency gate |c − 1| < 0.2.
  - Exclude R from, or model R in, the identification.
- **6-DOF.**
  - Position-only vs attitude-only split of the FF6 6-channel CMG augmentor.
  - Conditions with room to improve: sensor noise, disturbance, mismatch, aggressive references.
- **X2 roll/pitch dither model mismatch** (ARCHITECTURE_MATH Q5).
- **High-fidelity MuJoCo track** (`docs/HIGH_FIDELITY_MUJOCO_PROPOSAL.md`): not started. Covers CF2, X2 and
  Omnicopter.
