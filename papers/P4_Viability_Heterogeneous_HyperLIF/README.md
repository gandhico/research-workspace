# Viability-Aware Heterogeneous HyperLIF

This project tests whether one continuous-reset HyperLIF neuron family can be deliberately distributed
across low-, medium-, and high-event regimes, combine complementary information, adapt its activity
without collapsing that diversity, and control a robot inside explicit viability bounds.

The answer is not known yet. The architecture is implementable and its pieces have precedents, but the
current SHD runs are only pipeline evidence. The defensible novelty is the **cross-level coupling**:
plant-level viability margin → population arbitration and plasticity → heterogeneous HyperLIF dynamics
→ independently checked safety filter.

## Read first

1. `RESEARCH_PROGRAM.md` — literature, theory, hypotheses, experiments, and decision gates.
2. `AGENTS.md` — continuation contract for Claude, Codex, or another research agent.
3. `PROGRESS_REGISTER.md` — current evidence, blockers, and next action.
4. `CLAIM_LEDGER.md` — what may and may not be said.
5. `MATH_CODE_MAP.md` and `REPRODUCIBILITY.md` — equation-to-code and run provenance.

## Current status

- Julia package and core contracts: implemented and tested (44 tests).
- Constant-current regime atlas: implemented.
- **Per-regime input-gain calibration: falsified.** On the SHD cache every regime saturates at
  roughly one upward crossing per neuron per sequence regardless of gain, so the four
  "regimes" were four points on a saturation curve. See finding F1 in `PROGRESS_REGISTER.md`.
- **Shared-gain regime profile: implemented and measured.** One gain of 1.4 gives four ordered,
  separated, unsaturated populations.
- **Budget-matched model families: implemented.** `heterogeneous`, `ensemble`, and
  `homogeneous` at equal hidden state and effective parameter count.
- Matched triple over three seeds: running; LIF/PLIF/ALIF controls not yet built.
- **The prior paired homeostasis pilot was vacuous** (both runs selected the same
  configuration). The runner now detects this.
- The event-communication clause of the research question is **not yet measurable**: the
  `:hybrid_vr` readout never reads upward crossings.
- Image replication: blocked because the exact prior N-MNIST/DVS cache files are not local.
- Robot simulation and hardware: not started; they are deliberately gated on recognition evidence.

## Quick start

```powershell
cd C:\Research\papers\P4_Viability_Heterogeneous_HyperLIF\code
julia --project=. -e "using Pkg; Pkg.instantiate(); Pkg.test()"
julia --project=. experiments\regime_probe.jl
julia --project=. experiments\calibrate_dataset_activity.jl `
  C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5
julia --project=. experiments\train_h5.jl `
  --cache=C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5 `
  --smoke --results-root=results\smoke_shd
```

The P1 Julia package is a local path dependency and remains the authority for the HyperLIF equations
and event semantics. P4 should extend it, not copy or silently fork it.

