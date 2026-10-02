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

The exact TNNLS reviewer letter was not located in this workspace during this pass. The work addresses
the remembered/core concerns (novelty, exact event definition, gradient legitimacy, stability,
ablation, baselines, efficiency, reproducibility), but no response should say a specific reviewer
comment is closed until the verbatim letter is found and mapped line by line.

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
8. Find the verbatim TNNLS reviews and build a reviewer-comment → equation/code/experiment table.

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
