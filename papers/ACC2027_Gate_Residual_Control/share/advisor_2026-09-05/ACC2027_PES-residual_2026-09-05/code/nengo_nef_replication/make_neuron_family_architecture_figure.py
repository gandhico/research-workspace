"""Create a publication-ready schematic of the matched family benchmark."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "neuron_family_compiled"
OUT.mkdir(parents=True, exist_ok=True)


def box(ax, xy, wh, text, color, fontsize=9):
    patch = FancyBboxPatch(xy, *wh, boxstyle="round,pad=0.02", fc=color, ec="#333333", lw=1.2)
    ax.add_patch(patch)
    ax.text(xy[0] + wh[0] / 2, xy[1] + wh[1] / 2, text, ha="center", va="center", fontsize=fontsize)
    return patch


def arrow(ax, start, end, text="", bend=0):
    patch = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, lw=1.25,
                            color="#333333", connectionstyle=f"arc3,rad={bend}")
    ax.add_patch(patch)
    if text:
        ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.025, text,
                ha="center", va="bottom", fontsize=8)


fig, ax = plt.subplots(figsize=(15, 7), constrained_layout=True)
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
box(ax, (0.02, 0.60), (0.12, 0.16), "mission\n" + r"$q^\star,\omega^\star$", "#E8E8E8")
box(ax, (0.18, 0.60), (0.14, 0.16), "quaternion PD\n$\\tau_0$", "#D6EAF8")
box(ax, (0.36, 0.57), (0.16, 0.22), "paired currents\n$J^+,J^-\\in[0.75,2]$\n6 signed channels", "#FFF2CC")
box(ax, (0.56, 0.50), (0.17, 0.36), "natural observable\n\nCMG: gate activity\nLIF: filtered spikes\nALIF: filtered spikes\nIzh: filtered spikes\nLIFRate: filtered rate", "#E2F0D9", 8.5)
box(ax, (0.77, 0.60), (0.10, 0.16), "$y=Wa$\n$W\\in\\mathbb{R}^{3\\times6}$", "#F4CCCC")
box(ax, (0.90, 0.60), (0.08, 0.16), "clip, $\\beta$\n$\\delta\\tau$", "#FCE5CD")
box(ax, (0.73, 0.17), (0.16, 0.16), "actuator mixer +\nMuJoCo plant", "#D9D2E9")
box(ax, (0.43, 0.17), (0.16, 0.16), "measured $q,\\omega$\nerror + metrics", "#E8E8E8")
box(ax, (0.60, 0.89), (0.20, 0.08), "PES: $\\Delta W=\\eta(y^\\star-y)a^T$", "#F4CCCC", 9)

arrow(ax, (0.14, 0.68), (0.18, 0.68))
arrow(ax, (0.32, 0.68), (0.36, 0.68), "$\\tau_0$")
arrow(ax, (0.52, 0.68), (0.56, 0.68))
arrow(ax, (0.73, 0.68), (0.77, 0.68), "$a$")
arrow(ax, (0.87, 0.68), (0.90, 0.68), "$y$")
arrow(ax, (0.94, 0.60), (0.84, 0.33), "$\\tau=\\mathrm{sat}(\\tau_0+\\delta\\tau)$")
arrow(ax, (0.73, 0.25), (0.59, 0.25))
arrow(ax, (0.43, 0.25), (0.25, 0.60), "feedback", bend=-0.2)
arrow(ax, (0.54, 0.33), (0.68, 0.89), bend=0.15)
ax.text(0.57, 0.42, r"$y^\star=-8e_q$", ha="center", fontsize=9)
arrow(ax, (0.70, 0.89), (0.82, 0.76), "online only")

ax.text(0.5, 0.04,
        "Fixed and PES cases share plant, PD, six units, calibrated one-feature/channel representation, decoder size, bounds, and missions.",
        ha="center", fontsize=10, weight="bold")
fig.suptitle("Matched Nengo neuron-family residual-control testbench", fontsize=16, weight="bold")
fig.savefig(OUT / "neuron_family_architecture.png", dpi=260)
fig.savefig(OUT / "neuron_family_architecture.pdf")
plt.close(fig)
print(OUT / "neuron_family_architecture.png")
