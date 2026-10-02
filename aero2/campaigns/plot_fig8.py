"""Figure-8 plots: pitch + yaw response, PD (linear) vs qpd/quaternion (nonlinear),
on pitch_yaw_steps. One figure per platform x language.
Usage: python plot_fig8.py <offline|twin|hardware> <python|matlab>
"""
from __future__ import annotations
import glob
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = r"C:\Research\aero2"
backend = sys.argv[1] if len(sys.argv) > 1 else "twin"
lang = sys.argv[2] if len(sys.argv) > 2 else "python"
mode = {"twin": "virtual_twin", "hardware": "hardware", "offline": "offline"}[backend]
FIGDIR = os.path.join(REPO, "results_paper", "figures")
os.makedirs(FIGDIR, exist_ok=True)
CTRLS = [("pd", "PD (linear)", "tab:blue"), ("qpd", "Quaternion PD (nonlinear)", "tab:red")]


def load(ctrl):
    if lang == "matlab":
        fs = sorted(glob.glob(os.path.join(REPO, "results_matlab", f"steps_{backend}_{ctrl}_*.csv")))
        if not fs:
            return None
        a = np.genfromtxt(fs[-1], delimiter=",", names=True)
        return dict(t=a["t"], th=np.rad2deg(a["theta"]), ps=np.rad2deg(a["psi"]),
                    rth=np.rad2deg(a["theta_ref"]), rps=np.rad2deg(a["psi_ref"]))
    fs = sorted(glob.glob(os.path.join(REPO, "results_paper", backend,
                                       f"helicopter_2dof_{mode}_{ctrl}_pitch_yaw_steps_*.npz")))
    if not fs:
        return None
    d = np.load(fs[-1], allow_pickle=True)
    x, ref = d["x_est"], d["ref"]
    return dict(t=d["t"], th=np.rad2deg(x[:, 0]), ps=np.rad2deg(x[:, 2]),
                rth=np.rad2deg(ref[:, 0]), rps=np.rad2deg(ref[:, 2]))


fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
refdone = False
hz = ""
for ctrl, label, color in CTRLS:
    D = load(ctrl)
    if D is None:
        print("MISSING", lang, ctrl, flush=True)
        continue
    if not refdone:
        ax[0].plot(D["t"], D["rth"], "k--", lw=1.0, label="reference")
        ax[1].plot(D["t"], D["rps"], "k--", lw=1.0, label="reference")
        refdone = True
    ax[0].plot(D["t"], D["th"], color=color, lw=1.3, label=label)
    ax[1].plot(D["t"], D["ps"], color=color, lw=1.3, label=label)
    if not hz and len(D["t"]) > 1:
        hz = f"{(len(D['t'])-1)/(D['t'][-1]-D['t'][0]):.0f} Hz"

ax[0].set_ylabel("pitch  theta [deg]"); ax[1].set_ylabel("yaw  psi [deg]")
ax[1].set_xlabel("time [s]"); ax[0].grid(alpha=0.3); ax[1].grid(alpha=0.3)
ax[0].legend(fontsize=8, loc="best")
ax[0].set_title(f"Aero2 pitch-yaw steps  |  {backend}  |  {lang}  ({hz})")
out = os.path.join(FIGDIR, f"fig8_{backend}_{lang}.png")
fig.tight_layout(); fig.savefig(out, dpi=200)
print("SAVED_FIG", out, flush=True)
