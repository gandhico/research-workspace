# P1 Claim-Language Audit

Date: 2026-07-19

## Purpose

This note records the manuscript wording pass after APEX-v2 and bibliography integration. The goal was to remove lab-internal phrasing and keep all Julia/APEX and APEX-v2 statements in their proper evidentiary lane.

## Files Updated

- `C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper_ieee\main.tex`
- mirrored source and rebuilt artifacts under `C:\Users\gandhico\OneDrive - New Mexico State University\Documents\HyperLIF_Nengo\08_HyperLIF_Architectures\paper_ieee`

## Wording Changes

Polished the abstract, introduction, APEX subsection, discussion, limitations, and conclusion to:

- replace leaderboard-style wording with controlled benchmark/mechanism language
- replace "smoke" phrasing in the manuscript body with validation/check terminology
- replace "beat" with more neutral comparison language
- remove the internal note-like conclusion sentence
- clarify that APEX-v2 is traceability evidence, not paper-grade multi-epoch accuracy evidence

## Claim Discipline After Audit

Safe current claims:

- HyperLIF gives temporal-specific gains under controlled settings.
- HyperLIF exposes a decodable gate state absent from LIF.
- Adaptive HyperLIF provides an event-efficiency operating dial.
- PLIF/ALIF baselines make the story nuanced; HyperLIF does not universally dominate adaptive-threshold neurons.
- Native Julia/APEX provides a calibrated dense-cell cross-framework validation.
- APEX-v2 provides PyTorch-to-Julia implementation traceability for dense, recurrent, and delay cores.

Claims still blocked:

- paper-grade APEX-v2 recurrent/delay accuracy superiority
- final paired-test/CI claims across every table row
- submission-ready author/funding/repository statements

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
- output PDF: 5 pages, 441018 bytes
- no undefined citations
- no undefined references
- no overfull boxes
- BibTeX reports `warning$ -- 0`
- remaining messages are underfull layout warnings and MiKTeX's update reminder

## Readiness Impact

This closes the current claim-language cleanup gate. P1 remains at `97%`; the remaining gates are the final statistics/framing decision, author/funding/repository metadata, advisor copyedit, and submission packaging.
