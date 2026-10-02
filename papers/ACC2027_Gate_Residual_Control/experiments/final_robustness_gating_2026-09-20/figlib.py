"""Paper-figure library: title-free versions of the two existing figure formats.

* ``attitude_figure``  -- the *attitude_detail* format: error, then roll / pitch / yaw against the
  reference (optionally quaternion and actuator panels).
* ``neuron_figure``    -- the *neurons* format: membrane v, gate r, activity a, applied residual,
  decoder-row norm.

Nothing here carries a suptitle or per-panel title; identification lives in the caption.  All data
come from the decimated ``trace.csv`` written by ``run_final_robustness.py`` (5 ms sampling).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BLUE, VERMILION, GREEN, ORANGE, GRAY, PURPLE = "#0072B2", "#D55E00", "#009E73", "#E69F00", "#222222", "#7B3294"
COLORS = {"pdff_rho3": BLUE, "cmg_pes_table": VERMILION, "cmg_pes_b05_ungated": ORANGE, "cmg_pes_gated": GREEN,
          "izhikevich_pes": PURPLE}
NAMES = {"pdff_rho3": "PD+ff", "cmg_pes_table": "CMG-PES", "cmg_pes_b05_ungated": r"CMG-PES, $\beta{=}0.5$",
         "cmg_pes_gated": "CMG-PES, gated", "izhikevich_pes": "Izhikevich-PES"}
AXES = ("x", "y", "z")


def style(base: float = 7.0) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": base, "axes.labelsize": base,
        "xtick.labelsize": base - 0.5, "ytick.labelsize": base - 0.5, "legend.fontsize": base - 0.6,
        "axes.linewidth": 0.65, "lines.linewidth": 0.85, "xtick.major.width": 0.55,
        "ytick.major.width": 0.55, "xtick.major.size": 2.6, "ytick.major.size": 2.6,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.color": "#dddddd", "grid.linewidth": 0.45, "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.facecolor": "white", "figure.dpi": 100,
    })


def load(run_dir: Path) -> tuple[pd.DataFrame, dict]:
    run_dir = Path(run_dir)
    return pd.read_csv(run_dir / "trace.csv"), json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))


def euler_zyx(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q.T
    roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
    yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return np.degrees(np.column_stack((roll, pitch, yaw)))


def qcols(df: pd.DataFrame, prefix: str) -> np.ndarray:
    return df[[f"{prefix}_{c}" for c in "wxyz"]].to_numpy()


def check_euler_convention(df: pd.DataFrame, tol_deg: float = 1e-6) -> float:
    """The logged reference Euler triple must equal euler_zyx(qref); guards the convention."""
    ref = np.degrees(df[["ref_roll", "ref_pitch", "ref_yaw"]].to_numpy())
    got = euler_zyx(qcols(df, "qref"))
    # angle wrap
    d = (got - ref + 180) % 360 - 180
    return float(np.max(np.abs(d)))


def _unwrap(a: np.ndarray) -> np.ndarray:
    return np.degrees(np.unwrap(np.radians(a), axis=0))


def attitude_figure(runs: dict[str, pd.DataFrame], out: Path, *, size=(3.45, 3.9), t_window=None,
                    err_unit="mrad", err_ylim=None, extra_quat=False, extra_act=False, shade=None,
                    annotate=None, legend_cols=3, err_key="qerr_true_rad", ref_from=None, height_ratios=None,
                    euler_axes=(0, 1, 2), names=None, styles=None, legend_h=0.27, err_log=False):
    """runs: label -> trace DataFrame (labels are keys of COLORS).  Draws the reference once."""
    style()
    first = ref_from or next(iter(runs))
    df0 = runs[first]
    n_e = len(euler_axes)
    n = 1 + n_e + int(extra_quat) + int(extra_act)
    ratios = height_ratios or [1.25] + [1] * (n - 1)
    fig, axs = plt.subplots(n, 1, figsize=size, sharex=True, gridspec_kw={"height_ratios": ratios, "hspace": 0.16})
    t0, t1 = (t_window or (float(df0.t.min()), float(df0.t.max())))
    scale = 1e3 if err_unit == "mrad" else np.degrees(1.0)
    ylab = "Error (mrad)" if err_unit == "mrad" else "Error (deg)"

    nm = {**NAMES, **(names or {})}
    sty = {lab: {"color": COLORS[lab], "lw": 0.85, **(styles or {}).get(lab, {})} for lab in runs}
    for lab, df in runs.items():
        m = (df.t >= t0) & (df.t <= t1)
        axs[0].plot(df.t[m], df[err_key][m] * scale, label=nm[lab], **sty[lab])
    if err_log:
        axs[0].set_yscale("log")
    axs[0].set_ylabel(ylab)
    if err_ylim:
        axs[0].set_ylim(*err_ylim)
    if shade is not None:
        for a0, a1 in shade:
            for ax in axs:
                ax.axvspan(a0, a1, color="#f3e6c2", alpha=0.55, lw=0, zorder=0)

    ref = np.degrees(df0[["ref_roll", "ref_pitch", "ref_yaw"]].to_numpy())
    m0 = (df0.t >= t0) & (df0.t <= t1)
    for row, i in enumerate(euler_axes):
        name = ("Roll (deg)", "Pitch (deg)", "Yaw (deg)")[i]
        ax = axs[row + 1]
        ax.plot(df0.t[m0], ref[m0.to_numpy(), i], color=GRAY, ls=(0, (4, 2)), lw=0.8, label="Reference")
        for lab, df in runs.items():
            e = _unwrap(euler_zyx(qcols(df, "qtrue")))
            e0 = _unwrap(euler_zyx(qcols(df, "qref")))
            m = ((df.t >= t0) & (df.t <= t1)).to_numpy()
            # align the unwrapped branch with the reference branch
            shift = np.round((ref[m][0, i] - e0[m][0, i]) / 360.0) * 360.0
            ax.plot(df.t[m], e[m, i] + shift, **sty[lab])
        ax.set_ylabel(name)
    k = 1 + n_e
    if extra_quat:
        ax = axs[k]; k += 1
        df = runs[first]
        m = ((df.t >= t0) & (df.t <= t1)).to_numpy()
        for c, col in zip("wxyz", (GRAY, VERMILION, GREEN, PURPLE)):
            ax.plot(df.t[m], df[f"qtrue_{c}"][m], color=col, lw=0.8, label=f"$q_{c}$")
        ax.set_ylabel("Quaternion")
    if extra_act:
        ax = axs[k]
        df = runs[first]
        m = ((df.t >= t0) & (df.t <= t1)).to_numpy()
        for i in range(4):
            ax.plot(df.t[m], df[f"actuator_command_{i}"][m], lw=0.7, label=f"rotor {i}")
        ax.set_ylabel("Rotor force (N)")
    axs[-1].set_xlabel("Time (s)")
    axs[-1].set_xlim(t0, t1)

    handles = [plt.Line2D([], [], color=GRAY, ls=(0, (4, 2)), lw=0.9, label="Reference")]
    handles += [plt.Line2D([], [], color=COLORS[l], lw=1.0, label=nm[l]) for l in runs]
    fig.legend(handles=handles, loc="upper center", ncol=legend_cols, frameon=False, bbox_to_anchor=(0.5, 1.0),
               handlelength=1.6, columnspacing=1.1)
    if annotate:
        axs[0].text(0.985, 0.93, annotate, transform=axs[0].transAxes, ha="right", va="top", fontsize=6.4,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
    for ax in axs[:-1]:
        ax.tick_params(labelbottom=False)
    fig.subplots_adjust(left=0.15, right=0.985, top=(1 - legend_h / size[1]) if legend_cols else 0.99, bottom=0.41 / size[1])
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out.with_suffix(".png"), dpi=300)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)
    return out


def neuron_figure(df: pd.DataFrame, out: Path, *, size=(3.45, 3.3), t_window=None, gate_shade=True,
                  residual_key="realized_residual", limits=None, residual_ylim=None):
    """membrane v, gate r, activity a, applied residual, decoder row norm -- no titles."""
    style()
    t0, t1 = (t_window or (float(df.t.min()), float(df.t.max())))
    m = ((df.t >= t0) & (df.t <= t1)).to_numpy()
    fig, axs = plt.subplots(5, 1, figsize=size, sharex=True, gridspec_kw={"hspace": 0.18})
    units = ("+x", "+y", "+z", "-x", "-y", "-z")
    cmap = plt.get_cmap("tab10")
    for j in range(6):
        axs[0].plot(df.t[m], df[f"voltage_{j}"][m], color=cmap(j), lw=0.7, label=units[j])
        axs[1].plot(df.t[m], df[f"gate_{j}"][m], color=cmap(j), lw=0.8)
        axs[2].plot(df.t[m], df[f"activity_{j}"][m], color=cmap(j), lw=0.8)
    axs[0].set_ylabel("Membrane\n$v$")
    axs[1].set_ylabel("Gate $r$")
    axs[2].set_ylabel("Activity $a$")
    axs[0].legend(ncol=6, frameon=False, loc="upper right", handlelength=1.2, columnspacing=0.8, fontsize=5.8)
    for i, (ax_name, col) in enumerate(zip(("roll/x", "pitch/y", "yaw/z"), (VERMILION, GREEN, PURPLE))):
        axs[3].plot(df.t[m], df[f"{residual_key}_{AXES[i]}"][m], color=col, lw=0.85, label=ax_name)
    axs[3].set_ylabel("Residual\n(N$\\cdot$m)")
    if residual_ylim:
        axs[3].set_ylim(*residual_ylim)
    axs[3].legend(ncol=3, frameon=False, loc="upper right", handlelength=1.2, columnspacing=0.8, fontsize=5.8)
    W = df[[f"decoder_w_{k}" for k in range(18)]].to_numpy().reshape(len(df), 3, 6)
    for i, (ax_name, col) in enumerate(zip(("x", "y", "z"), (BLUE, ORANGE, GREEN))):
        axs[4].plot(df.t[m], np.linalg.norm(W[:, i, :], axis=1)[m], color=col, lw=0.85, label=f"{ax_name} row")
    axs[4].set_ylabel("$\\|W_i\\|_2$")
    axs[4].legend(ncol=3, frameon=False, loc="upper right", handlelength=1.2, columnspacing=0.8, fontsize=5.8)
    axs[4].set_xlabel("Time (s)")
    axs[4].set_xlim(t0, t1)
    for ax in axs[:-1]:
        ax.tick_params(labelbottom=False)
    fig.subplots_adjust(left=0.17, right=0.985, top=0.985, bottom=0.115)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out.with_suffix(".png"), dpi=300)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)
    return out
