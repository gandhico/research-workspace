# Source-package verification

`output/ACC2027_architecture_Overleaf.zip` was extracted into the separate `tmp/package_check` directory and built there, without reading assets from the working manuscript folder.

- Package: 20 entries, 2,692,947 bytes.
- Full paper: pdfLaTeX, BibTeX, two further pdfLaTeX passes succeeded; 10 pages, 3,069,561 bytes.
- Standalone `architecture_figure.tex`: pdfLaTeX succeeded; 1 page, 192,869 bytes.
- Final extracted-package paper log contains no overfull boxes, undefined references/citations, or multiply defined labels.
- Build logs remain in `tmp/package_check`; render checks of the delivered paper and diagram are recorded in `ARCHITECTURE_QA.md`.

The ZIP is manuscript source plus audit material, not a full experiment-code/data release.
