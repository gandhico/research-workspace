"""Build ACC-ready figures for positive-mean-error 3DOF Hover cases.

The source of truth is the frozen 2026-09-02 canonical direct-Nengo audit.
Raw traces are read only.  A mission is included only when the matched
CMG-PES run has lower mean quaternion-angle error than its PD baseline.

This deliberately does not imply that every secondary metric improves.
Peak-error changes are printed in the summary figure and manifest.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib


# --- portable paths (added for distribution) ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from acc2027_paths import HOVER_FINAL, HOVER_RESULTS, out_dir  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


DIRECT = HOVER_FINAL
AUDIT = (HOVER_RESULTS / "FROZEN_AUDIT_2026-09-02"
         / "canonical_physical_deep_audit.json")
ROLL_N3 = (HOVER_RESULTS / "hardware_armed_roll_n3_2026-09-01"
           / "armed_roll_n3_summary.json")
OUT = out_dir("hover3dof_positive_only")

PD_COLOR = "#3569A8"
CMG_COLOR = "#D55E00"
REF_COLOR = "#202020"
AXIS_COLORS = ("#0072B2", "#009E73", "#CC79A7")
ACTIVITY_COLORS = ("#0072B2", "#56B4E9", "#009E73", "#E69F00", "#D55E00", "#CC79A7")
MISSION_ORDER = ("hover", "roll", "hard45", "hardstep")
MISSION_LABEL = {
    "hover": "Hover hold",
    "roll": "Roll tracking",
    "hard45": "Hard45",
    "hardstep": "Hardstep",
}


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 9,
            "axes.labelsize": 8.5,
            "legend.fontsize": 7.2,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def load_trace(path: Path) -> dict[str, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if not rows:
        raise ValueError(f"Empty trace: {path}")
    numeric: dict[str, np.ndarray] = {}
    for key in rows[0]:
        try:
            numeric[key] = np.asarray([float(row[key]) for row in rows], dtype=float)
        except (TypeError, ValueError):
            continue
    return numeric


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_figure(fig: plt.Figure, stem: str) -> list[str]:
    paths = []
    for suffix in ("pdf", "png"):
        path = OUT / f"{stem}.{suffix}"
        fig.savefig(path)
        paths.append(str(path))
    plt.close(fig)
    return paths


def select_pairs() -> tuple[list[dict], list[dict]]:
    audit = load_json(AUDIT)
    runs = {Path(item["run_directory"]).name: item for item in audit["runs"]}
    by_mission: dict[str, dict[str, dict]] = {}
    for name, item in runs.items():
        mission = item["mission"]
        by_mission.setdefault(mission, {})[item["controller"]] = {**item, "run_name": name}

    selected, excluded = [], []
    for mission, controllers in by_mission.items():
        if "pd" not in controllers or "nengo-pes" not in controllers:
            continue
        pd = controllers["pd"]
        cmg = controllers["nengo-pes"]
        mean_imp = 100.0 * (pd["angle_err_mean_deg"] - cmg["angle_err_mean_deg"]) / pd["angle_err_mean_deg"]
        max_imp = 100.0 * (pd["angle_err_max_deg"] - cmg["angle_err_max_deg"]) / pd["angle_err_max_deg"]
        row = {
            "mission": mission,
            "reference_scale": pd["reference_scale"],
            "duration_s": pd["duration_s"],
            "pd_run": pd["run_name"],
            "cmg_run": cmg["run_name"],
            "pd_mean_deg": pd["angle_err_mean_deg"],
            "cmg_mean_deg": cmg["angle_err_mean_deg"],
            "mean_improvement_pct": mean_imp,
            "pd_max_deg": pd["angle_err_max_deg"],
            "cmg_max_deg": cmg["angle_err_max_deg"],
            "max_improvement_pct": max_imp,
            "mean_improved": mean_imp > 0.0,
            "max_improved": max_imp > 0.0,
        }
        (selected if mean_imp > 0.0 else excluded).append(row)

    order = {name: index for index, name in enumerate(MISSION_ORDER)}
    selected.sort(key=lambda row: order.get(row["mission"], 999))
    excluded.sort(key=lambda row: order.get(row["mission"], 999))
    return selected, excluded


def plot_mission_tracking(row: dict) -> list[str]:
    mission = row["mission"]
    pd = load_trace(DIRECT / row["pd_run"] / "trace.csv")
    cmg = load_trace(DIRECT / row["cmg_run"] / "trace.csv")

    fig, axes = plt.subplots(2, 2, figsize=(7.15, 4.75), sharex=True)
    for ax, axis, panel in zip(axes.flat[:3], ("yaw", "pitch", "roll"), ("a", "b", "c")):
        ax.plot(pd["t"], pd[f"{axis}_ref_deg"], color=REF_COLOR, ls="--", lw=1.25, label="Reference")
        ax.plot(pd["t"], pd[f"{axis}_deg"], color=PD_COLOR, lw=1.05, label="PD")
        ax.plot(cmg["t"], cmg[f"{axis}_deg"], color=CMG_COLOR, lw=1.05, label="CMG--PES")
        ax.set_ylabel(f"{axis.capitalize()} [deg]")
        ax.set_title(f"({panel}) {axis.capitalize()}", loc="left")
        ax.grid(alpha=0.22, linewidth=0.6)

    error_ax = axes.flat[3]
    pd_error = np.degrees(pd["qerr_rad"])
    cmg_error = np.degrees(cmg["qerr_rad"])
    error_ax.plot(pd["t"], pd_error, color=PD_COLOR, lw=1.15, label="PD")
    error_ax.plot(cmg["t"], cmg_error, color=CMG_COLOR, lw=1.15, label="CMG--PES")
    error_ax.axhline(row["pd_mean_deg"], color=PD_COLOR, lw=0.85, ls=":")
    error_ax.axhline(row["cmg_mean_deg"], color=CMG_COLOR, lw=0.85, ls=":")
    error_ax.set_ylabel(r"Quaternion error $\theta_e$ [deg]")
    error_ax.set_title("(d) Quaternion-angle error", loc="left")
    error_ax.grid(alpha=0.22, linewidth=0.6)

    for ax in axes[1, :]:
        ax.set_xlabel("Time [s]")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False)
    qualifier = ""
    if mission == "hover":
        qualifier = "; near encoder-resolution floor"
    fig.suptitle(
        rf"Quanser 3DOF Hover: {MISSION_LABEL[mission]} "
        rf"(mean $\theta_e$: {row['pd_mean_deg']:.3f}$^\circ$ $\rightarrow$ "
        rf"{row['cmg_mean_deg']:.3f}$^\circ$, {row['mean_improvement_pct']:+.2f}%{qualifier})",
        y=1.055,
        fontsize=9.5,
    )
    fig.tight_layout(pad=0.8)
    return save_figure(fig, f"fig_hover3dof_{mission}_tracking_positive")


def plot_summary(rows: list[dict]) -> list[str]:
    labels = [MISSION_LABEL[row["mission"]] for row in rows]
    y = np.arange(len(rows))
    pd_mean = np.asarray([row["pd_mean_deg"] for row in rows])
    cmg_mean = np.asarray([row["cmg_mean_deg"] for row in rows])
    mean_imp = np.asarray([row["mean_improvement_pct"] for row in rows])
    max_imp = np.asarray([row["max_improvement_pct"] for row in rows])

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7.15, 3.25), gridspec_kw={"width_ratios": [1.45, 1.0]})

    for i, row in enumerate(rows):
        ax0.plot([pd_mean[i], cmg_mean[i]], [i, i], color="#9AA3AD", lw=1.5, zorder=1)
    ax0.scatter(pd_mean, y, s=42, color=PD_COLOR, label="PD", zorder=3)
    ax0.scatter(cmg_mean, y, s=42, color=CMG_COLOR, marker="s", label="CMG--PES", zorder=3)
    ax0.set_xscale("log")
    ax0.set_yticks(y, labels)
    ax0.invert_yaxis()
    ax0.set_xlabel(r"Mean quaternion-angle error $\overline{\theta}_e$ [deg] (log scale)")
    ax0.set_title("(a) Positive mean-error cases", loc="left")
    ax0.grid(axis="x", alpha=0.25, which="both")
    ax0.legend(frameon=False, loc="lower right")
    for i, improvement in enumerate(mean_imp):
        x_text = max(pd_mean[i], cmg_mean[i]) * 1.08
        ax0.text(x_text, i, f"{improvement:+.2f}%", va="center", fontsize=7.5, fontweight="bold")

    colors = ["#009E73" if value >= 0.0 else "#B5483A" for value in max_imp]
    ax1.barh(y, max_imp, color=colors, height=0.58)
    ax1.axvline(0.0, color=REF_COLOR, lw=0.9)
    ax1.set_yticks(y, labels)
    ax1.invert_yaxis()
    ax1.set_xlabel("Peak-error change [%]\n(positive is better)")
    ax1.set_title("(b) Secondary peak metric", loc="left")
    ax1.grid(axis="x", alpha=0.22)
    for i, value in enumerate(max_imp):
        offset = 0.8 if value >= 0 else -0.8
        ax1.text(value + offset, i, f"{value:+.2f}%", va="center", ha="left" if value >= 0 else "right", fontsize=7.5)

    fig.suptitle("Physical 3DOF Hover cases selected by lower mean quaternion-angle error", fontsize=10, y=1.02)
    fig.tight_layout(pad=0.9)
    return save_figure(fig, "fig_hover3dof_positive_mean_summary")


def plot_mechanism_grid(rows: list[dict]) -> list[str]:
    fig, axes = plt.subplots(len(rows), 2, figsize=(7.15, 7.0), squeeze=False)
    activity_labels = (r"$+\psi$", r"$+\theta$", r"$+\phi$", r"$-\psi$", r"$-\theta$", r"$-\phi$")
    for row_index, row in enumerate(rows):
        mission = row["mission"]
        cmg = load_trace(DIRECT / row["cmg_run"] / "trace.csv")
        torque_ax, activity_ax = axes[row_index]
        for axis, color in zip(("yaw", "pitch", "roll"), AXIS_COLORS):
            torque_ax.plot(
                cmg["t"],
                cmg[f"requested_delta_tau_{axis}"],
                lw=0.8,
                color=color,
                label=axis.capitalize(),
            )
        for unit, (label, color) in enumerate(zip(activity_labels, ACTIVITY_COLORS)):
            activity_ax.plot(cmg["t"], cmg[f"neuron_activity_{unit}"], lw=0.65, color=color, label=label)
        torque_ax.set_ylabel(f"{MISSION_LABEL[mission]}\nResidual [N m]")
        torque_ax.grid(alpha=0.2, linewidth=0.6)
        activity_ax.grid(alpha=0.2, linewidth=0.6)
        if row_index == 0:
            torque_ax.set_title("(a) Requested CMG--PES residual torque", loc="left")
            activity_ax.set_title("(b) Gate-derived decoder activity", loc="left")
        if row_index == len(rows) - 1:
            torque_ax.set_xlabel("Time [s]")
            activity_ax.set_xlabel("Time [s]")
        activity_ax.set_ylabel("Activity")
    axes[0, 0].legend(frameon=False, ncol=3, loc="upper right")
    axes[0, 1].legend(frameon=False, ncol=3, loc="upper right")
    fig.suptitle("CMG--PES internal signals for positive-mean-error physical cases", fontsize=10, y=1.005)
    fig.tight_layout(pad=0.7)
    return save_figure(fig, "fig_hover3dof_positive_cmg_mechanism")


def plot_roll_n3() -> list[str]:
    data = load_json(ROLL_N3)
    trials = data["paired_trials"]
    aggregate = data["aggregate"]
    pd = np.asarray([row["pd_mean_error_deg"] for row in trials])
    cmg = np.asarray([row["cmg_mean_error_deg"] for row in trials])
    improvements = np.asarray([row["paired_mean_improvement_percent"] for row in trials])
    x = np.arange(1, len(trials) + 1)

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7.15, 3.15))
    for i in range(len(trials)):
        ax0.plot([x[i], x[i]], [pd[i], cmg[i]], color="#9AA3AD", lw=1.4)
    ax0.scatter(x, pd, s=46, color=PD_COLOR, label="PD", zorder=3)
    ax0.scatter(x, cmg, s=46, color=CMG_COLOR, marker="s", label="CMG--PES", zorder=3)
    ax0.set_xticks(x)
    ax0.set_xlabel("Matched trial")
    ax0.set_ylabel(r"Mean quaternion-angle error $\overline{\theta}_e$ [deg]")
    ax0.set_title("(a) Paired physical trials", loc="left")
    ax0.grid(alpha=0.23)
    ax0.legend(frameon=False)

    ax1.bar(x, improvements, color="#E69F00", width=0.62)
    mean = aggregate["paired_mean_improvement_percent"]["mean"]
    sd = aggregate["paired_mean_improvement_percent"]["sample_sd"]
    ax1.axhline(mean, color=REF_COLOR, ls="--", lw=1.0, label=f"mean {mean:.2f}%")
    ax1.set_xticks(x)
    ax1.set_xlabel("Matched trial")
    ax1.set_ylabel("Mean-error improvement [%]")
    ax1.set_title("(b) Improvement in every pair", loc="left")
    ax1.grid(axis="y", alpha=0.23)
    ax1.legend(frameon=False)
    for i, value in enumerate(improvements):
        ax1.text(x[i], value + 0.08, f"{value:.2f}%", ha="center", va="bottom", fontsize=7.5)

    fig.suptitle(
        rf"Quanser 3DOF Hover Roll validation: $n=3$ per controller; paired improvement "
        rf"{mean:.2f}% $\pm$ {sd:.2f}% (sample SD)",
        fontsize=9.5,
        y=1.02,
    )
    fig.tight_layout(pad=0.85)
    return save_figure(fig, "fig_hover3dof_roll_n3_primary")


def write_manifest(rows: list[dict], excluded: list[dict], figures: list[str]) -> None:
    manifest = {
        "schema": 1,
        "created": "2026-09-03",
        "purpose": "ACC 2027 Overleaf-ready physical 3DOF Hover figures",
        "selection_rule": "canonical matched direct-Nengo pair with mean_improvement_pct > 0",
        "metric": "mean quaternion-angle error computed from qerr_rad and verified against summary.json",
        "selected_positive_mean_cases": rows,
        "excluded_nonpositive_cases": excluded,
        "important_qualifications": [
            "Hover is near the encoder-resolution/noise floor and is not a headline performance result.",
            "Roll, Hard45, and Hardstep improve mean error in the selected single pair, but their single-run peak errors do not all improve.",
            "The independent Roll n=3 campaign is the primary physical performance evidence.",
            "Full3 and reduced-range Yaw360 remain valid negative results and must stay in the complete paper table even though no positive-only detail plot is generated.",
            "Historical LQR Hover figures are not mixed with this PD/Nengo bundle because they use an eight-unit four-motor-voltage architecture rather than the canonical three-channel quaternion-torque residual.",
        ],
        "sources": {
            "frozen_audit": str(AUDIT),
            "direct_hardware_data": str(DIRECT),
            "roll_n3_summary": str(ROLL_N3),
        },
        "generated_figures": figures,
    }
    (OUT / "FIGURE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with (OUT / "positive_mean_results.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "mission",
            "reference_scale",
            "duration_s",
            "pd_mean_deg",
            "cmg_mean_deg",
            "mean_improvement_pct",
            "pd_max_deg",
            "cmg_max_deg",
            "max_improvement_pct",
            "pd_run",
            "cmg_run",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    configure_style()
    OUT.mkdir(parents=True, exist_ok=True)
    selected, excluded = select_pairs()
    selected_names = [row["mission"] for row in selected]
    if selected_names != list(MISSION_ORDER):
        raise RuntimeError(f"Frozen positive-case set changed unexpectedly: {selected_names}")

    figures: list[str] = []
    figures.extend(plot_summary(selected))
    figures.extend(plot_roll_n3())
    figures.extend(plot_mechanism_grid(selected))
    for row in selected:
        figures.extend(plot_mission_tracking(row))
    write_manifest(selected, excluded, figures)

    print("Selected positive-mean cases:")
    for row in selected:
        print(
            f"  {row['mission']:<8} mean {row['pd_mean_deg']:.6f} -> "
            f"{row['cmg_mean_deg']:.6f} deg ({row['mean_improvement_pct']:+.3f}%); "
            f"peak change {row['max_improvement_pct']:+.3f}%"
        )
    print("Excluded from positive-only figures:")
    for row in excluded:
        print(f"  {row['mission']:<8} mean improvement {row['mean_improvement_pct']:+.3f}%")
    print(f"Wrote {len(figures)} figure files to {OUT}")


if __name__ == "__main__":
    main()

