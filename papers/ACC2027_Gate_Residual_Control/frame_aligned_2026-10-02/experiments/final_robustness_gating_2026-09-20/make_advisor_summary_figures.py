"""Two advisor-facing summary figures (not paper figures): Amendment A4 (neuron/non-neural basis
comparison, corrected 2026-09-24) and Amendment A5 (controller-family portability, certified 2026-09-24).
Numbers copied verbatim from REPORT_NEURON_BASIS_CORRECTION_2026-09-24.md sec. 3.2 and
REPORT_A5_CERTIFICATION_2026-09-24.md sec. 6 -- nothing recomputed here.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent / "figures_out" / "advisor_summary_2026-09-24"
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#0072B2"   # X2 -- Okabe-Ito colorblind-safe pair
VERM = "#D55E00"   # CF2
INK = "#1a1a1a"
MUTED = "#6e6e6e"
GRID = "#dddddd"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": INK,
})


def hbar_chart(categories, x2_vals, cf2_vals, dagger_idx, title, subtitle, fname, xlim, xstep=10):
    n = len(categories)
    y = np.arange(n)[::-1]
    h = 0.32

    fig, ax = plt.subplots(figsize=(9.8, 0.62 * n + 1.6))
    b1 = ax.barh(y + h / 2 + 0.02, x2_vals, height=h, color=BLUE, label="X2", zorder=3)
    b2 = ax.barh(y - h / 2 - 0.02, cf2_vals, height=h, color=VERM, label="CF2", zorder=3)

    ax.axvline(0, color=INK, linewidth=1.0, zorder=2)
    gx = xlim[0] - (xlim[0] % xstep)
    while gx <= xlim[1]:
        if gx != 0:
            ax.axvline(gx, color=GRID, linewidth=0.7, zorder=1)
        gx += xstep

    for bars, vals in ((b1, x2_vals), (b2, cf2_vals)):
        for rect, v in zip(bars, vals):
            ha = "left" if v >= 0 else "right"
            offset = 0.8 if v >= 0 else -0.8
            ax.text(v + offset, rect.get_y() + rect.get_height() / 2, f"{v:+.1f}%",
                     ha=ha, va="center", fontsize=9.5, color=INK)

    labels = [c + (" †" if i in dagger_idx else "") for i, c in enumerate(categories)]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10.5)
    ax.set_xlim(*xlim)
    ax.set_xlabel("Geometric-mean attitude-error reduction vs. own baseline [%]  (higher = better)", fontsize=10)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(left=False)
    ax.legend(loc="lower right", frameon=False, fontsize=10)
    ax.set_title(title, fontsize=13, fontweight="bold", loc="left", pad=30)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9.2, color=MUTED, ha="left")
    fig.text(0.01, 0.005, "experiments/final_robustness_gating_2026-09-20 -- generated 2026-09-24",
              fontsize=7.5, color=MUTED)

    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(OUT / f"{fname}.png", dpi=200, bbox_inches="tight")
    fig.savefig(OUT / f"{fname}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {fname}.png / .pdf")


# --- Figure A: Amendment A4 -- neuron / non-neural basis comparison, corrected 2026-09-24 ---
cats_a = [
    "CMG (HyperLIF) - adopted",
    "LIFRate (tuned, held out)",
    "Static-paired current (non-neural)",
    "LIF (tuned, held out)",
    "Constant basis (non-neural)",
    "ALIF (tuned, held out)",
    "Izhikevich (best-tuned, held out)",
    "Izhikevich (shared protocol, same as CMG)",
]
x2_a = [37.3, 15.8, 11.7, 10.7, 10.2, 7.1, 6.2, -19.0]
cf2_a = [22.4, 11.4, 4.7, 7.3, 4.2, 4.7, 1.5, -5.5]
dagger_a = {3, 5, 6}  # LIF/ALIF/Izhikevich-tuned: selection re-verified, aggregate not re-simulated from raw files

hbar_chart(
    cats_a, x2_a, cf2_a, dagger_a,
    "Online-PES residual basis comparison",
    "CMG vs. conventional spiking/rate neuron bases and non-neural controls, 5-mission geometric mean. "
    "Amendment A4, Nengo PES learning-rate normalization corrected 2026-09-24. "
    "† selection re-verified; aggregate not independently re-simulated from raw files (disclosed, low-risk).",
    "A4_neuron_basis_comparison", (-30, 48),
)

# --- Figure B: Amendment A5 -- controller-family portability, certified 2026-09-24, NMPC corrected 2026-09-25 ---
cats_b = ["PD+ff (backstepping)", "PID+ff (ki=.3)", "LQR", "SMC", "MPC", "NMPC"]
x2_b = [37.3, 36.7, 31.1, 43.8, 33.4, 31.9]
cf2_b = [22.4, 22.4, 22.4, 26.6, 22.7, 21.7]

hbar_chart(
    cats_b, x2_b, cf2_b, set(),
    "CMG-PES residual portability across controller families",
    "Same gated residual (beta=.5 X2/.2 CF2, bw_scale=3 uniform, not re-tuned per family) attached to each "
    "baseline; geometric mean over 5 missions. Amendment A5, certified 2026-09-24; NMPC corrected 2026-09-25 "
    "(an unrelated leftover 100 Hz update-rate hold, not NMPC itself, caused its original X2 anomaly -- see "
    "AUDIT_NMPC_HOLD_RATE_2026-09-25.md). All six families net-positive on both platforms, no exceptions.",
    "A5_controller_portability", (-15, 50),
)

print("done:", OUT)
