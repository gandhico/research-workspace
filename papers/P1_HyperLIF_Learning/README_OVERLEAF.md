# P1 IEEEtran Overleaf Package

Created: 2026-07-19

Main source:

- `main.tex`

Supporting files:

- `refs.bib`
- `FIGURE_TABLE_MAP.md`
- `../results/final_stats/p1_final_stats_summary_20260719.csv`
- `../results/final_stats/p1_final_paired_tests_20260719.csv`
- `../results/final_stats/P1_FINAL_STATISTICS_AUDIT_20260719.md`
- `figures/fig1_best_per_neuron.png`
- `figures/fig2_structural_blindness.png`
- `figures/fig3_efficiency_pareto.png`
- `figures/fig4_arch_transfer_gap.png`
- `figures/fig5_efficiency_pareto.png`

Build target:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Claim discipline:

- The APEX result is a calibrated cross-framework validation, not the headline benchmark.
- The APEX-v2 result is traceability/supplementary evidence. It verifies PyTorch-to-Julia forward parity and fixed-trunk readout stability, not a paper-grade recurrent/delay accuracy claim.
- Main quantitative tables now report mean plus sample standard deviation over five seeds, with zero-failure/zero-NaN framing from `p1_final_stats_audit.py`.
- Paired-test CSVs are provenance/context. With five paired seeds, exact two-sided sign-flip tests cannot support p<0.05 claims; use them as supplement or methods context unless a larger seed run is approved.
- The ALIF/PLIF table is a reviewer-facing baseline extension and must be described as a shortlist unless a larger final grid is run.
- The deep convres failure remains a limitation.
