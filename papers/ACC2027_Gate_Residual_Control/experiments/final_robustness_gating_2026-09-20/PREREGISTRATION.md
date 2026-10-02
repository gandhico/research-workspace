# Pre-registration — final robustness and saturation-gating campaign (2026-09-20)

Written **before any campaign result was produced**. The only results that exist at the time of
writing are the 20 validation cells (section 1), which contain no gate, no noise and no
disturbance. File hashes are appended at launch by `seal_prereg.py` and repeated in every
`campaign_plan_*.json`.

## 0. Why this experiment

The manuscript's primary baseline is PD + desired-rate feedforward at rho = 3. Three weaknesses
remain against it:

1. Noise and disturbance were tested only against the **fixed PD** baseline, and the noise rows
   score the error of the *corrupted* quaternion the controller sees, not the true attitude.
2. Hardstep is the one mission where the residual degrades (X2 -17.0 %, CF2 -1.3 %); the fix
   (saturation-aware gating) is only mentioned as future work.
3. The CF2 row of the primary block was produced at **beta = 0.05**, ten times below the beta = 0.5
   stated in Table I and the text (`master_table.csv`, column `beta_sel`; rule: beta >= 0.1
   diverges on Hardstep). The manuscript does not currently disclose this.

## 1. Validation gate (done, passed)

`run_validation.py` re-runs all 10 mission x platform cells for PD+ff (rho = 3) and CMG-PES at the
table's beta and compares with the archived values in `master_table.csv`.
Pre-declared tolerance 1e-4 relative. **Result: worst relative error 5.0e-15, PASS** — the new
runner is bit-identical to the archive. (`results_validation/`.)

## 2. Frozen configuration

* Baseline, shared by every arm: PD + rate feedforward, rho = 3, wn0 = (4, 4, 3.5) rad/s, zeta = 0.95.
* 45 s, dt = 5e-4 s, eta = 8e-4, target k_e = 8, k_w = 0, CF2 actuator scale 1.5.
* **Gate (exact saturation, output-only):** on axis i, block the requested residual when
  |u0_i| >= l_i - 1e-12 and sgn(residual_i) != sgn(u0_i). PES keeps learning.
* Arms: `pdff_rho3`; `cmg_pes_table` (beta X2 0.5 / CF2 0.05, ungated: reproduces Table II);
  `cmg_pes_gated` (beta = 0.5 on both airframes); CF2 only `cmg_pes_b05_ungated`.
* Metric: **true** quaternion-angle error (`qerr_true_mean_rad`); corrupted-feedback error is
  logged separately and reported only as a secondary column.

## 3. Confirmatory endpoints and decision rules

| id | question | campaign | rule (decided now) |
|---|---|---|---|
| H1 | Does the exact-saturation gate make the residual **beat** the baseline on Hardstep? | nominal, Hardstep, both airframes, beta = 0.5 | "Positive" = mean true error below PD+ff on **both** airframes **and** mean settling time (5 deg, 2 s censored) no worse. |
| H2 | Does the gate let CF2 run at the stated beta = 0.5 without loss? | nominal, all 5 missions | Report the CF2 geometric-mean reduction of `cmg_pes_gated` vs `pdff_rho3` next to the 6.5 % of `cmg_pes_table`; no cell may diverge. |
| H3 | Is the benefit robust to sensor noise against the tuned baseline? | noise | Per cell: mean and s.d. of the paired reduction over seeds, and the count of seeds with a positive reduction. "Robust" only if positive in **all** seeds. |
| H4 | Is it robust to repeated torque bursts against the tuned baseline? | disturbance | Burst-phase and quiet-phase mean true error at 0.5x, 1x, 2x the paper amplitude. |

**Priors, stated so they can be wrong.** From the 2026-09-16 direct-CMG harness (`hardstep_fix`):
gated Hardstep mean error was 15.56 deg vs 15.25 deg on X2 and 15.24 vs 15.06 deg on CF2, i.e.
**-2.0 % and -1.2 %**, with settling better than the baseline (0.570 vs 0.590 s, 0.508 vs 0.528 s).
Hardstep is slew-dominated (97-99 % of the mean) and X2's yaw box is 97 % of the rotor-feasible
torque, so a gate that only *removes* harm cannot be expected to produce a positive mean-error
reduction. **I expect H1 to fail on mean error and to pass on settling.** I expect H2 to hold.
Whatever happens is reported.

## 4. Sizes

nominal 35 runs; disturbance 21; noise 450 (realistic level 0.020 rad / 0.050 rad/s, 10 paired
seeds; moderate level 0.010 rad / 0.025 rad/s, 5 paired seeds; classical and CMG arms share the
same noise stream because the generator advances identically each step).

## 5. Exploratory screen and the promotion rule

`hardstep-development` is **X2-only and exploratory**: load thresholds {0.975, 0.95, 0.90} of the
axis limit for the output gate, and each of {1.0, 0.975, 0.95, 0.90} with the decoder rows also
frozen on blocked axes (7 runs; the confirmatory 1.0 output gate is not repeated). It can never be
a headline. A variant replaces the exact-saturation gate in the paper **only if all of:**

1. it lowers X2 Hardstep mean true error below `pdff_rho3` by at least 2 % **and** below the
   exact-saturation gate;
2. the identical, unchanged configuration is then run on CF2 Hardstep and on the other eight
   mission x platform cells (a separate, declared run) and lowers CF2 Hardstep mean error below
   `pdff_rho3`;
3. it changes no other cell's mean error by more than 1 % relative to the exact-saturation gate.

Otherwise it is reported, if at all, as a one-line sensitivity remark, and the exact-saturation
gate stays canonical. **No threshold is tuned on CF2.**

## 6. What is not being claimed

Results are simulation only, deterministic except for the noise seeds; no stability certificate
is claimed for the gated law. The gate preserves |u - u0| <= beta*l and exact recovery at
beta = 0 by construction, and does not touch the decoder, so Propositions 1-3 are unchanged for
the output-only gate.

## 7. Seal

Sealed 2026-09-20T20:49:39 (local), before launching any campaign.

| file | sha256 |
|---|---|
| `run_final_robustness.py` | `e4f076565dc658017b78e40dbc5e384d052f5d54be0914fbd33ffcdb6538a292` |
| `run_campaign.py` | `54aa403e694e77e0ef16cf78c4a095393672da51fd541d97fddc10b91339cf3c` |
| `run_validation.py` | `c7b6a07e3b57a62574853ec8a9fd0fadaac3e3249862a3579e21010530dcf521` |
| `PREREGISTRATION.md` (above this section) | `77778146ab4d2814a1d15bca156231d47d93773dc67ad1fc2c705fc821fb6c3c` |

## 8. Amendment A1 (2026-09-20, written after the first screen and before any A1 run)

**What the first screen showed** (`analyze_dev.py`, `hardstep_profile.py`): every variant of section 5 lands
between -1.65 % and -2.09 % on X2 Hardstep; none passes promotion rule (1). Decomposing the error by time
since each step onset shows the gated residual **helps during braking (0.25-0.75 s after a step) and hurts in
the settling tail (0.75-1.5 s)**, where the baseline has already left its torque box (it sits at the box in
only 10-31 % of samples). A rule conditioned on saturation therefore cannot remove that harm by construction.

**Declared extension (exploratory, X2-only, same promotion rule as section 5).** Continue the same gate family
to lower load thresholds, where it approaches a pure sign-consistency rule (block the residual whenever it
opposes the baseline command): output-only gate at load thresholds **{0.75, 0.5, 0.25, 0.0}** of the axis
limit. This is motivated by an exploratory result and is therefore **post hoc**; it can only be promoted by
the confirmatory route of section 5 (identical configuration on CF2 Hardstep and the other eight cells,
with rule (3) evaluated against the exact-saturation gate). It preserves |u - u0| <= beta*l and exact recovery
at beta = 0, and leaves the decoder untouched. It is implemented in `run_campaign_a1.py`, which imports the
sealed driver without modifying it.

## 9. Amendment A2 (2026-09-20, written after the moderate-noise CF2 result and before any A2 run)

**What happened.** In the moderate-noise campaign the exact-saturation output gate at beta = 0.5
**diverges on CF2 Hardstep in 5 of 5 seeds** (mean true error 94-118 deg against 15.1 deg for PD+ff; rotors
saturated in 61-79 % of samples). It is safe noise-free (15.2 deg), and the beta = 0.05 arm is safe under
noise (15.3 deg). Trace analysis (`diagnose_cf2_noise.py`, seed 2): at the 9 s step the requested collective
thrust rises to 0.66 N against a realized 0.525 N (the total rotor limit); every rotor saturates from
t = 9.67 s, realized torque falls short of the command, the tilt grows and tilt compensation demands still more
thrust. The residual is same-sign with u0 (or acts on unsaturated axes), so the torque-box rule of Eq. (gate)
never fires: the binding constraint is rotor-level, not the torque box.

**Declared variants (exploratory; CF2 only; development data = moderate-noise seeds 1 and 2, CF2 Hardstep):**

* (a) `rotor-flag`: in addition to the opposition rule, block the whole residual at step k if the allocator
  clipped any rotor at step k-1; beta = 0.5.
* (b) `starvation`: in addition to the opposition rule, block the whole residual at step k if the realized
  collective thrust at step k-1 was below the requested value by more than 1e-6 N; beta = 0.5.
* (c), (d) the exact-saturation gate, unchanged, at beta = 0.2 and beta = 0.1.

(a) and (b) preserve |u - u0| <= beta*l and exact recovery at beta = 0 and leave the decoder untouched.

**Selection rule (fixed now).** A variant is *safe* on the development data if, in both seeds, the mean true
error is below 2x that of PD+ff. Among safe variants, choose the one with the largest noise-free CF2
geometric-mean reduction (a noise-free five-mission CF2 run of each safe variant is part of this amendment).
If none is safe, none is adopted; the paper then reports the divergence and the beta = 0.05 arm.

**Confirmation on held-out data.** The chosen variant, unchanged, is run on everything not used for selection:
CF2 Hardstep moderate seeds 3-5 and realistic seeds 1-10, X2 Hardstep on the same seeds, and all nominal
cells. It is adopted only if (i) no held-out run diverges (mean error < 2x PD+ff), (ii) every non-Hardstep
nominal cell changes by at most 1 % against the exact-saturation gate, and (iii) X2 nominal Hardstep is not
worse than -3 % against PD+ff. Otherwise it is reported as a negative result.

**Stated regardless of outcome.** The manuscript will say that the exact-saturation gate does not guard
against rotor-level saturation on CF2 under measurement noise.

**Addendum to A1 (2026-09-20, before the limit-case run).** The sealed runner rejects a load threshold of 0
(`--gate-load-threshold must be in (0,1]`), so the declared limit case "0.0" could not run. It is run as
**0.001** of the axis limit (a pure sign-consistency rule for all practical purposes), fixed here before its
result is seen. Thresholds 0.75, 0.5, 0.25 completed on 2026-09-20; their results are in
`results/development_only/hardstep_variant_screen_a1/` and summarised in `README.md`.

**A2 development result (2026-09-20; `analyze_a2.py`).** CF2 Hardstep, moderate noise, seeds 1-2, ratio of mean true
error to PD+ff: `rotorflag` 6.25 / 7.78 and `starvation` 6.25 / 7.78 (both still diverge; the residual is blocked
in 68-82 % of samples, but blocking after rotor saturation has begun does not rescue the loop); exact-saturation gate
at beta = 0.2: 1.00 / 1.00; at beta = 0.1: 1.00 / 1.00. By the selection rule fixed above, `gated_b02` and
`gated_b01` are **safe**; the noise-free five-mission CF2 run of each (declared above) decides between them.

**Addendum to A2 confirmation scope (written before any confirmation run).** The confirmation clause above was
written with a gate variant in mind. Because the only safe variants are values of beta, which is a per-airframe
authority, X2 keeps beta = 0.5 (its Table I value; it is safe under noise) and the confirmation is **CF2 only**:
Hardstep at moderate seeds 3-5 and realistic seeds 1-10, plus the five nominal missions. Criteria (i)-(iii) are
unchanged, with (ii) and (iii) evaluated against the beta = 0.5 exact-saturation gate on CF2 (noise-free) where that
run exists. For the manuscript tables, the selected CF2 configuration is then also run on all missions and seeds of
the noise campaign and on the disturbance campaign; seeds 1-2 of CF2 Hardstep (moderate) were used for selection and
are flagged as such wherever they enter a reported number.

**Clarification of confirmation criterion (ii) for a beta variant (written 2026-09-20 after the selection-stage
nominal results were seen, and before any confirmation-stage result was analysed; recorded for transparency).**
Criterion (ii) as written (non-Hardstep nominal cells within 1 % of the beta = 0.5 gate) cannot hold when beta itself
is the variable. Its natural replacement: *no nominal CF2 cell is worse than the previously reported CF2
configuration (beta = 0.05, ungated)*. The selection-stage results (beta = 0.2: Roll 59.9, Full3 5.4, Hard45 7.3,
Hardstep -0.2, Yaw360 20.3 % against 22.9, 1.3, 1.8, -1.3, 5.6 % for beta = 0.05) satisfy it in every cell, so the
clarification does not change the outcome, but the reader should know the order in which things were written.
Criteria (i) (no held-out divergence) and (iii) (X2 Hardstep unchanged, since X2 keeps beta = 0.5) stand as written.

**A1 final (2026-09-20; `analyze_a1.py`).** X2 Hardstep, noise-free, beta = 0.5, output-only gate: load threshold
1.0 / 0.75 / 0.5 / 0.25 / 0.001 gives -2.05 / -1.21 / -0.16 / +0.11 / +0.32 % against PD+ff (gate share 20 / 24 / 29 /
36 / 79 % of samples; settled error 0.382 / 0.324 / 0.256 / 0.215 / 0.186 deg against 0.185 for PD+ff). No variant
reaches the 2 % margin of promotion rule (1): the exact-saturation gate stays canonical, and the family's ceiling on
this mission is parity.

## 10. Amendment A3 (2026-09-21): Izhikevich-PES under the same protocol as CMG-PES — reduced grid, declared before running

**Why.** The paper's Izhikevich rows are on the weak fixed-PD baseline. To report the rival basis "in the same circumstances"
as CMG (tuned PD+ff rho = 3, true-attitude error, paired noise, the same output gate), it is put into the validated runner.
The full grid would be ~415 runs (~3 h); the request was for minutes, so a **reduced grid** is declared here (about 35 runs,
~15 min at 4 workers). The gap to the full grid is stated wherever the results are reported.

**Implementation.** `izh_adapter.py` wraps the archived `NengoNeuronFamilyAugmentor` (calibrated feature scale 42.6, native
current scale 10; the same object the paper's family rows used) behind the interface the runner already uses for CMG;
`run_izh_robustness.py` is a copy of the sealed runner with the controller choice and summary labels patched (baseline,
noise, disturbance, gate and metrics untouched). **Validation gate (before any campaign run):** with the gate not acting, the
adapter must reproduce the archived-runner Izhikevich results (`supplementary_izhikevich/`, and one archived CF2 run) to a
relative error <= 1e-9.

**Disclosure.** The X2 nominal, ungated, beta = 0.5 results (Roll -811.6, Full3 +5.3, Hard45 +6.8, Hardstep -16.9,
Yaw360 -1454.9 % against PD+ff) were **seen before this amendment** (exploratory supplement, 2026-09-21). Everything else below is new.

**Arms and cells (all on PD+ff rho = 3; PES eta = 8e-4, k_e = 8; exact-saturation gate as for CMG):**

| block | X2 (beta 0.5) | CF2 (gated: beta 0.2, the CMG choice) |
|---|---|---|
| nominal, gated | 5 missions | 5 missions |
| nominal, ungated | 5 missions (already run, archived runner) + Hardstep in the new runner | Hardstep at beta 0.05 and at beta 0.2 |
| noise, realistic level (0.020 rad, 0.050 rad/s), seeds 1-3, gated | Roll, Hard45, Hardstep | Roll, Hard45, Hardstep |
| disturbance, hover, 1x amplitude, gated | 1 run | 1 run |

Not run (declared): moderate noise level; noise seeds 4-10; Full3 and Yaw360 under noise (they mirror Hard45 and Roll for CMG);
0.5x / 2x disturbance; CF2 at beta 0.5; the fixed-decoder variant at rho = 3. The PD+ff and CMG-PES noise and disturbance arms
for the same seeds already exist and are paired with these.

**Priors (stated so they can be wrong).** P1: Izhikevich's reduction is below CMG's in every nominal cell on both airframes.
P2: under noise it degrades Roll (its effort is baseline-independent) and does not beat CMG on Hard45. P3: the gate reduces the
X2 Hardstep loss (-16.9 %) but, as for CMG, does not turn it into a gain. P4 (uncertain): CF2 at beta 0.2 stays safe under noise.
**Reporting rule:** every cell of the reduced grid is reported; there is no selection among cells or seeds.


## 11. Amendment A3.1 (2026-09-21): validation outcome and how CF2 Izhikevich cells are read — written before any A3 campaign run

**Validation gate result** (`validate_izh_runner.py`, `results_validation_izh/validation_verdict.json`).
V1 X2 Hard45 beta 0.5: 9.816749 vs 9.816749 mrad, relative error 0.0. V2 X2 Hardstep beta 0.5: 310.737036 vs 310.737036 mrad, 0.0.
V3 CF2 Hard45 beta 0.2: 8.073354 vs 8.070892 mrad, relative error 3.05e-4 -> **misses the declared 1e-9 tolerance**.

**Diagnosis** (`diagnose_cf2_short.py`, `diagnose_cf2_izh_exact.py`, `sensitivity_izh.py`; outputs saved in `results_validation_izh/`).
1. Baseline only (classical PD+ff, CF2, 1 s, every step): the archived and the sealed runner are bit-identical (0 differing values in 2001 rows).
2. The only difference is the residual path. The sealed runner rebuilds the requested residual as beta * limits * decoded_clipped from the
   augmentor diagnostics (needed to audit the gate) and clips it; the archived runner applies the augmentor's own command. The two agree
   exactly unless beta * limits is inexact in floating point. The runner records the difference: `max_native_vs_reconstructed_command_error_Nm`
   = 0.0 on X2 (beta 0.5, scale 1) and 5.4e-20 N m on CF2 (beta 0.2, actuator scale 1.5).
3. A smooth controller does not amplify this: for CMG-PES on CF2 (1 s) |d omega| <= 4e-15 rad/s and |d q_err| <= 3e-16 rad. The spiking cell does:
   in the new runner, perturbing the initial attitude of CF2 Hard45 (beta 0.2) by 1e-12 deg (1.7e-14 rad) changes the 45-s mean error by 5.3e-3
   (relative), by 1e-10 deg by 5.5e-4; X2 Hard45 with 1e-12 deg: 8.3e-3. The archived-vs-new gap (3.05e-4) lies inside that range.

**Decisions.**
(a) V3 is not an integration error, but it did miss the declared tolerance, which was appropriate only for smooth or exactly representable cells.
It is reported as it is: bit-exact on both X2 cells, and "not bit-exact, inside the model's own reproducibility floor" on the CF2 cell. The tolerance is not relaxed after the fact.
(b) The campaign runs under the sealed runner's arithmetic, i.e. the same arithmetic as every CMG-PES result; the archived runner is not the reference for CF2.
(c) Reading rule for Izhikevich: a single-run difference below 1 % is not interpreted (the measured floor is about 0.5 %); noise cells use 3 seeds. Comparisons against CMG-PES,
which differ by tens of percent, are unaffected.
(d) The paper states this in one clause wherever Izhikevich CF2 numbers appear. Nothing else in section 10 changes.


## 12. Amendment A3.2 (2026-09-21): the single-run floor is measured, and the reading rule is revised — written after the campaign and the X2 half of the floor ensemble were seen, before any paper text

**What happened.** A3.1(c) set the reading rule from two perturbation runs (floor about 0.5 %, "differences below 1 % are not interpreted").
The A3 campaign then showed a cell whose gate was nearly inert (X2 Hard45, gate blocked 0.011 % of steps) changing by 3.2 % between the
ungated (9.817 mrad) and the gated run (9.503 mrad): the two-run estimate was too small. `floor_izh.py` measures the scatter properly: for the four
multi-axis nominal cells (Full3 and Hard45 on X2 at beta 0.5 and CF2 at beta 0.2, gated arm) the initial attitude is perturbed by k * 1e-12 deg
(k = 1..6; about 1.7e-14 rad per unit k), 24 runs; with the A3 run each cell has 7 values. The X2 half showed a standard deviation of about 1.5-2 % of the mean error.

**Revised rule (declared before the CF2 half of the ensemble was read).**
(a) A single-run difference between two Izhikevich cells, or between an Izhikevich cell and a CMG cell, is interpreted only if it exceeds
three times the largest standard deviation found in the ensemble, expressed in points of the PD+ff error of the cell (the unit of the reduction columns).
Smaller differences are called "level" and are counted neither for nor against a prior.
(b) Cells outside the ensemble (Roll, Yaw360, Hardstep) are chatter- or slew-dominated; only effects of tens of percent are interpreted there
(the Roll/Yaw360 error factors against PD+ff are 1.8 to 16, the gate effect on X2 Hardstep is 15 points, the CF2 divergence is a factor 8).
(c) The paper quotes the measured standard deviation and the threshold. P1 and P2 are re-evaluated under (a): a cell where Izhikevich and CMG differ by
less than the threshold is reported as level, in either direction. Nothing else in sections 10-11 changes.

**Clarification (2026-09-21, same day, while writing the paper; no result changes).** The runner applies `--initial-angle-deg theta` as the Euler
triple (theta, -0.7 theta, 0.5 theta), i.e. a rotation of 1.32 theta, not theta. The ensemble offsets (k = 1..6, theta = k * 1e-12 deg) are therefore
2.3e-14 * k rad, from 2.3e-14 to 1.4e-13 rad; the "1.7e-14 rad" quoted in A3.1 and above is the roll component of the first step. The paper states the offsets as
"below 2e-13 rad". The scatter numbers themselves are unchanged.


## 13. Amendment A4 (2026-09-24): Nengo PES learning-rate correction for the conventional neuron-family adapter — written after independent verification, before any paper text is changed

**What happened.** Gandhi ran a separate, independently-designed campaign with ChatGPT (`experiments/neuron_basis_decisive_2026-09-24/`, pre-registered 2026-09-24, 186 runs, audited 186/186) that found the archived
`nengo_neuron_family.py` computes its Nengo PES learning rate as `eta*N/(dt*S)`, one power of the feature-scale `S` short of what its own network wiring requires — making the effective learned-weight update `S` times too fast
(~42.6x for Izhikevich, S=42.602). This affects every non-CMG neuron-family PES result in the project, including the Izhikevich rows already in the paper (both the A3 rho=3 block and the original fixed-PD block), which all use this
same archived class. The CMG path does not use this class and is unaffected.

**Independent verification (this repository, before any number was accepted).** (1) Re-derived the correct formula from Nengo 4.1.0's actual installed `SimPES` source and the exact archived network wiring (not from the external
report): `eta_N = eta*N/(dt*S^2)`, matching the external finding exactly. (2) Confirmed the archived files are untouched (mtimes predate 2026-09-24). (3) Built an independent corrected implementation
(`izh_adapter_corrected.py`, `run_izh_corrected.py`, and, for the fixed-PD baseline, `run_mujoco_nef_corrected.py` — each a minimal, exact-diff copy of a sealed/archived file, verified by `diff`) rather than trusting the external
campaign's own code. (4) Cross-check 1: the independent corrected adapter reproduces the external campaign's X2 Hard45 rho=3 gated cell to 15 significant figures (10.063402866411398 mrad, both). (5) Cross-check 2: with the
correction flag OFF, the corrected-runner copy reproduces the currently-published fixed-PD CF2 Hardstep Izhikevich number almost exactly (335.18 mrad here vs 21.4% reduction published, i.e. 335.0 mrad) — isolating that only the
rate correction changes the result, not some other difference introduced by copying the file.

**New finding beyond the external report.** The external campaign's pre-registration scoped it to the rho=3 tuned baseline only; it did not re-examine the original fixed-PD baseline's Izhikevich row. Re-running that row here
(10 cells, corrected rate, same beta=0.5/eta=8e-4/k_e=8 as the archived campaign) finds: X2 is uniformly still positive but smaller than published (geo 33.8%, was 48.6%); CF2 Roll/Full3/Hard45/Yaw360 are similarly smaller-but-positive
(33.7/38.9/32.2/41.5%, were 51.5/51.9/50.3/56.4%); **CF2 Hardstep, currently published as a +21.4% improvement, actually diverges under the corrected rate** (2450.8 mrad mean error vs the PD baseline's 426.2 mrad, a 5.75x
increase — sustained near-180 deg tracking loss from t=3s onward, not a transient spike). This matches the failure mode already documented elsewhere in this paper for CF2 + Hardstep + an ungated residual at beta=.5 (e.g. CMG-PES's own
documented divergence at this same beta/gate/mission combination): the old, ~42.6x-too-fast rate likely rail-saturated the decoder almost immediately, which accidentally behaved like a bounded constant correction and avoided the
divergence a genuinely adaptive residual falls into on this mission. Full numbers: `experiments/nengo_nef_replication_2026-08-29/results/izh_fixed_pd_corrected_2026-09-24/` and `report_fixed_pd_correction.py`'s output.

**Decisions.**
(a) The paper's Izhikevich claims — abstract, Sec. VI-D, Table II's rho=3 block, and Table II's fixed-PD block — are corrected in the next revision using the exact-normalization rate throughout, not the archived one.
(b) The fixed-PD CF2 Hardstep divergence is reported like every other diverged cell in this table (the pre-existing "div." convention: geometric mean withheld for a row containing a diverged cell), not silently smoothed over.
(c) This is disclosed as a correction of previously published numbers, not a new result being added; the archived campaign's numbers remain on record in `results/neuron_family_compiled/` as historical, superseded evidence, consistent
with how amendment A3.1 treated the CF2 validation gap.
(d) The deadline moved to 2026-10-02 (from the previously understood 09-25), which is why this correction is being integrated now rather than deferred.

**Certification completed (2026-09-24, same day, before any paper text edited).** Amendment A4's correction is now
fully certified: LIFRate's development-grid selection independently re-derived from raw files (argmin matches
exactly, no leakage); LIFRate's held-out aggregate independently recomputed (15.73/11.31 vs reported 15.77/11.37,
agree to 0.05pp) and one held-out cell independently re-simulated from a from-scratch adapter (7.545217 vs 7.545
mrad); the non-neural static-paired basis independently reimplemented without reading the external code at all
(first attempt disagreed 19% due to a bug in my own verification script's diagnostics stub, found, fixed, and
reconciled to full double precision: 0.2869084838587546 both). Full derivation, every number, and the complete code
inventory are in `REPORT_NEURON_BASIS_CORRECTION_2026-09-24.md`.

## 14. Amendment A5 (2026-09-24): controller-family portability study (PID, LQR, backstepping, SMC, MPC, NMPC) — written before any A5 result is run

**Why.** CONTROLLER_EXTENSION_DECISION.md (experiments/neuron_basis_decisive_2026-09-24/, written by Gandhi + ChatGPT) recommends, and I independently agreed before reading that
document, that a full controller-native residual redesign (Stage C: bespoke anti-windup/matched-uncertainty/constrained-QP integration per controller) is next-paper/journal scope,
not this ACC submission. Stage A -- interface portability: does the bounded, gated CMG-PES residual attach cleanly to each controller family and recover the baseline exactly at
beta=0, without claiming universal improvement -- is small and well-scoped. This amendment runs Stage A only.

**Implementation.** `run_controllers_gated.py` is a copy of the sealed `run_final_robustness.py` with the frozen backstepping-only baseline replaced by a CLI-selectable one
(--baseline: pd, lqr, backstepping, smc, mpc, nmpc), reusing `AdvancedBaseline` from the archived, unmodified `run_mujoco_nef_baselines.py` verbatim (lqr/backstepping/smc/mpc/nmpc)
and that same file's own conditional-integration, rotor-level-anti-windup PID path (ki_factor>0 on the pd family). Nothing archived was edited; the diff is 7 named, exact-match
patches, verified: (1) with all new flags omitted, `run_controllers_gated.py` reproduces the sealed runner's output byte-for-byte (summary metric exact match, 0-line trace.csv
diff); (2) `--baseline pd --ki-factor 0` at the same bw_scale/rate_ff/no_model_ff as the default `--baseline backstepping` agree to ~1e-15 relative (floating-point-reordering level,
not a real difference -- two different code paths computing the same algebraic controller), confirming the "backstepping + no-model-ff = PD + desired-rate feedforward" identity the
paper already states.

**Frozen for every family (interface portability, not per-family re-tuning).** bw_scale=3 (reusing the paper's own already-validated PD-family finding of best mission-mean at rho=3;
applied uniformly, not re-swept per controller), beta=.5 (X2) / .2 (CF2), k_e=8, k_rate=0, eta=8e-4, the exact-saturation output gate, torque-policy=model, actuator-scale 1.0/1.5.
PID: ki_factor=0.3 (one round, undertuned value -- not selected by any sweep; disclosed as such), antiwindup=rotor. MPC: mpc-dt=0.02, mpc-horizon=120 (unconstrained finite-horizon
LQR-equivalent, aero2 form, no re-tuning). NMPC: nmpc-dt=0.06, nmpc-horizon=5, nmpc-grid=3, nmpc-predict=policy, baseline-rate-hz=100 (100 Hz update, matching the only prior
validated NMPC setting on record in `baselines_2026-09-10/stretch/nmpc/` -- update_every_steps=20 at dt=5e-4 -- reused rather than re-derived, since a full NMPC re-tuning is out of
scope for a portability check). SMC: smc-eta-frac=0.5 (the file's own default).

**Cells.** 6 families x 2 platforms x 5 missions x 2 arms (classical, nengo-nef-pes/CMG-gated) = 120 runs, one seed each, deterministic, no noise/disturbance (matching the primary
campaign's own nominal-cell design). `pd` (ki=0) is not separately run: proven identical to `backstepping` above; the existing sealed-runner `pdff_rho3`/`cmg_pes_gated` results
(already in `results/final_nominal.csv`) are reused for that row. So 5 NEW families x 2 platforms x 5 missions x 2 arms = 100 new runs.

**Reporting rule.** Every cell is reported once run; no selection among cells. Per CONTROLLER_EXTENSION_DECISION.md's own finding (predates the final gate, disclosed as such) and
this study's stated purpose, the result is read as "does the residual attach without breaking the baseline," not "does it universally help" -- a family where CMG does not improve
tracking (e.g. an already-near-optimal LQR/backstepping/MPC on an exact model) is not a negative result for CMG, it is the expected, disclosed outcome for a residual added to an
already-accurate baseline (Sec. VI-B's own language: "diminishing returns as the baseline improves").

**Results (2026-09-24, same day, all 100 cells run, 0 failures, reported in full per the pre-declared rule).**

| family | X2 geo baseline->CMG [mrad] | X2 Delta | CF2 geo baseline->CMG [mrad] | CF2 Delta |
|---|---|---:|---|---:|
| PD+ff (backstepping) | 4.544 -> 2.850 | +37.3% | 3.765 -> 2.921 | +22.4% |
| PID+ff (ki=.3, rotor anti-windup) | 3.725 -> 2.359 | +36.7% | 3.125 -> 2.427 | +22.4% |
| LQR | 4.634 -> 3.190 | +31.1% | 5.768 -> 4.478 | +22.4% |
| SMC | 6.275 -> 3.527 | +43.8% | 5.342 -> 3.919 | +26.6% |
| MPC (unconstrained) | 5.180 -> 3.450 | +33.4% | 6.401 -> 4.951 | +22.7% |
| NMPC (grid, 100 Hz) | 4.552 -> 4.731 | **-3.9%** | 3.544 -> 2.772 | +21.8% |

Full per-mission table: `results/A5_CONTROLLERS_RESULTS.md`. Three findings, reported as found:
(a) the residual attaches without incident to every family -- no crash, no NaN, Prop. 1's bound (which does not depend on how u0 was
computed) holds by construction; (b) SMC shows the largest gain, including on Hardstep (X2 +34.2%, CF2 +12.2%), where every other
family is flat-to-negative -- SMC's own baseline is markedly worse there (866.9 mrad, ~3.3x backstepping's) so there is real error
for the residual to remove, unlike the already-tuned baselines; (c) LQR and MPC show a large baseline (not CMG-caused) blowup on CF2
Hardstep specific to the linear-quadratic family (2100-2200 mrad, ~8x backstepping's; rotor-sat 0.83-0.89), consistent with an
under-actuated linear law meeting CF2's small torque limits on a 63-111 deg step it was not designed for -- CMG neither meaningfully
helps nor hurts it there (-0.7%/-1.8%); (d) NMPC is the one family with a net-negative X2 geometric mean, driven by Roll (+3.8%, far
below every other family's +59-78% there) and Yaw360 (-57.9%). Plausible mechanism, not confirmed: NMPC's baseline updates at 100 Hz
and holds between updates, so the residual (which updates every simulation step) sees a staircase u0 rather than the smooth signal
every other family produces -- flagged, not resolved, and not swept into the aggregate without the caveat.

**Disposition.** Per CONTROLLER_EXTENSION_DECISION.md's own recommendation and my independent agreement (both written before this
result), this is Stage A only (interface portability) and is not proposed for the 6-7 page ACC submission beyond at most one
sentence; Stages B (matched-uncertainty/disturbance) and C (controller-native residual redesign) remain next-paper/journal scope.

**Certification addendum (2026-09-24, same day, written after the results above, before any further experiment).** Full report:
`REPORT_A5_CERTIFICATION_2026-09-24.md`. Two checks closing this amendment:

1. *Backstepping unified onto the same pipeline.* The backstepping/pd row above was, at the time it was first reported, sourced from
   the older sealed `run_final_robustness.py` runs rather than the new `run_controllers_gated.py` runner (justified then by the
   proven 1e-15-level algebraic identity). `run_campaign_a5_backstepping.py` re-ran all 20 backstepping/pd cells (2 platforms x 5
   missions x 2 arms) through the identical new pipeline the other five families use, and diffed every cell against the sealed data:
   worst relative deviation across all 20 cells = **0.00e+00** (bit-exact). `analyze_a5.py` was updated to read this row from the
   uniform new location; the headline table (section above, `results/A5_CONTROLLERS_RESULTS.md`, `results/a5_numbers.json`) is now
   sourced identically across all six families and unchanged numerically.
2. *Proposition 1(iii) (exact recovery at beta=0), empirically re-checked for the four genuinely new families.* `certify_beta0_recovery.py`
   ran classical vs. CMG-at-beta=0 for lqr/x2/hard45, smc/cf2-rotor/hardstep, mpc/x2/full3, and both of NMPC's flagged-anomalous
   missions (nmpc/x2/roll, nmpc/x2/yaw360), diffing `qerr_true_mean_rad` bit-for-bit:

   ```
   family  platform  mission      classical      CMG beta=0    rel diff
   lqr     x2        hard45      15.654757275   15.654757275   0.00e+00
   smc     cf2-rotor hardstep   772.179640800  772.179640800   0.00e+00
   mpc     x2        full3       18.259169930   18.259169930   0.00e+00
   nmpc    x2        roll         0.386120410    0.386120410   0.00e+00
   nmpc    x2        yaw360       3.949386716    3.949386716   0.00e+00
   ```

   All five: 0.00e+00. Because Prop. 1 makes no assumption on how u0 is computed, this is the expected outcome, not a new
   theoretical claim -- the value of running it is confirming the *implementation* (the new dispatch in `run_controllers_gated.py`)
   does not silently violate the proof for control laws it had never been exercised against before today. Deliberately included
   NMPC's two anomalous missions: exact recovery holding there isolates the A5 NMPC net-negative finding (finding (d) above) as a
   *dynamic interaction of the learning residual at nonzero beta*, not an architectural or implementation defect.

**Amendment A5 status: CLOSED.** Both certifications pass at 0.00e+00. No further A5 experiments are planned. Per Gandhi's explicit
instruction (2026-09-24), this closes the experimental/research phase of the controller-portability study; remaining work is
figures, tables, and manuscript incorporation.

**Correction addendum (2026-09-25): finding (d)'s NMPC anomaly was an experimental-setup artifact, not a property of NMPC.**
Requested by Gandhi ("Is weird what happened in NMPC, when MPC is working perfectly. Review here, what is happening").
Full account, including a hypothesis that was tested and found wrong before the real cause was: `AUDIT_NMPC_HOLD_RATE_2026-09-25.md`.
Summary: `run_campaign_a5.py`'s NMPC arm carried `--baseline-rate-hz 100` (a 100 Hz zero-order-hold on the baseline command),
reused from an older, unrelated, NMPC-only exploratory setting -- no other family, MPC included, was run with any hold (default
0 = full rate). A two-way ablation on X2 Roll/Yaw360 confirmed the hold itself, not NMPC's predictive/rollout nature, causes the
anomaly: removing it from NMPC restores the 40-78% band every other family shows (Roll +3.8%->+67.6%, Yaw360 -57.9%->+41.8%);
imposing the identical hold on MPC (a non-predictive fixed-gain law) reproduces the same failure almost number-for-number
(+69.7%->+3.6%, +42.6%->-55.0%). This overturned an earlier, more specific hypothesis (NMPC's internal forward-model rollout
never simulates the residual it will be augmented with, so its own logged one-step prediction-error self-check blows up 30-86x
when CMG is active) -- that self-check result was real and is explained in the audit, but the ablation showed it is a symptom of
the longer hold window, not an independent cause. All 20 NMPC cells (both platforms, all 5 missions, both arms) were re-run at
full rate, matching every other family's methodology, in `results/a5_controllers_nmpc_corrected/` (original 100Hz-hold data kept
on disk, untouched, for the audit trail; `analyze_a5.py` updated to read the corrected location).

**Final, corrected A5 headline (both platforms, geometric mean over 5 missions):**

| family | X2 | CF2 |
|---|---:|---:|
| PD+ff (backstepping) | +37.3% | +22.4% |
| PID+ff (ki=.3) | +36.7% | +22.4% |
| LQR | +31.1% | +22.4% |
| SMC | +43.8% | +26.6% |
| MPC | +33.4% | +22.7% |
| **NMPC (corrected)** | **+31.9%** (was -3.9%) | **+21.7%** (was +21.8%, unchanged) |

**All six families are now net-positive on both platforms. Finding (d) is superseded: there is no remaining exception in
Amendment A5.** This is a corrected experimental setup producing a different answer, not a reinterpretation of the same data.
Disposition unchanged (Stage A only, at most one sentence for the ACC submission -- simpler now: "all six" instead of "5 of 6");
the resolved mechanism (matching a predictive controller's own forward model to whatever augments its output at runtime) is a
well-scoped, concrete Stage-C item for the journal.
