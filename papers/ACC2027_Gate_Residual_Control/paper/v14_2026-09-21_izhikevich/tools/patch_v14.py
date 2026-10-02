r"""v14 text patch: the rival-basis (Izhikevich) results under the primary protocol enter the paper.

Every number is read from the analysis outputs of amendment A3 (results/izh_a3_numbers.json, izh_a3_rails.json,
results_validation_izh/floor/floor_result.json) - nothing is typed by hand.  Exact-one-match assertions on every replaced passage,
so the script cannot be re-run on its own output (historical, like patch_stage7/8).  Start from the v13 sources:
    ACC2027.tex, tables/table_all_restructured.tex  copied from v13; then
    python experiments/final_robustness_gating_2026-09-20/make_table2_izh.py <v14>/tables/table_all_restructured.tex --write
    python tools/patch_v14.py

Edits: abstract (last sentence), Sec. IV-E, conclusion clause, Table II footnote, and the space/typography trims below (each loses
no result: the numbers of a trimmed sentence stay in Table II or in the text next to it; six paragraphs ending in a very short last
line get \looseness=-1).  Two figures are also 0.25 in shorter (experiments/.../make_v14_figures.py).
"""
import json
from pathlib import Path

D = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\paper\v14_2026-09-21_izhikevich")
EXP = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\final_robustness_gating_2026-09-20")
N = json.loads((EXP / "results" / "izh_a3_numbers.json").read_text(encoding="utf-8"))
RAIL = json.loads((EXP / "results" / "izh_a3_rails.json").read_text(encoding="utf-8"))
FLOOR = json.loads((EXP / "results_validation_izh" / "floor" / "floor_result.json").read_text(encoding="utf-8"))
nom, summ, dist, noise, hs = N["nominal"], N["summary"], N["disturbance"], N["noise"], N["hardstep_cells"]

sd_rel = max(v["sd_rel"] for v in FLOOR.values()) * 100          # worst cell, % of the mean error
sd_pp = max(v["sd_pp_of_pdff"] for v in FLOOR.values())         # worst cell, points of the PD+ff error
T = {
    "SD": f"{sd_rel:.1f}", "THR": f"{3 * sd_pp:.0f}",
    "RMIN": f"{100 * RAIL['izh_rails_min']:.0f}", "RMAX": f"{100 * RAIL['izh_rails_max']:.0f}",
    "EIX": f"{summ['x2']['effort_izh']:.2f}", "EIC": f"{summ['cf2-rotor']['effort_izh']:.2f}",
    "GX": f"{summ['x2']['geo_izh_mrad'] / summ['x2']['geo_pd_mrad']:.1f}", "GC": f"{summ['cf2-rotor']['geo_izh_mrad'] / summ['cf2-rotor']['geo_pd_mrad']:.1f}",
    "UX": f"{-hs['x2/izh_pes_ungated_b0p5']['red']:.1f}", "GXH": f"{-hs['x2/izh_pes_gated_b0p5']['red']:.1f}",
    "CGH": f"{-hs['cf2-rotor/izh_pes_gated_b0p2']['red']:.1f}",
    "GEOX": f"{-summ['x2']['geo_red_izh']:.0f}", "GEOC": f"{-summ['cf2-rotor']['geo_red_izh']:.0f}",
}
# effort ratio (mean over the two airframes' ratios is not quoted: the text says "ten times", which both ratios bracket)
ratios = (summ["x2"]["effort_ratio"], summ["cf2-rotor"]["effort_ratio"])
assert 9.0 <= min(ratios) and max(ratios) <= 12.0, ratios


def fill(s: str) -> str:
    for k, v in T.items():
        s = s.replace(f"@{k}@", v)
    assert "@" not in s.replace(r"\@", ""), s
    return s


def sub(text: str, old: str, new: str, tag: str) -> str:
    assert text.count(old) == 1, f"{tag}: {text.count(old)} matches"
    print("ok  ", tag)
    return text.replace(old, new)


tex_path = D / "ACC2027.tex"
tex = tex_path.read_text(encoding="utf-8")

# ---- abstract
tex = sub(tex,
          r"An Izhikevich basis lowers fixed-PD error a few points more than CMG at three times the realized effort ($0.37$ versus $0.12$ of the axis bound); ablations",
          fill(r"On the same tuned baseline an Izhikevich basis raises the geometric-mean error of PD+ff by $@GEOX@\%$ (X2) and $@GEOC@\%$ (CF2) at about ten times the realized effort of CMG; ablations"),
          "abstract")

# ---- Sec. IV-E
a = tex.index(r" Second, lower error is not free:")
b = tex.index(r"markedly lower realized effort.", a) + len(r"markedly lower realized effort.")
new_E = fill(
    r" Second, persistent activity is necessary but not sufficient. Proposition~\ref{prop:pes} explains the flat rows: a silent basis stalls the update. "
    r"LIF, ALIF and LIFRate units are active in at most $0.1\%$ of unit-samples, whereas CMG (resting at $a_j\approx0.37$) and Izhikevich are active in ${\ge}99.9\%$."
    "\n\n"
    r"Izhikevich--PES leads on the fixed-PD baseline (Table~\ref{tab:all}, last block) but not on the tuned one: under the primary protocol it is level with or below CMG on Full3 and Hard45, "
    r"but its residual sits on a $\pm\beta\ell$ rail in $@RMIN@$--$@RMAX@\%$ of samples whatever the mission, so its effort ($@EIX@$ of the axis bound on X2, $@EIC@$ on CF2) is ten times CMG's, which follows the baseline error. "
    r"That floor exceeds the baseline's whole error on Roll and Yaw360 and persists under noise and between hover bursts: the geometric-mean error is $@GX@\times$ (X2) and $@GC@\times$ (CF2) the baseline's. "
    r"The gate is not specific to CMG: it cuts Izhikevich's X2 Hardstep loss from $@UX@\%$ to $@GXH@\%$ and turns its CF2 divergence at $\beta=.2$ into $-@CGH@\%$."
)
tex = tex[:a] + new_E + tex[b:]
print("ok   Sec. IV-E")

# ---- conclusion (one clause)
tex = sub(tex,
          r"the ablations identify online decoder adaptation and persistent activity as the principal mechanisms in the tested regime.",
          r"the ablations identify online decoder adaptation and persistent activity (necessary, but not sufficient for low effort) as the principal mechanisms in the tested regime.",
          "conclusion")

# ---- space trims (no result lost)
tex = sub(tex,
          r"so the residual has nothing left to remove and changes it by $-$1.4/$-$3.9\% (X2) and $+$2.2/$-$2.0\% (CF2); at the realistic level, $-$4.2/$-$5.3\% and $-$0.4/$-$2.2\%.",
          r"so the residual has nothing left to remove and changes it by $-$5.3 to $+$2.2\% at the two levels (Table~\ref{tab:all}).",
          "trim noise sentence")
tex = sub(tex,
          r"Pitch and yaw are as indistinguishable from the reference as roll, so the residual's effect is read from the error panel; the",
          r"Pitch and yaw are as indistinguishable from the reference as roll; the",
          "trim Fig. 2 caption")
tex = sub(tex,
          r"Table~\ref{tab:all} also reports the baseline ladder. Against the original fixed PD law, the residual lowers mean quaternion-angle error in all ten nominal cases by $17.3$--$60.6\%$. The apparent margin thus shrinks as the classical baseline is strengthened.",
          r"Against the original fixed PD law (Table~\ref{tab:all}, which also gives the $\rho=1$ ladder), the residual lowers mean quaternion-angle error in all ten nominal cases by $17.3$--$60.6\%$, so the apparent margin shrinks as the classical baseline is strengthened.",
          "trim ladder sentence")
tex = sub(tex,
          r"For CF2 the burst-phase reduction is $13.7\%$ at $\beta=.5$ and $1.5\%$ in the ungated $\beta=.05$ configuration.",
          r"For CF2 it is $13.7\%$ at $\beta=.5$ and $1.5\%$ ungated at $\beta=.05$.",
          "trim CF2 burst sentence")
tex = sub(tex,
          r" Without the gate, CF2 admits only $\beta=.05$ and the reduction is $6.5\%$ (Table~\ref{tab:all}, ungated row); with the gate at $\beta=.5$ it reaches $36.5\%$ noise-free but diverges on Hardstep under noise (Sec.~\ref{sec:noise}).",
          r" Without the gate, CF2 admits only $\beta=.05$ and the reduction is $6.5\%$ (Table~\ref{tab:all}, ungated row).",
          "trim beta=.5 clause (kept in Secs. IV-F, IV-G)")
tex = sub(tex,
          r" Removing the tail would need decoder-side lag compensation; we leave that, and a systematic study of the gate, to future work.",
          "",
          "trim future-work sentence (kept in the conclusion)")
tex = sub(tex,
          r"Both tests use the tuned PD+feedforward baseline and score the error of the \emph{true} attitude.",
          r"Both tests use the tuned PD+feedforward baseline and score the \emph{true}-attitude error.",
          "trim noise-section opening")

# ---- typography only: paragraphs that end in a very short last line get \looseness=-1 (no wording changes)
for tail in (r"preserving its plant and actuator interface.",
             r"These are kinematic identities; no convergence claim is implied.",
             r"not an optimization-based allocator \cite{monteiro2016allocation}.",
             r"This bandwidth-tuned PD+feedforward controller is the primary baseline.",
             r"Both arms see the same noise stream.",
             r"being dominated by missions whose baseline error is already near the noise floor."):
    tex = sub(tex, tail + "\n", tail + r"\looseness=-1" + "\n", f"looseness: ...{tail[-40:]}")
tex_path.write_text(tex, encoding="utf-8")

# ---- table footnote
tp = D / "tables" / "table_all_restructured.tex"
tt = tp.read_text(encoding="utf-8")
tt = sub(tt,
         r"Noise rows: true-attitude error, seed means, same noise stream for both arms (realistic $0.020$\,rad, $0.050$\,rad\,s$^{-1}$, $10$ seeds; moderate $0.010$, $0.025$, $5$).",
         fill(r"Noise rows: true-attitude error, seed means, same noise stream for both arms (levels: Sec.~\ref{sec:noise}). "
              r"Izhikevich $\rho=3$ rows: gated, one run per cell (noise: seeds 1--3; $33$ runs in all); single-run scatter is $@SD@\%$ of the error "
              r"(s.d. of seven runs with initial-attitude offsets below $2\times10^{-13}$\,rad), so differences below $@THR@$ points are not interpreted."),
         "table footnote")
tp.write_text(tt, encoding="utf-8")
print(json.dumps(T, indent=1))
