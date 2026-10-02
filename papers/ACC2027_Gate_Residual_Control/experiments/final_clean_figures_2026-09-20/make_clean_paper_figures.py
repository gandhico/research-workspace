"""Rebuild the canonical X2 Hard45 paper figures from frozen CSV traces.

The inputs are the matched primary comparison used by the paper's rho=3
PD-plus-reference-rate-feedforward table:

* baseline: ``baselines_2026-09-10/tune/pdff/bw3``;
* residual controller: ``baselines_2026-09-10/stretch/pdff/bw3``.

No simulation is rerun and no frozen input is modified.  The utility checks
the archived summaries, reconstructs measured Euler angles from the logged
error quaternion and reference, and writes publication-scale PNG/PDF figures
plus a machine-readable provenance record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = (
    HERE.parent
    / "nengo_nef_replication_2026-08-29"
    / "results"
    / "baselines_2026-09-10"
)

# Frozen values recorded in the canonical summaries.  These assertions make
# an accidental path change or substitution fail loudly.
EXPECTED_BASELINE_MEAN_RAD = 0.010537051191250089
EXPECTED_CMG_MEAN_RAD = 0.00908033280131453
SUMMARY_TOL = 5e-12

BLUE = "#0072B2"
VERMILION = "#D55E00"
GREEN = "#009E73"
ORANGE = "#E69F00"
GRAY = "#222222"


def _configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7.0,
            "axes.labelsize": 7.0,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.4,
            "axes.linewidth": 0.65,
            "lines.linewidth": 0.8,
            "xtick.major.width": 0.55,
            "ytick.major.width": 0.55,
            "xtick.major.size": 2.8,
            "ytick.major.size": 2.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
            "savefig.edgecolor": "white",
        }
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_run(path: Path) -> tuple[pd.DataFrame, dict]:
    trace_path = path / "trace.csv"
    summary_path = path / "summary.json"
    if not trace_path.is_file() or not summary_path.is_file():
        raise FileNotFoundError(f"Incomplete frozen run: {path}")
    frame = pd.read_csv(trace_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return frame, summary


def _quat_mul_batch(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    p0, p1, p2, p3 = p.T
    q0, q1, q2, q3 = q.T
    return np.column_stack(
        (
            p0 * q0 - p1 * q1 - p2 * q2 - p3 * q3,
            p0 * q1 + p1 * q0 + p2 * q3 - p3 * q2,
            p0 * q2 - p1 * q3 + p2 * q0 + p3 * q1,
            p0 * q3 + p1 * q2 - p2 * q1 + p3 * q0,
        )
    )


def _reference_quaternion(frame: pd.DataFrame) -> np.ndarray:
    roll = frame["ref_roll"].to_numpy()
    pitch = frame["ref_pitch"].to_numpy()
    yaw = frame["ref_yaw"].to_numpy()
    cr, sr = np.cos(roll / 2.0), np.sin(roll / 2.0)
    cp, sp = np.cos(pitch / 2.0), np.sin(pitch / 2.0)
    cy, sy = np.cos(yaw / 2.0), np.sin(yaw / 2.0)
    return np.column_stack(
        (
            cr * cp * cy + sr * sp * sy,
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
        )
    )


def _quat_to_euler_zyx(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q.T
    roll = np.arctan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2.0 * (w * y - z * x), -1.0, 1.0))
    yaw = np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return np.column_stack((roll, pitch, yaw))


def _recover_euler(frame: pd.DataFrame) -> np.ndarray:
    # The logged convention is q_e = q_ref (x) conjugate(q_meas), hence
    # q_meas = conjugate(q_e) (x) q_ref.
    qe = frame[["qe_w", "qe_x", "qe_y", "qe_z"]].to_numpy()
    qe_conj = qe * np.array((1.0, -1.0, -1.0, -1.0))
    q_meas = _quat_mul_batch(qe_conj, _reference_quaternion(frame))
    norms = np.linalg.norm(q_meas, axis=1)
    if not np.allclose(norms, 1.0, atol=2e-9):
        raise ValueError(f"Recovered quaternion norm error: {np.max(np.abs(norms - 1.0)):.3e}")
    return _quat_to_euler_zyx(q_meas)


def _clean_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, color="#D9D9D9", linewidth=0.45, alpha=0.75)
    ax.set_axisbelow(True)


def _save_figure(fig: plt.Figure, stem: str, png_dir: Path, pdf_dir: Path, dpi: int) -> list[Path]:
    png = png_dir / f"{stem}.png"
    pdf = pdf_dir / f"{stem}.pdf"
    metadata = {
        "Creator": "make_clean_paper_figures.py",
        "Title": stem.replace("_", " "),
        "Subject": "ACC 2027 canonical X2 Hard45 comparison",
    }
    fig.savefig(png, dpi=dpi, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.02, metadata=metadata)
    plt.close(fig)
    return [png, pdf]


def _tracking_figure(
    baseline: pd.DataFrame,
    cmg: pd.DataFrame,
    baseline_mean_mrad: float,
    cmg_mean_mrad: float,
) -> plt.Figure:
    t = baseline["t"].to_numpy()
    b_euler = np.rad2deg(_recover_euler(baseline))
    n_euler = np.rad2deg(_recover_euler(cmg))
    reference = np.rad2deg(baseline[["ref_roll", "ref_pitch", "ref_yaw"]].to_numpy())
    b_error = 1e3 * baseline["qerr"].to_numpy()
    n_error = 1e3 * cmg["qerr"].to_numpy()

    fig, axes = plt.subplots(
        4,
        1,
        figsize=(3.45, 5.15),
        sharex=True,
        gridspec_kw={"height_ratios": (1.18, 1.0, 1.0, 1.0)},
    )

    axes[0].plot(t, b_error, color=BLUE, label="PD + rate feedforward")
    axes[0].plot(t, n_error, color=VERMILION, label="CMG-PES residual")
    axes[0].set_ylabel("Error (mrad)")
    axes[0].set_ylim(0.0, 25.0)
    axes[0].text(
        0.985,
        0.93,
        rf"mean: {baseline_mean_mrad:.2f} $\rightarrow$ {cmg_mean_mrad:.2f} mrad",
        ha="right",
        va="top",
        transform=axes[0].transAxes,
        fontsize=6.2,
        color="#333333",
    )

    # The initial reference offset is common to both runs and peaks near
    # 409 mrad.  The inset preserves that full transient while the main axis
    # resolves the 0.5-45 s tracking behavior that separates the controllers.
    transient = inset_axes(axes[0], width="31%", height="43%", loc="upper left", borderpad=0.7)
    transient.plot(t, b_error, color=BLUE, lw=0.65)
    transient.plot(t, n_error, color=VERMILION, lw=0.65)
    transient.set_xlim(0.0, 0.6)
    transient.set_ylim(0.0, 430.0)
    transient.set_xticks((0.0, 0.3, 0.6))
    transient.set_yticks((0.0, 200.0, 400.0))
    transient.tick_params(labelsize=4.8, length=1.8, pad=1.0)
    transient.grid(True, color="#E5E5E5", lw=0.35)
    transient.text(0.04, 0.93, "initial transient", transform=transient.transAxes,
                   ha="left", va="top", fontsize=4.8, color="#333333")

    for axis, label, column in zip(axes[1:], ("Roll (deg)", "Pitch (deg)", "Yaw (deg)"), range(3)):
        axis.plot(t, reference[:, column], color=GRAY, ls="--", lw=0.8)
        axis.plot(t, b_euler[:, column], color=BLUE)
        axis.plot(t, n_euler[:, column], color=VERMILION)
        axis.set_ylabel(label)

    handles = (
        Line2D((0,), (0,), color=GRAY, ls="--", lw=0.9, label="Reference"),
        Line2D((0,), (0,), color=BLUE, lw=0.9, label="PD + rate ff"),
        Line2D((0,), (0,), color=VERMILION, lw=0.9, label="CMG-PES"),
    )
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False,
               handlelength=1.7, columnspacing=0.9, bbox_to_anchor=(0.5, 0.999))
    for axis in axes:
        _clean_axis(axis)
        axis.margins(x=0.0)
    axes[-1].set_xlabel("Time (s)")
    fig.align_ylabels(axes)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.965), pad=0.45, h_pad=0.42)
    return fig


def _neuron_figure(cmg: pd.DataFrame) -> plt.Figure:
    t = cmg["t"].to_numpy()
    branch_labels = ("+x", "+y", "+z", "-x", "-y", "-z")
    branch_colors = (BLUE, GREEN, ORANGE, BLUE, GREEN, ORANGE)
    branch_styles = ("-", "-", "-", "--", "--", "--")

    fig, axes = plt.subplots(4, 1, figsize=(3.45, 4.75), sharex=True)
    for idx, (label, color, style) in enumerate(zip(branch_labels, branch_colors, branch_styles)):
        axes[0].plot(t, cmg[f"voltage_{idx}"], color=color, ls=style, label=label)
        axes[1].plot(t, cmg[f"gate_{idx}"], color=color, ls=style)
        axes[2].plot(t, cmg[f"activity_{idx}"], color=color, ls=style)

    axes[0].set_ylabel(r"Membrane $v_j$")
    axes[1].set_ylabel(r"Gate $r_j$")
    axes[2].set_ylabel(r"Activity $a_j$")
    axes[1].set_ylim(-0.04, 1.04)
    axes[2].set_ylim(-0.04, 1.04)

    weights = cmg[[f"decoder_w_{idx}" for idx in range(18)]].to_numpy().reshape(-1, 3, 6)
    for axis_idx, (label, color) in enumerate(zip((r"$W_x$", r"$W_y$", r"$W_z$"), (BLUE, GREEN, ORANGE))):
        axes[3].plot(t, np.linalg.norm(weights[:, axis_idx, :], axis=1), color=color, label=label)
    axes[3].set_ylabel(r"$\|W_{i,:}\|_2$")
    axes[3].set_xlabel("Time (s)")
    axes[3].legend(loc="best", ncol=3, frameon=False, handlelength=1.5,
                   columnspacing=0.75, fontsize=5.9)

    branch_handles = tuple(
        Line2D((0,), (0,), color=color, ls=style, lw=0.9, label=label)
        for label, color, style in zip(branch_labels, branch_colors, branch_styles)
    )
    fig.legend(handles=branch_handles, loc="upper center", ncol=6, frameon=False,
               handlelength=1.3, columnspacing=0.55, handletextpad=0.25,
               bbox_to_anchor=(0.5, 0.999), fontsize=5.9)
    for axis in axes:
        _clean_axis(axis)
        axis.margins(x=0.0)
    fig.align_ylabels(axes)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.962), pad=0.45, h_pad=0.42)
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-root", type=Path, default=HERE / "output")
    parser.add_argument("--dpi", type=int, default=400)
    args = parser.parse_args()

    baseline_dir = args.source_root / "tune" / "pdff" / "bw3" / "x2_hard45_classical"
    cmg_dir = args.source_root / "stretch" / "pdff" / "bw3" / "x2_hard45_nengo_nef_pes"
    baseline, baseline_summary = _load_run(baseline_dir)
    cmg, cmg_summary = _load_run(cmg_dir)

    if abs(float(baseline_summary["qerr_mean_rad"]) - EXPECTED_BASELINE_MEAN_RAD) > SUMMARY_TOL:
        raise ValueError("Baseline summary is not the frozen primary rho=3 run")
    if abs(float(cmg_summary["qerr_mean_rad"]) - EXPECTED_CMG_MEAN_RAD) > SUMMARY_TOL:
        raise ValueError("CMG summary is not the frozen primary rho=3 run")
    if len(baseline) != len(cmg) or not np.allclose(baseline["t"], cmg["t"], atol=1e-12):
        raise ValueError("Baseline and CMG traces are not time-matched")
    reference_columns = ["ref_roll", "ref_pitch", "ref_yaw"]
    reference_mismatch = float(
        np.max(np.abs(baseline[reference_columns].to_numpy() - cmg[reference_columns].to_numpy()))
    )
    if reference_mismatch > 1e-12:
        raise ValueError(f"Reference trajectories differ by {reference_mismatch:.3e} rad")

    required_neural = [
        *(f"voltage_{idx}" for idx in range(6)),
        *(f"gate_{idx}" for idx in range(6)),
        *(f"activity_{idx}" for idx in range(6)),
        *(f"decoder_w_{idx}" for idx in range(18)),
    ]
    missing = [column for column in required_neural if column not in cmg]
    if missing:
        raise ValueError(f"CMG trace lacks neural state columns: {missing}")

    png_dir = args.output_root / "png"
    pdf_dir = args.output_root / "pdf"
    png_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    _configure_style()

    baseline_mean_mrad = 1e3 * float(baseline_summary["qerr_mean_rad"])
    cmg_mean_mrad = 1e3 * float(cmg_summary["qerr_mean_rad"])
    improvement = 100.0 * (baseline_mean_mrad - cmg_mean_mrad) / baseline_mean_mrad
    outputs: list[Path] = []
    outputs.extend(
        _save_figure(
            _tracking_figure(baseline, cmg, baseline_mean_mrad, cmg_mean_mrad),
            "x2_hard45_attitude_detail_clean",
            png_dir,
            pdf_dir,
            args.dpi,
        )
    )
    outputs.extend(
        _save_figure(
            _neuron_figure(cmg),
            "x2_hard45_neuron_states_clean",
            png_dir,
            pdf_dir,
            args.dpi,
        )
    )

    source_files = (
        baseline_dir / "trace.csv",
        baseline_dir / "summary.json",
        baseline_dir / "manifest.json",
        cmg_dir / "trace.csv",
        cmg_dir / "summary.json",
        cmg_dir / "manifest.json",
    )
    record = {
        "schema": 1,
        "comparison": "X2 Hard45, rho=3 PD+rate-feedforward versus CMG-PES residual",
        "baseline_run": str(baseline_dir.resolve()),
        "cmg_run": str(cmg_dir.resolve()),
        "summary_qerr_mean_mrad": {
            "baseline": baseline_mean_mrad,
            "cmg_pes": cmg_mean_mrad,
            "reduction_percent": improvement,
        },
        "decimated_trace_qerr_mean_mrad": {
            "baseline": 1e3 * float(baseline["qerr"].mean()),
            "cmg_pes": 1e3 * float(cmg["qerr"].mean()),
        },
        "trace_samples": int(len(cmg)),
        "logged_dt_s": float(np.median(np.diff(cmg["t"]))),
        "reference_max_abs_mismatch_rad": reference_mismatch,
        "full_rate_neural_archive_available": bool(cmg_summary.get("neural_trace_full_rate")),
        "neural_plot_source": "decimated trace.csv neural-state columns",
        "visible_titles_removed": True,
        "source_sha256": {str(path.resolve()): _sha256(path) for path in source_files},
        "output_sha256": {str(path.resolve()): _sha256(path) for path in outputs},
    }
    record_path = args.output_root / "figure_provenance.json"
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    print(f"Baseline summary mean: {baseline_mean_mrad:.6f} mrad")
    print(f"CMG-PES summary mean: {cmg_mean_mrad:.6f} mrad")
    print(f"Mean-error reduction: {improvement:.6f}%")
    for output in outputs:
        print(output)
    print(record_path)


if __name__ == "__main__":
    main()
