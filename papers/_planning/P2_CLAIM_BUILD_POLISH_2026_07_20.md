# P2 Claim And Build Polish - 2026-07-20

## Decision

P1 is frozen for advisor review. P2 is now the active near-submission paper.

For P2, the completed three-seed core capability preflight is sufficient for the
current implementation-and-methods claim: 84/84 Nengo simulations completed with
zero failures across T001/T002/T023/T033 and seven core apps. A five-seed run is
reserved for a venue or reviewer request for broader margins; it is not a
blocking item for this manuscript state.

## Manuscript State

Active source:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\paper\main.tex`

Build artifact:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\paper\main.pdf`

Verified state:

- `main.pdf` builds to 26 pages.
- `main.log` has no undefined references/citations and no overfull boxes.
- `main.blg` reports `warning$ -- 0`.
- The local workspace mirror matches the canonical paper build.

## Edits Completed

- Removed the long inline artifact list that was causing an overfull box.
- Reframed artifact paths through the project reproducibility/figure-table map.
- Shortened the conclusion wording around depolarization-block prediction and
  adaptive boundedness to avoid another overfull box.
- Clarified that the five-seed capability run is a contingency, not a current
  blocker.
- Updated `FIGURE_TABLE_MAP.md`, `RESULTS_AUDIT.md`, `REPRODUCIBILITY.md`, and
  `RUNNERS.md` so capability, PES, backend, and seed-preflight claims are linked
  to their scripts/CSVs/logs.

## Current Readiness

P2 moves from 85% to 86%.

Remaining gates:

- Final claim-to-artifact audit against every manuscript table, figure, and
  paragraph-level result.
- Decide whether NEF ensemble/decoder ablations remain future work or get a
  compact paper-grade experiment.
- Final IEEE copyedit, table economy pass, author/funding metadata, and Overleaf
  packaging.

## Recommended Next Action

Run a compact NEF decoder-ablation planning pass before launching new long
experiments. The best next experiment is likely a bounded multi-neuron decoder
validation for `theta_event=0.95`, origin-aware T023, and Adaptive T033 with
spike-only, voltage-only, gate-only, and combined readouts. If it is cheap and
stable, it strengthens P2; if not, it becomes an explicit future-work boundary.
