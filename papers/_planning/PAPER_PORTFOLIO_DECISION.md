# Paper Portfolio Decision

Date: 2026-07-19

## Executive Recommendation

Work toward **three manuscripts**, not five papers and not one overloaded resubmission.

The strongest portfolio is:

1. **P1 - HyperLIF Learning**: the main journal paper answering the TNNLS criticism about practical advantage, non-MLP architectures, multi-seed statistics, ablations, and efficiency.
2. **P2 - HyperLIF in Nengo / NEF**: the reference implementation, stability, parity, calibration, and Nengo capability paper answering the criticism about heuristic theory and implementation trust.
3. **P3 - Gate-State and Adaptive/Learned Residual Control**: one fused robotics/control journal or RA-L style paper. The fixed gate-state residual is the core contribution; Adaptive HyperLIF and learned-gate variants become the second layer only after experiments prove that they add something beyond fixed HyperLIF gate saturation.

This answers the advisor question: combine only what shares the same central claim, and separate papers when the evaluation domain, reviewer expectations, and contribution are different.

## Why Not One Large Paper

The old TNNLS paper was rejected partly because it tried to carry theory, biological framing, neuron novelty, and limited experiments all at once. The new evidence is much stronger, but the same danger remains if all results are merged into one giant manuscript.

The clean split is:

- P1 asks: does the neuron improve temporal learning and sparse efficiency under controlled ML experiments?
- P2 asks: is the neuron mathematically and numerically trustworthy inside Nengo/NEF?
- P3 asks: can the continuous gate state become a useful control residual, and when does adaptive or learned gating improve beyond fixed gate-state residuals?

## Readiness Estimates

### P1 - HyperLIF Learning: 94%

Evidence already strong:

- Multi-seed PyTorch runs.
- HyperLIF >= LIF in all reported architecture x dataset cells.
- Gate readout is meaningful where LIF gate readout is structurally blind.
- Sparse efficiency is a real mechanism, not a cosmetic metric.
- Draft manuscript exists in `08_HyperLIF_Architectures/paper/paper2_manuscript.md`.

Remaining:

- APEX GPU cross-framework validation now has a reviewer-safe calibration result. The Julia HDF5 ingestion, `[F,N,T]` data-topology gate, APEX engine import, CUDA check, loader smoke, bounded train/eval smoke, tuning grid, and 10-epoch 5-seed direct comparison now pass. Tuned HyperLIF/NSA (`beta=0.10`, `gamma=0.80`) beats matched dense LIF on the same SHD-wide HDF5 cache (`0.2490 +/- 0.0666` vs `0.2411 +/- 0.0778`) with lower test loss.
- A compact IEEEtran source package now exists under `08_HyperLIF_Architectures\paper_ieee` and builds successfully to a 5-page PDF.
- Stronger contemporary baseline evidence: PLIF and ALIF/LSNN are wired into the same harness, pass smoke, have a local five-neuron FF N-MNIST tiny preflight table, have an SHD-wide FF shortlist, and now have an SHD-wide `rsnn`/`delay` architecture shortlist. Final claim still needs the chosen full paper-grid table scope, or a clean statement that the shortlist is the baseline extension used for reviewer response.
- Final statistical reporting: mean, standard deviation or CI, paired seed tests, stability/failure counts for the final selected P1 tables.
- Add final paired/statistical tests, verify bibliography metadata, replace author/funding placeholders, and polish the IEEEtran source.

### P2 - Nengo / NEF Reference: 85%

Evidence already strong:

- IEEEtran manuscript and PDF exist.
- Python stable stepping and Nengo port match exactly.
- Depolarization-block onset and fixed-point claims have CSV-backed validation.
- Exponential stepping is stable and traceable to code.
- Capability matrix shows all nine NengoCore applications run.
- New calibration evidence and PES rate-matching results identify both strengths and limitations.
- Three-seed core capability preflight now completes 84/84 Nengo simulations with 0 failures for T001/T002/T023/T033 across seven NEF apps.
- The active manuscript source `paper/main.tex` now integrates the seed-preflight table and builds successfully to a 26-page PDF.

Missing:

- Decide whether to extend the three-seed preflight to the five-seed paper-grade sweep.
- Add NEF ensemble tuning/decoder validation for the final calibrated candidate.
- Frame OpenCL/Loihi/NengoDL as backend limitations, not as failed claims.
- Final copyediting, table/figure economy, and Overleaf package preparation.

### P3 - Fused Gate-State and Adaptive/Learned Residual Control: 62%

Evidence already promising:

- Full LaTeX draft exists under the gate-residual project.
- MuJoCo Crazyflie 2 and Skydio X2 results are present.
- HyperLIF gate-state residual improves selected hard maneuvers where LIF/Izhikevich/Nengo LIF-rate degrade.
- The safety/residual-blending story is clear and publishable.
- Learned/adaptive gate transfer evidence is promising enough to keep inside this manuscript as an extension.

Missing:

- Fill paper TODOs: gate-gain sweep rows, X2 rotor-level rows, figure inclusion paths.
- Multi-seed or repeated-trial statistics, with failure/fault counts.
- Timing-shuffled and energy-matched ablation tables.
- Clarify that gate-mode residual currently attributes improvement to HyperLIF gate state; Adaptive HyperLIF is inert in gate mode unless voltage/event pathways are used.
- Connect the controller to the calibrated Nengo/NEF implementation instead of a parallel duplicate neuron implementation.
- Define the learned/adaptive gate mechanism precisely.
- Validate fixed vs learned/adaptive gates across both MuJoCo quadrotors and at least two missions.
- Show that Adaptive HyperLIF contributes through voltage/event or conductance pathways, not merely through a saturated gate signal.

## Recommended Venue Strategy

P1: IEEE Transactions on Artificial Intelligence, IEEE Transactions on Emerging Topics in Computational Intelligence, Neural Networks, or a new TNNLS submission only if the scope, title, and evidence are clearly distinct from the rejected paper.

P2: IEEE Transactions on Cognitive and Developmental Systems, IEEE Transactions on Neural Systems and Rehabilitation Engineering if framed as neural engineering, Neuromorphic Computing and Engineering, Neural Computation, or Frontiers/Neurocomputing style methods venues.

P3: IEEE Robotics and Automation Letters, IEEE Transactions on Robotics if strengthened substantially, IEEE Control Systems Letters with CDC/ACC option, or IEEE Transactions on Cybernetics if the control-theory framing is deepened. If the adaptive/learned gate extension remains exploratory, keep it as a section and limitation rather than splitting it into a separate conference paper.

## Where To Mention Gate-State Residual Control Outside P3

P1 should mention control in the discussion as a one-paragraph translational implication: the same gate state that is decodable for temporal classification can be decoded as a residual signal in control. Do not include MuJoCo tables in P1.

P2 should mention control in the Nengo/NEF bridge: a calibrated custom `NeuronType` makes gate-state residual control a principled NEF target. Include at most a conceptual figure or short future-work paragraph unless the controller is directly run through the Nengo implementation.

## ArXiv Recommendation

Post an arXiv preprint only after P1 and P2 have safe claims, corrected old benchmark language, and reproducibility packages. The arXiv strategy should not expose a half-corrected TNNLS revision. It should present the new split as distinct papers.
