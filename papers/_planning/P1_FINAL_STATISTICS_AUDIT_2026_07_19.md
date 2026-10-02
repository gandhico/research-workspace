# P1 Final Statistics Audit

Date: 2026-07-19

## Purpose

This note records the final-statistics audit for the current IEEEtran P1 package. The goal was to determine which manuscript tables can be upgraded from compact mean-only reporting to traceable five-seed statistics without rerunning experiments.

## Files Added

- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\p1_final_stats_audit.py`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\final_stats\p1_final_stats_summary_20260719.csv`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\final_stats\p1_final_paired_tests_20260719.csv`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\final_stats\P1_FINAL_STATISTICS_AUDIT_20260719.md`

## Inputs Audited

- full 450-run feedforward sweep: `07_AdHyperLIF_Triage\results\hpc_559182\hpc_export\_registry.csv`
- full architecture-transfer sweep: `07_AdHyperLIF_Triage\results\roster60\_registry.csv`
- N-MNIST tiny FF reviewer-baseline preflight
- SHD-wide FF reviewer-baseline shortlist
- SHD-wide RSNN/delay reviewer-baseline shortlist

The script selected the best readout per neuron within each scope and generated:

- 74 selected configurations
- 94 paired comparison rows
- sample standard deviation and CI95 values
- failure and NaN-batch counts
- paired t-test context using the triage SciPy environment
- exact two-sided sign-flip p-values

## Manuscript Integration

Updated `paper_ieee\main.tex`:

- `tab:ff-temporal` now reports mean test accuracy plus sample standard deviation over five seeds.
- `tab:arch-transfer` now reports mean test accuracy plus sample standard deviation over five seeds.
- `tab:baseline-shortlist` now reports sample standard deviation values from the audit.
- all three quantitative table captions explicitly state that selected rows had zero failures and zero NaN batches.

Rebuilt canonical `main.pdf` successfully:

- 5 pages, 441466 bytes
- no undefined citations
- no undefined references
- no overfull boxes
- BibTeX reports `warning$ -- 0`

## Statistical Decision

The existing registries are sufficient for descriptive five-seed statistics and paired directional deltas. They should not be used for strict two-sided nonparametric p<0.05 claims because with five paired seeds the exact sign-flip lower bound is 0.0625 when all five differences agree.

Recommended framing:

- Main paper: report mean/sample-std and zero-failure status.
- Supplement/provenance: keep paired t-test and exact sign-flip audit CSVs.
- Advisor decision only: run more seeds if formal nonparametric p<0.05 is required.

## Readiness Impact

This closes the final-statistics/provenance gate for the main quantitative tables. P1 moves from `97%` to `98%`. The remaining gates are author/funding/repository metadata, final copyedit, and advisor approval.
