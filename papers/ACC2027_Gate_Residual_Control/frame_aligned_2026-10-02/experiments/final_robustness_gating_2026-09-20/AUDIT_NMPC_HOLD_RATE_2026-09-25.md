# Audit: the A5 NMPC anomaly was a leftover experimental-setup inconsistency, not a real finding (2026-09-25)

Requested by Gandhi: "Is weird what happened in NMPC, when MPC is working perfectly. Review here, what is
happening." Closes the open caveat in `REPORT_A5_CERTIFICATION_2026-09-24.md` finding (d) ("plausible mechanism,
not confirmed"). The mechanism is now confirmed, and it is a different, simpler one than first suspected -- and
it is fixable, not a property of NMPC as a control law. **All six A5 families are now net-positive on both
platforms; there is no remaining exception.**

## 1. What was flagged

Amendment A5's original NMPC row was net-negative on X2 (geo -3.9%), driven by Roll (+3.8%, versus +59-78% for
every other family) and Yaw360 (-57.9%, versus +40-42% for every other family) -- while MPC, a similarly-named
family, was solidly positive everywhere (X2 geo +33.4%). The original disposition (PREREGISTRATION.md sec. 14)
disclosed a hypothesis -- NMPC's baseline updates at 100 Hz and holds between updates, producing a staircase u0
that the every-step residual might fight -- but flagged it explicitly as "plausible, not confirmed."

## 2. First lead: a real but, it turns out, misleading correlate

`AdvancedBaseline` logs its own internal one-step-ahead self-check for NMPC specifically
(`nmpc_pred_err_mean_deg`, in `baseline.stats` of every summary.json): it compares what NMPC's forward-model
rollout predicted the attitude would be one hold-period ahead against what actually happened. Reading this
already-logged field for all 5 X2 missions (classical vs. CMG-gated, both already on disk from the original A5
run) showed:

| mission | pred. err, classical | pred. err, +CMG | ratio | qerr baseline->CMG |
|---|---:|---:|---:|---|
| Roll | 0.000108 deg | 0.003163 deg | 29x | 0.345->0.332 mrad (+3.8%) |
| Full3 | 0.001698 deg | 0.001859 deg | 1.1x | 10.07->9.00 mrad (+10.6%) |
| Hard45 | 0.001984 deg | 0.001699 deg | 0.9x | 10.51->9.11 mrad (+13.3%) |
| Hardstep | 0.011566 deg | 0.013029 deg | 1.1x | 267.5->275.3 mrad (-2.9%) |
| Yaw360 | 0.000036 deg | 0.003143 deg | **86x** | 0.200->0.317 mrad (-57.9%) |

Torque was nowhere near saturated when this happened (rotor-sat = box-sat = 0.0 on Roll/Yaw360), ruling out
clipping. This looked like a clean mechanistic story: NMPC is the *only* one of the six A5 families whose control
law depends on an internal forward-model rollout (`_nmpc()` in `run_mujoco_nef_baselines.py` scores candidate
torques by RK4-simulating the closed loop `nmpc_horizon` steps ahead); every other family, "MPC" included
(despite the name, it reduces at runtime to a fixed closed-form gain computed once in `__init__` -- an
instantaneous state-feedback law, not a re-planner), computes torque as a function of the current state only.
The hypothesis: NMPC's rollout only forward-simulates its own candidate torque, never candidate + residual, so
its forecast goes stale the moment the residual is non-negligible -- and this floor is roughly constant in
absolute terms (~0.0017-0.0032 deg) across missions, invisible against Full3/Hard45/Hardstep's 10-270 mrad of
real baseline error, but comparable to or larger than Roll/Yaw360's already-near-zero baseline error (0.2-0.35
mrad), flipping the sign there.

This was reported to Gandhi as the leading hypothesis, explicitly labeled unconfirmed, with a stated prediction
for the ablation about to run: removing the update-rate hold should *not* fully fix it, since the rollout's
blindness to the residual has nothing to do with hold rate.

## 3. The decisive test: a two-way ablation, and the prediction above was wrong

`audit_nmpc_anomaly_2026-09-24.py`, X2 Roll + Yaw360, classical + CMG-gated, 4 cases:

| case | Roll: baseline->CMG | Delta | Yaw360: baseline->CMG | Delta |
|---|---|---:|---|---:|
| NMPC, as originally run (100 Hz hold) | 0.345->0.332 mrad | +3.8% | 0.200->0.317 mrad | -57.9% |
| **NMPC, hold removed** (`--baseline-rate-hz 0`) | 0.348->0.113 mrad | **+67.6%** | 0.200->0.117 mrad | **+41.8%** |
| MPC, as originally run (no hold) | 0.410->0.124 mrad | +69.7% | 0.233->0.134 mrad | +42.6% |
| **MPC, same hold imposed** (`--baseline-rate-hz 100`) | 0.407->0.393 mrad | **+3.6%** | 0.233->0.361 mrad | **-55.0%** |

Both directions agree almost exactly with each other and with the corresponding NMPC/MPC-native numbers they
mirror. Removing NMPC's hold restores it to the same 40-78% band every other family occupies (its Yaw360 result,
+41.8% at 0.117 mrad, is close to bit-identical to backstepping's and LQR's own Yaw360 results -- consistent with
`nmpc_nonzero_offset_fraction: 0.0` in the logged stats, meaning the grid search never picks a nonzero offset on
these gentle missions, so NMPC's law *is* the same instantaneous backstepping-style law here once the hold is
gone). Imposing the identical hold on MPC -- which has no forward-model rollout at all -- reproduces NMPC's
original failure almost number-for-number.

**Conclusion: the cause is the 100 Hz zero-order-hold itself, not NMPC's predictive machinery.** The
prediction-error self-check in sec. 2 was a real, measurable symptom (a longer hold window makes any one-step
forecast staler, residual or not) but not an independent cause -- a plausible-looking mechanism that a direct
test overturned. This is disclosed here exactly as it happened, prediction and all, rather than only reporting
the version that turned out to be right.

## 4. Where the hold came from

`run_campaign_a5.py`'s `FAMILY_ARGS["nmpc"]` included `--baseline-rate-hz 100`, reused from a prior validated
*exploratory, NMPC-only* setting (`baselines_2026-09-10/stretch/nmpc/`, PREREGISTRATION.md sec. 14) because NMPC
was the only family that setting had ever been exercised with before. No other family's `FAMILY_ARGS` set this
flag (default 0.0 = every sim step), including MPC. It was carried over as "the known-working NMPC setting," not
chosen with the CMG-PES portability question in mind -- an experimental-setup inconsistency between families, not
a deliberate, defensible asymmetry.

## 5. Corrected re-run

`run_campaign_a5_nmpc_corrected.py`: all 20 NMPC cells (2 platforms x 5 missions x 2 arms), identical to every
other A5 family's methodology, `--baseline-rate-hz` at its default (0, full rate). Written to
`results/a5_controllers_nmpc_corrected/`; the original 100Hz-hold data in `results/a5_controllers/nmpc/` is left
on disk, untouched, for the audit trail -- not read by `analyze_a5.py` any longer.

| platform | mission | old (100 Hz hold) | Delta | new (full rate, adopted) | Delta |
|---|---|---|---:|---|---:|
| X2 | Roll | 0.345->0.332 mrad | +3.8% | 0.348->0.113 mrad | **+67.6%** |
| X2 | Full3 | 10.067->8.998 mrad | +10.6% | 10.074->8.818 mrad | +12.5% |
| X2 | Hard45 | 10.508->9.108 mrad | +13.3% | 10.518->9.125 mrad | +13.2% |
| X2 | Hardstep | 267.474->275.342 mrad | -2.9% | 269.661->274.697 mrad | -1.9% |
| X2 | Yaw360 | 0.200->0.317 mrad | -57.9% | 0.200->0.117 mrad | **+41.8%** |
| CF2 | Roll | 0.573->0.236 mrad | +58.8% | 0.577->0.239 mrad | +58.7% |
| CF2 | Full3 | 7.055->6.557 mrad | +7.1% | 7.071->6.573 mrad | +7.0% |
| CF2 | Hard45 | 6.298->6.039 mrad | +4.1% | 6.304->6.072 mrad | +3.7% |
| CF2 | Hardstep | 262.020->262.139 mrad | -0.0% | 260.680->260.532 mrad | +0.1% |
| CF2 | Yaw360 | 0.084->0.067 mrad | +20.3% | 0.084->0.067 mrad | +20.3% |

CF2 barely moves (it was never the platform showing the anomaly); every X2 cell not already near-perfect is
essentially unchanged; the two floor missions on X2 are transformed.

**Corrected geometric means: X2 +31.9% (was -3.9%), CF2 +21.7% (was +21.8%, unchanged within rounding).**

Ran overnight unattended on Gandhi's machine; 18 of 20 cells completed in 33-40 min each, two (CF2 Full3/Hard45
classical+CMG) took ~9 hours each -- almost certainly background resource contention on shared/rented hardware
over the unattended stretch, not a correctness issue: those two cells' numbers are nearly identical to the
original 100Hz-hold run's (7.055 vs 7.071, 6.298 vs 6.304 mrad), as expected since removing the hold barely
changes the classical arm.

## 6. Final A5 headline (both platforms, geometric mean over 5 missions, all six families now uniform methodology)

| family | X2 | CF2 |
|---|---:|---:|
| PD+ff (backstepping) | +37.3% | +22.4% |
| PID+ff (ki=.3) | +36.7% | +22.4% |
| LQR | +31.1% | +22.4% |
| SMC | +43.8% | +26.6% |
| MPC | +33.4% | +22.7% |
| **NMPC (corrected)** | **+31.9%** | **+21.7%** |

**Every one of six structurally different controller families improves on both platforms. There is no remaining
exception in Amendment A5.** This is a strictly better, cleaner result than what was reported and registered on
2026-09-24 -- not a reinterpretation of the same data, a corrected experimental setup that changed the answer.

## 7. Disposition

Supersedes the "(d) NMPC nets negative on X2... flagged, not resolved" finding in PREREGISTRATION.md sec. 14 and
`REPORT_A5_CERTIFICATION_2026-09-24.md` sec. 6. Still Stage A (interface portability) only, still at most one
sentence for the ACC submission -- the sentence gets simpler now ("all six" instead of "5 of 6"). A well-scoped
Stage-C item for the journal falls out of this for free: matching a predictive controller's own internal forward
model to whatever augments its output at runtime is a real, general design consideration for pairing a
receding-horizon baseline with a learned residual -- distinct from, and next to, the rate-mismatch fix here.

## 8. Minor, unrelated observation

`summary.json`'s `baseline.name` / `baseline.implementation` fields are a stale, hardcoded label
("PD + desired-rate feedforward" / "AdvancedBaseline(backstepping, no model feedforward)") left over from before
A5 made the baseline family selectable -- present regardless of which family actually ran. Does not affect any
number (confirmed correct via `nmpc_updates` counts and the actual physics in every case above); only misleading
if someone reads the raw JSON's descriptive strings without cross-checking `baseline.stats`/the run command.
