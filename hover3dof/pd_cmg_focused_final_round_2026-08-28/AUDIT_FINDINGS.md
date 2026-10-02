# Read-only audit findings

Result cutoff: 2026-08-28 after run
`online-pes-adaptive_armed_20260828_112637` appeared (107 result folders).
The source progress note changed concurrently at 11:28:33 while this audit was
running; that later note was read and is handled explicitly below. Existing
source, documentation, and result files were not edited by this audit.

## Executive conclusions

1. The Python `K_LQR` matrix correctly represents the vendor MATLAB LQR after
   swapping rows 3/4 into the physically verified `[Front, Back, Left, Right]`
   AO order. In torque coordinates it is exactly diagonal PD.
2. The current CMG hardware path is not yet a one-to-one port of the MuJoCo
   architecture. MuJoCo learns a 3-axis torque residual; the hover runner learns
   four motor-voltage residuals after actuator clipping.
3. The documented Set-K “+38.83%” is not a valid matched-duration improvement.
   It used a 30 s adaptive run against the older 25 s classical yaw baseline,
   but yaw360 changes its trajectory when duration changes.
4. The matched data are two 30 s classical runs and three K runs. The progress
   note records that a person physically touched the rig during K run 112330 at
   28.3 s; its per-step pitch/roll discontinuity is much larger than every other
   matched yaw run. Treating this as a documented external-intervention invalid
   run leaves two clean K runs.
5. On the clean subset, classical mean error is 6.031° ± 0.010 and K is
   5.879° ± 0.074: a descriptive +2.53%. Classical peak error is
   8.798° ± 0.105 and K is 8.554° ± 0.092: a descriptive **+2.77%**, because
   lower peak error is better. The current progress note has the sign of this
   peak comparison reversed when it calls -2.8% “slightly worse.”
6. The all-recorded-runs sensitivity analysis, retaining the touched run, gives
   only +1.22% in mean and -20.0% in peak. Both the clean result and this
   sensitivity result should be preserved; n=2 clean per controller is not yet
   paper-level statistical verification.

## MATLAB-to-Python LQR replication

Verified against:

- vendor `setup_lab_hover.m`: amplifier gain 3, 24 V amplifier limit, 10 V
  DAC limit, 20 Hz/0.8 rate filter, 2 V bias, Q and R;
- vendor `HOVER_ABCD_eqns.m`: state order and four-motor input matrix;
- vendor `config_hover.m`: `Kt`, `Kf`, arm length, inertias, encoder signs;
- current Python runner: tare, rate filter, channel reorder, bias, clipping.

The matrix identity `G @ K_LQR = [diag(Kp), diag(Kd)]` verifies the gain and
row-order logic independently of comments in the code.

Important remaining implementation qualifications:

- the Python loop timestamps data as `k/200`, not measured wall-clock time, so
  loop jitter/overrun is not observable in the trace;
- the runner has `try/finally` zeroing but no configured Q8 watchdog, stale-data
  trip, mechanical-angle abort, or loop-deadline abort visible in this code;
- the safety checklist still contains stale statements (“no hardware entrypoint”
  and unchecked prerequisites) even though many armed runs now exist;
- `summary.json` does not record saturation fractions, per-axis error metrics,
  residual statistics, gate statistics, timing jitter, or final decoder weights.

## Why the 30 s yaw comparison is confounded

The yaw360 reference is

\[
\psi_d(t)=2\pi(3s^2-2s^3),\qquad s=t/T.
\]

Its maximum commanded rate is

\[
\max|\dot\psi_d|=3\pi/T.
\]

Changing T from 25 s to 30 s lowers peak command rate from 21.6°/s to 18.0°/s,
a 16.7% easier trajectory. Thus “longer time to learn” and “slower mission” are
inseparable in the present mission generator.

Recorded evidence:

| Run | Duration | Controller/config | Mean | Max |
|---|---:|---|---:|---:|
| classical_armed_20260827_232330 | 25 s | classical | 9.696° | 17.377° |
| online-pes-adaptive_armed_20260828_111307 | 30 s | K | 5.931° | 8.489° |
| classical_armed_20260828_112257 | 30 s | classical | 6.038° | 8.724° |
| online-pes-adaptive_armed_20260828_112330 | 30 s | K repeat | 6.114° | 14.569° |
| classical_armed_20260828_112604 | 30 s | classical repeat | 6.024° | 8.872° |
| online-pes-adaptive_armed_20260828_112637 | 30 s | K repeat | 5.826° | 8.618° |

The first K value only yields 38.83% if compared with the mismatched 25 s
classical run. Relative to the mean of the two 30 s classical runs, the three K
mean errors correspond individually to +1.66%, -1.38%, and +3.40%. The clean
K subset (runs 111307 and 112637) gives +2.53% mean and +2.77% peak improvement.
The all-run sensitivity gives +1.22% mean and -20.0% peak. With n=2 clean per
controller and nonrandom session ordering, these remain diagnostics rather than
confirmatory statistics.

### Contaminated-run handling

The external touch is a valid exclusion reason because it is unrelated to
controller performance and has an observable trace signature. Record the reason,
run ID, time, and objective discontinuity threshold in the experiment ledger.
For future runs, define invalidation rules before seeing aggregate outcomes. In
the paper/report, show clean statistics and an all-recorded-runs sensitivity
line so the exclusion is transparent.

## Set L and Set M

Set L (full3) produced 14.908° mean / 39.589° max and is clearly poor relative
to the historical 25 s classical cluster (~12.23–12.46° mean, ~28.52–28.60°
max). It supports rejecting that configuration, but not locating a precise
optimum from one run.

Set M (hard45) produced 12.758° / 31.927°. Historical 25 s classical hard45
runs are about 12.87–12.95° / 31.73–31.84°. The mean change is small and the
peak is not improved; this is consistent with “no resolved benefit,” not a
settled +0.99% scientific effect.

## Concurrent documentation issue

`PROGRESS_2026-08-27.md` changed from SHA-256
`4ead2db55226522e1aa876f17286081faecec075f8c6c152d0d357be6fd1d516`
to `8b1969766b70fc8b7fa95a71fc77792d6168e834e29f3fb68ef0b82befc21d18`
at 11:28:33 while this read-only audit was in progress. That update correctly
catches the duration confound and records the physical-touch exclusion. Its
remaining issues are the reversed peak-error sign, language stronger than n=2
supports (“carefully verified”), and stale open-item text that still calls the
already executed Round 3 “planned, not yet run.”

## Result-reporting rule

For every claim, compare only runs with identical mission, duration, code hash,
rate, baseline, and session conditions. Use interleaved baseline/adaptive pairs
and at least 3–4 repeats per condition. Report mean±standard deviation and both
mean and peak error. Tuning runs can motivate a candidate but cannot also serve
as its confirmatory evidence.
