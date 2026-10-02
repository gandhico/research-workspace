# Paper 3 — advisor handoff (complete draft)

**Status: complete, self-consistent draft.** `paper/main.tex` compiles cleanly with `pdflatex` +
`bibtex` to a **26-page PDF** (`paper/main.pdf`) — no LaTeX errors, no undefined references or
citations, all figures embedded. Every number, figure, and table regenerates from the included code
(`experiments/01–16`, `make_capability_figure.py`) and data (`results/csv/01–15`). This note is the
front door: what the paper claims, and the few decisions that are yours to make.

## Title
> A Mathematically Consistent, Nengo-Compatible Reference Implementation of HyperLIF and Adaptive
> HyperLIF Neurons: Exact Validation, Capability Coverage, and Operating-Point Calibration

## What the paper contributes
1. **Single-source, equation-faithful reference** implementation of LIF / HyperLIF / Adaptive HyperLIF.
2. **Closed-form DB fixed-point** analysis (onset `J_DB=(v_thresh−γ)(1+τG_b)`, latched voltage, β-bound), validated against simulation.
3. **Numerical-scheme analysis** (explicit vs exponential Euler vs RK4): the exponential scheme is unconditionally stable.
4. **Exact Python↔Nengo parity** (voltage/gate RMSE = 0, zero event mismatch) via a shared kernel.
5. **Operating-point calibration + capability coverage** (new): with a calibrated readout, HyperLIF runs all nine canonical Nengo capabilities (representation, dynamics, memory, online learning, cognition), matching or *exceeding* LIF on dynamics and memory at ~3.5× fewer spikes; online-learning speed is a tunable firing-rate trade. This overturns the earlier "weak integrator" reading as an operating-point artifact.
6. **Backend-portability characterization** (new): a custom continuous-gate `NeuronType` runs only in the reference simulator — OpenCL/Loihi reject it, NengoDL is version-locked.
7. **Gate-as-readiness interpretation** + an explicitly future-work bridge to gate-state residual decoding for control.

## Decisions for you (the draft is written so any of these can be flipped)
1. **Title** — currently the calibration/capability framing above (option A). Alternative that keeps a control hook: "*…: Exact Validation, Capability Coverage, and a Readiness Bridge to Gate-State Control*" (option B).
2. **Target venue** — the paper is pitched as a rigorous reference + characterization. Best fits: *Neuromorphic Computing and Engineering* (IOP), *Neural Computation*, *IEEE TNNLS*, or *Frontiers in Neuroscience: Neuromorphic Engineering*. (It is a strong specialized-venue paper; the flagship "control" swing is reserved for the companion control papers.)
3. **Optional strengthening — one experiment.** Decoding is currently single-neuron (an acknowledged limitation, §Limitations iv). The one add that would most strengthen the readiness story is a **multi-neuron NEF gate-decoder ablation** (spike / voltage / gate / combined). It is scoped in `PAPER3_WORKPLAN.md` and can be run in the existing environment. Not required for submission; a clear upgrade if desired.
4. **Control scope** — the control connection (§Connection to Residual Augmentation) is deliberately kept *forward-looking only*, with no closed-loop results, to reserve the full control contribution for the companion papers. Confirm this boundary matches your plan.

## How it fits the program
Paper 3 is the validated Nengo substrate the control papers build on: it proves the neuron ports exactly, characterizes where it works and where it doesn't in the NEF, and gives the **operating-point calibration recipe** (θ_event, origin, rate-to-current, ~40 Hz PES sweet spot) that Paper 5's PES-adaptive HyperLIF controller will need. It is the launchpad for Papers 4 (gate-residual mechanism) and 5 (Nengo controller).

## Where everything is
- Manuscript: `paper/main.tex` → `paper/main.pdf` (compiled). Tables `paper/tables/`, figures `paper/figures/`.
- Code: `experiments/`, neurons `src/neurons/`. Data: `results/csv/`.
- Full technical inventory: `NENGO_MASTER_REPORT.md`. Capability findings: `NENGO_CAPABILITY_FINDINGS.md`.
- Reproduce: `python experiments/run_all.py` (core), `python experiments/13_…py` / `make_capability_figure.py` (capability); rebuild PDF with `pdflatex main.tex; bibtex main; pdflatex main.tex; pdflatex main.tex`.
