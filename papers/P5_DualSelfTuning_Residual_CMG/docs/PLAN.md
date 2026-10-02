# Plan (declared 2026-09-12, before any P5 results)

## Hypotheses

- **H1.** A CMG–PES self-tuned PID (S) reduces attitude error versus the fixed PID on moving-reference missions.
- **H2.** The dual architecture (S + residual R) reduces error beyond R alone. Risk: over-stiffening Hardstep.
- **H3.** The benefit of S or R grows under model mismatch and disturbance (as the Omnicopter frozen result
  NRCTRL-OMNI-2026-09-10-R1 found for R), and shrinks on an exact-model nominal plant.

## Controllers (v0)

| id | base | self-tuning S | residual R |
|---|---|---|---|
| `pid` | PID (k_i = 0.05 k_q) | — | — |
| `pid_res` | PID | — | CMG–PES, β = 0.5 |
| `st_pid` | PID | CMG–PES, β_g = 0.5 | — |
| `dual` | PID | CMG–PES, β_g = 0.5 | CMG–PES, β = 0.5 |

**v0 hyperparameters, fixed a priori (no tuning on the evaluation missions):**
- tuner: e_ref = 0.1 rad, ω_ref = 1 rad/s, κ_d = 1, τ_lp = 1 s, η_S = 1×10⁻⁴, λ_S = 10⁻⁶;
- residual: η_R = 8×10⁻⁴;
- G = 10⁵;
- h = 0.5 ms, 45 s;
- CF2 rotor scale 1.5.

## Pre-declared evaluation rules

1. **Primary metric.** Mean quaternion-angle error per cell.
2. **Aggregate.** Geometric mean over the five missions of the per-mission error ratio versus `pid`
   (the mission-mean is Hardstep-dominated).
3. **Admissibility.** Every mission must stay below 1 rad mean error with rotor saturation fraction below 0.5.
   A controller that fails on any mission is reported, not ranked.
4. **Separate reporting.** Hardstep is reported separately.
5. **No retuning.** Results that motivate a hyperparameter change are called exploratory, and the changed
   configuration gets a new version (v1) and a held-out check.
6. **Mechanism logs.** Mean, min and max gain multipliers per axis, residual RMS, decoder norms, and the
   saturation fraction.

## v1 declaration (2026-09-12, after reading Olivares et al. and before any v1 run)

**New controllers (see ARCHITECTURE_MATH §6b):**

| id | description |
|---|---|
| `st_pid_f` | v0 tuner + conditional adaptation: on saturation, targets for m_p and m_i are set to 0 (retreat to nominal) |
| `dual_f` | st_pid_f + residual R |
| `stn` | faithful CMG STN-PID-PES (unbounded MIT-rule gradients with the CMG-PES sensitivity) |
| `stn_b` | bounded STN: projection [0.5, 1.5], leak, conditional adaptation |
| `dual_stn_b` | stn_b + residual R |

**A-priori hyperparameters (no tuning):**
- μ_p = μ_i = μ_d = 5×10⁻⁵ per step, i.e. 0.1/s at unit normalized excitation;
- e_ref = 0.1, ω_ref = 1 rad/s, ξ_ref = 0.1 s;
- τ = 0.05 s, κ_s = 1, sensitivity η_s = 8×10⁻⁴;
- λ_m = 5×10⁻⁵ per step (10 s time constant).

**Held-out missions, defined now and used for no design decision:**
- `hard45b`: Euler (0.50 sin(0.85t+0.3) + 0.18 sin(1.95t), 0.40 sin(1.05t+1.0) + 0.20 sin(1.55t+0.7),
  0.60 sin(0.65t+2.0) + 0.22 sin(1.25t)).
- `hardstep_b`: zero for 1 s, then cycles every 2.5 s through (−0.60, 0.50, −0.45), (0.70, −0.40, 0.80),
  (−0.55, −0.55, −0.60), (0.65, 0.45, −0.30).

**Gates:**
- G1/G2 as in v0.
- G3: rerunning st_pid and dual on two cells must reproduce the v0 summaries exactly.

**Addendum (2026-09-12, after a 5 s smoke test, before any full v1 run).** The smoke test of `dual_stn_b`
on X2 Full3 showed a *negative* learned sensitivity (Ŷ ≈ −0.17 to −0.35). Under feedback, u ≈ −K_ω ω, so
Δθ/Δu estimated in closed loop does not carry the open-loop sign (closed-loop identification bias).

Two ablations are added, each labelled **post-smoke, exploratory**, with Ŷ ≡ +1 (the physically known
torque→attitude sign) and all other settings identical:
- `stn_b_ks`
- `dual_stn_b_ks`

The declared v1 controllers are unchanged.

**Evaluation.** Same rules 1–6. All v0 and v1 controllers also run on the two held-out missions.
H1/H2 claims for the bounded variants need the original missions *and* the held-out missions to agree in
direction.

## v2 declaration (2026-09-12, after v1 results, before any v2 code or run)

**Motivation (from the v1 report).**
- Gain-raising tuners crash CF2 on step missions: attitude aggressiveness takes collective thrust.
- The learned closed-loop sensitivity has the wrong sign.
- The residual alone is the robust reference.

**New admissibility rule, applied retroactively to all controllers.** No ground contact: z_min > 0.2 m over the
45 s. Rules 1–6 otherwise unchanged.

**v2 mechanisms (a priori, no tuning):**
1. **Authority gating.** Gain increases (m_p, m_i, and m_d above 1) are multiplied by the rotor headroom
   h = clip(min_i min(f_i, f_max,i − f_i) / (0.5 f_max,i), 0, 1) from the previous step. h = 1 at mid-range
   and 0 at any rotor bound, so gains rise only when every rotor has headroom.
2. **Local-validity gating.** The gradient/target rules assume small errors, so adaptation *increases* are
   allowed only while |e_q,i| < e_gate = 0.25 (half-angle units, about 29°). At or above e_gate the p and i
   multipliers retreat to nominal with a 1 s time constant (reference jumps reset the tuning).
3. **Damping floor.** m_d ∈ [1, 1.5]; damping is never tuned below nominal.

**v2 controllers.** Every other setting matches v1.

| id | tuner | residual |
|---|---|---|
| `st_pid_v2` | target tuner (v0) + mechanisms 1–3 (targets for p, i scaled by h·1[\|e\|<e_gate]; d target clipped to ≥ 0) | — |
| `dual_v2` | st_pid_v2 | R |
| `stn_ks_v2` | bounded STN, known sign (Ŷ = +1) + mechanisms 1–3 | — |
| `dual_stn_ks_v2` | stn_ks_v2 | R |

**Missions.** 5 original + 2 held-out (hard45b, hardstep_b), both vehicles.

**Claims to test.**
- (i) Are the v2 tuners admissible everywhere under the new rule?
- (ii) Do they keep the smooth-mission advantage (dual < pid_res, both mission sets)?
- (iii) Does dual_v2 beat pid_res on the geometric mean over all 7 missions on both vehicles?

## v3 declaration (2026-09-12, approved by Gandhi; before any v3 code or run)

**Plant interface.** All v3 controllers use thrust-priority allocation (ARCHITECTURE_MATH §7.1). v0–v2 results
(clipped inverse allocation) stay as the separate "clip" layer.

**Controllers (all TPA):**

| id | description |
|---|---|
| `pid`, `pid_res` | new baselines under TPA |
| `st_pid`, `dual` | v0 tuner, **ungated**: tests whether TPA removes the crash mode at its cause |
| `st_pid_v2`, `dual_v2` | v2 gated tuner |
| `stn_ks_v2` | gated STN, known sign (reference for the dither estimator) |
| `stn_dx_v3`, `dual_stn_dx_v3` | gated STN with the dither-identified sensitivity (§7.2): a_d = 0.02, f = (9, 11, 13) Hz, τ_d = 0.5 s; + residual for the dual |

**Missions.**
- The 5 original missions.
- hard45b and hardstep_b.
- A **new held-out pair, used for no design decision:**
  - `hard45c`: (0.45 sin(0.70t+1.2) + 0.22 sin(2.30t+0.5), 0.52 sin(0.90t) + 0.16 sin(1.85t+1.3),
    0.58 sin(0.60t+0.4) + 0.20 sin(1.45t+2.2));
  - `hardstep_c`: zero for 1.5 s, then every 3.0 s through (0.55, 0.60, −0.50), (−0.75, −0.30, 0.65),
    (0.40, −0.65, −0.85), (−0.50, 0.55, 0.35).

**Admissibility (declared).** Mean < 1 rad, saturation < 0.5, **z_min ≥ 0.05 m** (sustained contact = crash;
threshold from the v2 classification).

**Gates.**
- G4: with allocation = clip, the runner reproduces a v2 cell bit-identically.
- G5: pid under TPA equals pid under clip to 10⁻¹² relative on a mission with no rotor bound hit (Roll).

**Claims.**
- **C1.** Both TPA baselines are admissible on all 9 missions, both vehicles.
- **C2 (root cause).** The ungated st_pid and dual are admissible on all 9 missions, both vehicles.
- **C3.** Ungated dual (TPA) beats pid_res (TPA): geometric mean over all 9 missions, and over the new held-out
  pair, on both vehicles.
- **C4.** The dither sensitivity has positive mean Ŷ on every axis for the smooth missions. stn_dx_v3 beats pid
  (TPA) on smooth missions, and dual_stn_dx_v3 beats pid_res (TPA) over all 9 missions, on both vehicles.

**v3 addendum (2026-09-12, after two short smoke tests, before any full v3 run).**

**Smoke results.**
- The dither estimator works as designed: 8 s on X2 Full3 gave ŝ ≈ +1.07, +1.21, +0.39.
- Pure TPA does **not** stop the CF2 Hardstep crash for ungated dual (12 s: z_min 0.018 m, α_min = 0, torque
  scaled in 86% of steps).

**Mechanism.** Tilt compensation (guard 0.35, up to 2.86 Mg) requests more collective than CF2 can produce
(T/W 1.98). TPA then gives all rotor authority to the collective, leaving α = 0 and no attitude control.
Thrust priority fails in the opposite direction from clipping.

**Two allocation variants replace pure TPA:**
- `tpa_r`: thrust priority with a 25% torque reserve. The collective is capped at 0.75·T_max before computing α.
- `apa`: attitude priority. Keep τ and move the collective to the closest feasible value. If no collective makes τ
  feasible, scale τ by the largest feasible α (bisection) and then choose the closest collective.

**Screening rule (declared now).**
- Run pid, st_pid (ungated) and dual (ungated) on CF2 Hardstep and Hardstep_b (missions already seen) with each
  variant.
- Select the variant with the higher *worst-case z_min* across those 6 cells.
- Tie-break (within 0.05 m): the lower geometric mean error.
- The selected variant becomes the v3 allocation for all controllers and missions. hard45c/hardstep_c stay untouched.
- Pure `tpa` is reported as a documented negative result.

**Screen result (`results/quat_v3_2026-09-12/alloc_screen/SCREEN.md`).** **`apa` selected.**
- Worst-case z_min tied (0.017 vs 0.015 m); `apa` has the lower geometric-mean error (0.488 vs 1.340 rad).
- `tpa_r` lowers even PID to z_min 0.13 m: the collective cap starves the altitude loop.
- Under `apa`, the ungated st_pid survives both steps. The ungated dual still crashes on Hardstep only.

The full v3 campaign uses allocation = `apa`, and the claims C1–C4 are read with TPA → APA.

## v4 declaration (2026-09-12, approved by Gandhi; before any v4 code or run)

**Motivation (v3).** The dither lock-in recovers ŝ = j_tune/diag(J). X2 gains are mis-scaled
(roll ×1.66, pitch ×1.43, yaw ×0.42); CF2 ≈ 1.

**Controllers.** All use `apa` allocation and the 9 v3 missions. References pid, pid_res and dual_v2 come from
the v3 folder.

| id | description |
|---|---|
| `pid_body` | PID whose gains use diag(J) instead of j_tune (torque limits ℓ unchanged, to isolate gain scaling) |
| `pid_res_body` | pid_body + residual R |
| `idgc_v4` | identification-based gain correction (below) |
| `dual_idgc_v4` | idgc_v4 + residual R |

**idgc_v4 mechanism:**
- The v3 dither is kept (a_d = 0.02, f = 9/11/13 Hz, lock-in τ_d = 0.5 s).
- ŝ is used in **magnitude**. The v3 PES estimator learned Ŷ too slowly to deliver magnitude, so the
  neuromorphic element of the dual controller is the residual R.
- After a 3 s warm-up, per axis m ← m + (h/τ_id)(clip(1/ŝ, 0.33, 3.0) − m), with τ_id = 5 s. All three gains
  share m, since k_q, k_ω and k_i are all ∝ j.
- The v2 authority gate still scales increases.

**Claims:**
- **D1.** The X2 multipliers settle near 1/ŝ (≈ 0.60, 0.70, 2.38) and the CF2 multipliers near 1.
- **D2.** Report pid_body vs pid on X2.
- **D3.** idgc_v4 < pid, geometric mean over 9 missions, X2; CF2 within ±3%.
- **D4.** dual_idgc_v4 < dual_v2 and < pid_res over 9 missions, X2; admissible everywhere, both vehicles.
- **D5.** On X2, (pid_res_body / pid_body) vs (pid_res / pid): how much of the ACC 2027 residual gain
  compensates gain mis-scaling.

**Limitation.** No new held-out pair for v4; the v3 pair was not used to choose any v4 setting.

## 6-DOF pilot declaration (2026-09-12, exploratory; "an idea how it behaves", then freeze)

**Baseline.** The ACC 2027 tuned cascade (FF6_FINDINGS_2026-09-10):
- X2: wn_att (20, 20, 17.5), wn_pos (2, 2, 2.4);
- CF2: wn_att (24, 24, 20.4), wn_pos (2.25, 2.25, 2.7);
- position feedforward on, 15 s, h = 0.5 ms, clipped allocation (as published).

The pilot changes **only the inner attitude loop**:
- `cas`: baseline (gate G6: reproduces the FF6 selected classical cells).
- `cas_res`: + 3-channel CMG-PES attitude residual, β = FF6 selection (X2 0.05, CF2 0.008), η as in FF6
  (X2 8e-4, CF2 2e-4).
- `cas_dual_v2`: + gated v2 tuner on (k_q, k_ω), plus the residual.
- `cas_idgc_v4`: + v4 identification-based gain correction, without the residual.

**Missions.** hover3d, waypoint_step, circle_xy, full6_stress, both vehicles.

**Metrics.** Mean position error, mean attitude error, z_min, rotor saturation.

**Status.** Exploratory: no claims beyond direction. Then **freeze** (freeze ID P5-QUAT-6DOF-2026-09-12-R1).

### 6-DOF pilot addendum (2026-09-12, before any 6-DOF run)

**Why.** The quadrature lock-in behind v3/v4 is an open-loop estimate. Under a PD loop with stiffness
k = k_q/2 (because e_q ≈ θ/2) and damping k_ω, it returns

ŝ = j ω²(Jω² − k) / ((k − Jω²)² + (k_ω ω)²)

(`experiments/six_dof_pilot/predict_dither_bias.py`).

**Validation.** At the quaternion bandwidth this predicts X2 ŝ = (1.59, 1.41, 0.42). v3 observed
(1.58, 1.38, 0.42), so the model holds.

**Prediction at the tuned 6-DOF bandwidths:**
- X2 ŝ = (0.70, 0.90, 0.42), so v4 would *raise* the roll and pitch gains (×1.42, ×1.11) instead of lowering
  them (×0.60, ×0.70).
- CF2 ŝ = (0.62, 0.73, 0.85), so v4 would raise its gains ×1.2–1.6 when they are already correct.

**Change.** Add `cas_idgc_kc`, a known-controller (indirect) estimate:
- in-phase and quadrature lock-in give the complex response H(jω) = 2(z_s + j z_c)/A;
- 1/H = k_ω + j(Jω² − k)/ω, so Ĵ = (ω Im(1/H) + k)/ω², with the current gains k = m k_q/2;
- Re(1/H)/(m k_ω) is reported as a consistency check and should be ≈ 1;
- update law, warm-up, bounds and gating are identical to v4.

**Pre-declared expectation:**
- `cas_idgc_v4` moves X2 roll/pitch and all CF2 multipliers above 1 (wrong direction);
- `cas_idgc_kc` settles near (0.60, 0.70, 2.38) on X2 and near 1 on CF2.

**Gate G8.** `cas` reproduces the ACC FF6 selected classical summaries bit-for-bit (`x2_tune/a20_20_17.5_p2_2_2.4`,
`cf2_tune/a24_24_20.4_p2.25_2.25_2.7`).

### Outcomes (2026-09-12; frozen as P5-QUAT-6DOF-2026-09-12-R1)

**v4** (`results/quat_v4_2026-09-12/REPORT_v4.md`). Gates G6 and G7 pass.

| claim | outcome |
|---|---|
| D1 | Fails on multi-axis missions (holds on single-axis missions) |
| D2 | X2 body-axis PID 0.968 |
| D3 | Fails: 1.056 X2 / 1.022 CF2 |
| D4 | Fails: CF2 Hardstep crash; X2 0.993 vs dual_v2 |
| D5 | Residual gain survives body-axis gains: 0.641 vs 0.613 |

**6-DOF pilot** (`results/six_dof_pilot_2026-09-12/REPORT_6dof_pilot.md`). G8 passes.
- Attitude-level residual and dual change moving-mission position error by ≤ 1%.
- The quadrature bias prediction is confirmed.
- The known-controller estimate is correct on CF2 and on X2 yaw, and fails on X2 roll/pitch; its consistency check
  flags the failure.

## ACC 2027 update (2026-09-25, before any v5 code or run)

Two amendments closed in the ACC 2027 repo (`C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\final_robustness_gating_2026-09-20\`)
bear directly on this project's open questions.

**Amendment A4 (neuron-basis correction, `REPORT_NEURON_BASIS_CORRECTION_2026-09-24.md`).** A Nengo PES
learning-rate normalization bug in the *comparison* neuron families (Izhikevich/LIFRate/LIF/ALIF) was found,
corrected, and independently re-verified. CMG's own rate formula was checked and confirmed unaffected by
construction (its neuron output is natively clipped to `[0,1]`, so the feature-scale factor the bug was one power
short of is exactly 1 for CMG — no correction needed). Corrected result: CMG still beats every conventional and
non-neural basis tested, by a wide margin (X2 +37.3% vs. next-best LIFRate-tuned +15.8%). **Relevant here:** this
project's own `SelfTuner` (`dual_controller.py`) already uses CMG units for S, same as the ACC residual for R —
the basis choice for *both* layers is now on firmer footing than when P5 started.

**Amendment A5 (controller-family portability, `REPORT_A5_CERTIFICATION_2026-09-24.md`,
`AUDIT_NMPC_HOLD_RATE_2026-09-25.md`).** The bounded, gated CMG-PES residual R (Stage A: interface portability
only, no per-family redesign) was attached to five more controller families beyond PD+ff: PID+ff, LQR, SMC, MPC,
NMPC — all via `AdvancedBaseline` in `run_mujoco_nef_baselines.py` (Gandhi's Aero2 work) and a new merged runner
`run_controllers_gated.py`. **All six families improve on both platforms, no exceptions** (X2: PD+ff +37.3%,
PID+ff +36.7%, LQR +31.1%, SMC +43.8%, MPC +33.4%, NMPC +31.9%; CF2: +21.7% to +26.6%). Exact baseline recovery
at beta=0 (Prop. 1(iii)) was independently re-certified for four of the five new families. **Relevant here:** R's
portability is now proven; S's is not — every P5 version (v0-v4, 6-DOF pilot) tuned PID gains only. Closing that
gap is v5, below.

## v5 declaration (2026-09-25, after reading A4/A5, before any v5 code or run)

**Motivation.** The dual architecture (S+R) is a P5-specific contribution beyond the ACC 2027 paper. A5 just
showed R generalizes across seven controller families (PD/PID/LQR/SMC/MPC/NMPC/backstepping, the last two sharing
one law here) with no redesign. S has never been tested outside PID. If S does not generalize the same way, "the
dual architecture" is really "the dual architecture, PID-only" -- worth knowing before any hardware commitment.

**Key structural fact, read directly from `SelfTuner.step()` (`dual_controller.py:60-108`) and `AdvancedBaseline`
(`run_mujoco_nef_baselines.py`, ACC 2027 repo).** `SelfTuner` is already generic in its *mechanism*: 18 CMG units,
a 9x18 PES decoder trained toward hand-specified saturating targets (not a gradient), gated identically to v2
(authority/headroom, local-validity `|e_q|<e_gate`, damping floor). It knows nothing PID-specific except which
three quantities its 9 output channels multiply (Kp, Ki, Kd). Every `AdvancedBaseline` family reduces to the same
shape: an angle-error gain and a rate-error gain (LQR: `k1=wn^2, k2=sqrt(2)*wn`; backstepping/NMPC-nominal:
`k1=wn^2, k2=2*zeta*wn`; SMC: `lam` and `eta` play the p/reaching-law roles but `eta` is a bounded effort limit,
not a smooth d-gain -- flagged as the one family needing a real design decision, not a mechanical port; MPC:
`K0[:,0], K0[:,1]` after the finite-horizon solve). So a generalized S is a scope question (which multiplier
channels exist per family, 2 or 3), not a redesign of the tuner itself.

**Proposed v5 controllers** (all under `apa` allocation, all missions from v3+v4, PID reference values reused
unchanged from the frozen R1):

| id | base family | S output channels | R |
|---|---|---|---|
| `st_lqr_v2` / `dual_lqr_v2` | LQR | mult_k1, mult_k2 (p/d only, no integral) | — / R |
| `st_bs_v2` / `dual_bs_v2` | backstepping | mult_k1, mult_k2 | — / R |
| `st_smc_v2` / `dual_smc_v2` | SMC | mult_lam only, first pass (eta held fixed, disclosed) | — / R |
| `st_mpc_v2` / `dual_mpc_v2` | MPC | mult_K0p, mult_K0d | — / R |
| `st_nmpc_v2` / `dual_nmpc_v2` | NMPC | mult_k1, mult_k2 on the nominal law only (grid offset untouched) | — / R |

**A-priori hyperparameters.** Identical to `st_pid_v2`/`dual_v2` (frozen R1): `e_ref=0.1, w_ref=1.0, kappa_d=1,
tau_lp=1.0 s, learning_rate=1e-4, leak=1e-6, w_max=6, e_gate=0.25, beta_p=beta_i=beta_d=0.5` (beta_i unused where
there is no integral channel). No retuning per family -- if a family needs different hyperparameters to be
admissible, that is itself a finding, reported as such, not silently fixed.

**Gates.**
- G9: with S disabled (beta=0 equivalent, or the new channels' mult forced to 1), every new `st_*_v2`/`dual_*_v2`
  reproduces the corresponding A5 `run_controllers_gated.py` classical/nengo-nef-pes cell exactly -- the S=identity
  case must be the already-certified A5 number, not a new computation.
- G10: `st_pid_v2`/`dual_v2` (existing, PID) rerun bit-for-bit against the frozen R1 values -- confirms nothing
  shared was touched.

**Claims.**
- **E1.** S is admissible (rule 3, plus the v2 no-ground-contact rule) on every new family, both vehicles.
- **E2.** dual_*_v2 < *_res (R alone, from A5) on the geometric mean, for families where E1 holds -- mirrors H2
  for the newly-added families.
- **E3.** SMC is reported separately as exploratory (mult_lam only, one design decision short of the others).

**Explicitly not v5.** Re-deriving the STN-PID-PES-style gradient law (v1) for other families; the idgc
identification approach (v4, already found unreliable); 6-DOF for the new families (stays PID-only until Phase 2
is revisited); anything on hardware (Phase 5, below).

### v5 outcomes (2026-09-25; 128/128 cells run, 0 failures, 0 diverged)

Full grid for lqr/backstepping/mpc (2 platforms x 5 missions x 4 arms). NMPC reduced to an 8-cell pilot (X2,
Hard45+Roll, all 4 arms) after a smoke test suggested a cost of ~3.7 h/cell under `apa` allocation -- the real
campaign cells actually ran in ~36 min each (the smoke test's 884 s/3 s figure was evidently a transient
contention spike, not the real per-cell cost; worth revisiting full NMPC coverage later, now that the true cost
is known to be closer to lqr/backstepping/mpc's regime once amortized). Full table: `results/v5_2026-09-25/V5_RESULTS.md`.

| family | platform | st vs base (E1) | dual vs res (E2) | dual vs base |
|---|---|---:|---:|---:|
| lqr | x2 / cf2 | +0.2% / +0.1% | +0.1% / -0.2% | +28.7% / +5.7% |
| backstepping | x2 / cf2 | +0.3% / +0.6% | +0.1% / +0.3% | +35.7% / +4.4% |
| mpc | x2 / cf2 | +0.2% / +0.3% | -0.1% / +0.1% | +31.1% / +8.0% |
| nmpc (pilot) | x2 | +0.5% | +0.3% | +47.1% |

**E1 and E2 both fail, honestly and by a wide margin -- self-tuning is essentially a no-op for these four
families in this first pass.** The large dual-vs-base numbers are almost entirely R (the already-certified A5
residual result restated under apa allocation); S adds noise-level amounts (0.1-0.6%) on top. This is a real
negative finding, reported as found (rule 1), not a bug: multiplier excursions stayed within 1-4% of 1.0 in
every case (`multiplier_min/max` in each summary.json) and the self-tuner's decoder-weight norm stayed near
0.015-0.017 against a `w_max=6` ceiling -- essentially unused capacity, not "correctly learned that no
correction is needed."

**Diagnosed cause, confirmed quantitatively against the frozen R1 data, not just plausible.** S's targets
(`y_p = tanh(|eq|/e_ref)`, etc., `e_ref=0.1` rad, unchanged since v0 by the no-retuning rule) were implicitly
scaled for PID's baseline error, which has no rate feedforward and runs ~10x larger on Hard45 (132.5 mrad,
`results/quat_v2_2026-09-12/x2/hard45/dual_v2/summary.json`) than the feedforward-augmented families here
(~10.5-12.5 mrad). PID's own v2 multipliers on that same mission reach mean 1.05-1.09, max 1.21-1.23, decoder
norm 0.101 -- 6-7x stronger engagement under the identical, unchanged tuner hyperparameters. `e_ref=0.1` is
simply too coarse a threshold once feedforward has already shrunk the error an order of magnitude; it is not
that these families have nothing left for a tuner to correct.

**Reading for the dual architecture, and for the journal paper.** This sharpens rather than weakens the
contribution: R generalizes cleanly and dominates (A5, now reconfirmed here under a second allocation scheme);
S's benefit is conditional on the baseline's own error scale relative to a fixed target reference, and was
never shown to be family-general, only PID-general. The honest claim for a journal draft is "the residual
generalizes across seven controller families; self-tuning's benefit is real for PID specifically and its
generalization requires per-family target calibration, which we did not yet do" -- not "the dual architecture
generalizes." A properly-declared v6 (a-priori: e_ref set relative to each family's own *_base geometric-mean
error, not a fixed 0.1 rad; one new held-out check) is the next step if S's generalization is worth pursuing
further before the journal draft; it is not required to submit the R-generalization result, which stands on
its own regardless of this outcome.

### Deep-dive addendum (2026-09-25, exploratory, post-v5, before any v6 declaration): two separate mechanisms, not one

Requested by Gandhi: review deeply why S is not helping, per family, against the adaptive-control SOTA, and
reach a real conclusion before any hardware commitment. Two experiments, using the already-collected v5 data
plus one small targeted probe, disentangle two effects that were conflated above.

**SOTA framing (why the mismatch is expected, not surprising).** P5's `SelfTuner` targets are a heuristic,
error-magnitude-triggered gain boost -- exactly the classical self-tuning-PID idea (Astrom & Hagglund),
appropriate for a controller whose fixed gains are *not* derived from an optimality/stability condition. LQR's
`k1,k2` and MPC's `K0` *are* the closed-form answer to a linear-quadratic optimization given the assumed model;
the adaptive-control literature's principled way to adapt them is online re-identification of the plant model
feeding the *same* Riccati solve (`ioannou1984sigma`, `ioannou1996robust` -- both already in the ACC2027
bibliography), not heuristic multiplication away from the already-optimal gain. Backstepping's principled
adaptation (Krstic/Kanellakopoulos/Kokotovic) ties parameter estimates to the same Lyapunov function used for
the stability proof, not a free-standing multiplier. NMPC's SOTA analogue (learning-based/adaptive MPC) corrects
the *internal predictive model*, which is structurally closer to a residual-on-the-model than an output-side
gain tweak -- consistent with this session's separate finding that NMPC's rollout never sees the residual either
(`AUDIT_NMPC_HOLD_RATE_2026-09-25.md` in the ACC2027 repo). None of that machinery is what `SelfTuner` does, so
a shortfall relative to PID was the expected default, not a bug to be surprised by.

**Experiment 1: does S engage more where error is naturally larger (Hardstep), and does that help?** X2,
lqr/backstepping/mpc, Hard45 (non-saturating, base ~10.5-12.2 mrad) vs. Hardstep (saturating slew, base
~266-288 mrad, i.e. already 2.7-2.9x e_ref=0.1). Multiplier max jumps from ~1.01-1.05 (Hard45) to ~1.05-1.13
(Hardstep); decoder-weight norm jumps ~4-5x (0.02 -> 0.07-0.10). **But st-vs-base and dual-vs-res both turn
negative on Hardstep for all three families** (lqr -0.91%/-0.70%, backstepping -0.26%/-0.67%, mpc -1.29%/-1.80%),
while roll (tiny, non-saturating error) shows ~0% both ways, multiplier essentially exactly 1.000.
**Conclusion 1: more engagement is not sufficient -- on Hardstep it actively hurts.** This rules out "just a
threshold problem" as the whole story: e_ref-scale alone cannot explain a result that gets *worse* as the
tuner fires harder.

**Experiment 2: isolate the calibration question from the saturation question.** `probe_eref.py`, exploratory,
X2, lqr/backstepping, Hard45 only (non-saturating), e_ref forced to 0.005 (20x smaller, matching Hard45's
actual error scale the way 0.1 matched PID's in v0). Multiplier mean reaches 1.06-1.13, max 1.17-1.27, decoder
norm 0.105-0.117 -- now *stronger* engagement than PID's own v2 (mean 1.05-1.09, max 1.21-1.23, norm 0.101).
**Result: st-vs-base +10.6% (lqr) / +10.0% (backstepping); dual-vs-res +8.4% / +8.0% -- exceeding PID's own
2-5% dual-vs-residual benefit.** Conclusion 2: on a non-saturating mission, once e_ref matches the family's own
error scale, S helps substantially. The mechanism generalizes; only the original v5 threshold was wrong, by
roughly the 10-20x this probe used to correct it.

**The real, complete conclusion.** Two separate, now-disentangled effects, both real: (a) S's benefit
generalizes across controller families once its target scale is calibrated per family -- confirmed
empirically, not just argued theoretically, and the effect size (8-10%) is larger than PID's own; (b) S shares
the residual's own already-documented Hardstep failure mode (Sec. VI-E of the ACC2027 paper: latched/boosted
correction fighting a physically actuator-saturated slew, not a correctable tracking error) -- more error there
triggers more "help," and that help cannot manifest as faster physical response once the actuators are already
maxed out, so it just adds overshoot/windup-like cost. **This is fixable the same way R was fixed**: R already
has a saturation-aware output gate (eq. (gate) in the ACC2027 paper); S needs the analogous gate on its own
targets (freeze/retreat multipliers toward 1 when the relevant axis is loaded), which the v2 gating mechanism's
`headroom`/`e_gate` inputs already partially provide but evidently not enough to prevent the Hardstep regression
above -- worth checking whether the *existing* v2 gate is simply too weak/slow (retreat_tau, e_gate threshold)
before designing something new.

**v6, properly scoped by this deep-dive (run 2026-09-25, 128/128 cells, 0 failures).** Implemented in
`run_dual_v5.py` behind a `sat_gate_axes` flag (default off; confirmed bit-exact no-op against an
already-registered v5 cell, rel diff 0.0, before anything new was trusted): (1) `e_ref` per family+platform,
read programmatically from that cell's own v5 `*_base` Hard45 mean error, not hand-transcribed; (2) a new
saturation-aware gate on S, derived and proved in `docs/ARCHITECTURE_MATH.md` sec.8 -- a gain *increase* on an
axis already at its torque box last step is set back to exactly 1 (the un-boosted nominal gain), mirroring the
residual's own `eq:gate` exactly; decreases always pass through. Full 5-mission x 2-platform grid for
lqr/backstepping/mpc; nmpc pilot as in v5.

**Result 1 (what was being tested): self-tuning generalizes, confirmed at full scope, consistent with the
deep-dive's probe.** Geometric-mean gains, all 5 missions (2 for the nmpc pilot):

| family | platform | S vs base | dual vs residual |
|---|---|---:|---:|
| lqr | x2 / cf2 | +2.6% / +2.4% | +2.0% / +1.3% |
| backstepping | x2 / cf2 | +2.7% / +3.0% | +1.9% / +1.8% |
| mpc | x2 / cf2 | +2.6% / +2.8% | +1.9% / +1.4% |
| nmpc (pilot) | x2 | +2.9% | +2.2% |

Consistent, positive, real, and landing in the same 2-5% range PID itself showed (v2: 0.976 X2 / 0.963 CF2). The
probe's much larger +8-10% was an artifact of testing one non-saturating mission in isolation with an
aggressively small e_ref; the honest, full-grid, properly-gated number is smaller but still a genuine,
reproducible gain across every family and both platforms. **E1/E2, generalized correctly: both now hold.**

**Result 2 (found while checking Hardstep specifically, not solicited but not ignorable): a real, pre-existing,
CF2-specific finding, unrelated to self-tuning.** `lqr/cf2-rotor/hardstep/res` and `dual` blow up to ~2100-2190
mrad (base: 262-301 mrad) with rotor-saturation fraction 0.81-0.87 and z_min collapsing to 0.013-0.017 m
(base: 0.41-0.69 m) -- confirmed **byte-identical between v5 and v6** (the `res` arm doesn't involve S at all),
so this predates today's work and is not caused or fixed by the gate. Confirmed uniform across all three
families (lqr/backstepping/mpc), all specific to CF2 + Hardstep + R active; X2 shows the same direction but
stays safe (qerr worsens ~25-30%, z_min stays ~0.21 m, sat_frac 0.01-0.04 vs CF2's 0.81-0.87). Trace inspection:
`apa`'s own feasibility bisection never triggers (alpha=1.0 throughout -- ruling out an allocation-infeasibility
bug); τ_0 itself sits pinned at CF2's torque box (±0.29-0.32 mN·m, genuinely tiny) while qerr oscillates between
~1.4 and ~3.1 rad, near the θ_q ∈ [0, π] ceiling -- torque-saturated chatter consistent with the ACC2027 paper's
own disclosed Sec. II-A limitation ("no continuous feedback globally stabilizes rigid-body attitude... shortest-
path branch away from the 180° sign boundary"), here triggered by CF2's tiny torque authority under Hardstep's
aggressive steps once R's extra demand is added on top of an otherwise-apa-safe baseline. Likely the same class
of fragility A5 already disclosed for LQR/MPC's CF2-Hardstep *baseline* blowup under `clip` allocation
(2100-2200 mrad, rotor-sat 0.83-0.89) -- `apa` fixes it for the unmodified baseline but not once R is added back.

**Scope of result 2, stated precisely.** This does not touch Phase 5: the Quanser Aero2 is a fixed 2-DOF
pitch/yaw platform, not a free-flying quadrotor, and is not subject to the shortest-path quaternion antipodal
issue this mechanism implicates. It **does** need resolving or explicitly excluding before any claim involving
CF2 + these new families + Hardstep + R (sim or, eventually, a real CF2 quadrotor if one is ever used) --
flagged here rather than smoothed over, per the standard this addendum was asked to meet.

**Hardware readiness, answering what was asked.** Do not hardware-test "the dual architecture" as currently
built -- it would show large gains on gentle missions and a real regression on aggressive/saturating ones,
an unconvincing and easily-misread result. R alone is hardware-ready now (SOTA-consistent: a generic additive
correction has no family-specific optimality structure to conflict with, and Prop. 1's bound holds regardless
of the baseline). S is hardware-ready *after* v6 lands with the saturation-gate fix confirmed, not before --
this deep-dive is precisely the "conclusion needed before hardware" that was asked for, and the answer is
"promising and worth finishing, not yet done."

## Phase 5 (new, 2026-09-25): Quanser Aero2 hardware -- scoping note, not yet a declaration

`C:\Research\aero2\` (Gandhi's existing project, source of `AdvancedBaseline`) already has: a backend-agnostic
`Controller`/`Backend` contract (offline / QLabs virtual-twin / hardware, mode is a config field per that repo's
own CLAUDE.md rule 3); **real hardware runs already on file** for PD, LQR, backstepping, SMC, and NMPC
(`results_hardware/helicopter_2dof_hardware_{pd,lqr,backstepping,smc,nmpc}_*`, Sep 2026, plus a documented
hardware benchmark in that repo's CLAUDE.md: PD best overall, SMC best nonlinear tail-pitch, NMPC realtime at
~303 Hz but not competitive, yaw unresolved for every model-based controller); and its **own**, separate,
earlier neuromorphic residual (`aero2_residual/residual_gate.py`, ported from a Qube ServoPendulum project) --
a single hand-designed demand-driven gate, fixed weights, *no* online PES learning, explicitly not yet beating
classical per that repo's CLAUDE.md ("needs trained gates + harder regimes"). That is a materially simpler
architecture than the now-validated CMG-PES (six units, 18-weight online PES decoder, A4/A5-certified) -- porting
the validated architecture in, rather than iterating the older fixed gate, is the natural move, and there is a
real hardware baseline already on disk to compare against for five of the seven target families.

**Sequencing (per Gandhi: optimize the dual first, hardware after).** This phase does not start until v5 (sim)
is reported. When it does, `run_gate_residual.py`'s existing QLabs-first pattern (`execution_mode="virtual_twin"`
before `"hardware"`) is the right staging order, and MPC/PID hardware baselines are the two gaps to fill in
`results_hardware/` before a fair seven-family comparison is possible there.

## Phases

| Phase | Scope | Exit criterion |
|---|---|---|
| **0 (2026-09-12)** | v0 quaternion experiment on X2 and CF2, 5 missions x 4 controllers; architecture math v0 | Runs complete, rules applied, report written |
| **1** | Align S with the published STN-PID-PES law (Q1); slow-variation bound (Q2); disturbance and mismatch cells (mass/inertia +-, motor lag, persistent torque) | Math note with a proof sketch; held-out mismatch batch |
| **2** | 6-DOF on X2 and CF2 (flatness feedforward cascade from `six_dof_expansion_2026-08-31`), S on attitude and position gains | Circle, Full6 and Waypoint campaigns |
| **3** | Omnicopter: 6-channel wrench, S on the geometric PD gains, R = existing 6-channel CMG-PES | 25-mission campaign plus held-out mismatch, compared with frozen R1 |
| **4** | High-fidelity models (motors, propellers, aero, sensors) replace ideal thrust; rerun Phases 2-3 | Fidelity gates in `HIGH_FIDELITY_MUJOCO_PROPOSAL.md` |
| **5 (new)** | Generalize S to LQR/backstepping/SMC/MPC/NMPC in sim (v5, above), then port the validated dual architecture to Quanser Aero2 hardware (residual-only and dual, same families where admissible) | v5 report with E1-E3; then a hardware campaign against the existing `results_hardware/` baselines |

## Reporting target

This work evolves the ACC 2027 contribution. It is a candidate for a journal extension
(TCST / RA-L / TNNLS) or CDC/ACC 2028. Hardware availability, previously the open condition on that sentence, is
resolved: Quanser Aero2 hardware access exists now (`C:\Research\aero2\`), with prior real hardware results for
most of the target controller families already on disk.
