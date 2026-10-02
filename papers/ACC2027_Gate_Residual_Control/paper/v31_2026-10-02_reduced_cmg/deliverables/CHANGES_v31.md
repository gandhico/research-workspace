# ACC 2027 manuscript — changes from v30 to v31 (2026-10-02)

**Paper:** *Online Prescribed Error Sensitivity Decoder Learning in Neuromorphic Residual UAV Attitude Control*
(Contreras, Sandoval, Garcia Carrillo).
**Base:** Overleaf export `Online_PES_Decoder_HyperLIF_Residual_Control___Quaternion_Tracking (7).zip` (= PDF v30).
**Files changed:** `ACC2027.tex`, `tables/table_all_restructured.tex`. No other project file was modified.

## Summary

1. **Page limit.** v30 compiled to **9 pages**: the references ran onto page 9, past the ACC limit of 8 pages including
   references. v31 compiles to **8 pages**, references included.
2. **New result.** A reduced, non-latching CMG ablation (Sec. VI-C, one Table II row). It answers the review question
   "what does the CMG neuron add beyond a filter and a sigmoid?" and identifies the mechanism.
3. **Claim correction.** Sec. VI-D said every alternative basis "remains well short of CMG". The reduced CMG exceeds
   CMG, so that sentence is now qualified.
4. **Nothing removed except duplication.** Every equation, table entry, figure result and number from v30 is still in
   v31. Space came from repeated passages, a redundant inertia restatement, the roadmap paragraph, and the
   vehicle-photo strip (kept in the source behind `\iffalse`).
5. **Verified.** `reproduce/verify_acc2027_claims.py` now checks **73 claims (59 original + 14 new): 73/73 match.**

## Review points and how v31 addresses them

| Review point | Response in v31 | Evidence |
|---|---|---|
| Which constant was used in the constant-basis control? With a ≠ 1 the gap could be learning gain, not dynamics. | Stated explicitly: **a ≡ 1** (Sec. VI-D), so ‖a‖² = 6 matches a fully latched CMG. Eq. (30) is identified as PD+ff plus a matched lagged-proportional term. | Claim 73; archived `constant-one` trace |
| Gates latch permanently: release fold near v ≈ −0.89 lies below v_reset = 0. | Gate/activity paragraph now gives both folds (v ≈ 0.888 onset, −0.888 release) and ties non-release to Proposition 1(i). | Claims 70–71 (0 releases in the ten primary runs) |
| Control: replace each unit with LPF + static logistic (same τ, α_h, v_th, G). | New paragraph **Reduced CMG (non-latching ablation)**: derived as γ = 0, g₀ = g₁ = 0, τ_r → 0. Result **46.3% / 28.6%** at comparable mean effort, equal to CMG within 1.5 pp on Roll/Yaw360/Hardstep, higher on Full3/Hard45. New Table II row. | Claims 60–65, 72 |
| Choose G so activity is unsaturated, then repeat the χ ablation. | G = 10³ and G = 1 reported (9.0/3.6%, 4.4/1.7%): lowering G removes the graded tail. χ has no measurable effect at any tested G. | Claims 66–67, 69 |
| Log per-unit latch time and the fraction of samples with a = 1. | Per-unit latch times are summarized in text; a two-level replay of the recorded latch times reaches 9.6/3.8%. Full diagnostics are in the experiment folder. | Claim 68; `analysis/phase0/` |
| Will a reviewer ask what CMG adds over a first-order filter plus a sigmoid? | Abstract, Sec. VI-C and the conclusion now state the mechanism: decoder adaptation on the graded sub-threshold part of the basis, limited by irreversible latching. | Sec. VI-C |
| Notation: G is the conductance in the HyperLIF paper and the readout gain here. | Within this manuscript G is only the readout gain (conductance is c_j with g₀, g₁), so there is no clash inside the paper. Harmonize in the HyperLIF journal paper. | — |

## Change list

| Location | Change | Reason |
|---|---|---|
| Abstract | Added one sentence on the reduced-CMG ablation (46.3% / 28.6% at comparable effort). | Main new finding |
| Introduction, contribution (iv) | Added "mechanism ablations that isolate decoder adaptation, conductance, activity gain, and gate latching". | Reflects new content |
| Introduction | Roadmap paragraph commented out. | Page limit; the section headings carry it |
| Sec. II (opening) | Last sentence shortened to a pointer to the objective in Sec. II-C. | It repeated the Sec. II-C objective |
| Sec. II-A | Duplicate "Let J ≻ 0 denote the body-frame inertia" merged into the eq. (9) sentence. | Duplication |
| Sec. II-B | Allocation and collective-thrust remarks tightened; all statements kept. | Page limit |
| Sec. III-A, III-B | Gate description, numerical-integration remark and G remark tightened; equations unchanged. | Page limit |
| Remark 1, Sec. IV | Wording tightened; scope statements (no ISS, no stability or robustness certificate) kept. | Duplication with conclusion |
| Sec. VI-A | Body/principal-frame inertia restatement removed (repeated eq. (9)). Vehicle-photo strip (former Fig. 3) moved behind `\iffalse` with restore instructions. β-selection paragraph tightened. | Page limit; the strip had no technical content (already removed once in v13 for the same reason) |
| Sec. VI-C | χ sentence extended to all tested G. Gate/activity paragraph adds the fold analysis. Eq. (30) identified with the constant basis. **New paragraph: Reduced CMG (non-latching ablation).** Closing sentence revised. | Review points; new result |
| Sec. VI-D a) | Constant basis defined as a ≡ 1; the "every alternative remains well short of CMG" sentence qualified. | Correctness |
| Sec. VI-D, VI-E, VI-F | Izhikevich, noise-floor and Hardstep-gate paragraphs tightened; all numbers kept. The unverified "without overshoot or chattering" wording was replaced by the measured near-parity statement. | Page limit; precision |
| Sec. VII | Mechanism sentence revised; theoretical-conclusions paragraph tightened. Future work now lists non-latching CMG designs and testing the reduced CMG under noise, disturbances and other families, replacing "sweep G and χ more systematically" (now partly done). | New result |
| Table II | New row: Δ, reduced CMG, gated (Sec. VI-C). | New result |
| Figures | Architecture 0.90 → 0.84 text width; Hard45 ladder and Hardstep zoom → 0.90 / 0.92 column width. | Page limit; still legible |
| Cross-references | "Remark VI-C" (rendering quirk in v30) now reads "Remark 2". | Correctness |

## Scope stated in the paper

The reduced-CMG runs are single-seed and noise-free on the ρ = 3 PD+ff baseline, the same protocol as Table II's
primary rows. They have not yet been run under noise, burst disturbances, or the LQR/SMC/MPC/NMPC families; the
paper lists these as future work. Gains on Roll and Yaw360 remain near-noise-floor results, as already discussed.

## Deferred to future work (not in this paper)

- η = 0 (frozen decoder) control on the reduced CMG, to apportion fixed feedforward vs. PES learning.
- Reduced CMG with noise, disturbances, multiple seeds and the other control families.
- Non-latching CMG designs (α_hγ < 4, or v_reset below the release fold), which also make the relaxation-oscillation
  regime reachable.
- Fold / relaxation-oscillation theory and the exact event-based gradient limit (HyperLIF journal paper).
- Bias sensitivity of the resting activity before hardware experiments.

## Provenance

- Experiment: `experiments/cmg_mechanism_controls_2026-10-01/` (preregistration, harness gates G1–G3, 82 runs,
  0 failures). Mechanism note: `MECHANISM_AND_TRANSFER.md`.
- Verifier: `reproduce/verify_acc2027_claims.py` → `reproduce/claims_check.md` (73/73).
- Build: MiKTeX pdflatex + bibtex, `ieeeconf` class, 8 pages, no undefined references.
