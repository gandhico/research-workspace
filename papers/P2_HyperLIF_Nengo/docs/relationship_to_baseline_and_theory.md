# Relationship to the Baseline and the Theory Manuscript

This paper project sits between two existing artifacts.

## 1. The clean baseline (`04_Adaptive_HyperLIF_Nengo`)

The `src/neurons/` and `src/simulation/` code here is a **verbatim copy** of the
baseline, so the equations validated in the baseline are the equations in this
paper. What this project *adds* on top of the baseline:

- `src/analysis/depolarization_block.py` — fixed-point / DB-onset / adaptive
  stabilization analysis (new).
- `src/visualization/plotting.py` — publication styling (PNG + PDF, serif, fixed
  palette) replacing the baseline's minimal style.
- A reorganized experiment suite that separates **data generation**
  (`experiments/`) from **figure** (`figures/`) and **table** (`tables/`)
  rendering, so every figure/table is traceable to a CSV.
- New experiments beyond the baseline's six: an extended high-resolution current
  sweep with analytical DB cross-checks (`03`), a sustained-drive DB latch
  demonstration (`04`), and a numerical-integration accuracy/stability study
  (`06`).

The baseline is intentionally left untouched.

## 2. The theory manuscript (Adaptive HyperLIF, under review)

The theory manuscript derives the HyperLIF family via nonstandard analysis,
identifies the depolarization block as a resolved Zeno phenomenon, derives the
adaptive conductance law through a flux-balance argument, and demonstrates
differentiable training (BPTT) on neuromorphic benchmarks (N-MNIST, DVS128).

This project is the **companion implementation/validation study**. It does not
reproduce or re-claim the theory's training results. Its job is to show that the
stated dynamics can be realized as a faithful, numerically sound, Nengo-ready
component, and to characterize the implemented dynamics structurally
(fixed points, DB onset, stepping schemes, exact port parity).

Two consistency checks worth highlighting:

- The observed fixed-gain firing collapse near `J≈2.4` matches the theory
  manuscript's "early collapse (`I≈2.4`)" observation, although the two use
  different normalized parameter sets; here we *derive* the onset
  `J_DB=(v_thresh−γ)(1+τG_b)` for the implemented parameters and confirm it.
- The exponential ("stable") membrane update used by the Nengo port is the
  discrete-time analogue of the exact gate relaxation the theory manuscript uses
  for stiff integration.

See `PAPER_NOTES.md` for the notation alignment table and the scope boundary.
