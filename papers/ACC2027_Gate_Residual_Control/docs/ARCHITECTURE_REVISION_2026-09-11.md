# Figure 1 architecture revision, 2026-09-11

Latest architecture-only manuscript copy:
`C:\Research\papers\ACC2027_Gate_Residual_Control\paper\architecture_review_2026-09-11`

Read `ARCHITECTURE_AUDIT.md` and `ARCHITECTURE_QA.md` there first. The active editable drawing is `source/architectures/tikz/arch_residual_io.tex`, used by both the updated Figure 1 and standalone PDF. The updated paper is `source/ACC2027.tex`; exports are in `output/`.

The revision makes the teacher's error/rate input, gate-derived activity, pre-update decoding, one-step weight memory, torque scaling, rotor-force clipping, and collective-height branch explicit. No experimental code or results changed. All old displayed equations/tables and the other eight figures are preserved. The paper still has ten pages.

6,144 offline equation-to-code tests passed to below 1e-15 absolute discrepancy. This tests the direct CMG-PES implementation; it does not claim identical Nengo weight scheduling or new mission performance. Backend timing and the existing unfavorable constant-basis mechanism findings remain documented honestly.

Previous source remains at `paper/gate_gain_review_2026-09-11`. The architecture revision is not a new controller version, a hardware revision, or the postponed code/data distribution.
