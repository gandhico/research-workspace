# ACC 2027 — Final Polish Instructions for Overleaf Agent
**Manuscript:** Online PES Decoder Learning in Neuromorphic Residual UAV Attitude Control
**Constraint:** 8 pages, already full. Every edit below is length-neutral or length-saving. No new paragraphs, equations, figures, tables, references, experiments, or claims.

---

## PART 0 — DO NOT APPLY (rejected suggestions)

**0.1 — CRITICAL. Do not insert any statement that β = 0.5 lies below β_max.**
One proposed edit reads: *"(Note: Empirical β = 0.5 operates safely below the conservative theoretical bound β_max)."* **This is false.** Section III-D reports β_max = 9.69×10⁻⁵ (X2) and 6.43×10⁻⁴ (CF2), 2.14×10⁻³ with exact allocation. The experiments use β = 0.5, which is roughly **three to four orders of magnitude above** the bound, not below it. The manuscript already states this correctly ("far outside this conservative certificate"). Inserting the proposed sentence would put a checkable false claim in a paper whose main credibility asset is its honesty about the theory–experiment gap. A reviewer would find it in under a minute. Reject unconditionally.

**0.2 — Do not add the inertia-mismatch experiment (J → 1.2J).** It requires a new run and new numbers. Out of scope for a polish pass. (Worth doing before a journal version; not now.)

**0.3 — Do not move Eqs. (20)–(22) into a footnote.** The frozen-coefficient step is load-bearing and is referenced from Sec. III-B. Long math footnotes read badly in two-column IEEE format and the saving is small.

**0.4 — Do not compress the Nengo paragraph into a table row.** It contains the clause "tested numerical agreement, not formal equivalence," which is exactly the kind of scoped language the paper should keep.

**0.5 — Do not add a notation table.** It costs space the manuscript does not have.

**0.6 — Skip these as redundant; the text already says them.** "No motor/RPM/battery dynamics are modeled" (already in Sec. IV-A); "G = 10⁵ places resting activity at a_j ≈ 0.37" (already in Sec. IV-E); "a sweep of G is future work" (already in Sec. V).

**0.7 — Do not use `\setlength{\belowcaptionskip}{-5pt}` or similar negative skips.** ACC enforces the IEEE template; aggressive skip surgery risks a compliance flag for a couple of lines that are not needed.

---

## PART 1 — APPLY THESE (ordered by value; all length-neutral)

### 1.1 Fix the placeholder URL — *highest urgency, trivial*
**Find:** `https://github.com/your-repo`
**Replace:** `https://github.com/gandhico/cmg-pes-residual-control`

Confirm the repository name before applying — the URL must resolve at submission time. If the repository is not public by the deadline, use `available on request` instead; a dead link is worse than no link. A live placeholder in a submitted PDF is the single most conspicuous defect in the document.

---

### 1.2 Reframe the theorem's role — *highest value, same length*
**Section III-D. Find:**
> The experiments use β = 0.5, far outside this conservative certificate: stability of the reported runs is observed, not certified.

**Replace:**
> The experiments use β = 0.5, far outside this conservative certificate; the theorem is structural rather than numerical — it establishes local ISS for some β > 0 and fixes the scaling d̄ ∝ β‖ℓ‖ — while stability at β = 0.5 is observed, not certified.

**Why.** A reviewer skimming "β_max ≈ 10⁻⁴, experiments at 0.5" concludes the theory is decorative and stops reading. Naming what the theorem *does* buy you, in the same sentence that concedes what it does not, converts the paper's most obvious objection into a statement of scope. The conservatism sources (L_r overbounding the quadratic remainder, L_A taken at a vertex maximum) are already stated nearby — do not repeat them.

---

### 1.3 Quantify the abstract — *same length, stronger first impression*
**Abstract. Find:**
> Against tuned PD-feedforward baselines, the residual retains positive geometric-mean gains on both platforms after bandwidth tuning.

**Replace:**
> Against tuned PD-feedforward baselines at ρ = 3, the residual retains geometric-mean error reductions of 6.5–35.6%, degrading only on Hardstep.

**Verified against Table II:** X2 4.54 → 2.93 (35.5%), CF2 3.77 → 3.52 (6.6%); Hardstep is the only negative cell in that block (−17.0, −1.3). Naming the Hardstep exception yourself is worth more than the space it costs — it signals you know where the method breaks, and it is the first thing a careful reviewer will look for.

---

### 1.4 Scope the mechanism claim — *same length*
**Section IV-E. Find:**
> Persistent activity is therefore necessary for PES to act at all, but it does not by itself set effort;

**Replace:**
> Persistent activity is therefore necessary for effective PES adaptation in the tested regime, but it does not by itself set effort;

**Why.** "At all" is an absolute over five neuron families in one simulation study. The evidence (LIF/ALIF/LIFRate active in 0.1% of unit-samples, staying within 0.1% of baseline) supports the scoped version exactly and the absolute version only loosely. This is the one place where the manuscript's otherwise careful hedging slips, and it is in the sentence stating the paper's headline mechanism.

---

### 1.5 Fix the Fig. 1 caption — *same length*
**Find:**
> Online PES decoder learning CMG-PES Neuromorphic Residual Control architecture

**Replace:**
> CMG–PES neuromorphic residual control architecture with online PES decoder learning.

Current version is a five-noun pile with inconsistent capitalization and no terminal period. Fig. 1 is the paper's best asset; its caption should not be the weakest sentence in the document.

---

### 1.6 Define Δgeo in the Table II caption — *five words*
**Append to the Table II caption:**
> Δ geo: reduction between geometric means.

**Why.** Two plausible readings exist — reduction between geometric means (what you computed) versus geometric mean of the per-mission Δ values — and they give different numbers. Since 1.3 promotes 6.5–35.6% to the abstract, a reviewer who recomputes it under the wrong definition will file a false error report. Five words closes that.

---

### 1.7 Disambiguate "CMG" — *five words, recommended for this venue*
**Section I, first use. Find:** `coupled membrane–gate (CMG) units`
**Replace:** `coupled membrane–gate (CMG, not a control-moment gyroscope) units`

**Why.** At ACC, in an attitude-control paper about a vehicle, "CMG" has an overwhelming prior meaning as a momentum-exchange actuator. Phrases in the current text such as "the CMG path has no direct collective output" actively reinforce the wrong reading. Five words of insurance against a reviewer spending two pages confused about what your actuator is.

---

## PART 2 — FIGURE FIXES (these *save* space)

### 2.1 Fig. 4 — remove burned-in debug text
The figure carries a rendering-script suptitle (`x2 -- hard45 -- outputs / Euler / quaternions / inputs  beta=0.5  k_error=8.0  duration=45.0s`) and debug-style panel titles (`OUTPUTS -- x2 hard45 (mean improvement +53.07%)`). These duplicate the caption and look unfinished. Strip them in the plotting script; this also reclaims vertical space.

### 2.2 Fig. 4 — drop one panel
Five stacked panels in one column are illegible at print size. Drop the quaternion panel (four components, least interpretable, largely redundant with the error panel) and keep error / Euler angles / inputs. Keeping the Euler panel over the quaternion panel is the right call for a control audience. This is the largest single legibility gain available and it reduces page pressure rather than adding to it.

### 2.3 Fig. 2 — fix burned-in labels and verify the caption
The image contains lowercase labels `crazyflie 2` and `skydio x2` rendered into the graphic. Set these in title case or remove them and rely on the caption. Also **verify the caption order against the panels** — the caption reads "Left: CF2 hardware and MuJoCo model. Centre: X2 hardware and MuJoCo model," but the in-image labels appear to place the X2 model in the second position. Confirm before submission.

### 2.4 Fig. 4 axis and legend fonts
```latex
\pgfplotsset{
  every axis y label/.append style={font=\footnotesize},
  legend style={font=\tiny}
}
```
Applies inside the existing bounding box; no layout change.

---

## PART 3 — GLOBAL CONSISTENCY PASS (zero space)

Normalize throughout, without rewording surrounding text:

- **Dashes:** `CMG–PES` and `membrane–gate` with en dashes everywhere. The abstract currently uses "membrane-gate" (hyphen) while the body uses an en dash; `CMG-PES` and `CMG–PES` both appear.
- **Terminology, one term per concept:** CMG–PES · residual authority · decoder adaptation (PES) · conductance modulation · requested torque · realized torque · rotor allocation · baseline recovery.
- **Repeated phrases** — trim the second and later occurrences of "same baseline and bounded interface," "in the tested regime," and "baseline recovery" where the meaning is already established.
- **Section transitions** — improve III-D → IV and IV-E → IV-F by *rewriting the existing opening sentence*, never by adding one.
- **Captions** — make Figs. 1–4 and Tables I–II self-contained without lengthening them.

---

## PART 4 — EXACT ORDERS FOR THE OVERLEAF AGENT (standalone; paste this whole block)

> Perform a final publication-quality polish of this ACC 2027 manuscript. It is exactly 8 pages and must stay at 8 pages.
>
> ### Hard constraints
> - Do not exceed 8 pages. Do not add paragraphs, equations, figures, tables, references, experiments, or claims.
> - Prefer sentence-level rewriting, shortening, and replacement over addition.
> - Preserve every numerical value, equation, citation, label, and cross-reference exactly.
> - Do not alter mathematical derivations except to correct grammar or notation consistency.
> - Do not weaken the explicit distinction between what is proved and what is observed.
>
> ### A. Apply these seven edits verbatim
>
> **A1.** Find `https://github.com/your-repo` → replace with `https://github.com/gandhico/cmg-pes-residual-control`
>
> **A2.** Section III-D. Find:
> "The experiments use β = 0.5, far outside this conservative certificate: stability of the reported runs is observed, not certified."
> Replace with:
> "The experiments use β = 0.5, far outside this conservative certificate; the theorem is structural rather than numerical — it establishes local ISS for some β > 0 and fixes the scaling d̄ ∝ β‖ℓ‖ — while stability at β = 0.5 is observed, not certified."
>
> **A3.** Abstract. Find:
> "Against tuned PD-feedforward baselines, the residual retains positive geometric-mean gains on both platforms after bandwidth tuning."
> Replace with:
> "Against tuned PD-feedforward baselines at ρ = 3, the residual retains geometric-mean error reductions of 6.5–35.6%, degrading only on Hardstep."
>
> **A4.** Section IV-E. Find:
> "Persistent activity is therefore necessary for PES to act at all,"
> Replace with:
> "Persistent activity is therefore necessary for effective PES adaptation in the tested regime,"
>
> **A5.** Fig. 1 caption. Find:
> "Online PES decoder learning CMG-PES Neuromorphic Residual Control architecture"
> Replace with:
> "CMG–PES neuromorphic residual control architecture with online PES decoder learning."
>
> **A6.** Table II caption. Append at the end: "Δ geo: reduction between geometric means."
>
> **A7.** Section I, first use only. Find `coupled membrane–gate (CMG) units` → replace with `coupled membrane–gate (CMG, not a control-moment gyroscope) units`
>
> ### B. Global consistency pass (no rewording of surrounding text)
> - Use en dashes consistently: `CMG–PES` and `membrane–gate` everywhere. The abstract currently has "membrane-gate" with a hyphen; both `CMG-PES` and `CMG–PES` appear in the body.
> - One term per concept throughout: CMG–PES · residual authority · decoder adaptation (PES) · conductance modulation · requested torque · realized torque · rotor allocation · baseline recovery.
> - Trim second and later occurrences of "same baseline and bounded interface," "in the tested regime," and "baseline recovery" where the meaning is already established.
> - Improve the III-D → IV and IV-E → IV-F transitions by rewriting the existing opening sentence only. Do not add a sentence.
> - Polish captions for Figs. 1–4 and Tables I–II for grammar and self-containment without lengthening them.
> - Find 2–5 word cuts that improve readability. The revision should occupy the same space or slightly less.
>
> ### C. Figure changes
> - Fig. 4: remove the burned-in plotting-script title (`x2 -- hard45 -- ... beta=0.5 k_error=8.0 duration=45.0s`) and the debug-style panel headers such as `OUTPUTS -- x2 hard45 (mean improvement +53.07%)`. These duplicate the caption.
> - Fig. 4: drop the quaternion panel; keep error, Euler angles, and inputs. Five stacked panels are illegible at print size.
> - Fig. 4: add inside the figure environment —
>   `\pgfplotsset{every axis y label/.append style={font=\footnotesize}, legend style={font=\tiny}}`
> - Fig. 2: set the burned-in labels `crazyflie 2` and `skydio x2` in title case or delete them and rely on the caption. Also verify the caption's left/centre/right ordering against the actual panel order and report any mismatch; do not silently reorder.
>
> ### D. Never do these
> - **Never state or imply that β = 0.5 is below, within, or compatible with β_max.** It is three to four orders of magnitude above it. Reject any such phrasing.
> - Do not add a notation table, move Eqs. (20)–(22) into a footnote, or compress the Nengo paragraph.
> - Do not use negative `\belowcaptionskip` or similar skip surgery to reclaim space.
> - Do not add any claim about hardware validation, global stability, neuromorphic efficiency, or generality beyond the current experiments.
>
> ### E. Preserve exactly; flag rather than "simplify"
> 1. That the local stability result is conditional and does not certify the reported β = 0.5 experiments.
> 2. The Hardstep explanation — degradation occurs only in the tuned high-bandwidth Hardstep cells, where 63°–111° changes every 2 s interact with latched-decoder lag and torque-box saturation.
> 3. The Section V limitations paragraph, which is correctly scoped.
>
> ### F. Style and override rule
> Concise ACC/IEEE technical prose. Direct claims, minimal adjectives, no promotional language.
>
> **Override rule:** if any proposed change could alter scientific meaning, leave the original text unchanged and flag it in a list at the end instead of editing it. This applies especially to theorem statements, bound values, and experimental claims.
>
> Output the diff and the page count. Do not apply changes silently.

---

## Review the diff for these four things before accepting
1. No sentence anywhere now asserts that β = 0.5 satisfies the theorem's bound.
2. Every number in Table II and Sec. III-D is byte-identical to the current version.
3. The word "necessary" in Sec. IV-E is scoped, and no other hedge was removed elsewhere to "improve directness."
4. Proposition and Theorem statements are untouched.
