# Architecture revision: final QA

## Scope and preserved material

- Figure 1 replaced; its caption and the residual-notation paragraph updated.
- All existing displayed equation/align environments compare unchanged with `paper/gate_gain_review_2026-09-11/source/ACC2027.tex`.
- All table environments compare unchanged.
- Nine manuscript figures remain; the other eight figure environments compare unchanged.
- All seven pre-existing binary figure assets compare byte-for-byte unchanged.
- No controller or experiment source was edited; the direct core SHA-256 still equals `ea6d7853fff724d2a6c6fd15afb9a18cf7f9cdae19ce6f04bcf4a5e2300a5e53`.
- No MuJoCo mission or hardware session was run for this drawing revision.

## Equation-to-code checks

6,144 offline arithmetic steps passed; 2,681 steps exercised the weight-projection boundary. Maximum absolute discrepancies:

| Quantity | Maximum absolute discrepancy |
|---|---:|
| Gate | 1.1102230246251565e-16 |
| Membrane | 1.1102230246251565e-16 |
| Activity | 9.992007221626409e-16 |
| Decoder weights | 8.881784197001252e-16 |
| Command / requested residual | 6.106226635438361e-16 |

Output dimensions, the residual-authority bound, and exact beta-zero baseline-command recovery were also checked. This verifies the canonical direct recursion; it is not a proof of plant stability or identical native Nengo scheduling.

## Rendering and compilation

- Standalone diagram: one vector PDF page; embedded fonts; also exported to SVG and PNG.
- Updated manuscript: ten pages; all ten pages visually inspected after rendering.
- No overfull boxes, undefined references/citations, or multiply defined labels in the final manuscript log.
- Figure 1 checked both at standalone resolution and within the two-column paper layout.
- Current/next decoder weight paths, activity branch, teacher input, height input/output, and rotor clipping all have explicit, non-overlapping connections.
- Standard page size, margins, and manuscript font sizes are unchanged. Figure-to-text gaps use 16 pt separation to retain ten pages without deleting content.

The paper remains an advisor-review draft; this architecture revision does not resolve the existing eight-page submission task or the scientific limitations reported in the mechanism study.

## Deliverables

- `output/pdf/CMG_PES_residual_architecture.pdf`
- `output/CMG_PES_residual_architecture.svg`
- `output/CMG_PES_residual_architecture.png`
- `output/pdf/ACC2027_architecture_review.pdf`
- `output/ACC2027_architecture_Overleaf.zip`
- `source/architectures/tikz/arch_residual_io.tex` (shared editable source)
- `ARCHITECTURE_AUDIT.md` (complete block-by-block explanation and code mapping)
- `ARCHITECTURE_VALIDATION.json` (machine-readable arithmetic checks and source hashes)

The Overleaf package contains the manuscript, its required assets, a standalone diagram wrapper, and supporting audit files. It is not the separately planned controller/data ZIP release.
