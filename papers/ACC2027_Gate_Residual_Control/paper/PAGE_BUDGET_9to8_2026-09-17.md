# Getting the 9-page Overleaf version to 8 — measured page budget

Source measured: `Online_PES_Decoder_HyperLIF_Residual_Control___Quaternion_Tracking (13).pdf`
(9 pp., 40 refs, 4 figures, 2 tables). All numbers below are measured from the PDF
geometry, not estimated: `scratchpad/measure_v13*.py`, `slack_hist.py`.

## 1. How much has to go

| Quantity | Value |
|---|---|
| Text frame | 688.9 pt per column, 2 columns = 1377.8 pt per page |
| Page 9 occupies | left column 684 pt (full) + right column 419 pt |
| **Space to free** | **1103 pt = 1.60 columns = 0.80 page** |
| In prose terms | 99 body lines at 11.14 pt = **~880 words** |

This is not a trim. Page 9 is 72 % full of bibliography, and killing it means
recovering four fifths of a page from somewhere.

## 2. Where the space currently is

Non-body area on pp. 1–8 totals 2731 pt (1.98 pages):

| Block | Column-pt | Share of a page |
|---|---|---|
| Fig. 1 (architecture, full width, p2 top) | **574** | 0.42 |
| Table II (results, full width, p7 top) | **561** | 0.41 |
| Fig. 4 (X2 Hard45, p6 right) | **402** | 0.29 |
| Title block + abstract + index terms (p1) | 397 | 0.29 |
| Table I (parameters, p6 left) | 328 | 0.24 |
| Fig. 2 (vehicle photos, full width, p2) | 256 | 0.19 |
| Fig. 3 (CMG coupling topology, p4 left) | 160 | 0.12 |
| Orphan blank, bottom of p1 left column | 53 | 0.04 |

## 3. The prose is already tight — this is the decisive measurement

49 paragraph-final prose lines across pp. 1–8:

| Last line fills | Paragraphs |
|---|---|
| 0–30 % of the column | 4 |
| 30–50 % | 5 |
| 50–70 % | 13 |
| 70–85 % | 11 |
| 85–100 % | 16 |

Median 72 %, mean 71 %. Only **9** paragraphs carry a short tail, so
`\looseness=-1` and two-word trims are worth about **100 pt (0.07 page)** in total,
not the half-page such a pass usually yields. **8 pages cannot be reached by
rewriting.** It has to come out of the bibliography and the floats.

## 4. Levers, with measured yield

### Free — no content lost (722 pt total)

| # | Action | Yield |
|---|---|---|
| 1 | Bibliography 40 → 31: merge the five duplicate-source pairs and drop four single-purpose cites (§5) | **255 pt** |
| 2 | Bibliography formatting: drop "accessed Sep. 5, 2026" and add `\url` break points on the eight web entries (~1 line each) | **69 pt** |
| 3 | Fold Sec. IV-E (Ablation) into Table II's note — the text already reads "(figure omitted)" there | **~150 pt** |
| 4 | Tables I and II: `\renewcommand\arraystretch{0.92}`, `\tabcolsep=4pt`, note at `\scriptsize` | **~95 pt** |
| 5 | `\looseness=-1` on the nine short-tailed paragraphs, plus the 53 pt orphan blank on p1 | **153 pt** |

That is 722 pt of the 1103 needed — **65 %. It lands at about 8.4 pages.**
The remaining 381 pt has to come from a figure or from the theory.

### Route A — keep every equation and proof, lose the photo strip

| # | Action | Yield |
|---|---|---|
| 6 | Drop Fig. 2 (hardware/model photos) and state it in one sentence in Sec. IV-A | **256 pt** |
| 7 | Fig. 1 at `0.85\textwidth`, Fig. 4 at `0.82\linewidth`, Fig. 3 at `0.88\linewidth` | **~200 pt** |

Total **1178 pt** vs 1103 needed — 7 % margin. Fig. 2 is the only element in the
paper with no technical content; the three results figures survive at 15 % smaller
print. Nothing mathematical is removed.

### Route B — touch no figure, move the proof out

| # | Action | Yield |
|---|---|---|
| 6' | Move Thm. 1's proof and the `r*`/`beta_max` algebra to the companion; keep the statement and every number | **~690 pt** |

Total **1412 pt** — comfortable. But this is exactly Steven's comment #7 (the LaSalle
argument he asked for) and comment #8, so it gives back a reviewer-visible strength
to save space.

**Recommendation: Route A.** The photo strip costs nothing to lose; the proof does.

## 5. The nine bibliography entries to merge or drop

Each entry averages 28.3 pt (3.3 lines at 8 pt), so this is 255 pt.

| Drop | Keep | Why |
|---|---|---|
| [31] Menagerie repo | [32] Menagerie `crazyflie_2` README | Same source; the README is the one carrying the actuator-limit caveat |
| [36] Measuring Propeller RPM | [35] PWM to Thrust | Same vendor measurement note, cited together |
| [33] Crazyflie 2.0 product page | [32], [35] | Vendor page adds nothing the README and thrust note do not |
| [10] MacNeil & Eliasmith | [11] Voelker PES report | Both are PES background; [11] is the derivation actually used |
| [13] DeWolf, Jaworski, Eliasmith | [12] DeWolf et al. | Two PES-application cites; [12] is the adaptive-control one |
| [17] Schaub & Junkins | [18] Diebel | Both for quaternion conventions |
| [20] Chaturvedi et al. | [19] Bhat & Bernstein, [21] Mayhew et al. | Three cites for one topological-obstruction claim |
| [38] Ioannou & Kokotovic | [39] Ioannou & Sun | Both for sigma-modification |
| [3] Li et al. HPA-PPO | [1], [2] | Related-work padding; [1] residual RL and [2] L1 carry the argument |

The eight co-author self-cites ([4]–[7], [14], [15], [22], [23]) are left alone.

## 6. What is *not* worth doing

- Shrinking the abstract or title block: 397 pt, but it is content and IEEE-fixed.
- Cutting Table II: it is the paper's main result, and at 561 pt it is already
  carrying five controllers x ten cells x two platforms.
- A general prose pass: measured above at 100 pt for the whole paper.

## 7. Order of operations

Do 1–5 first and rebuild — they cost nothing and the yield is certain. Measure the
page count, then add exactly as much of Route A as the overflow needs; LaTeX reflow
is lumpy, so expect the last 100 pt to move the page break by more than its size.
