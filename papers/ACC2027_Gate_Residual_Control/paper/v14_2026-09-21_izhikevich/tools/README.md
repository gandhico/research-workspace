# tools/ — paper-side helpers (v14)

| script | use |
|---|---|
| `build_v14.py [jobname]` | `pdflatex → bibtex → pdflatex ×2` in the paper folder (no latexmk/Perl needed); reports pages, undefined refs, overfull boxes |
| `overflow.py [pdf] [limit]` | how far the build is beyond the page limit, and the slack on the last page (measure only with the bibliography present) |
| `make_v14_zip.py` | derives the file list from the `.tex`, writes `ACC2027_v14_overleaf.zip`, and verifies it by compiling a clean extraction |
| `label_audit.py`, `cite_inventory.py` | every float referenced? every cite key defined and where is it used? |
| `chi_check.py` | the numbers behind the "why chi has no effect" sentence (Sec. IV-C) |
| `patch_stage7.py`, `patch_stage8.py` | **historical**: the scripts that wrote the results text with every number computed from `experiments/final_robustness_gating_2026-09-20/results/final_*.csv`. They assert exact matches against the pre-patch source, so they cannot be re-run on the final `.tex`; they document how each number entered the paper. The live check is `experiments/final_robustness_gating_2026-09-20/audit_v13.py`. |
