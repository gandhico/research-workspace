"""
Generate all paper figures that cannot be produced directly by make_comparison_figures.py.

Produces (saved to paper/figures/):
  1. hyperlif_dynamics.pdf  — HyperLIF v(t) and r(t) for several current levels
  2. arch_a_diagram.pdf     — Architecture A body-torque block diagram
  3. arch_b_diagram.pdf     — Architecture B rotor-level block diagram

Usage (from v2_clean/):
    python paper/gen_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

_HERE    = Path(__file__).resolve().parent
_PROJECT = _HERE.parent
_SRC     = _PROJECT / "src"
sys.path.insert(0, str(_SRC))
sys.path.insert(0, str(_PROJECT))

OUT = _HERE / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ─── IEEE-style matplotlib defaults ─────────────────────────────────────────
plt.rcParams.update({
    "font.family":      "serif",
    "font.size":        9,
    "axes.labelsize":   9,
    "legend.fontsize":  8,
    "xtick.labelsize":  8,
    "ytick.labelsize":  8,
    "axes.linewidth":   0.8,
    "lines.linewidth":  1.4,
    "figure.dpi":       200,
    "pdf.fonttype":     42,  # embed fonts (required by IEEE)
    "ps.fonttype":      42,
})

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


# ─── 1. HyperLIF dynamics ───────────────────────────────────────────────────

def _sig(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def simulate_hyperlif(I_const, dt=0.0005, T=1.0,
                      tau=0.05, tau_r=0.005, reset_gain=120.0,
                      gamma=2.0, alpha=50.0,
                      v_thresh=1.0, v_rest=0.0, v_reset=0.0):
    steps = int(T / dt)
    t_arr = np.arange(steps) * dt
    v_arr = np.zeros(steps)
    r_arr = np.zeros(steps)
    v, r = 0.0, 0.0
    for i in range(steps):
        eff_thresh = v_thresh - gamma * r
        r_target   = _sig(alpha * (v - eff_thresh))
        r_decay    = np.exp(-dt / tau_r)
        r = r_target + (r - r_target) * r_decay

        conductance = reset_gain * r**2
        lam   = (1.0 / tau) + conductance
        drive = (v_rest / tau) + (I_const / tau) + conductance * v_reset
        decay = np.exp(-lam * dt)
        v = v * decay + (drive / lam) * (1.0 - decay)

        v_arr[i] = v
        r_arr[i] = r
    return t_arr, v_arr, r_arr


def fig_hyperlif_dynamics():
    currents = [0.50, 0.75, 1.05, 1.25, 1.50]
    labels   = ["$I=0.50$ (sub-threshold)",
                "$I=0.75$ (hover bias)",
                "$I=1.05$ (near threshold)",
                "$I=1.25$ (above threshold)",
                "$I=1.50$ (strongly active)"]
    T = 0.25  # 250 ms is enough to see full dynamics

    fig, axes = plt.subplots(2, 1, figsize=(3.5, 4.0), sharex=True)
    for I, lab, col in zip(currents, labels, PALETTE):
        t, v, r = simulate_hyperlif(I, T=T)
        axes[0].plot(t * 1e3, v, color=col, label=lab)
        axes[1].plot(t * 1e3, r, color=col)

    axes[0].axhline(1.0, color="k", lw=0.9, ls="--", alpha=0.6, label="$v_{\\mathrm{thresh}}$")
    axes[0].set_ylabel("Membrane voltage $v$")
    axes[0].set_ylim(-0.05, 1.35)
    axes[0].legend(fontsize=6.5, loc="upper left", framealpha=0.9)
    axes[0].grid(True, alpha=0.25)

    axes[1].axhline(0.5, color="k", lw=0.9, ls="--", alpha=0.45, label="$r=0.5$")
    axes[1].set_ylabel("Gate state $r$")
    axes[1].set_xlabel("Time [ms]")
    axes[1].set_ylim(-0.03, 1.08)
    axes[1].legend(fontsize=7, loc="upper left", framealpha=0.9)
    axes[1].grid(True, alpha=0.25)

    fig.suptitle("HyperLIF Neuron Dynamics", fontsize=9, y=1.01)
    fig.tight_layout()
    out = OUT / "hyperlif_dynamics.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(str(out).replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ─── Helper: draw a block diagram box ────────────────────────────────────────
# Each block: bold name at center-top, italic formula at center-bottom, both
# strictly inside the box boundaries.

def _box(ax, cx, cy, w, h, name, formula=None,
         fc="#ddeeff", ec="#336699"):
    """Draw a rounded box centred at (cx,cy)."""
    patch = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                           boxstyle="round,pad=0.015",
                           facecolor=fc, edgecolor=ec, linewidth=0.9,
                           zorder=3)
    ax.add_patch(patch)
    ty = cy + h * 0.18 if formula else cy
    ax.text(cx, ty, name,
            ha="center", va="center", fontsize=7.5,
            fontweight="bold", zorder=4)
    if formula:
        ax.text(cx, cy - h * 0.22, formula,
                ha="center", va="center", fontsize=5.5,
                color="#333333", style="italic", zorder=4)


def _arrow(ax, x0, y0, x1, y1, label=None, lc="#222222", lw=1.1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>",
                                color=lc, lw=lw,
                                mutation_scale=10),
                zorder=5)
    if label:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx = x1 - x0; dy = y1 - y0
        # offset perpendicular to arrow direction
        norm = max((dx**2 + dy**2)**0.5, 1e-9)
        ax.text(mx + 0.04 * (-dy / norm), my + 0.04 * (dx / norm),
                label, fontsize=6.0, color="#333333",
                ha="center", va="center", zorder=6)


def _node(ax, x, y, label, fc="#fff8cc", ec="#888800", r=0.04):
    circ = plt.Circle((x, y), r, fc=fc, ec=ec, lw=0.9, zorder=3)
    ax.add_patch(circ)
    ax.text(x, y, label, ha="center", va="center", fontsize=8, zorder=4)


# ─── 2. Architecture A (body-torque residual) ─────────────────────────────
# Layout: main column at cx=0.38, blend node at (0.80, yblend)
# 5 blocks: PD → Normalize → PairEncode → HyperLIF×6 → Decode
# Block height BH=0.14, width BW=0.32
# y centres: 0.88, 0.70, 0.52, 0.34, 0.16  (gaps = 0.18 - 0.14 = 0.04)

def fig_arch_a():
    fig, ax = plt.subplots(figsize=(3.5, 4.4))
    ax.set_xlim(0, 1.05); ax.set_ylim(-0.02, 1.02)
    ax.axis("off")

    BW, BH = 0.32, 0.14
    CX = 0.38
    YS = [0.88, 0.70, 0.52, 0.34, 0.16]   # block centers
    YBLEND = 0.52                           # blend node y

    # Input label
    ax.text(0.10, YS[0], r"$[\mathbf{e}_q,\boldsymbol{\omega}]$",
            ha="center", va="center", fontsize=8, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="#f0f0f0", ec="#888888", lw=0.8))
    _arrow(ax, 0.16, YS[0], CX - BW/2, YS[0])

    # Blocks
    blocks = [
        ("Classical PD",     r"$\tau_\mathrm{pd}{=}{-}k_q e_q{-}k_\omega\omega$", "#dde8ff"),
        ("Normalize",         r"$\tau_\mathrm{n}{=}\tau_\mathrm{pd}/\tau_\mathrm{lim}$",     "#dde8ff"),
        ("Pair Encode",       r"$I_\pm{=}b{+}g\max(\pm\tau_\mathrm{n},0)$",                  "#dde8ff"),
        ("HyperLIF $\\times$6", r"$\dot{r}{=}(\sigma(\alpha(v{-}\theta_\mathrm{eff})){-}r)/\tau_r$", "#ffe8cc"),
        ("Decode",            r"$\delta\tau{=}\mathrm{clip}(r_+{-}r_-,\pm 1)\!\cdot\!\tau_\mathrm{lim}$", "#ffe8cc"),
    ]
    for i, (name, formula, fc) in enumerate(blocks):
        _box(ax, CX, YS[i], BW, BH, name, formula, fc=fc)
        if i < len(blocks) - 1:
            _arrow(ax, CX, YS[i] - BH/2, CX, YS[i+1] + BH/2)

    # Blend node
    _node(ax, 0.82, YBLEND, r"$+$")

    # Direct PD path (right → blend)
    x_right = CX + BW/2
    ax.annotate("", xy=(0.82, YBLEND + 0.04), xytext=(0.82, YS[0]),
                arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.0,
                                mutation_scale=9, connectionstyle="arc3,rad=0"),
                zorder=5)
    ax.plot([x_right, 0.82], [YS[0], YS[0]], color="#555555", lw=1.0, zorder=4)
    ax.text(0.86, (YS[0] + YBLEND) / 2 + 0.04, r"$(1{-}\beta)$",
            fontsize=6.0, color="#333333", va="center")

    # Neural path (Decode right → blend)
    ax.plot([x_right, 0.82], [YS[4], YS[4]], color="#555555", lw=1.0, zorder=4)
    ax.annotate("", xy=(0.82, YBLEND - 0.04), xytext=(0.82, YS[4]),
                arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.0,
                                mutation_scale=9),
                zorder=5)
    ax.text(0.86, (YS[4] + YBLEND) / 2 - 0.04, r"$\beta$",
            fontsize=6.5, color="#333333", va="center")

    # Output arrow
    ax.annotate("", xy=(1.02, YBLEND), xytext=(0.86, YBLEND),
                arrowprops=dict(arrowstyle="-|>", color="#222222", lw=1.1,
                                mutation_scale=10),
                zorder=5)
    ax.text(1.03, YBLEND, r"$\boldsymbol{\tau}_\mathrm{f}$",
            fontsize=7, ha="left", va="center", color="#222222")

    ax.set_title("Architecture A — Body-Torque Residual", fontsize=8, pad=4)
    fig.tight_layout()
    out = OUT / "arch_a_diagram.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(str(out).replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ─── 3. Architecture B (rotor-level residual) ──────────────────────────────

def fig_arch_b():
    fig, ax = plt.subplots(figsize=(3.5, 4.4))
    ax.set_xlim(0, 1.05); ax.set_ylim(-0.02, 1.02)
    ax.axis("off")

    BW, BH = 0.32, 0.14
    CX = 0.38
    YS = [0.88, 0.70, 0.52, 0.34, 0.16]
    YMIXER = YS[1]      # Motor Mixer y → tap point for nominal path
    YBLEND = YS[2]      # Add node y

    # Input label
    ax.text(0.10, YS[0], r"$[\mathbf{e}_q,\boldsymbol{\omega}]$",
            ha="center", va="center", fontsize=8, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="#f0f0f0", ec="#888888", lw=0.8))
    _arrow(ax, 0.16, YS[0], CX - BW/2, YS[0])

    blocks = [
        ("Classical PD",        r"$\tau_\mathrm{pd}{=}{-}k_q e_q{-}k_\omega\omega$", "#dde8ff"),
        ("Motor Mixer",          r"$\mathbf{u}_\mathrm{nom}{=}\mathbf{B}^{-1}[T,\tau_\mathrm{pd}]^\top$", "#dde8ff"),
        ("Pair Encode",          r"$I_\pm[i]{=}b{+}g\max(\pm\delta_\mathrm{dir}[i],0)$",                  "#dde8ff"),
        ("HyperLIF $\\times$8",  r"$\dot{r}[i]{=}(\sigma(\alpha(v{-}\theta_\mathrm{eff})){-}r)/\tau_r$",  "#ffe8cc"),
        ("Decode",               r"$\Delta u[i]{=}\mathrm{clip}(r_+{-}r_-,\pm 1)\!\cdot\! u_\mathrm{sc}$","#ffe8cc"),
    ]
    for i, (name, formula, fc) in enumerate(blocks):
        _box(ax, CX, YS[i], BW, BH, name, formula, fc=fc)
        if i < len(blocks) - 1:
            _arrow(ax, CX, YS[i] - BH/2, CX, YS[i+1] + BH/2)

    # Add node
    _node(ax, 0.82, YBLEND, r"$+$")

    # Nominal path: from Motor Mixer right → right rail → down to add node
    x_right = CX + BW/2
    ax.plot([x_right, 0.82], [YMIXER, YMIXER], color="#555555", lw=1.0, zorder=4)
    ax.annotate("", xy=(0.82, YBLEND + 0.04), xytext=(0.82, YMIXER),
                arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.0,
                                mutation_scale=9),
                zorder=5)
    ax.text(0.86, (YMIXER + YBLEND) / 2 + 0.02, r"$\mathbf{u}_\mathrm{nom}$",
            fontsize=6.0, color="#333333", va="center")

    # Decode (Δu) path: right → right rail → up to add node
    ax.plot([x_right, 0.82], [YS[4], YS[4]], color="#555555", lw=1.0, zorder=4)
    ax.annotate("", xy=(0.82, YBLEND - 0.04), xytext=(0.82, YS[4]),
                arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.0,
                                mutation_scale=9),
                zorder=5)
    ax.text(0.86, (YS[4] + YBLEND) / 2 - 0.02, r"$\beta_r\Delta\mathbf{u}$",
            fontsize=6.0, color="#333333", va="center")

    # Clip box + output
    _box(ax, 0.95, YBLEND, 0.13, 0.10, "clip", fc="#f0f0f0", ec="#666666")
    ax.annotate("", xy=(0.89, YBLEND), xytext=(0.86, YBLEND),
                arrowprops=dict(arrowstyle="-|>", color="#222222", lw=1.1,
                                mutation_scale=10),
                zorder=5)
    ax.text(1.03, YBLEND, r"$\mathbf{u}_\mathrm{f}$",
            fontsize=7, ha="left", va="center", color="#222222")

    ax.set_title("Architecture B — Rotor-Level Residual", fontsize=8, pad=4)
    fig.tight_layout()
    out = OUT / "arch_b_diagram.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(str(out).replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ─── 4. Yaw360 comparison figure ─────────────────────────────────────────────

def _load_csv(path: Path) -> dict:
    import csv
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {}
    out = {}
    for k in rows[0]:
        try:
            out[k] = np.array([float(r[k]) for r in rows])
        except (ValueError, KeyError):
            pass
    return out


def fig_yaw360(logs_dir: Path):
    import re

    quad = "bitcraze_crazyflie_2"
    mission = "yaw360"

    controllers = ["classical", "direct_hyperlif"]
    colors = {"classical": "#1f77b4", "direct_hyperlif": "#2ca02c"}
    labels = {"classical": "Classical PD", "direct_hyperlif": "HyperLIF (gate)"}

    datasets = {}
    for ctrl in controllers:
        pattern = f"{quad}_{mission}_{ctrl}_*.csv"
        files = [f for f in logs_dir.glob(pattern)
                 if "summary" not in f.name and "config" not in f.name]
        if not files:
            print(f"  No CSV found for yaw360 {ctrl} — run simulations first")
            return
        p = max(files, key=lambda f: f.stat().st_mtime)
        d = _load_csv(p)
        if d:
            datasets[ctrl] = d
            print(f"  Loaded {ctrl}: {len(d.get('t',[]))} rows from {p.name}")

    if len(datasets) < 2:
        print("  Need both classical and direct_hyperlif yaw360 CSVs.")
        return

    fig, axes = plt.subplots(2, 1, figsize=(3.5, 4.0), sharex=True)

    # Top: yaw angle — unwrap to avoid ±180° flip artifact
    d_ref = next(iter(datasets.values()))
    if "psi_ref" in d_ref:
        axes[0].plot(d_ref["t"], np.degrees(np.unwrap(d_ref["psi_ref"])),
                     "k--", lw=1.0, alpha=0.55, label="Reference")
    for ctrl, d in datasets.items():
        if "psi" in d:
            axes[0].plot(d["t"], np.degrees(np.unwrap(d["psi"])),
                         color=colors[ctrl], label=labels[ctrl])
    axes[0].set_ylabel(r"Yaw $\psi$ [°]")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(fontsize=7, loc="upper left")

    # Bottom: qerr angle
    for ctrl, d in datasets.items():
        if "qerr_angle" in d:
            qmean = float(np.mean(d["qerr_angle"]))
            axes[1].plot(d["t"], d["qerr_angle"],
                         color=colors[ctrl],
                         label=f"{labels[ctrl]} (mean={qmean:.4f})")
    axes[1].set_ylabel(r"$\|\mathbf{e}_q\|$ [rad]")
    axes[1].set_xlabel("Time [s]")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend(fontsize=7)

    fig.suptitle(r"Yaw360 — Crazyflie 2 ($0^\circ \to 360^\circ$)", fontsize=9)
    fig.tight_layout()

    out = logs_dir.parent / "figures" / f"compare_{quad}_{mission}_yaw.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(str(out).replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    print("Generating paper figures...\n")

    print("[1/3] HyperLIF dynamics")
    fig_hyperlif_dynamics()

    print("[2/3] Architecture A block diagram")
    fig_arch_a()

    print("[3/3] Architecture B block diagram")
    fig_arch_b()

    # Yaw360 is conditional on simulation results existing
    logs_dir = _PROJECT / "results" / "logs"
    print("[4/4] Yaw360 comparison (requires prior simulation run)")
    fig_yaw360(logs_dir)

    print(f"\nAll figures saved to: {OUT}")


if __name__ == "__main__":
    main()
