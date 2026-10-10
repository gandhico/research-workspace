# v10 (2026-09-16): cutting v9 toward the ACC 8-page ceiling

**Goal:** advisors asked to cut v9 (10 pp) to 8 pp, following `writingpapers_1.pdf` (Hespanha,
"Writing a Control Paper"). This v10 does the cut. It does **not** touch any of Sandoval's
12 v7 verdicts, any equation, any numeric result, or the certificate macros — only prose,
one full derivation write-out, and three figures.

**Heads up on the deadline:** ACC 2027's own call for papers puts the hard ceiling at
8 pages (6 included, up to 8 with an overlength fee) and the manuscript deadline at
**September 25, 2026** — 9 days out from this edit. Worth confirming with Steven/Luis that
this is still the target date you're tracking.

**Build check — read this before trusting the page count below.** I don't have your
Overleaf project's `ieeeconf.cls`, the real figures, or `architectures/tikz/*.tex` in this
session (the zip you uploaded only ever contained `ACC2027.tex`, `certificate_macros.tex`,
`references.bib` — consistent with it being an *upload-to-an-existing-project* bundle, not a
full export). So I built a local approximation: `IEEEtran.cls` in conference mode standing in
for `ieeeconf.cls`, and gray placeholder images in place of your real figures. As a sanity
check, I compiled the **unmodified v9** through this same harness first — it came out to
exactly 10 pages, matching your real Overleaf build, so the harness is tracking this
document's layout reasonably well. Treat the page numbers below as a good estimate, not a
substitute for compiling this on Overleaf.

## Result

- v9 → this edit, same harness: **10 pp → 9 pp**, and page 9 is only about 40% full
  (references [12]–[40], nothing else). That's roughly **8.75–8.8 pages worth of content**.
- Still short of 8 by a bit under a full page. See "What's left" below — closing that
  last stretch needs a call from you/Steven/Luis, not something I should decide alone.

## What changed, and why

**Cut entirely:**
1. `fig:full3_neurons` (the fixed-vs-PES internal-signal figure, was a full-width `figure*`
   after Table III). Section IV-C already narrates this figure row-by-row in prose (membrane
   rests at 0.75, gate opens past 0.5, ±y pair latches on Full3, etc.) — the figure was
   illustrating an argument the text already completes on its own. Both references to it
   (`\ref{fig:full3_neurons}`, once after Table III and once in the Ablation section) are
   repointed to the companion report. **This was the single biggest lever** — removing it
   alone (plus the small edits bundled with it) took the harness from 10 pp to ~9.15 pp.
2. `fig:cmgunit` (the single-CMG-unit coupling-topology diagram). Fully redundant with
   \eqref{eq:cmg} and the paragraph right after it, which already states the same
   membrane↔gate coupling in words. Kept the TikZ source on disk in case a journal/extended
   version wants it back.

**Shrunk:**
3. `fig:models` (CF2/X2 photo figure) from double-column `figure*` to single-column
   `figure`. **This one needs your attention**: the underlying image
   (`fig2_drones_only.pdf`) still has three panels (CF2, X2, relative-scale) baked in at
   full-textwidth size. I can't re-render that image myself — I don't have the source plot.
   At single-column width it will likely be too small to read as-is. I left a `% TODO(Gandhi)`
   comment at that spot in the .tex: either re-render it as a 2-panel image sized for one
   column, or revert this specific change back to `figure*` if you'd rather keep it full width.

**Compressed (prose only — no equation, inequality, or numeric macro was touched):**
4. Sec. III-C (Allocation-Aware Local Stability): removed the "yaw-weighted norm" aside,
   the now-redundant repeats of "not a bound between two different trajectories / not a PES
   convergence proof" (each is still stated once, consolidated into a single scope sentence
   right after the β-max discussion instead of three separate spots), and compressed the
   *derivation walk-through* for $L_r$ (the orthogonality/condition-number argument) into
   a parenthetical, pointing to the companion report for the full steps. The formula, both
   numeric values, and the sampled suprema are all still there verbatim.
5. Sec. IV-C (Ablation): removed the explicit \eqref{eq:constantbasis} display, which was
   re-deriving a special case of Proposition 3's own \eqref{eq:contraction} with leak added
   back in. Replaced with a direct pointer to Prop. 3 plus "(full recursion in the companion
   report)" — every numeric finding (pole location, DC gain 0.9998, stiffness ratios, corner
   frequency) is unchanged.
6. "Nengo realization" paragraph: trimmed from 2 sentences of implementation-API detail to 2
   tighter sentences, keeping the $2.013\times10^{-6}$ agreement number.
7. Table I footnotes (manufacturer thrust/motor-response context): shortened both.
8. Discussion (Sec. V): cut one sentence restating a minor hyperparameter note already
   covered in Sec. IV-C; trimmed the future-work sentence from 8 listed items to the 4 you
   yourselves flagged as most important (physical-platform validation is still called out as
   "most importantly," matched-effort baselines, the sampled-data certificate, and 6-DOF).

**Deliberately left untouched**, because cutting these would need your/Steven's sign-off,
not mine:
- Every equation, inequality, and every `\cert*` macro value.
- All three Proposition proofs (III-B) — on inspection these are already close to minimal;
  there wasn't defensible fat to remove without thinning the actual argument.
- Theorem 1's proof (the Lyapunov/LaSalle/ISS argument) — same call. I compressed the two
  *lemma derivations* feeding into it ($L_A$, $L_r$) but left the theorem's own proof intact,
  since it's already tight and Hespanha's own guide is explicit that a proof still needs to
  "read well," not just be a shorter equation chain.
- `fig:mech_dashboard` (neuron-family benchmark) and `fig:arch` (architecture figure) —
  your two most load-bearing figures; not touched.
- `fig:hover_int` (disturbance/retention plot) — this is the *only* visual evidence for
  Contribution 4 (the hold-equilibrium retention study). The numbers are in the text, but the
  qualitative "stays at numerical precision before the first burst, recovers after" story is
  genuinely easier to see than to read. I didn't cut it, but it's the next candidate if you
  need more room (see below).
- All 54 citations. Several are co-author self-citations added specifically in the v7→v9
  review; not mine to prune.

## What's left to close the final ~0.75–0.9 page

In rough order of how much it should recover, with the least content-costly first:

1. **Re-render `fig:models` as a real 2-panel image** sized for single-column width (item 3
   above). I couldn't measure this one's savings directly since I bundled it with the
   `fig:cmgunit` cut in the same build — do this and it may close a real chunk of what's left.
2. **Cut `fig:hover_int`**, folding its caption's one clarifying sentence ("residual is at
   numerical precision before the first burst... negligible initial correction, not zero
   computation") into the Sec. IV-D prose, which already has all the numbers. This costs
   Contribution 4 its only figure — genuinely your and Steven's call, not mine.
3. **Trim 3–5 citations.** 54 references is on the high side for an 8-page ACC paper (most
   run 20–35). I didn't touch this list since several entries look co-author-relationship-motivated,
   but if any are truly tangential a small trim here is low-risk to the science and directly
   reduces the reference block, which is currently taking up nearly a full page by itself.
4. If none of the above gets you the rest of the way, the remaining lever is the one I held
   back deliberately: turning Theorem 1's proof into a genuine 3–4 sentence sketch (full
   argument moved to the companion report), the same treatment already applied to $L_A$/$L_r$'s
   derivations. I'd want that read over by you and Steven specifically before it goes in,
   given it's the paper's main theoretical result.

## Following `writingpapers_1.pdf`

Already compliant, worth defending if a reviewer asks for more: no separate Related Work
section (guide says fold it into the intro for a conference paper — yours already does), no
numbered Definition environments, no appendix, no "In this paper..." openers, title is
plain. See my earlier message in this conversation for the full point-by-point mapping;
nothing in this edit pass changed that analysis.

## Files in this delivery

- `ACC2027.tex` — the edited source. Diff-able against your v9 copy; every change is a
  clean insertion/deletion, nothing reflowed unnecessarily.
- `certificate_macros.tex`, `references.bib` — unchanged, included so the three files can
  go straight into Overleaf as a set.
- `ACC2027_v10_for_overleaf.zip` — the three files above, zipped, ready to upload.
- `ACC2027_v10_PLACEHOLDER_FIGURES_preview.pdf` — my local build, **with gray "placeholder"
  boxes standing in for your real figures** (I don't have them in this session). Useful only
  to check that text/equations/references flow correctly after the cuts — not a real preview.
  The real page count comes from compiling on Overleaf.
