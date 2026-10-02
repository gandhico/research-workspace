# HyperLIF three-stage development report

**Date:** 2026-09-09  
**Immediate milestones:** preliminary screening by Thursday 2026-09-10; presentation Friday
2026-09-11.  
**Scope:** neuron → architecture → learning, with a Julia-first implementation and HPC execution.

## Outcome of this development pass

A new Julia package now expresses the three requested learning regimes under one explicit numerical
contract:

| Learning regime | Forward information | Backward rule | Main limitation |
|---|---|---|---|
| Continuous-state | voltage/readiness/conductance states | AD of the discretized piecewise-smooth map | not intrinsically event-driven |
| Surrogate-event | hard upward crossings | declared fast-sigmoid pseudo-derivative | biased gradient; slope sensitive |
| Event-time | interpolated first upward-crossing time | local derivative at fixed topology | no-event and grazing singularities |

The package implements HyperLIF, the historical adaptive-gain HyperLIF, and an exploratory next cell;
each can be embedded in dense, recurrent, or delayed architectures. The next cell adds fast, medium,
and slow dendritic filters plus a slow readiness-adaptation state. The three filters are combined by
a learned convex softmax mixture, keeping the resulting drive inside their pointwise convex hull.
This is a testable computational abstraction inspired by multiscale processing, not a claim of
biological equivalence.

For recurrent architectures, the raw matrix is mapped to
`W_eff = recurrent_gain tanh(W_raw)/H`. Since the spectral norm is bounded by the Frobenius norm and
the latter is at most `recurrent_gain`, the recurrent **linear operator** has an explicit norm bound.
This is useful regularization but is not a contraction proof for the complete nonlinear dynamics.

## Mathematical contracts implemented

For readiness `r`, with a target `r_inf(v,a)` frozen over one step,

`r_(k+1) = r_inf + (r_k-r_inf) exp(-dt/tau_r)`.

Therefore `r_(k+1)` is a convex combination of `r_k` and `r_inf`, so `[0,1]` is invariant when both
are in `[0,1]`. For voltage, after freezing conductance `g_k >= 0`,

`dv/dt = -lambda_k v + b_k`,  
`v_(k+1) = exp(-lambda_k dt) v_k + (b_k/lambda_k)(1-exp(-lambda_k dt))`.

This exactly solves the scalar affine frozen-coefficient subproblem. It is not a proof that the full
coupled split map is exact or globally stable.

The historical adaptive law used `|I|`, which is nondifferentiable at zero. The new reference uses
the zero-preserving smooth magnitude `sqrt(I^2+epsilon^2)-epsilon`. Sigmoid-argument clamps still
introduce piecewise-smooth boundaries; “exact AD” therefore means the derivative of the implemented
discrete branch away from those boundaries, not an unrestricted continuous-time sensitivity claim.

An event is only

`z_k = 1[v_k < theta and v_(k+1) >= theta]`.

Threshold occupancy `1[v_k >= theta]` is logged separately. This corrects the most consequential
ambiguity in the historical architecture, whose output named `spk` was occupancy.

For event-time learning,

`t* = t_k + dt (theta-v_k)/(v_(k+1)-v_k)`.

The implementation logs the minimum crossing speed and fraction of event-producing neurons below a
transversality floor. The derivative is not represented as valid if event topology changes.

## Verification completed

- Julia package environment instantiated with Julia 1.12.
- 100 tests pass: seven learning/event primitives, 81 cell/mode forward-loss-gradient checks, and
  twelve architecture/configuration contracts.
- The local CUDA preflight passes forward loss and reverse-mode input gradients for continuous,
  surrogate-event, and event-time learning on the exploratory recurrent next cell. This validates
  GPU execution of the mechanism fixture; the cluster environment still requires its own preflight.
- The surrogate event has a hard zero/one forward value and a nonzero declared backward derivative.
- The event-time derivative agrees with finite differences within a fixed crossing topology.
- The SHD HDF5 cache contract was verified as 700 features × 20 time bins × 2,000 train samples and
  800 test samples, with 20 classes.
- A complete CPU smoke (dense HyperLIF, continuous `hybrid_vr`, hidden 12, one epoch, 14/2/16
  train/validation/test examples) wrote a checkpoint and provenance summary. Test accuracy was
  0.0625, which is chance-level and scientifically uninterpretable at this sample size. It measured
  5.125 true upcrossings/sample versus 49.875 threshold-occupancy states/sample, directly exposing
  the magnitude of the historical semantic mismatch. The no-event neuron/sample fraction was
  0.6354 and minimum observed crossing speed was 7.056 normalized-voltage units/s.
- A bundled real-SHD CUDA smoke then completed end to end for all three modes with hidden 24 and
  86/10/64 train/validation/test examples. All three obtained 0.046875 test accuracy (chance is 0.05),
  so there is no performance claim. The mechanism/provenance results were:

| mode/readout | parameters | validation accuracy | test loss | upcrossings/sample | occupancy/sample | no-event neuron fraction | wall s |
|---|---:|---:|---:|---:|---:|---:|---:|
| continuous / `hybrid_vr` | 18,620 | 0.00 | 3.8105 | 12.406 | 127.047 | 0.5592 | 127.3 |
| surrogate / `hybrid_zr` | 18,620 | 0.10 | 3.6411 | 11.891 | 121.891 | 0.5801 | 2.9 |
| event-time / `hybrid_time_vr` | 19,100 | 0.10 | 3.4258 | 11.469 | 118.219 | 0.5951 | 4.1 |

  The first mode's wall time contains first-gradient/GPU compilation; later modes reuse compiled code.
  This confirms that bundling is operationally important. It does not establish that one learning
  mode is more accurate than another.
- The Python HPC entry point was repaired so portable `--data-file` runs no longer import a missing
  dataset package, and architecture discovery now includes the real `code/src/arch` location.

The repaired Python entry point passes bytecode compilation. A local Python runtime test was not
possible because none of the available environments contains PyTorch; its dependency/runtime check
therefore remains part of the existing cluster Python preflight. This does not affect the independently
instantiated and executed Julia package.

The first optimized Julia reverse-mode compilation on the local CPU takes several minutes and several
gigabytes. That is an engineering limitation, not an algorithmic result. The HPC launcher therefore
bundles learning modes in one Julia process to amortize compilation. A future PackageCompiler sysimage
or a custom adjoint/scan is a worthwhile optimization.

## Result interpretation

The three modes answer different scientific questions and should not be reduced to a single ranking:

1. Continuous-state learning asks whether HyperLIF's smooth internal state is a useful representation,
   including in almost non-spiking regimes.
2. Surrogate-event learning asks whether hard crossing communication can be trained using a biased but
   practical pseudo-gradient.
3. Event-time learning asks whether timing carries usable information when crossings exist and are
   transversal.

Pure event-time learning has no useful local gradient for a neuron that never crosses. The
`hybrid_time_vr` readout is consequently included as a continuation/scaffold. It should be compared
against pure `first_event_time`, and it must not be presented as a pure temporal code. Similarly,
`hybrid_zr` tests whether smooth readiness rescues or complements sparse event communication.

## Thursday and serious HPC matrices

The `thursday` profile spans every HDF5 cache present at submission time:

- architectures: dense, recurrent, causal delay;
- cells: HyperLIF, adaptive HyperLIF, next cell;
- learning: continuous, surrogate-event, event-time;
- one seed, three epochs, hidden size 64;
- at most 1,024 training and 512 test samples.

This is a smoke/screening experiment. It can support statements such as “the pipeline ran,” “the
gradient remained finite,” or “this configuration produced/no produced crossings.” It cannot support
a state-of-the-art or statistically reliable ranking.

The `serious` profile uses all samples, five seeds, 40 epochs, pure and hybrid event readouts, and adds
centered-delay as a clearly labelled noncausal offline upper-bound ablation. Every job writes an
independent JSON summary and checkpoint. Hardware energy is null by design; activity statistics and
wall time are not relabelled as energy.

Future profile runs use seeded class-stratified capped subsets and a class-stratified validation
split. The already completed tiny smoke results above predate this refinement and used seeded random
subsets; they remain pipeline evidence only and should not be mixed with future profile summaries.

This serious grid is intentionally a **HyperLIF-family mechanism matrix**, not yet a superiority
benchmark. Matched Julia LIF/ALIF/PLIF or equally stateful continuous baselines are not implemented in
this package. Until those are added—or a byte-identical, semantics-matched baseline table is joined
from the validated PyTorch run—the matrix can compare learning regimes within the family but cannot
support “HyperLIF beats existing methods.”

## Reviewer-risk matrix

| Concern | Current response | Still required |
|---|---|---|
| Event definition | Upcrossing and occupancy are separate | re-audit all legacy tables |
| Gradient rigor | exact/surrogate/event-time rules explicitly separated | slope/topology sensitivity curves |
| Stability | invariant readiness and exact frozen scalar steps | coupled-system local/global analysis |
| Novelty/biology | next cell labelled computational abstraction | hypothesis-specific biological mapping |
| Fair comparisons | parameter counts and common caches logged | matched LIF/ALIF baselines and budgets |
| Efficiency | no energy claim; activity and wall time only | device power/latency measurement |
| Reproducibility | SHA-256, splits, seeds, checkpoint, JSON | cluster/container/module manifest |
| Statistics | serious plan uses five seeds | confidence intervals and paired tests |

The exact TNNLS reviewer text was not found in this workspace. The matrix above addresses the known
categories, but a formal rebuttal requires locating the letter and mapping each sentence to evidence.

## Files and commands

- Core: `code/julia/learning/src/HyperLIFLearning.jl`
- Tests: `code/julia/learning/test/runtests.jl`
- Single experiment: `code/julia/learning/train_hpc.jl`
- Matrices/bundling: `code/julia/learning/grid.jl`, `run_bundle.jl`
- Cluster: `code/julia/learning/preflight.jl`, `submit.sh`, `run_array.slurm`
- Aggregation: `code/julia/learning/aggregate_results.jl`
- Continuation contract: `AGENTS.md`

```bash
cd code/julia/learning
julia --project=. -e 'using Pkg; Pkg.test()'
julia --project=. preflight.jl "$HLL_CACHE"
bash submit.sh thursday
```

Record the SLURM job ID and cluster preflight output here after submission. Until that is done, the
correct status is **HPC-ready, not yet evidenced as submitted**.
