# Decision log

## 2026-09-10 — Separate P4 from the existing paper portfolio

P1's continuation contract says not to turn the learning paper into a control paper. The new work is
therefore a sibling P4 project with a local dependency on the P1 Julia package.

## 2026-09-10 — Use one equation family, multiple parameter regimes

The initial study varies intrinsic HyperLIF parameters rather than mixing unrelated neuron equations.
This directly tests whether one continuous-reset family spans useful operating regimes.

## 2026-09-10 — Use upcrossings as the event

Historical `events_per_sample` values in the old Python stack were threshold occupancy. P4 uses the
P1 upward-crossing definition and reports occupancy separately.

## 2026-09-10 — Preserve the naive high-reactivity failure

The first candidate produced high occupancy with almost no repeated upcrossings. The result is kept
as evidence that parameter labels do not establish firing regimes. A label-free synthetic calibration
selected a stronger-reset candidate.

## 2026-09-10 — Calibrate activity without labels or test accuracy

Input gain is calibrated on training-only signal dynamics and target event bands. Dataset labels and
test performance are excluded so the activity definition does not become a hidden hyperparameter
search on the test set.

## 2026-09-10 — Start with recognition before robotics

SHD provides the only exact local cache and the existing P1 train/test contract. Recognition first
tests population complementarity and activity regulation cheaply. Robot control is gated on matched
recognition evidence and a production safety solver.

## 2026-09-10 — Treat safety as a separate supervisory layer

Plant viability cannot be delegated to neural firing homeostasis. The neural controller proposes an
action; an independently checked safety filter modifies it when required. The current cyclic
halfspace projection is a reference implementation only.


## 2026-09-10 (second session) — Replace per-regime input gain with one shared gain

Measurement showed that per-regime `input_scale` does not set the firing regime on the SHD
cache: every regime saturates at the same crossing ceiling, and two of the four previously
calibrated gains were search-grid boundary artifacts. `shd_shared_gain_regimes` uses one gain
(default 1.4) inside the unsaturated window so the intrinsic parameters set the regime, which
is what the heterogeneity hypothesis claims, and so that populations no longer differ in input
signal-to-noise. `shd_calibrated_regimes` is kept, not deleted, as the record of the failure.

## 2026-09-10 (second session) — Re-derive target rate bands from measurement

The original bands came from the synthetic constant-current atlas, where burst reaches 0.49.
On SHD at a non-saturating gain the burst regime reaches roughly 0.022, so the old band
midpoint of 0.17 was unreachable and drove the homeostatic offset into its clamp. The bands in
`shd_shared_gain_regimes` are ordered, non-overlapping, and inside the measured envelope.

## 2026-09-10 (second session) — Three budget-matched model families

`--model` selects `heterogeneous`, `ensemble` (four populations at the bank's mean parameters),
or `homogeneous` (one population carrying the whole hidden budget at mean parameters). All hold
total hidden state equal; effective parameter counts agree to within the extra readout biases
and mixer logits the multi-population families need (63 parameters out of ~179k at hidden 64).
`ensemble` exists because heterogeneous-versus-homogeneous alone confounds heterogeneity with
plain ensembling; `ensemble` is the control that separates them.

## 2026-09-10 (second session) — Report effective parameter count

`init_parameters` always allocates recurrent, delay, and dendritic blocks even under `:dense`,
where `W_rec` is never read. The raw count therefore grows with the square of hidden width and
makes one wide population look larger than four narrow ones for parameters neither model uses.
Budget matching is now stated on the parameters the declared architecture actually reads.

## 2026-09-10 (second session) — Detect vacuous homeostasis pairings

Threshold offsets were applied only after each epoch's validation evaluation, so a run whose
best checkpoint was epoch 1 carried the untouched reference thresholds and was numerically
identical to its homeostasis=false control. The runner now records `homeostasis_effective` and
warns when this happens, and `--homeostasis-interval` allows the slow rule to act within an
epoch so that a paired comparison is not vacuous by construction.
