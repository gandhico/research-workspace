# P1 IEEEtran Conversion

Date: 2026-07-19

Purpose: record the first Overleaf-ready IEEEtran source package for P1 after freezing the final table/figure scope.

## New Package

Created:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper_ieee`

Contents:

- `main.tex`: IEEEtran journal manuscript source.
- `refs.bib`: initial bibliography seed.
- `README_OVERLEAF.md`: build and claim-discipline instructions.
- `FIGURE_TABLE_MAP.md`: figure/table provenance map.
- `figures\fig1_best_per_neuron.png`
- `figures\fig2_structural_blindness.png`
- `figures\fig3_efficiency_pareto.png`
- `figures\fig4_arch_transfer_gap.png`
- `figures\fig5_efficiency_pareto.png`

Also added:

`C:\00_Research_\Neural_Networks_and_Learning\10_IEEE_Paper_Proposals_2026_07_19\P1_FINAL_TABLE_SCOPE_2026_07_19.md`

## Manuscript Surface

Main-text figures:

- Temporal-specific gain.
- Gate-readout structural blindness.
- Shallow efficiency Pareto.
- Architecture-transfer gap.
- Architecture-scale efficiency Pareto.

Main-text tables:

- Dataset/factor scope.
- Feedforward temporal gain.
- Gate-readout mechanism.
- Architecture transfer.
- PLIF/ALIF reviewer baseline extension.
- Tuned Julia/APEX cross-framework validation.

## Build Verification

Build command sequence:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Result:

- `main.pdf` generated successfully.
- Final PDF: `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper_ieee\main.pdf`
- Current length: 5 IEEEtran pages.
- Final log scan found no undefined citations or references.
- MiKTeX reports only its usual update-check warning.

## Claim Discipline Preserved

- ALIF is described as a serious baseline and not as a weak control.
- HyperLIF is not claimed to universally dominate ALIF.
- APEX default-gamma failure is retained as calibration evidence.
- Tuned APEX HyperLIF/NSA is framed as cross-framework validation, not the headline benchmark.
- The deep convres failure remains a limitation.

## Remaining Before Submission

- Add paired seed tests or nonparametric paired statistics for final tables.
- Verify all bibliography metadata against the final `.bib` library.
- Replace placeholder author/funding/acknowledgment metadata.
- Decide whether to expand the paper from a compact 5-page source into a full-length TNNLS/TETCI/TAI submission.
- Copyedit tone and table economy after advisor review.

## Readiness Effect

P1 moves from 93% to 94%. The first compiled IEEEtran source exists and the table scope is frozen, but the paper still needs final statistical tests, bibliography verification, and advisor-level narrative polish.
