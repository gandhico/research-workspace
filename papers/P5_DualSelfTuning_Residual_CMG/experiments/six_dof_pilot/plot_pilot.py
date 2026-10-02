"""6-DOF pilot figure: gain multipliers from quadrature (v4) vs known-controller identification, full6_stress."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "results" / "six_dof_pilot_2026-09-12"
TARGET = {"x2": (1 / 1.6564388, 1 / 1.43510296, 1 / 0.41983376), "cf2-rotor": (1.0, 1.0, 1.0)}
COLORS = ("#1b6ca8", "#d1495b", "#3c8d2f")
fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True, constrained_layout=True)
for i, (p, pname) in enumerate((("x2", "Skydio X2 (wn_att 20/20/17.5)"), ("cf2-rotor", "Crazyflie 2 (wn_att 24/24/20.4)"))):
    for j, (c, cname) in enumerate((("cas_idgc_v4", "quadrature lock-in (v4)"),
                                    ("cas_idgc_kc", "known-controller complex lock-in"))):
        ax = axes[i, j]
        with (OUT / p / "full6_stress" / c / "trace.csv").open(encoding="utf-8") as f:
            tr = list(csv.DictReader(f))
        t = np.array([float(r["t"]) for r in tr])
        for a, name, col, tg in zip("xyz", ("roll", "pitch", "yaw"), COLORS, TARGET[p]):
            ax.plot(t, [float(r[f"mp_{a}"]) for r in tr], color=col, lw=2, label=f"m {name}")
            ax.axhline(tg, color=col, lw=1, ls="--")
        ax.axvline(3.0, color="#888888", lw=1, ls=":")
        ax.set_ylim(0.3, 2.6)
        ax.grid(alpha=0.25)
        ax.set_title(f"{pname}: {cname}", fontsize=9.5)
        ax.set_ylabel("gain multiplier m")
        if i == 1:
            ax.set_xlabel("time [s]")
        if i == 0 and j == 0:
            ax.legend(fontsize=8, loc="upper left")
fig.suptitle("6-DOF pilot, full6_stress: identification-based gain correction on the tuned cascade "
             "(dashed = model J/j_tune; dotted = end of 3 s warm-up)", fontsize=10.5)
for ext in ("png", "pdf"):
    fig.savefig(OUT / f"pilot_idgc_multipliers.{ext}", dpi=170)
print("wrote", OUT / "pilot_idgc_multipliers.png")
