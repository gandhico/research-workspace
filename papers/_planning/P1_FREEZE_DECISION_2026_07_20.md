# P1 Freeze Decision

Date: 2026-07-20

## Decision

P1 HyperLIF Learning is frozen for advisor review. Do not open new P1 experiments unless an advisor explicitly requests them.

## Frozen Scope

The frozen P1 package is the IEEEtran source under:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\paper_ieee`

The package includes:

- IEEEtran `main.tex`
- compiled `main.pdf`
- bibliography with verified DOI/page metadata
- five manuscript figures
- final figure/table provenance map
- final-statistics audit CSVs and Markdown note
- APEX-v2 traceability table and claim-discipline language

## Frozen Claims

Safe claims:

- HyperLIF gives temporal-specific gains under controlled settings.
- HyperLIF exposes a decodable gate state absent from LIF.
- Adaptive HyperLIF provides an event-efficiency operating dial.
- HyperLIF transfers across feedforward, convolutional, recurrent, and delay cells, with bounded deep-residual limitations.
- PLIF/ALIF reviewer baselines make the story nuanced; HyperLIF does not universally dominate adaptive-threshold neurons.
- Native Julia/APEX provides a calibrated dense-cell cross-framework validation.
- APEX-v2 provides PyTorch-to-Julia implementation traceability, not paper-grade recurrent/delay accuracy evidence.

## Remaining Non-Experimental Items

- final author order, affiliations, and IEEE membership labels
- funding, acknowledgments, compute-resource statement, and repository statement
- final advisor copyedit
- target journal decision

## Next Active Track

Active research work now moves to P2: HyperLIF / Adaptive HyperLIF in Nengo and NEF.
