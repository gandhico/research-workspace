"""Build the paper's single result table: one two-column matrix, missions as columns.

Layout notes that matter for the printed geometry:
  * the explanatory note lives AFTER \\end{tabular}, not as a \\multicolumn p{} row inside it --
    a full-width p{} row forces the tabular to that width and dumps the slack into the last
    column, which is what put a gap in front of the CF2 "geo" column;
  * a small gap separates the two platform groups;
  * error and Delta rows close with a geometric mean, effort rows with an arithmetic mean.
"""
from __future__ import annotations

import collections
import csv
import statistics as st
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
R = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\results")
NF = R / "neuron_family_compiled/neuron_family_results.csv"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ML = ("Roll", "Full3", "Hard45", "Hardstep$^\\dagger$", "Yaw360")
PLATS = (("x2", "X2"), ("cf2-rotor", "CF2"))
# Table as published: PD, CMG, reduction, fixed-decoder reduction, realistic-noise reduction
TAB2 = {
    ("x2", "roll"): (.050565, .041785, 17.36, 1.93, 32.2), ("x2", "full3"): (.303275, .131748, 56.56, 9.74, 55.7),
    ("x2", "hard45"): (.294082, .138007, 53.07, 10.27, 52.3), ("x2", "hardstep"): (.454528, .359355, 20.94, 0.46, 20.6),
    ("x2", "yaw360"): (.075863, .029902, 60.58, 0.12, 47.8),
    ("cf2-rotor", "roll"): (.051337, .042439, 17.33, 3.31, 32.5),
    ("cf2-rotor", "full3"): (.288383, .126476, 56.14, 4.53, 55.2),
    ("cf2-rotor", "hard45"): (.285449, .132319, 53.65, 6.80, 52.7),
    ("cf2-rotor", "hardstep"): (.426182, .347886, 18.37, 0.42, 18.1),
    ("cf2-rotor", "yaw360"): (.075812, .029870, 60.60, 0.06, 47.8),
}
MOD = {("x2", "roll"): 32.3, ("x2", "full3"): 56.4, ("x2", "hard45"): 52.9, ("x2", "hardstep"): 20.8,
       ("x2", "yaw360"): 56.8, ("cf2-rotor", "roll"): 32.4, ("cf2-rotor", "full3"): 55.9,
       ("cf2-rotor", "hard45"): 53.4, ("cf2-rotor", "hardstep"): 18.3, ("cf2-rotor", "yaw360"): 56.8}
master = {(r["platform"], r["mission"]): r for r in
          csv.DictReader((HERE / "master_table.csv").open(encoding="utf-8"))}
fam = collections.defaultdict(dict)
for r in csv.DictReader(NF.open(encoding="utf-8")):
    fam[r["family_mode"]][(r["platform"], r["mission"])] = r


def geo(v):
    return float(np.exp(np.mean([np.log(x) for x in v])))


def err(x):
    v = 1e3 * x
    return f"{v:.2f}" if v >= 0.1 else f"{v:.3f}"


def row_abs(get):
    out = []
    for p, _ in PLATS:
        vals = [get(p, m) for m in MISSIONS]
        out += [err(v) for v in vals] + ["\\emph{%s}" % err(geo(vals))]
    return out


def row_red(get_base, get_new, dash_geo=False):
    out = []
    for p, _ in PLATS:
        b = [get_base(p, m) for m in MISSIONS]
        n = [get_new(p, m) for m in MISSIONS]
        out += [f"{100 * (1 - x / y):.1f}" for x, y in zip(n, b)]
        out += ["--"] if dash_geo else ["\\emph{%.1f}" % (100 * (1 - geo(n) / geo(b)))]
    return out


def row_effort(mode):
    """Normalized residual effort per mission, closed by the arithmetic mean."""
    out = []
    for p, _ in PLATS:
        v = [float(fam[mode][(p, m)]["residual_utilization_rms"]) for m in MISSIONS]
        out += [f"{x:.2f}" for x in v] + ["\\emph{%.2f}" % st.mean(v)]
    return out


pd_e = lambda p, m: TAB2[(p, m)][0]           # noqa: E731
cmg_e = lambda p, m: TAB2[(p, m)][1]          # noqa: E731
ff1_b = lambda p, m: float(master[(p, m)]["PDff_1x"])         # noqa: E731
ff1_c = lambda p, m: float(master[(p, m)]["CMG_on_PDff_1x"])  # noqa: E731
ff3_b = lambda p, m: float(master[(p, m)]["PDff_3x"])         # noqa: E731
ff3_c = lambda p, m: float(master[(p, m)]["CMG_on_PDff_3x"])  # noqa: E731
fam_err = lambda mode: (lambda p, m: float(fam[mode][(p, m)]["qerr_mean_rad"]))  # noqa: E731

BLOCKS = [
    ("PD baseline, $\\bm\\omega_n=(4,4,3.5)$ rad/s", [
        ("PD", row_abs(pd_e)),
        ("\\;+CMG--PES", row_abs(cmg_e)),
        ("\\;\\;$\\Delta$ [\\%]", row_red(pd_e, cmg_e)),
        ("\\;\\;$\\Delta$, fixed decoder [\\%]", row_red(pd_e, fam_err("cmg-fixed"))),
        ("\\;\\;$\\Delta$, moderate noise [\\%]",
         [v for p, _ in PLATS for v in [f"{MOD[(p, m)]:.1f}" for m in MISSIONS] + ["--"]]),
        ("\\;\\;$\\Delta$, realistic noise [\\%]",
         [v for p, _ in PLATS for v in [f"{TAB2[(p, m)][4]:.1f}" for m in MISSIONS] + ["--"]]),
    ]),
    ("Same baseline and bounded interface: strongest rival basis, and realized effort", [
        ("\\;\\;$\\Delta$, Izhikevich--PES [\\%]", row_red(pd_e, fam_err("izhikevich-pes"))),
        ("\\;\\;$\\Delta$, Izhikevich fixed [\\%]", row_red(pd_e, fam_err("izhikevich-fixed"))),
        ("\\;\\;effort, CMG--PES", row_effort("cmg-pes")),
        ("\\;\\;effort, Izhikevich--PES", row_effort("izhikevich-pes")),
    ]),
    ("PD + rate feedforward \\eqref{eq:pdff}, $\\rho=1$", [
        ("PD+ff", row_abs(ff1_b)), ("\\;+CMG--PES", row_abs(ff1_c)),
        ("\\;\\;$\\Delta$ [\\%]", row_red(ff1_b, ff1_c)),
    ]),
    ("PD + feedforward, $\\rho=3$ (bandwidth-tuned)", [
        ("PD+ff", row_abs(ff3_b)), ("\\;+CMG--PES", row_abs(ff3_c)),
        ("\\;\\;$\\Delta$ [\\%]", row_red(ff3_b, ff3_c)),
    ]),
]

silent = {k: st.mean(float(fam[k][(p, m)]["residual_utilization_rms"])
                     for p in ("x2", "cf2-rotor") for m in MISSIONS)
          for k in ("lif-pes", "alif-pes", "lifrate-pes")}
NC = 1 + 2 * (len(MISSIONS) + 1)
GAP = "@{\\hspace{7pt}}"
L = [r"\begin{table*}[t]",
     r"\caption{Mean $q$-error, $10^{-3}$\,rad, 45\,s; $\Delta$ = reduction over the block's own "
     r"baseline [\%]; effort = RMS residual as a fraction of the per-axis bound. Closing column: "
     r"geometric mean, arithmetic for the effort rows.}",
     r"\label{tab:all}\centering\scriptsize\setlength{\tabcolsep}{3.4pt}",
     r"\begin{tabular}{@{}l" + "rrrrrr" + GAP + r"rrrrrr@{}}", r"\toprule",
     r"&\multicolumn{6}{c" + GAP + r"}{Skydio X2}&\multicolumn{6}{c}{Crazyflie~2, $1.5\times$ rotor design}\\",
     r"\cmidrule(lr){2-7}\cmidrule(l){8-13}",
     " & ".join([""] + list(ML) + ["\\emph{geo}"] + list(ML) + ["\\emph{geo}"]) + r"\\"]
for title, rows in BLOCKS:
    L.append(r"\midrule")
    L.append(r"\multicolumn{%d}{@{}l}{\textit{%s}}\\[1pt]" % (NC, title))
    for lab, vals in rows:
        L.append(" & ".join([lab] + vals) + r"\\")
L += [r"\bottomrule", r"\end{tabular}",
      r"\par\smallskip",
      r"\begin{minipage}{\textwidth}\footnotesize",
      r"LIF, ALIF and LIFRate stay within $0.1\%%$ of the baseline outside Hardstep (best $18.5\%%$ on "
      r"X2, $8.4\%%$ on CF2 there) at an effort of $%.2f$--$%.2f$, so they are summarised here rather "
      r"than tabulated. Noise rows are two-seed means, seed SD below $0.03$ pp. $^\dagger$Hardstep "
      r"commands $63$--$111^\circ$ steps every $2$\,s, so $97$--$99\%%$ of its mean error is slew; "
      r"Sec.~\ref{sec:ladder} scores it by settling time instead."
      % (min(silent.values()), max(silent.values())),
      r"\end{minipage}", r"\end{table*}"]
(HERE / "tex_table_all.tex").write_text("\n".join(L) + "\n", encoding="utf-8")

md = ["| | " + " | ".join(list(ML) + ["geo"] + list(ML) + ["geo"]) + " |", "|" + "---|" * NC]
for title, rows in BLOCKS:
    t = (title.replace("$\\bm\\omega_n$", "wn").replace("$\\rho", "rho").replace("\\rho", "rho")
         .replace("$", "").replace("\\%", "%").replace("\\eqref{eq:pdff}", "(12)"))
    md.append(f"| **{t}** " + "| " * (NC - 1) + "|")
    for lab, vals in rows:
        clean = (lab.replace("\\;", "").replace("$\\Delta$", "D").replace("[\\%]", "%")
                 .replace("--", "-"))
        cells = [v.replace("\\emph{", "**").replace("}", "**") if "emph" in v else v for v in vals]
        md.append("| " + " | ".join([clean] + cells) + " |")
(HERE / "merged_table_preview.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
