# HyperLIF research continuation contract

This file is the handoff for Claude, Codex, or any later research agent. Read it completely before
changing equations, code, experiments, or manuscripts. The working date for this handoff is
2026-09-09; the near-term target is preliminary results on Thursday 2026-09-10 and a presentation
on Friday 2026-09-11.

## Read first

1. `HYPERLIF_THEORY_LEARNING_AND_RESEARCH_PROGRAM_2026-09-09.md` is the current mathematical and
   literature synthesis.
2. `code/julia/learning/src/HyperLIFLearning.jl` is the current three-mode reference implementation.
3. `code/julia/learning/test/runtests.jl` contains the mathematical/autodiff contracts.
4. `code/julia/portable/` is the earlier dependency-light parity implementation.
5. `THREE_STAGE_DEVELOPMENT_REPORT_2026-09-09.md` records implementation status, limitations, and
   the experiment plan.

## Current research priority (2026-10-06)

The current user request prioritizes single-neuron mathematics and two- to
three-cell learning mechanisms under limited local memory. The continuation
notes in `theory/` and their standard-library Julia scripts are the active
starting point. The September HPC grid below is historical project context;
do not treat it as the next action for this memory-limited phase. Preserve
negative and no-event findings while comparing PES, exact internal-weight
sensitivity, and local approximations.
`theory/HH_JAXLEY_BASELINE_EVIDENCE_2026-10-06.md` audits the published HH-type
learning evidence and defines the small matched HH/HyperLIF/stateful-LIF
comparison. Use the final published Jaxley figures (94.2% MNIST and 607
retina parameters), not preliminary talk figures. Do not compare accuracy
across unlike datasets as if they were a controlled benchmark.
`theory/HH_HYPERLIF_TINY_COMPARISON_2026-10-06.md` now records the first
canonical-HH/HyperLIF/adaptive-leaky two-cell decoder experiment, an HH
initial-basin counterexample, and validated constant-memory HH forward
sensitivity. Its operating currents and feature budgets are not yet a
matched benchmark; preserve the negative equilibrium-start transfer result.
`theory/COUPLED_WEIGHT_HORIZON_AND_GATE_2026-10-06.md` is the current
coupled-weight continuation. Exact and detached local traces were checked
in canonical HH and ACC-type HyperLIF; short-to-long teacher-weight
learning succeeds in tested HH regimes, while saturated gate-only
eligibility vanishes late. Treat this as one-parameter teacher recovery,
not independent-task learning. The next control is an external target
with a coupled two-state leaky baseline and matched readout budget.
`theory/COUPLED_EXTERNAL_DELAY_AND_BASIN_TRANSFER_2026-10-06.md` now adds
that independent 20 ms delay target for coupled HyperLIF and a coupled
continuous adaptive-leaky baseline. The gamma=2 local connection can
improve a single validation phase while switching to a different gate
basin and failing severely on a fresh test phase, despite zero events.
Do not infer external-task success from the teacher-weight recovery.
`ADVISOR_BRIEF_FRIDAY_2026-10-09.md` is the current advisor-facing
conclusion, seven-slide talk outline, covered/open checklist, and
claim-discipline guide for Friday 2026-10-09.
`theory/ACC_CLOSED_LOOP_STABILITY_OPTIONS_2026-10-06.md` separates the
ACC paper's proved bounded interface from a proposed regional practical
tracking theorem. It includes the rotor-headroom condition and the
disturbances needed for a valid plant-level claim. Two plot artifacts in
`theory/results/current_*_2026-10-06.png` summarize readouts and learning
limits from saved exploratory CSVs; no closed-loop theorem is yet proved.

Do not treat old comments or filenames as evidence. In particular, several legacy Julia files under
`code/apex_julia/` used phrases such as “fully differentiable,” “A-stable,” or “guarantees no dead
band” without a complete proof. Those are historical implementations, not the claim authority.

## Scientific invariant

Always distinguish these quantities:

- **Readiness**: the smooth state `r(t)` in `[0,1]`.
- **Threshold occupancy**: `1[v_k >= theta]` at a sampled time. This is not a spike count.
- **Event/upcrossing**: `1[v_{k-1} < theta and v_k >= theta]`.
- **Event time**: an interpolated crossing time, valid for differentiation only while event topology
  is unchanged and the crossing is transversal.

The historical PyTorch/snnTorch HyperLIF architecture returns threshold occupancy under a variable
named `spk`; legacy `events_per_sample` values from that stack are occupancy. The portable Julia
implementation and the new learning package explicitly support/report upward crossings. Never mix
these semantics in a table or efficiency claim.

## Three learning modes

### Continuous-state learning

Use reverse-mode differentiation through the discretized voltage, readiness, conductance,
adaptation, and dendritic states. The adaptive magnitude is smoothed as
`sqrt(I^2+epsilon^2)-epsilon`; finite sigmoid-argument clamps still make the numerical program only
piecewise smooth. Away from clamp boundaries, AD gives the derivative of this discretized program,
not automatically the derivative of the continuous-time solution. Hard events may be measured but
are diagnostic; they are not differentiated.
This is the strongest default when a tuned HyperLIF is nearly non-spiking. It converts apparent
“failure to spike” into an analog recurrent representation, but it does not justify calling the
system event-driven.

### Surrogate-event learning

The forward observable is the hard upward crossing. The backward pass uses the declared fast-
sigmoid pseudo-derivative around the post-update voltage threshold. Call this a surrogate gradient,
not an exact gradient or a derivative of the Boolean event map. Report slope sensitivity and compare
pure `spike_count` with the scaffolded `hybrid_zr` readout.

### Event-time learning

For a crossing within `[t_k,t_k+dt]`, use linear interpolation

`t* = t_k + dt (theta-v_k)/(v_{k+1}-v_k)`.

This derivative is only local to a fixed event sequence. Report no-event fraction and minimum
crossing speed; grazing events are ill-conditioned. Compare pure `first_event_time` against
`hybrid_time_vr`. The hybrid is an optimization continuation/scaffold, not a pure temporal code.

## Model hierarchy

- `cell=:hyperlif`: two states `(v,r)` with fixed reset conductance scale.
- `cell=:adaptive`: two states `(v,r)` with input-dependent reset conductance scale. It is adaptive
  in the historical computational sense; do not imply spike-frequency adaptation.
- `cell=:next`: adds three stable dendritic filters (fast/medium/slow), combined by a learned convex
  softmax mixture, and a slow readiness-adaptation state. These are promising computational
  abstractions, not demonstrated biological mechanisms.
- `architecture=:dense|:recurrent|:delay`. Causal delay is deployable online; centered delay is an
  offline upper-bound ablation and must be labelled noncausal.
- The recurrent matrix is parameterized so its operator norm is bounded above by
  `recurrent_gain` via a conservative Frobenius bound. This bounds one linear operator; it does not
  prove contraction or global stability of the complete nonlinear recurrent cell.

## Mathematical claim discipline

- The readiness substep is the exact frozen-target solution and preserves `[0,1]` for an admissible
  initial state.
- The voltage substep is the exact frozen-conductance scalar affine solution. This does not prove the
  whole coupled discretization is exact, A-stable, or globally stable.
- Any claim about contraction, equilibria, bifurcation, passivity, ISS, Lyapunov stability, or global
  absence of a dead band requires explicit assumptions and a proof or numerical qualification.
- “No spike” can mean subthreshold information, dead activity, or a dataset/time-scale mismatch.
  Diagnose it; do not relabel it as success.
- Events/activity are not hardware energy. Only claim energy after device-specific power/latency
  measurement with an explicit accounting boundary.
- Capped subsets and the validation split are class-stratified and seeded. Test data are evaluated
  once after checkpoint selection by held-out validation accuracy. Do not select epochs or
  hyperparameters on the test split.
- Preserve negative results, failed seeds, NaNs, no-event runs, and noncausal ablations.

Update 2026-10-06: the exact TNNLS decision and reviewer letter is present at
`tnnls/TNNLS_reviews.pdf` (four pages). The reviewer-specific map and new PES
theory are in `theory/PES_SINGLE_NEURON_SMALL_NETWORK_2026-10-06.md`. Earlier
notes saying the letter was missing are historical and should not be repeated.
The letter is evidence of criticisms, not proof that any criticism is resolved.
The follow-on local fold certificate, decoder-rule comparison, and one-weight
recurrent sensitivity experiment are in
`theory/PES_CONTINUATION_FOLDS_AND_TINY_NETWORK_2026-10-06.md`.
That continuation also encloses canonical fixed/adaptive local linear
stability crossings and records a high-drive no-event adaptive regime.
The next ACC-specific result is
`theory/ACC_ABSORBING_LATCH_AND_PES_IDENTIFIABILITY_2026-10-06.md`:
for the supplied ACC parameters, a saturated high-readiness, no-event
rectangle is forward invariant for arbitrary bounded input current.
This gives a mathematical rank-loss obstruction for the clipped-readiness
PES decoder. Use this result when assessing any claim that these
parameters eliminate silent/dead regimes or guarantee PES learnability.
The same note includes a small independent-target feature map across
feedback and readout gains; it identifies candidate operating regions
for a fair next PES-versus-sensitivity comparison.
The follow-up multi-signal readout study is
`theory/MULTISIGNAL_READOUTS_GATE_MEMBRANE_CONDUCTANCE_2026-10-06.md`.
It tests raw/clipped gate, voltage, full and gate-only conductance,
reset current, derivatives, and combinations on same-time and delayed
targets. Its key distinction is that full conductance contains the
applied input directly, while raw gate adds useful temporal information
in the reduced-feedback operating regime.
`theory/GATE_OBSERVABILITY_DECODER_GRAM_BOUNDS_2026-10-06.md` now adds
finite-horizon local observability and finite-window decoder-Gram bounds.
The gate's observability margin can vanish quadratically with sigmoid
slope; a nearly constant gate also creates a near-null bias/gate decoder
direction even when other readouts predict the target well. This is a
mathematical limitation, not a new benchmark result.

## Commands

From `code/julia/learning`:

```bash
julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.test()'
julia --project=. preflight.jl "$HLL_CACHE"
julia --project=. grid.jl --profile=thursday --cache-dir="$HLL_CACHE" --bundle-count
bash submit.sh thursday
julia --project=. aggregate_results.jl "$HLL_JULIA_RESULTS"
```

The `thursday` profile is a screening matrix: every available `.h5` cache, three architectures,
three cells, three learning modes, one seed, three epochs, capped data. It is evidence of execution
and gross behavior, not a benchmark conclusion. The `serious` profile uses full data, five seeds,
40 epochs, pure and scaffolded event readouts, plus centered-delay as a labelled offline ablation.

One Julia process executes all modes for a fixed dataset/architecture/cell/seed bundle so the heavy
first-gradient compilation is amortized. On the current Windows CPU, the first reverse-mode compile
can take several minutes and gigabytes; do not estimate training throughput from that first step.

## Required next actions

1. Run the unit tests and one complete real-data smoke after any model change.
2. Verify CUDA and HDF5 caches with `preflight.jl` on an allocated GPU node.
3. Submit `thursday`; record the returned SLURM job ID in the development report.
4. Aggregate only completed JSON summaries; mark missing/failed cells explicitly.
5. Inspect event topology: upcrossings, occupancy, no-event fraction, crossing-speed conditioning.
6. Start `serious` only after the Thursday profile has no systematic failures.
7. Add matched LIF/ALIF and parameter/FLOP/latency controls before comparative performance claims.
8. Use the now-located verbatim TNNLS reviews and keep the reviewer-comment to
   equation/code/experiment table current as new evidence is obtained.

## Definition of done for a reported result

A result has a cache SHA-256, split sizes, seed, architecture/cell/mode/readout, event and gradient
semantics, parameter count, validation-selected epoch, one-shot test metrics, activity diagnostics,
device, wall time, and a saved checkpoint. A run without those fields is exploratory and must not be
quoted as a final benchmark.

Local status at handoff: 100/100 tests pass; the HDF5/CPU preflight passes; and the CUDA mechanism
preflight passes all three learning modes. A bundled real-SHD CUDA smoke also completed all three
modes and wrote checkpoints/JSON under `code/julia/learning/results/smoke_cuda`; its chance-level
accuracy is pipeline evidence only. Cluster-specific modules, caches, and scheduler submission remain
unverified until an actual allocation and SLURM job ID exist.
