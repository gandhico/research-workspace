"""Per-unit activity a_j(t) for CMG and the new neural arms, one figure per platform."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
STRICT = HERE.parents[0] / "neuron_basis_decisive_2026-09-24" / "results" / "strict_exact"
CONFIRM = HERE / "results" / "confirm"
OUT = HERE / "analysis"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ARMS = (("cmg", "CMG (archived, chi=1)", STRICT), ("lpf-logistic", "LPF + static logistic", CONFIRM),
        ("latch-replay", "latch replay", CONFIRM), ("cmg_chi0", "CMG chi=0", CONFIRM))
UNITS = ("+x", "+y", "+z", "-x", "-y", "-z")


def main(platforms) -> None:
    for platform in platforms:
        fig, axes = plt.subplots(len(MISSIONS), len(ARMS), figsize=(19, 12), sharex=True, sharey=True)
        for c, (arm, label, root) in enumerate(ARMS):
            for m, mission in enumerate(MISSIONS):
                z = np.load(root / platform / mission / arm / "neural_trace_full_rate.npz")
                ax = axes[m, c]
                lines = ax.plot(z["t"][::20], z["activity"][::20], lw=0.8)
                ax.set_title(f"{platform}/{mission} — {label}", fontsize=8)
                ax.set_ylim(-0.05, 1.05)
        fig.legend(lines, UNITS, loc="upper center", ncol=6, fontsize=9)
        for ax in axes[-1]:
            ax.set_xlabel("t [s]")
        for ax in axes[:, 0]:
            ax.set_ylabel("activity a")
        fig.tight_layout(rect=(0, 0, 1, 0.97))
        fig.savefig(OUT / f"activity_new_arms_{platform}.png", dpi=110)
        plt.close(fig)
        print("wrote", OUT / f"activity_new_arms_{platform}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or ("x2", "cf2-rotor"))
