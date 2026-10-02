"""Status figure: what the stronger baselines did to the picture.

Top row: attitude-only missions (the Table V setting), mean quaternion-angle
error. Bottom row: 6-DOF cascade, mean position error. Log axis, because the
values span ~1e-6 to ~1; a dot plot, because bars on a log axis have no
meaningful baseline. Colour follows the controller across every panel; each
series also has its own marker, so colour is never the only cue.
CMG on the tuned baselines uses the beta chosen by the pre-declared rule
(sweep_cmg_beta_2026_09_10.py / compile_ff6_report.py).
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
RES = HERE.parent
SIX = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments"
           r"\six_dof_expansion_2026-08-31\results\ff6_2026-09-10\ff6_report.csv")

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
S = {  # fixed categorical order: reference palette slots 1-6
    "orig": ("Original PD (Table V / canonical)", "#2a78d6", "o"),
    "cmg_orig": ("CMG on original PD", "#eb6834", "s"),
    "pdff": ("Tuned PD + feedforward", "#1baf7a", "D"),
    "cmg_tuned": ("CMG on tuned PD + ff", "#eda100", "^"),
    "bs": ("Backstepping, tuned", "#e87ba4", "v"),
    "cmg_bs": ("CMG on tuned backstepping", "#008300", "P"),
}
OFFS = {"orig": -0.30, "cmg_orig": -0.18, "pdff": -0.06,
        "cmg_tuned": 0.06, "bs": 0.18, "cmg_bs": 0.30}
ATT_M = ("roll", "full3", "hard45", "hardstep", "yaw360")
SIX_M = ("waypoint_step", "circle_xy", "full6_stress")


def rows(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


ff = {(r["platform"], r["mission"]): r
      for r in rows(RES / "pid_baseline_2026-09-10" / "rate_ff_summary.csv")}
bl = rows(HERE / "baselines_summary.csv")
pdff_t = {(r["platform"], r["mission"]): float(r["PDff_tuned"]) for r in bl if r["family"] == "pdff"}
bs_t = {(r["platform"], r["mission"]): float(r["family_alone"]) for r in bl if r["family"] == "backstepping"}
cb = rows(HERE / "cmg_beta_summary.csv")
cmg_pdff = {(r["platform"], r["mission"]): float(r["CMG_on_family"]) for r in cb if r["family"] == "pdff"}
cmg_bs = {(r["platform"], r["mission"]): float(r["CMG_on_family"]) for r in cb if r["family"] == "backstepping"}
beta_of = {(r["family"], r["platform"]): r["beta"] for r in cb}
six = {(r["platform"], r["mission"]): r for r in rows(SIX)}

fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor=SURFACE)


def panel(ax, missions, series_vals, title, ylabel):
    ax.set_facecolor(SURFACE)
    for key, vals in series_vals.items():
        label, color, mk = S[key]
        xs = [i + OFFS[key] for i in range(len(missions))]
        # The 2 px surface ring separates overlapping dots, but it eats most
        # of a plus glyph, so the plus gets a thin ring and a larger size.
        ax.scatter(xs, vals, s=(150 if mk == "P" else 100 if mk in "^v" else 64),
                   color=color, marker=mk, zorder=3, edgecolors=SURFACE,
                   linewidths=(0.6 if mk == "P" else 2), label=label)
    ax.set_yscale("log")
    ax.set_xticks(range(len(missions)))
    ax.set_xticklabels([m.replace("_step", "").replace("_xy", "").replace("_stress", "")
                        for m in missions], color=INK2, fontsize=10)
    ax.tick_params(axis="y", colors=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.set_title(title, loc="left", color=INK, fontsize=11.5, fontweight="bold")
    ax.set_ylabel(ylabel, color=INK2, fontsize=10)


for col, (plat, name) in enumerate((("x2", "X2"), ("cf2-rotor", "CF2"))):
    panel(axes[0, col], ATT_M, {
        "orig": [float(ff[(plat, m)]["PD"]) for m in ATT_M],
        "cmg_orig": [float(ff[(plat, m)]["CMG_on_PD"]) for m in ATT_M],
        "pdff": [pdff_t[(plat, m)] for m in ATT_M],
        "cmg_tuned": [cmg_pdff[(plat, m)] for m in ATT_M],
        "bs": [bs_t[(plat, m)] for m in ATT_M],
        "cmg_bs": [cmg_bs[(plat, m)] for m in ATT_M],
    }, f"{name} — attitude missions\n"
       f"CMG β: on PD+ff {beta_of[('pdff', plat)]}, on backstepping "
       f"{beta_of[('backstepping', plat)]}", "mean attitude error [rad]")
    p6 = "X2" if plat == "x2" else "CF2"
    panel(axes[1, col], SIX_M, {
        "orig": [float(six[(p6, m)]["canonPD_pos"]) for m in SIX_M],
        "cmg_orig": [float(six[(p6, m)]["canonCMG_pos"]) for m in SIX_M],
        "pdff": [float(six[(p6, m)]["tunedPD_pos"]) for m in SIX_M],
        "cmg_tuned": [float(six[(p6, m)]["CMGtuned_pos"]) for m in SIX_M],
    }, f"{name} — 6-DOF cascade   (CMG β {six[(p6, 'circle_xy')]['beta']})",
       "mean position error [m]")

handles = [plt.Line2D([], [], marker=S[k][2], color=S[k][1], linestyle="", markersize=8,
                      markeredgecolor=SURFACE, markeredgewidth=1.5, label=S[k][0]) for k in S]
fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=9.5,
           labelcolor=INK, bbox_to_anchor=(0.5, 0.995))
fig.text(0.01, 0.005, "Log scale; lower is better. CMG β on each tuned baseline is chosen by a rule "
         "fixed before the results (geometric mean of per-mission ratios). "
         "The 6-DOF cascade has no backstepping variant.", color=INK2, fontsize=8.5)
fig.tight_layout(rect=(0, 0.02, 1, 0.92))
out = HERE / "status_2026-09-10.png"
fig.savefig(out, dpi=170, facecolor=SURFACE)
print(f"wrote {out}")
