# Proposal — Strengthening the Statistical Treatment of the Ceiling Effect (§VII-C, Fig. 10)

**To:** Dr. Garcia Carrillo, Hilda C. Contreras Aguirre, Hengameh Mirhajianmoghadam, Omar A. Garcia Alcantara
**From:** Gandhi A. S. Contreras Torres
**Re:** Reviewer-flagged weakness in the score-distribution analysis, and a correct, defensible replacement.

---

## 1. Why we should change the current analysis

Reviewers flagged the score-distribution analysis (Fig. 10 / §VII-C) as *"the most exploitable methodological weakness in the paper."* Three concrete problems:

1. **An unbounded Gaussian is fit to bounded [0, 100] data.** The theoretical curve (µ = 93.6, σ = 14.9) necessarily extends past 100 and assigns probability to impossible scores. This is not a cosmetic issue: **it argues *against* us.** A ceiling effect means probability mass *piles up against the wall at 100*; a symmetric Gaussian instead spreads that mass *through and beyond* 100. So the very figure meant to show a ceiling is drawn with a model that cannot represent one. A sharp reviewer will say the ceiling claim is an artifact of the wrong distributional model.
2. **"Significantly broader variance" is asserted with no inferential test.** As written, "significantly" is unsupported and should either be backed by a test or replaced with "noticeably."
3. **The θ→DT transition is analyzed as two independent pools**, ignoring that the same 21 students generate both sets of scores (repeated measures), and the performance index δ = s_theory − s_DT is never aggregated across the cohort — so the two case studies (Students A, B) float free of the class.

The good news: **the underlying finding is real and defensible.** Scores drop and disperse when students move from theory to digital-twin labs. We just need to measure it with tools that respect the data's structure (bounded, skewed, paired, clustered).

---

## 2. Proposed analysis (what to do instead)

### 2.1 Describe the distributions honestly (replaces the Gaussian overlay)
For each category (Theoretical, Digital-Twin) report: **n** (state both the number of scores and that they come from 21 students × k modules), **mean, median, SD, IQR, skewness**, and — the quantity that actually defines a ceiling — **the proportion of scores at/near the maximum** (e.g., % ≥ 95 and % = 100). A common rule of thumb: **> 15 % of observations at the maximum indicates a ceiling effect** [Terwee et al.]; report that number for both categories. This turns "pronounced ceiling effect" from an assertion into a measurement.

Replace the unbounded Gaussian with one of (in order of preference):
- **(a) Empirical only** — histogram + a *bounded* kernel density (reflected boundary or a Beta kernel) so nothing spills past 100. Simplest and unimpeachable.
- **(b) Beta fit** on x/100 ∈ [0, 1] — its natural support is [0, 1] and it can be strongly left-skewed, so it *represents* a ceiling rather than contradicting it. Overlay it if a smooth parametric curve is wanted.
- **(c) Truncated normal** on [0, 100] — acceptable but weaker than Beta for skewed data.

### 2.2 Test the theory→DT difference with a paired, nonparametric test
The design is **within-student and paired**: each student takes a theoretical lab, then the matched digital-twin lab on the *same topic* (module pairs (4,5), (6,7), (10,11) per Table II). Use this structure:
- **Wilcoxon signed-rank test** on the aligned within-student pairs. It is nonparametric (no normality assumption) and robust to the ceiling/skew — exactly the right tool for bounded scores.
- Report the test statistic, an **exact p-value**, and a **matched-pairs effect size** (rank-biserial correlation, or Cliff's δ). Effect size matters more than p at N = 21.
- With three module pairs, apply a **Holm correction** across them, or analyze the pooled within-student δ.

### 2.3 Report the δ index across the whole cohort (reviewer asked for this explicitly)
Aggregate δ = s_theory − s_DT over all students and aligned pairs; report **median, IQR, and range**, and show a **box or violin plot of δ**. Then Students A and B are presented as points on that distribution — anchored to the cohort, not floating anecdotes.

### 2.4 Support the "broader variance" claim with a dispersion test
The ceiling argument is fundamentally *about variance* (the ceiling compresses it). Test it directly:
- **Brown–Forsythe / Levene** (robust to non-normality) or **Fligner–Killeen** for equal dispersion between the two categories.
- Report the **SD or IQR ratio with a bootstrap 95 % CI**. "DT variance is 1.3× theoretical (95 % CI …)" is a clean, honest sentence that replaces "significantly broader."

### 2.5 Respect the clustering (independence caveat)
Scores are **repeated within students**. Either (i) do the analysis on the within-student aligned pairs as above (recommended, sidesteps the issue), or (ii) if pooling across modules for the distribution plots, state it explicitly and add a one-line caveat, or fit a **linear mixed model** with a random intercept per student. Do **not** present 21 × k pooled scores as independent observations.

### 2.6 Frame honestly for N = 21
Keep it descriptive/exploratory: exact nonparametric tests, effect sizes with CIs, no causal language. This is fully consistent with the Limitations paragraph already in §IX (small, mostly-graduate, single offering, non-equated instruments). Also resolve the **COI note** from §V — if any co-author's own scores are inside N = 21, exclude them and report N = 20.

---

## 3. Concrete change to Fig. 10
Replace the two-Gaussian figure with a two-panel figure:
- **(a)** Overlaid **violin + box** of Theoretical vs Digital-Twin scores with jittered individual points; annotate median, IQR, and **% at ceiling**. No unbounded curve.
- **(b)** **δ distribution** (box/violin across all 21 students) with Students A and B marked — ties §VII-B to §VII-C.

Suggested caption sentence: *"Digital-twin laboratories show a lower median (82 vs 94) and X× greater dispersion (IQR ratio, 95 % CI …); Y % of theoretical scores sit at the ceiling (≥ 95) versus Z % for digital-twin labs (Wilcoxon signed-rank on aligned module pairs, p = …, rank-biserial = …)."*

---

## 4. What I can do next
I've written a ready-to-run script, `ceiling_effect_analysis.py`, that produces **every number and both panels above** from a de-identified scores table. I just need the data in this shape (no names — an anonymous `student_id` is enough):

```
student_id, module, category, score      # category ∈ {theoretical, digital_twin}
S01, 4, theoretical, 90
S01, 5, digital_twin, 40
...
```

Send me that CSV (or the gradebook export and I'll reshape it) and I'll return the corrected Fig. 10, the filled-in caption, and the exact test statistics for §VII-C — usually within one pass.

---

*Note on scope:* this proposal is about **measurement rigor**, not about softening the result. Every recommended method is *more* likely to survive review than the current one, and each directly answers a specific reviewer note (unbounded model, missing test, missing δ distribution, unstated n/clustering).
