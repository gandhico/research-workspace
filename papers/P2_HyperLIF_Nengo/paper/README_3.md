# HyperLIF companion paper - IEEE two-column (TNNLS) version

## Current status as of 2026-07-20

This README describes the older `main_ieee.tex` package from 2026-06-09.
It is now stale.

Do not upload `main_ieee.tex` to Overleaf as the current paper. The active
manuscript is:

- `paper/main.tex`
- `paper/main.pdf`

The active manuscript now includes the Nengo capability matrix, three-seed
capability preflight, backend-portability evidence, PES trade, and the final
five-seed scalar NEF decoder-ablation table. The old `main_ieee.tex` does not
include these results.

The next packaging task is to regenerate an IEEEtran version from the current
`main.tex`, not to edit the stale IEEE file by hand.

Files
- `main_ieee.tex`   — the manuscript, rewritten for `\documentclass[journal]{IEEEtran}`
- `references.bib`  — the 12 references (rebuilt from your reference list)
- `figures/`        — the 7 figures (extracted from your PDF as PNG)
- `main_ieee.pdf`   — a compiled preview (9 pages)

## How to compile
This targets the standard IEEEtran class, which is the default on Overleaf's
"IEEE Transactions" template and ships with TeX Live / MiKTeX:

    pdflatex main_ieee
    bibtex   main_ieee
    pdflatex main_ieee
    pdflatex main_ieee

On Overleaf: create a project, upload these files (keep `figures/` as a folder),
set the compiler to pdfLaTeX, main document = `main_ieee.tex`.

## Notes
- The tables that your original drew via `\input{tables/*.tex}` are now inlined
  directly in `main_ieee.tex`, so no `tables/` folder is needed. Wide tables
  (model comparison) use the two-column-spanning `table*` float.
- Figures are 200-dpi raster crops from your PDF. For camera-ready quality,
  drop your original vector PDFs into `figures/` (same base names:
  `fig_step`, `fig_stress`, `fig_fi`, `fig_db`, `fig_integration`,
  `fig_parity`, `fig_decode`) — `\includegraphics` will pick them up.
- Added an `Index Terms` (IEEEkeywords) block, which TNNLS requires.
- All numbers/equations are unchanged from your draft (including `Gbase=20`,
  `beta=80`, `Gb=100` in the parameter table).

## About the preview PDF
The preview was built in an environment without the official `IEEEtran.cls`,
using a layout-compatible fallback, so spacing/fonts are approximate. The
`.tex` is written for the genuine class — compile on Overleaf/TeX Live for the
exact IEEE look.
