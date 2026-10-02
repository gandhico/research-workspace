# P1 Bibliography Metadata Verification

Date: 2026-07-19

## Purpose

This note records the bibliography metadata pass for the IEEEtran P1 manuscript. The goal was to reduce submission friction by adding DOI/page metadata to the key references and then rebuilding the canonical PDF with BibTeX.

## Files Updated

- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper_ieee\refs.bib`
- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper_ieee\main.pdf`
- mirrored copy under `C:\Users\gandhico\OneDrive - New Mexico State University\Documents\HyperLIF_Nengo\08_HyperLIF_Architectures\paper_ieee`

## Metadata Added

The bibliography was enriched with DOI and/or page metadata for:

- Neftci et al., surrogate-gradient learning in SNNs
- Bellec et al., LSNN
- Bellec et al., e-prop
- Fang et al., PLIF
- Zenke and Ganguli, SuperSpike
- Cramer et al., SHD
- Orchard et al., N-MNIST
- Roy et al., neuromorphic/SNN review
- Davies et al., Loihi

## Verification Sources

Metadata was cross-checked against primary publisher or stable indexing pages where available:

- CVF Open Access ICCV page for Fang et al. PLIF
- NeurIPS and DBLP records for Bellec et al. LSNN
- Nature Communications page for Bellec et al. e-prop
- Zenke Lab publication index for Neftci et al. and Zenke/Ganguli DOI metadata
- Frontiers and PubMed pages for Orchard et al. N-MNIST
- Nature page for Roy et al.
- IEEE/Mendeley-indexed metadata for Cramer et al. SHD
- Bibbase/CiNii-indexed metadata for Davies et al. Loihi

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

- `main.pdf` rebuilt successfully
- output PDF: 5 pages, 441139 bytes
- no undefined citations
- no undefined references
- no overfull boxes
- BibTeX reports `warning$ -- 0`
- remaining messages are underfull layout warnings and MiKTeX's update reminder

## Readiness Impact

This closes the bibliography-metadata gate for the current reference set. P1 remains at `97%` because the remaining blockers are not bibliographic:

- final paired/statistical tests or explicit decision to submit with the current shortlist/preflight framing
- author, funding, repository, and acknowledgment metadata
- final copyedit and advisor approval
