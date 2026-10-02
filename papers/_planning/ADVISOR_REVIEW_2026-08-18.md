# P1/P2/P3 Review for Advisors — 2026-08-18 night session

Extensive review of latest results/code/paper drafts, cross-checked against raw registries.
Nothing discarded — this ranks/segments what's most advisor-ready tonight; all underlying
data stays in place under `papers\P*\`.

---

## P1 — HyperLIF Learning (`papers\P1_HyperLIF_Learning\`)

**Status: strong, near submission-ready. Top priority to share tonight.**

- Paper's central claims are well-calibrated against the data, not overclaimed. The abstract
  and "six claims" (main.tex line 44) explicitly say HyperLIF "does not universally dominate
  adaptive neurons" — this matches the raw July 19 preflight registry's own
  `results\p1_plif_alif_ff_nmnist_tiny_20260719\P1_FF_NMNIST_TINY_PREFLIGHT_SUMMARY.md`,
  which lists "Unsafe: HyperLIF universally beats ALIF" as an explicit claim boundary. The
  paper respects that boundary.
- **Verified data freshness**: the reviewer-baseline table in main.tex (PLIF/ALIF numbers:
  0.8967, 0.5570, 0.5650, 0.5473...) matches the July 19, 2026 HPC registry
  (`results\p1_baseline_arch_shortlist_shd_wide_20260719\HPC_RESULTS.md` and the N-MNIST
  preflight summary) to 3-4 decimal places. The paper is using current, correctly-transcribed
  numbers, not stale ones.
- Discussion/Limitations sections are honestly self-critical: deep residual conv case doesn't
  train reliably, Julia/APEX cross-framework accuracy is weak in absolute terms (~24-25% on a
  20-class task) and is explicitly scoped as "not the headline benchmark table."
- **Open item**: Acknowledgment section is still a placeholder — *"Funding, advisor
  acknowledgments, compute resources, and repository links will be inserted before
  submission."* Advisors will see this as unfinished if shared as-is; either fill it in or
  flag it explicitly when sharing.
- **Minor note, not a problem**: an older `results\spine_summary.md` (dated 2026-06-24) shows
  different SHD accuracy numbers (~0.79) than the July 19 registry (~0.57) under different
  naming (`HyperLIF.voltage` vs `rsnn.hyperlif.hybrid_vr`). This looks like an earlier/looser
  exploratory sweep superseded by the more rigorous July 19 run — the paper does not cite
  spine_summary.md's numbers. Kept as archival data per your "don't discard anything" rule,
  but don't confuse it for a current result if you spot it.

**Recommended for tonight's package**: `main.pdf`/`main.tex`, the 5 figures, and the two
July 19 results folders (`p1_baseline_arch_shortlist_shd_wide_20260719`,
`p1_plif_alif_ff_nmnist_tiny_20260719`) as the supporting data.

---

## P2 — HyperLIF in Nengo/NEF (`papers\P2_HyperLIF_Nengo\`)

**Status: strongest self-documented readiness of the three. Send tonight with its own audit attached.**

P2 already has a rigorous internal audit the user (or a past session) wrote on 2026-07-20:
`RESULTS_AUDIT.md` (22 claims individually classified ✅ validated / 🔬 exploratory /
🔮 future work, each tied to a specific evidence CSV) and
`CLAIM_ARTIFACT_AUDIT_2026_07_20.md` (submission-readiness checklist). I verified these are
still current — no results have changed since (`results\csv\18_nef_decoder_state_ablation*`
dated 7/19/2026 8:23pm is the latest file in the whole results tree, one day before the audit).

- **Readiness Decision (from the audit): P2 is at 91%.** "The scientific core is strong. The
  remaining 9% is not mainly experiments. It is submission mechanics."
- Every core claim (exact Python/Nengo parity, DB-onset prediction `J_DB=2.4`, latched voltage
  prediction, adaptive stability bound, integration-scheme stability, backend-portability
  limitation, 5-seed decoder ablation) is marked "Paper-ready," each with a named CSV/log as
  evidence — not just asserted.
- **Submission Risks Still Open** (the audit's own list, all still valid):
  1. `paper\main_ieee.tex` is a stale June draft missing the Nengo capability/decoder-ablation
     results — needs regenerating from current `paper\main.tex`.
  2. Author block/metadata are placeholders — no acknowledgments, funding, or data/code
     availability statement yet.
  3. 27-page PDF with dense tables — needs a main-text-vs-appendix decision.
  4. **Journal target undecided** — the audit notes *"TNNLS rejected the old paper; this P2 is
     a different implementation/NEF paper."* This is a real open question for advisors, not
     just formatting.
  5. Advisor approval itself is pending — the audit literally recommends sending this package
     with the audit attached and asking whether they want another decoder expansion or
     submission polish.

**Recommended for tonight's package**: `paper\main.tex`/PDF, `RESULTS_AUDIT.md`,
`CLAIM_ARTIFACT_AUDIT_2026_07_20.md` (send these two audits *as-is* — they're already written
for exactly this purpose), and the `figures\`/`tables\` directories. This is the most
"ready to just send" of the three papers — the audit already frames the two open questions
(venue choice, scope of remaining polish) you need advisor input on.

---

## P3 — Gate-Residual Control (`papers\P3_Gate_Residual\`)

**Status: this is your flagship paper — and I found and fixed a real internal contradiction tonight.**

`_planning\P3_FUSION_PLAN_2026_07_20.md` (also written a month ago) frames P3 as the paper
meant to directly answer a prior **TNNLS rejection** ("practical advantage unclear") by
fusing three results into one arc: fixed decode = safety, adaptive conductance = a proven
boundary/null result, learned decode = the performance headline (+86.7% CF2 / ~57% X2). That
fusion into one manuscript **has not happened yet** — `fixed_adaptive\` and `learned\` are
still two separate `.tex` sources. That's a real scope decision (4 open questions in the
fusion plan §7: venue, hardware-as-pillar, cross-substrate depth, learned-gate-as-main-result)
— I did not make that call for you, it needs your advisors' input.

**What I did fix tonight**: the fusion plan states a non-negotiable — *"never attribute a
gate-mode improvement to Adaptive."* `fixed_adaptive\paper\main2.tex` was violating its own
non-negotiable: the Contributions list (bullet 3) and the Results-section opening sentence
both still claimed "Adaptive HyperLIF... outperforms fixed HyperLIF," while the paper's own
detailed Results section (lines 526-601) already correctly proved the two are bit-for-bit
*identical* in gate mode, with the mechanism explained. This was an internal contradiction a
reviewer would have caught immediately. I corrected the two contradicting spots to match what
the rest of the paper already correctly says — no results were changed, only two sentences
that were describing them wrong.

**PDF rebuilt successfully** (installed MiKTeX — this machine had no LaTeX distribution at
all before tonight; none of P1/P2/P3's `.tex` sources had ever actually been compiled here,
only pre-built PDFs existed). Rebuilding surfaced **3 more pre-existing issues**, unrelated to
my content fix, that had never been caught because the paper had never been compiled:
- `skydiox2_crazyflie2_mujoco_cropped (1)` (the platforms illustration photo) — file doesn't
  exist anywhere on C: or the D: backup.
- `compare_skydio_x2_hard45_euler` and `compare_skydio_x2_hard45_torques` (a two-panel Skydio
  diagnostics figure) — also missing from both locations.

I commented out these 3 figure blocks (with `TODO` markers naming exactly what's missing and
how to regenerate the two data plots — `run_rotor_level.py --mission hard45 --quad skydio_x2
--save-figures`) and softened the sentences that referenced them by name, so the PDF compiles
cleanly rather than blocking on missing images. **`main2.pdf` now builds clean, 7 pages.**
The platforms photo likely needs to be re-taken/re-exported by hand — it's an illustration,
not a data plot, so I can't regenerate it from results data.

The `learned\` paper was already internally consistent: it has its own dedicated
"Performance–robustness frontier" section (`\label{sec:frontier}`) discussing the `k_rate`
robustness knob alongside the headline number (respecting the fusion plan's second
non-negotiable), and explicitly states "Adaptive HyperLIF is provably redundant" — no
contradiction there.

**Real open gap, not fixable tonight**: the `learned\` results dossier says everything is
reproducible from `neuromorphic-robotics-control\experiments\controller_benchmarks\
learned_gate_experiment.py` — this file **does not exist** on either C: or D:. Only the paper
and results dossier survive; the generating code is gone from every location available on
this machine. If an advisor or reviewer asks to see the code, that's a gap you'd need to
answer (recovered from GitHub? another old machine?), not something I can restore from backup.

Also restored tonight: `quaternion_quad\` (independent Julia/Python ODE cross-check, separate
from the MuJoCo sim, tiny — 0.15MB) — this is supporting/validation code, not itself a paper
draft.

**Recommended for tonight's package**: both `fixed_adaptive\paper\` (once PDF rebuilds) and
`learned\paper\`, plus `_planning\P3_FUSION_PLAN_2026_07_20.md` itself — since it already
frames exactly the questions you need advisor input on (fuse now vs. later, which of the 4
open scope decisions). Flag the missing `learned_gate_experiment.py` explicitly rather than
letting an advisor discover it by asking.
