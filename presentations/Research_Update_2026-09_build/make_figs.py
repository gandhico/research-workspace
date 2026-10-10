"""Figures for the Sept-2026 research-update deck.

Every figure is drawn from a saved result file (no typed numbers):
  - Julia Qube-Servo 3 twin swing-up + LQR balance CSV (julia_bridge/results)
  - DILISIC 80 s contract-fixed reference trajectory (dilisic/reference)
  - Basilisk MJScene single-satellite 600 s trace (spacecraft_twin/results)
Also autocrops the MuJoCo omnicopter render and downsizes the ToE platform photo.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

OUT = Path(__file__).resolve().parent / "figs"
OUT.mkdir(parents=True, exist_ok=True)

CRIMSON = "#8C0B41"
TEAL = "#5F7F86"      # darker variant of the template's A7BABE for lines
TEAL_LIGHT = "#A7BABE"
SAND = "#CFC7BD"
INK = "#262626"
GRID = "#D9D9D9"

plt.rcParams.update({
    "font.family": ["Calibri", "DejaVu Sans"],
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "axes.edgecolor": "#7F7F7F",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": "#404040",
    "ytick.color": "#404040",
    "axes.labelcolor": INK,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "legend.frameon": False,
    "savefig.dpi": 220,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.04,
})


def julia_qube():
    csv = Path(r"C:\Research\julia_bridge\results\twin_swingup_julia_twin_sign1_20260723_025715.csv")
    meta = json.loads(csv.with_suffix(".json").read_text())
    d = pd.read_csv(csv)
    t = d["t"].to_numpy()
    alpha = d["alpha_deg"].to_numpy()
    volt = d["voltage"].to_numpy()
    mode = d["mode"].to_numpy()
    t_catch = float(t[np.argmax(mode == 1)])

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(4.9, 3.15), sharex=True,
                                 gridspec_kw={"height_ratios": [2.0, 1.0], "hspace": 0.12})
    for ax in (a1, a2):
        ax.axvspan(0, t_catch, color=SAND, alpha=0.45, lw=0)
    a1.plot(t, alpha, color=CRIMSON, lw=1.3)
    a1.axhline(0, color=INK, lw=0.8, ls="--")
    a1.set_ylabel("α [deg] (0 = upright)")
    a1.set_ylim(-200, 265)
    a1.set_yticks([-180, -90, 0, 90, 180])
    a1.text(t_catch / 2, 228, "energy swing-up", ha="center", va="center", fontsize=10, color="#5A5048")
    a1.text(t_catch + (t[-1] - t_catch) / 2, 228, "LQR balance (latched)", ha="center", va="center",
            fontsize=10, color=CRIMSON)
    a1.annotate(f"catch at {t_catch:.2f} s", xy=(t_catch, 0), xytext=(t_catch + 3.0, -120),
                fontsize=10, color=INK, arrowprops=dict(arrowstyle="->", color=INK, lw=0.8))
    a2.plot(t, volt, color=TEAL, lw=0.9)
    a2.set_ylabel("motor [V]")
    a2.set_xlabel("time [s]")
    a2.set_xlim(0, t[-1])
    rms_deg = np.degrees(meta["alpha_rms_tail_rad"])
    a1.set_title(f"Pure Julia on the QLabs twin · {meta['realized_hz']:.2f} Hz · "
                 f"final-2 s α RMS {rms_deg:.2f}°", loc="left", fontsize=10, color=INK)
    fig.savefig(OUT / "julia_qube_swingup.png")
    plt.close(fig)
    return {"t_catch": t_catch, "rms_deg": rms_deg, **meta}


def dilisic():
    csv = Path(r"C:\Research\dilisic\reference\dilisic_80s_contract_fixed_20260908\trajectory.csv")
    summ = json.loads((csv.parent / "plots" / "summary.json").read_text())
    d = pd.read_csv(csv)
    t = d["t"].to_numpy()
    q = d[[f"q_{i}" for i in range(7)]].to_numpy()
    com = q.mean(axis=1)
    ref = -np.pi * np.sin(t) / 10.0   # same reference as dilisic.experiments.plot_flexible_arm_mas

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(5.2, 3.4), sharex=True,
                                 gridspec_kw={"height_ratios": [1.7, 1.0], "hspace": 0.12})
    for ax in (a1, a2):
        ax.axvspan(30, 45, color=SAND, alpha=0.55, lw=0)
        ax.axvspan(70, 75, color=CRIMSON, alpha=0.12, lw=0)
    shades = plt.cm.Greys(np.linspace(0.35, 0.75, 7))
    for i in range(7):
        a1.plot(t, q[:, i], color=shades[i], lw=0.8)
    a1.plot(t, ref, color=INK, lw=1.2, ls="--", label="reference")
    a1.plot(t, com, color=CRIMSON, lw=1.4, label="center of mass (7 agents)")
    a1.set_ylabel("joint angle [rad]")
    a1.legend(loc="upper right", ncol=2, fontsize=9, bbox_to_anchor=(1.0, 1.2))
    a1.text(37.5, -0.93, "obstacle", ha="center", fontsize=9, color="#5A5048")
    a1.text(72.5, -0.93, "disturbance", ha="center", fontsize=9, color=CRIMSON)
    a1.set_ylim(-1.0, 0.95)
    a2.plot(t, com - ref, color=CRIMSON, lw=1.0)
    a2.axhline(0, color=INK, lw=0.6)
    a2.set_ylabel("CoM error [rad]")
    a2.set_xlabel("time [s]")
    a2.set_xlim(0, 80)
    fig.savefig(OUT / "dilisic_replication.png")
    plt.close(fig)
    return summ


def basilisk():
    csv = Path(r"C:\Research\spacecraft_twin\results\verified_single_satellite_600s_20260908\trace.csv")
    summ = json.loads((csv.parent / "summary.json").read_text())
    d = pd.read_csv(csv)
    t = d["time_s"].to_numpy()
    sig = d[["sigma_1", "sigma_2", "sigma_3"]].to_numpy()
    tq = d[["rw_torque_1", "rw_torque_2", "rw_torque_3"]].to_numpy()
    nrm = np.linalg.norm(sig, axis=1)

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(5.3, 3.45), sharex=True,
                                 gridspec_kw={"height_ratios": [1.5, 1.0], "hspace": 0.12})
    a1.semilogy(t, nrm, color=CRIMSON, lw=1.6)
    a1.set_ylabel(r"$\|\sigma_{BR}\|$ (MRP error)")
    a1.set_ylim(3e-4, 1.0)
    a1.annotate(f"{nrm[0]:.3f}", xy=(t[0], nrm[0]), xytext=(40, 0.5), fontsize=10, color=INK)
    a1.annotate(f"{nrm[-1]:.1e}", xy=(t[-1], nrm[-1]), xytext=(500, 2.0e-3), fontsize=10, color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.8))
    cols = [CRIMSON, TEAL, "#7F7F7F"]
    for i in range(3):
        a2.plot(t, tq[:, i], color=cols[i], lw=1.0, label=f"wheel {i+1}")
    lim = summ["max_abs_wheel_torque_nm"]
    for s in (+1, -1):
        a2.axhline(s * lim, color=INK, lw=0.7, ls=":")
    a2.text(598, lim * 0.62, f"±{lim:.1f} N·m limit", ha="right", fontsize=9, color=INK)
    a2.set_ylabel("wheel torque [N·m]")
    a2.set_xlabel("time [s]")
    a2.set_xlim(0, 600)
    a2.set_ylim(-0.26, 0.26)
    a2.legend(loc="lower right", ncol=3, fontsize=9, bbox_to_anchor=(1.0, 0.10))
    fig.savefig(OUT / "basilisk_satellite.png")
    plt.close(fig)
    return summ


def autocrop(src, dst, pad=20, max_side=1400):
    im = Image.open(src).convert("RGB")
    arr = np.asarray(im).astype(int)
    mask = (arr < 245).any(axis=2)
    ys, xs = np.where(mask)
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0),
           min(xs.max() + pad, im.width), min(ys.max() + pad, im.height))
    im = im.crop(box)
    im.thumbnail((max_side, max_side))
    im.save(dst)
    return im.size


if __name__ == "__main__":
    print("julia", julia_qube())
    print("dilisic", dilisic())
    print("basilisk", basilisk())
    print("omni", autocrop(OUT / "omni_model.png", OUT / "omni_model_crop.png"))
    ph = Image.open(OUT / "toe_fig1_native.jpeg").convert("RGB")
    ph.thumbnail((1100, 1200))
    ph.save(OUT / "toe_platforms.jpg", quality=90)
    print("toe", ph.size)
