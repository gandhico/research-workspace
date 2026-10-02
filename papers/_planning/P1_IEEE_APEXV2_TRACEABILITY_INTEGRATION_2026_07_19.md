# P1 IEEE APEX-v2 Traceability Integration

Date: 2026-07-19

## Purpose

This note records the manuscript integration of the APEX-v2 evidence into the IEEEtran P1 package. The integration keeps APEX-v2 in the correct claim lane: traceability and reproducibility, not a new headline accuracy result.

## Files Updated

- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper_ieee\main.tex`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper_ieee\FIGURE_TABLE_MAP.md`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper_ieee\README_OVERLEAF.md`

## Manuscript Changes

Added a compact APEX-v2 traceability table:

- `tab:apex-v2-traceability`

The table records:

- G1/G2 forward traces: `54/54` finite rows
- G3 one-batch readout: loss `4.0835 -> 1.7929`
- shared-weight HyperLIF parity: max feature error `<= 1.05e-5`
- shared-weight Adaptive HyperLIF parity: max feature error `<= 5.09e-4`
- G5 three-seed preflight: stable, `0` NaN batches

Updated the Discussion and Limitations sections to clarify:

- native APEX remains the calibrated dense cross-framework validation
- native APEX recurrent/fixed-delay limitations remain limitations
- APEX-v2 closes the forward-portability gap for PyTorch-style recurrent and temporal-current delay cores
- APEX-v2 training evidence remains bounded fixed-trunk/readout-head evidence, not paper-grade accuracy

Updated the figure/table map and Overleaf README so the APEX-v2 claim discipline is explicit.

## Build Verification

Canonical build directory:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper_ieee`

Build sequence:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Build status:

- `main.pdf` built successfully
- no undefined citations
- no undefined references
- no overfull boxes after table polish
- remaining messages are underfull layout warnings and MiKTeX's update reminder

## Readiness Impact

P1 moves from `96%` to `97%`.

Remaining blockers:

- final paired/statistical tests or explicit decision to submit with shortlist/preflight framing
- author, funding, repository, and acknowledgment metadata
- final copyedit and advisor approval
