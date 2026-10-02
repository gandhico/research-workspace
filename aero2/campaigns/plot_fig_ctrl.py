"""Paper figure: PD (linear) vs Backstepping (nonlinear) on reference tracking.
2x2 minimal layout: pitch & yaw response (top) + control inputs (bottom).
Usage: python plot_fig_ctrl.py <twin|hardware> [python|matlab]
"""
from __future__ import annotations
import glob
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update({
    "font.size": 10, "axes.grid": True, "grid.alpha": 0.25,
    "axes.linewidth": 0.8, "lines.linewidth": 1.5, "figure.dpi": 110,
})

REPO = r"C:\Research\aero2"
backend = sys.argv[1] if len(sys.argv) > 1 else "twin"
lang = sys.argv[2] if len(sys.argv) > 2 else "python"
mode = {"twin": "virtual_twin", "hardware": "hardware", "offline": "offline"}[backend]
DATA = os.path.join(REPO, "results_paper", backend)
FIG = os.path.join(REPO, "results_paper", "figures")
os.makedirs(FIG, exist_ok=True)
CTRLS = [("pd", "PD (linear)", "#1f77b4"), ("backstepping", "Backstepping (nonlinear)", "#d62728")]


def latest(ctrl):
    fs = sorted(glob.glob(os.path.join(DATA, f"helicopter_2dof_{mode}_{ctrl}_reference_tracking_*.npz")))
    return fs[-1] if fs else None


fig, ax = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
refd = False
hz = ""
for ctrl, label, color in CTRLS:
    f = latest(ctrl)
    if not f:
        print("MISSING", ctrl, flush=True)
        continue
    d = np.load(f, allow_pickle=True)
    t, x, u, ref = d["t"], d["x_est"], d["u"], d["ref"]
    if not refd:
        ax[0, 0].plot(t, np.rad2deg(ref[:, 0]), "k--", lw=1.0, label="reference")
        ax[0, 1].plot(t, np.rad2deg(ref[:, 2]), "k--", lw=1.0, label="reference")
        refd = True
    ax[0, 0].plot(t, np.rad2deg(x[:, 0]), color=color, label=label)
    ax[0, 1].plot(t, np.rad2deg(x[:, 2]), color=color, label=label)
    ax[1, 0].plot(t, u[:, 0], color=color)
    ax[1, 1].plot(t, u[:, 1], color=color)
    if not hz and len(t) > 1:
        hz = f"{(len(t)-1)/(t[-1]-t[0]):.0f} Hz"

ax[0, 0].set_ylabel(r"pitch $\theta$ [deg]")
ax[0, 1].set_ylabel(r"yaw $\psi$ [deg]")
ax[1, 0].set_ylabel(r"$u_\theta$ [V]")
ax[1, 1].set_ylabel(r"$u_\psi$ [V]")
ax[1, 0].set_xlabel("time [s]")
ax[1, 1].set_xlabel("time [s]")
for a in ax.ravel():
    a.margins(x=0)
handles, labels = ax[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 0.99))
fig.suptitle(f"Aero2 reference tracking  |  {backend}  |  {lang}  ({hz})", y=0.925, fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.90])
out = os.path.join(FIG, f"fig_ctrl_{backend}_{lang}.png")
fig.savefig(out, dpi=220)
print("SAVED", out, flush=True)
