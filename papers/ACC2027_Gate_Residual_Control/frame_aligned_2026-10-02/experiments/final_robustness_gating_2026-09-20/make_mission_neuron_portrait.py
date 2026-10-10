"""Advisor-facing 'surprise' figure: mission portraits + CMG neuron activity, across all 5 X2 missions.
Not a paper figure. Data: results/a5_controllers/backstepping/x2/{mission}/{classical,nengo-nef-pes}/trace.csv
(certified bit-exact against the sealed primary campaign -- REPORT_A5_CERTIFICATION_2026-09-24.md sec.4), the
primary architecture (PD+ff/backstepping) at rho=3, beta=.5, the paper's own headline configuration.

Three rows per mission column: (1) the reference Euler triple actually commanded -- abstract in the paper
(equations only), concrete here; (2) the six CMG units' activity a_j(t) as a heatmap -- direct visual evidence
for the paper's own claimed mechanism (Sec. IV-B: resting a_j~0.37, latched a_j=1); (3) true attitude error,
baseline vs. +CMG-PES, log scale, showing where the residual helps and by how much.
"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "results" / "a5_controllers" / "backstepping" / "x2"
OUT = HERE / "figures_out" / "advisor_summary_2026-09-24"
OUT.mkdir(parents=True, exist_ok=True)

MISSIONS = ["roll", "full3", "hard45", "hardstep", "yaw360"]
TITLES = {"roll": "Roll", "full3": "Full3", "hard45": "Hard45", "hardstep": "Hardstep", "yaw360": "Yaw360"}

BLUE = "#0072B2"    # baseline (classical) -- matches X2's color in the other advisor chart
RED = "#B2182B"     # CMG -- matches the paper's established red=CMG convention
INK = "#1a1a1a"
MUTED = "#6e6e6e"
GRID = "#e5e5e5"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "text.color": INK,
                      "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})


def load(mission, arm):
    with open(DATA / mission / arm / "trace.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    t = np.array([float(r["t"]) for r in rows])
    ref = np.array([[float(r["ref_roll"]), float(r["ref_pitch"]), float(r["ref_yaw"])] for r in rows])
    qerr = np.array([float(r["qerr_true_rad"]) for r in rows]) * 1e3  # mrad
    act = None
    if arm == "nengo-nef-pes":
        act = np.array([[float(r[f"activity_{i}"]) for i in range(6)] for r in rows]).T  # (6, T)
    return t, ref, qerr, act


fig = plt.figure(figsize=(19, 9.2))
gs = gridspec.GridSpec(3, 5, height_ratios=[1.0, 1.05, 1.0], hspace=0.42, wspace=0.24,
                        left=0.045, right=0.985, top=0.90, bottom=0.075)

ref_lines = None
err_lines = None
for col, m in enumerate(MISSIONS):
    t, ref_c, qerr_c, _ = load(m, "classical")
    _, ref_g, qerr_g, act = load(m, "nengo-nef-pes")

    ax1 = fig.add_subplot(gs[0, col])
    l1, = ax1.plot(t, ref_c[:, 0], color="#333333", lw=1.3, label="Roll ref")
    l2, = ax1.plot(t, ref_c[:, 1], color="#D55E00", lw=1.3, label="Pitch ref")
    l3, = ax1.plot(t, ref_c[:, 2], color="#0072B2", lw=1.3, label="Yaw ref")
    ax1.set_title(TITLES[m], fontsize=13, fontweight="bold", pad=8)
    ax1.axhline(0, color=GRID, lw=0.8, zorder=0)
    ax1.set_xlim(0, 45)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)
    if col == 0:
        ax1.set_ylabel("reference\n[rad]", fontsize=10)
        ref_lines = (l1, l2, l3)
    ax1.tick_params(labelbottom=False)

    ax2 = fig.add_subplot(gs[1, col])
    im = ax2.imshow(act, aspect="auto", origin="lower", cmap="Reds", vmin=0, vmax=1,
                     extent=[0, 45, 0.5, 6.5], interpolation="nearest")
    ax2.set_yticks([1, 2, 3, 4, 5, 6])
    if col == 0:
        ax2.set_ylabel("CMG unit\nactivity $a_j$", fontsize=10)
        ax2.set_yticklabels(["1", "2", "3", "4", "5", "6"], fontsize=8)
    else:
        ax2.set_yticklabels([])
    ax2.tick_params(labelbottom=False)
    mean_act = act.mean()
    ax2.text(0.98, 0.92, f"mean {mean_act:.2f}", transform=ax2.transAxes, ha="right", va="top",
              fontsize=8.5, color="white" if mean_act > 0.55 else INK,
              bbox=dict(boxstyle="round,pad=0.15", fc=RED if mean_act > 0.55 else "white",
                         ec="none", alpha=0.85 if mean_act > 0.55 else 0.0))

    ax3 = fig.add_subplot(gs[2, col])
    lb, = ax3.plot(t, np.maximum(qerr_c, 1e-4), color=BLUE, lw=1.5, ls="--", label="baseline (classical)")
    lc, = ax3.plot(t, np.maximum(qerr_g, 1e-4), color=RED, lw=1.5, label="+CMG-PES")
    ax3.set_yscale("log")
    ax3.set_xlim(0, 45)
    ax3.set_xlabel("t [s]", fontsize=9.5)
    for s in ("top", "right"):
        ax3.spines[s].set_visible(False)
    if col == 0:
        ax3.set_ylabel("attitude error\n[mrad, log]", fontsize=10)
        err_lines = (lb, lc)

fig.legend(ref_lines, ["Roll ref", "Pitch ref", "Yaw ref"], loc="upper left", bbox_to_anchor=(0.045, 0.985),
           ncol=3, frameon=False, fontsize=9.5, handlelength=1.6, columnspacing=1.2)
fig.legend(err_lines, ["baseline (classical)", "+CMG-PES (gated)"], loc="upper right", bbox_to_anchor=(0.985, 0.985),
           ncol=2, frameon=False, fontsize=9.5, handlelength=1.6, columnspacing=1.2)

cax = fig.add_axes([0.40, 0.965, 0.20, 0.012])
cb = fig.colorbar(im, cax=cax, orientation="horizontal")
cb.set_ticks([0, 0.37, 1])
cb.set_ticklabels(["0", "rest .37", "1 (latched)"])
cb.ax.tick_params(labelsize=8, length=2)
cb.outline.set_visible(False)

fig.suptitle("Mission portraits: reference, CMG neuron activity, and tracking error -- X2, PD+ff (backstepping), "
             "$\\rho=3$, $\\beta=.5$, gated", fontsize=13.5, fontweight="bold", y=1.015, x=0.045, ha="left")
fig.text(0.045, 0.995, "Same run family reported in Table II / Fig. 4 of the paper (certified bit-exact vs. the "
          "sealed campaign). Row 2: darker = more CMG units driven off their resting activity ($a_j{\\approx}.37$) "
          "toward latched ($a_j{=}1$) -- direct visual evidence for Sec. IV-B's mechanism claim.",
          fontsize=9, color=MUTED, ha="left", va="top")
fig.text(0.005, 0.005, "experiments/final_robustness_gating_2026-09-20 -- generated 2026-09-25", fontsize=7.5, color=MUTED)

fig.savefig(OUT / "mission_neuron_portraits.png", dpi=200, bbox_inches="tight")
fig.savefig(OUT / "mission_neuron_portraits.pdf", bbox_inches="tight")
plt.close(fig)
print("wrote mission_neuron_portraits.png / .pdf ->", OUT)
