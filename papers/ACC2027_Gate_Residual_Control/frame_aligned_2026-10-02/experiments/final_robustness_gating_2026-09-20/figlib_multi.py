"""Multi-arm figures: CMG-PES ungated vs gated vs Izhikevich-PES on the same baseline, in the two existing formats.

* ``load_archived``           reads a trace written by the ARCHIVED runner (run_mujoco_nef_baselines.py) into the schema figlib uses
                              (validated against a run that exists in both formats; see validate_adapter.py)
* ``neuron_columns_figure``   the *neurons* format, one column per arm (the three units differ, so columns, not overlays)
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import figlib as F


def _qmul(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    p0, p1, p2, p3 = p.T
    q0, q1, q2, q3 = q.T
    return np.column_stack((p0 * q0 - p1 * q1 - p2 * q2 - p3 * q3,
                            p0 * q1 + p1 * q0 + p2 * q3 - p3 * q2,
                            p0 * q2 - p1 * q3 + p2 * q0 + p3 * q1,
                            p0 * q3 + p1 * q2 - p2 * q1 + p3 * q0))


def _ref_quat(roll, pitch, yaw) -> np.ndarray:
    cr, sr, cp, sp, cy, sy = np.cos(roll / 2), np.sin(roll / 2), np.cos(pitch / 2), np.sin(pitch / 2), np.cos(yaw / 2), np.sin(yaw / 2)
    return np.column_stack((cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy,
                            cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy))


def load_archived(run_dir: Path) -> tuple[pd.DataFrame, dict]:
    """Archived-runner trace.csv -> figlib schema (t, qerr_true_rad, ref_*, qref_*, qtrue_*, residual, neuron states, decoder)."""
    run_dir = Path(run_dir)
    tr = pd.read_csv(run_dir / "trace.csv")
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    out = pd.DataFrame({"t": tr["t"], "qerr_true_rad": tr["qerr"]})
    for c in ("ref_roll", "ref_pitch", "ref_yaw"):
        out[c] = tr[c]
    qref = _ref_quat(tr["ref_roll"].to_numpy(), tr["ref_pitch"].to_numpy(), tr["ref_yaw"].to_numpy())
    qe = tr[["qe_w", "qe_x", "qe_y", "qe_z"]].to_numpy()
    qtrue = _qmul(qe * np.array((1.0, -1.0, -1.0, -1.0)), qref)          # q_meas = conj(q_e) (x) q_ref
    for i, c in enumerate("wxyz"):
        out[f"qref_{c}"] = qref[:, i]
        out[f"qtrue_{c}"] = qtrue[:, i]
    for a in "xyz":
        out[f"realized_residual_{a}"] = tr[f"residual_{a}"]
        out[f"tau0_{a}"] = tr[f"tau0_{a}"]
    for k in range(6):
        for name in ("voltage", "gate", "activity"):
            out[f"{name}_{k}"] = tr[f"{name}_{k}"]
    for k in range(18):
        out[f"decoder_w_{k}"] = tr[f"decoder_w_{k}"]
    return out, summary


def neuron_columns_figure(cols: list[dict], out: Path, *, size=(7.1, 4.7), residual_lim=None, t_window=None):
    """cols: [{'name': str, 'df': DataFrame, 'family': 'cmg' | 'izh'}, ...] -> one column per arm, five rows.

    Rows 1-3 (membrane, gate or recovery, activity) keep each family's own units; rows 4-5 (applied residual, decoder
    row norm) share their y-axis across columns so effort and decoder movement compare directly.
    """
    F.style()
    n = len(cols)
    t0, t1 = t_window or (float(cols[0]["df"].t.min()), float(cols[0]["df"].t.max()))
    fig, axs = plt.subplots(5, n, figsize=size, sharex=True, gridspec_kw={"hspace": 0.16, "wspace": 0.36})
    cmap = plt.get_cmap("tab10")
    units = ("+x", "+y", "+z", "-x", "-y", "-z")
    lim_res = 0.0
    lim_w = [np.inf, -np.inf]
    for j, c in enumerate(cols):
        df = c["df"]
        m = ((df.t >= t0) & (df.t <= t1)).to_numpy()
        izh = c["family"] == "izh"
        for u in range(6):
            axs[0, j].plot(df.t[m], df[f"voltage_{u}"][m], color=cmap(u), lw=0.5, alpha=0.75 if izh else 1.0, label=units[u])
            axs[1, j].plot(df.t[m], df[f"gate_{u}"][m], color=cmap(u), lw=0.5 if izh else 0.8, alpha=0.75 if izh else 1.0)
            axs[2, j].plot(df.t[m], df[f"activity_{u}"][m], color=cmap(u), lw=0.5 if izh else 0.8, alpha=0.75 if izh else 1.0)
        for i, (nm, col) in enumerate(zip(("roll/x", "pitch/y", "yaw/z"), (F.VERMILION, F.GREEN, F.PURPLE))):
            axs[3, j].plot(df.t[m], df[f"realized_residual_{F.AXES[i]}"][m], color=col, lw=0.7, label=nm)
        W = df[[f"decoder_w_{k}" for k in range(18)]].to_numpy().reshape(len(df), 3, 6)
        for i, (nm, col) in enumerate(zip(("x", "y", "z"), (F.BLUE, F.ORANGE, F.GREEN))):
            w = np.linalg.norm(W[:, i, :], axis=1)
            axs[4, j].plot(df.t[m], w[m], color=col, lw=0.8, label=f"{nm} row")
            lim_w = [min(lim_w[0], float(w[m].min())), max(lim_w[1], float(w[m].max()))]
        r = df[[f"realized_residual_{a}" for a in "xyz"]].to_numpy()[m]
        lim_res = max(lim_res, float(np.percentile(np.abs(r), 99.9)))
        axs[0, j].text(0.02, 0.96, c["name"], transform=axs[0, j].transAxes, va="top", ha="left", fontsize=6.6, fontweight="bold",
                       bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
        if not izh:
            axs[1, j].set_ylim(-0.05, 1.05)      # gate r and activity a live in [0, 1]; keep the full range so 'latched at 1' reads
            axs[2, j].set_ylim(-0.05, 1.05)
        axs[0, j].set_ylabel("Membrane $v$ (mV)" if izh else "Membrane $v$", fontsize=6.6)
        axs[1, j].set_ylabel("Recovery $u$" if izh else "Gate $r$", fontsize=6.6)
        axs[2, j].set_ylabel("Activity $a$" + (" (trace)" if izh else ""), fontsize=6.6)
        axs[4, j].set_xlabel("Time (s)")
    rl = residual_lim or 1.08 * lim_res
    pad = 0.06 * (lim_w[1] - lim_w[0] + 1e-9)
    for j in range(n):
        axs[3, j].set_ylim(-rl, rl)
        axs[4, j].set_ylim(lim_w[0] - pad, lim_w[1] + pad)
        axs[4, j].set_xlim(t0, t1)
        for r_ in range(4):
            axs[r_, j].tick_params(labelbottom=False)
        if j > 0:
            axs[3, j].tick_params(labelleft=False)
            axs[4, j].tick_params(labelleft=False)
        else:
            axs[3, j].set_ylabel("Residual\n(N$\\cdot$m)", fontsize=6.6)
            axs[4, j].set_ylabel("$\\|W_i\\|_2$", fontsize=6.6)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=cmap(u), lw=1.2, label=f"unit {units[u]}") for u in range(6)]
    handles += [Line2D([], [], color=col, lw=1.2, label=f"residual {nm}")
                for nm, col in zip(("roll/x", "pitch/y", "yaw/z"), (F.VERMILION, F.GREEN, F.PURPLE))]
    handles += [Line2D([], [], color=col, lw=1.2, label=f"$\\|W_{nm}\\|$") for nm, col in zip("xyz", (F.BLUE, F.ORANGE, F.GREEN))]
    fig.legend(handles=handles, loc="lower center", ncol=12, frameon=False, fontsize=5.4, handlelength=1.0, columnspacing=0.75,
               bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(left=0.105, right=0.985, top=0.985, bottom=0.115)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out.with_suffix(".png"), dpi=300)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)
    return out
