# P2 Manuscript Integration Summary

Date: 2026-07-19

Purpose: record the manuscript edit that moved the completed seed-preflight result from logs/CSV into the active IEEE paper source.

## Edited Files

Active manuscript:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\paper\main.tex`

Traceability docs:

- `C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\FIGURE_TABLE_MAP.md`
- `C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\RESULTS_AUDIT.md`
- `C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\RUNNERS.md`
- `C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\REPRODUCIBILITY.md`

## Manuscript Changes

- Added `17_capability_seed_sweep_summary.csv` to the capability-section evidence list.
- Added Table `tab:capability-seeded`, a three-seed core capability preflight table with error mean +/- standard deviation and mean firing rate.
- Updated limitation language so P2 no longer describes Nengo evidence as only a Phase-A smoke test.
- Updated future work to distinguish the current seven-app seeded core and nine-app matrix from remaining extensions.
- Updated conclusion with the 84/84, zero-failure preflight result and the calibrated HyperLIF vs Adaptive HyperLIF division of labor.

## Build Verification

Command:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper
.\scripts\build_paper.ps1
```

Result:

- Build status: OK.
- Output PDF: `C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\paper\main.pdf`
- PDF size: 851,508 bytes.
- Page count from `main.log`: 26 pages.
- Undefined-reference scan: no `undefined` or `Undefined` matches in the final log scan.
- MiKTeX printed only its standard update-check warning.

## Readiness Effect

P2 moves from 84% to 85%. Remaining blockers are no longer evidence discovery; they are final manuscript polish, optional five-seed expansion, NEF decoder/ensemble validation depth, and Overleaf packaging.
