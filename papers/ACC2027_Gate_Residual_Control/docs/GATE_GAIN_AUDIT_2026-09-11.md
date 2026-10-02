# Entry point: gain/conductance audit and revised paper

Latest revised manuscript: `C:\Research\papers\ACC2027_Gate_Residual_Control\paper\gate_gain_review_2026-09-11\source\ACC2027.tex`.

Paper PDF: `C:\Research\papers\ACC2027_Gate_Residual_Control\paper\gate_gain_review_2026-09-11\output\pdf\ACC2027_gate_gain_review.pdf`.

Overleaf source ZIP: `C:\Research\papers\ACC2027_Gate_Residual_Control\paper\gate_gain_review_2026-09-11\output\ACC2027_gate_gain_Overleaf.zip`.

Full analysis: `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\gate_gain_sweep_2026-09-11\REPORT.md`.

Reviewer decisions: `C:\Research\papers\ACC2027_Gate_Residual_Control\paper\gate_gain_review_2026-09-11\REVISION_DECISIONS.md`.

## Important finding for any continuing session

Do not repeat the claim that CMG conductance is generally negligible or that CMG dynamics are necessary for the large improvements. The frozen main matrix reproduces, but new constant non-neural activity features with the same PES teacher/update improve X2 Roll by 57.78%, X2 Full3 by 56.98%, and CF2 Hardstep by 18.38%. Canonical CMG gives 17.36%, 56.56%, and 18.37%, respectively.

Raw gates in X2 Full3 are >.9 for 97.7% of unit-samples and mean conductance is 7.08 times membrane leak. Persistent high gates and readout saturation obscure conductance-dependent membrane changes. With constant activity and inactive projection, the direct decoder reduces exactly to a target-filter recursion; it matches saved weights to floating-point roundoff. Conductance-sensitive new regimes were tested, but none exceeded canonical CMG. Some were worse than PD.

All 71 new cases are stored under the experiment's `results` directory. They contain 71 plant CSV traces, 67 full-rate neural/basis archives and per-case provenance. `analysis/FINAL_VALIDATION.json` and `analysis/frozen_result_manifest.json` record checks and hashes. `reproduction_cases.json` + `reproduce_study.py` reproduce this exact staged campaign. The originally declared 148-cell factorial remains optional and was NOT completed.

Canonical simulation/control sources and older frozen results were not edited. No hardware was accessed. Concurrent baseline-controller campaigns were left untouched and were not imported into this manuscript without audit.

The paper remains a 10-page advisor draft, not yet an eight-page/2-MB ACC upload. All nine previous figures are retained. New claims should be based on the honest reframing in the revised abstract and discussion, not the older CMG-necessity hypothesis.
