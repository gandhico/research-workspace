# Focused final round protocol

## Status correction

Sets K, L, and M were already executed before this audit. Do not rerun them as a
new tuning sweep and do not select a “winner” from their single-run deltas.

## Immediate decision

- **Yaw360:** the 38.83% claim must be withdrawn. Excluding the run with the
  documented physical touch, the matched 30 s clean subset is +2.53% in mean
  and +2.77% in peak error (lower is better), n=2 per controller. Retaining all
  recorded runs gives +1.22% mean and -20.0% peak. Report both views.
- **Full3:** reject Set L. Retain Set E only as a candidate selected by tuning.
- **Hard45:** Set M is practically tied with the classical cluster. Treat the
  present result as no resolved benefit at the tested authority.

## One mission, one scientific question

The next round should validate rather than tune:

| Mission | Fixed candidate | Question | Required matched baseline |
|---|---|---|---|
| yaw360 | K: beta .4, limit 3 V, lr 3e-4, k-error 2, 30 s | Does K improve a genuinely matched 30 s mission? | classical yaw360, 30 s, same session |
| full3 | E: beta .4, limit 3 V, lr 3e-4, k-error 4, 25 s | Does the selected candidate reproduce its small benefit? | classical full3, 25 s, same session |
| hard45 | M: beta .4, limit 3 V, lr 2e-4, k-error 3, 25 s | Is the effect distinguishable from repeatability? | classical hard45, 25 s, same session |

One adaptive run per mission is not enough unless a valid same-session baseline
already brackets it. The minimum useful block is `baseline → candidate → baseline`
for each mission; the paper-quality block is randomized/interleaved with at
least 3–4 clean candidate and 3–4 clean baseline repeats. Predefine external
intervention, mechanical contact, missed-deadline, and sensor-discontinuity
invalidation rules before the block starts.

## Acceptance criteria fixed before running

For a candidate to be called improved:

1. lower mean combined error across repeats;
2. no increase in peak combined error beyond baseline repeatability;
3. no higher zero/upper saturation fraction that indicates hidden authority
   trading;
4. no mechanical-limit event, deadline miss, or safety abort;
5. the 95% confidence interval or a paired nonparametric interval must not be
   represented as decisive if it spans zero.

## Architecture experiment after validation

Do not mix the proposed torque-space CMG redesign into this validation block.
First freeze and validate the existing motor-space candidate. Then test exactly
one architecture change: 3-channel torque-space CMG plus constrained allocation,
against the same explicit PD/LQR-equivalent baseline. This separates a scientific
architecture question from parameter tuning.

## Hardware boundary

This folder contains no armed command. Before another hardware session, reconcile
the stale checklist, verify the active board and E-stop, and add or independently
confirm watchdog, mechanical-angle aborts, and actual residual slew limiting.
