"""Paired noise-robustness figure: per-seed reduction of the gated residual vs PD+ff (rho=3), both platforms.

Each dot is one seed (identical noise stream for both arms); bars are seed means; the black diamond is the
noise-free reduction.  True-attitude error.  Title-free; identification lives in the caption.
"""
import csv
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import figlib as F

HERE = Path(__file__).resolve().parent
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
LABELS = ("Roll", "Full3", "Hard45", "Hardstep", "Yaw360", "geo")
PLATFORMS = (("x2", "Skydio X2"), ("cf2-rotor", "Crazyflie 2"))


def gm(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def main(level="realistic", out_name=None):
    F.style()
    rows = [r for r in csv.DictReader((HERE / "results" / "final_noise.csv").open()) if r["noise_level"] == level]
    nom = {(r["platform"], r["mission"], r["label"]): float(r["qerr_true_mean_rad"])
           for r in csv.DictReader((HERE / "results" / "final_nominal.csv").open())}
    idx = {(r["platform"], r["mission"], int(r["seed"]), r["label"]): float(r["qerr_true_mean_rad"]) for r in rows}
    seeds = sorted({int(r["seed"]) for r in rows})
    fig, axs = plt.subplots(1, 2, figsize=(7.1, 2.35), sharey=True, gridspec_kw={"wspace": 0.06})
    rng = np.random.default_rng(3)
    for ax, (plat, title) in zip(axs, PLATFORMS):
        for j in range(6):
            if j < 5:
                m = MISSIONS[j]
                red = [100 * (1 - idx[(plat, m, s, "cmg_pes_gated")] / idx[(plat, m, s, "pdff_rho3")]) for s in seeds]
                clean = 100 * (1 - nom[(plat, m, "cmg_pes_gated")] / nom[(plat, m, "pdff_rho3")])
            else:
                red = [100 * (1 - gm([idx[(plat, m, s, "cmg_pes_gated")] for m in MISSIONS]) /
                              gm([idx[(plat, m, s, "pdff_rho3")] for m in MISSIONS])) for s in seeds]
                clean = 100 * (1 - gm([nom[(plat, m, "cmg_pes_gated")] for m in MISSIONS]) /
                               gm([nom[(plat, m, "pdff_rho3")] for m in MISSIONS]))
            col = F.GREEN if j < 5 else F.GRAY
            FLOOR = -14.0
            mean_red = np.mean(red)
            if mean_red < FLOOR:                      # diverged cell: clip, hatch, and say so
                ax.bar(j, FLOOR, width=0.62, color="#c0392b", alpha=0.30, lw=0, hatch="////", edgecolor="#c0392b")
                ax.text(j, FLOOR + 2.0, f"diverges\n({mean_red:.0f}%)", ha="center", va="bottom", fontsize=5.8, color="#8e2b20")
            else:
                ax.bar(j, mean_red, width=0.62, color=col, alpha=0.28, lw=0)
                ax.scatter(j + rng.uniform(-0.2, 0.2, len(red)), red, s=6, color=col, zorder=3, lw=0)
            ax.scatter([j], [clean], marker="D", s=14, color="black", zorder=4,
                       label="noise-free" if j == 0 else None)
        ax.axhline(0, color="#444444", lw=0.6)
        ax.set_xticks(range(6))
        ax.set_xticklabels(LABELS, rotation=0)
        ax.set_xlim(-0.6, 5.6)
        ax.set_ylim(-16, 92)
        ax.text(0.985, 0.96, title, transform=ax.transAxes, va="top", ha="right", fontsize=7)
    axs[0].set_ylabel("Error reduction (%)")
    axs[0].legend(loc="upper center", frameon=False, handletextpad=0.2, fontsize=6.4, bbox_to_anchor=(0.5, 0.99))
    fig.subplots_adjust(left=0.075, right=0.995, top=0.98, bottom=0.14)
    out = HERE / "figures_out" / (out_name or f"noise_{level}_paired_reductions")
    fig.savefig(out.with_suffix(".png"), dpi=300)
    fig.savefig(out.with_suffix(".pdf"))
    print("wrote", out)


if __name__ == "__main__":
    for lvl in (sys.argv[1:] or ["realistic"]):
        main(lvl)
