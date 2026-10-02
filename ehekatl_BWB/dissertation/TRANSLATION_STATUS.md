# EHEKATL revised English dissertation status

## Current state

- Immutable Spanish source: `source_es/`
- English working copy: `source_en/`
- Approved English title inserted into the working copy.
- PDF metadata keywords and subject corrected.
- Abstract translated and scientifically tightened without adding experimental claims.
- A complete 188-page machine-translated review PDF has been compiled at
  `output/pdf/EHEKATL_English_Dissertation_2026.pdf`.
- The automated audit preserved label, reference, citation, graphic and equation
  structure across the active translated files, and the rendered PDF received a
  visual layout review.
- This is a complete **author-review draft**, not a human-copyedited or
  arXiv-ready final edition.

## Required before the arXiv-ready English edition

1. Complete a human technical and stylistic edit of all active narrative,
   captions and tables; verify specialist terminology against the Spanish source.
2. Translate or redraw Spanish text embedded in figure artwork where required.
3. Split or clearly document the logical Chapters 3--6 currently carried by
   `Capitulo3/diseno_experimento.tex` without breaking labels or numbering.
4. Manually audit equations, units, symbols, labels and cross-references despite
   the successful automated parity checks.
5. Repair bibliography metadata and strengthen citations in the controller and
   X-Plane chapters.
6. Audit third-party figure permissions and identify reused CCE 2022 material.
7. Build a minimal arXiv source package, compile it on an arXiv-compatible
   toolchain and inspect the generated PDF before upload.

The current PDF should be labelled “complete English review draft.” It will not
be labelled “arXiv-ready final” until all seven gates pass.
