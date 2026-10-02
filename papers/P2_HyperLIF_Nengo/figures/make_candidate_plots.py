"""Generate plots for the origin-aware tuning candidate sweep."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import matplotlib.pyplot as plt  # noqa: E402

from visualization.plotting import configure  # noqa: E402


CSV_DIR = PROJECT_ROOT / "results" / "csv"
OUT_DIRS = [PROJECT_ROOT / "results" / "figures", PROJECT_ROOT / "paper" / "figures"]
SUMMARY_CSV = CSV_DIR / "12_origin_aware_calibration_summary.csv"
ROWS_CSV = CSV_DIR / "12_origin_aware_calibration_sweep.csv"

APP_ORDER = [
    "communication_channel",
    "function_square",
    "transform_2d",
    "working_memory",
    "oscillator",
    "pes_learning",
]
APP_LABELS = ["Comm.", "Func.", "2D trans.", "Memory", "Osc.", "PES"]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_float(row: dict[str, str], key: str, default: float = np.nan) -> float:
    try:
        return float(row.get(key, ""))
    except ValueError:
        return default


def compact_label(row: dict[str, str]) -> str:
    label = row["candidate_id"]
    if row["family"] == "lif":
        return f"{label} LIF"
    fam = "H" if row["family"] == "hyperlif" else "A"
    theta = row["theta_event"]
    origin = ""
    if row["origin_policy"] == "static_v_reset":
        origin = f", vr={row['v_reset']}"
    rtc = row["rate_to_current"]
    if row["stage"] == "2_origin_aware_calibration":
        origin += f", rtc={rtc}"
    return f"{label} {fam} th={theta}{origin}"


def save(name: str) -> None:
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_dir / f"{name}.png", dpi=300)
        plt.savefig(out_dir / f"{name}.pdf")
    plt.close()


def plot_heatmap(summary: list[dict[str, str]]) -> None:
    top = summary[:18]
    data = np.array([
        [as_float(row, f"{app}_penalty") for app in APP_ORDER]
        for row in top
    ])
    clipped = np.clip(data, 0.0, 3.0)

    fig, ax = plt.subplots(figsize=(8.4, 7.2))
    im = ax.imshow(clipped, aspect="auto", cmap="viridis_r", vmin=0.0, vmax=3.0)
    ax.set_xticks(np.arange(len(APP_LABELS)))
    ax.set_xticklabels(APP_LABELS, rotation=30, ha="right")
    ax.set_yticks(np.arange(len(top)))
    ax.set_yticklabels([compact_label(row) for row in top], fontsize=7.4)
    ax.set_title("Candidate robustness by Nengo app (lower is better)")
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Penalty (clipped at 3)")

    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(
                j,
                i,
                f"{data[i, j]:.2f}",
                ha="center",
                va="center",
                color="white" if clipped[i, j] > 1.5 else "black",
                fontsize=6.2,
            )

    plt.tight_layout()
    save("fig_candidate_robustness_heatmap")


def plot_score_events(summary: list[dict[str, str]]) -> None:
    colors = {"lif": "#444444", "hyperlif": "#d64f45", "adaptive": "#5b5fc7"}
    markers = {"none": "o", "static_v_reset": "s"}

    fig, ax = plt.subplots(figsize=(7.2, 5.1))
    for row in summary:
        family = row["family"]
        origin = row["origin_policy"]
        ax.scatter(
            as_float(row, "mean_event_rate_hz"),
            as_float(row, "robust_score"),
            s=72,
            color=colors.get(family, "#888888"),
            marker=markers.get(origin, "^"),
            edgecolor="white",
            linewidth=0.8,
            alpha=0.9,
        )
        if int(float(row["rank"])) <= 8:
            ax.text(
                as_float(row, "mean_event_rate_hz") + 0.25,
                as_float(row, "robust_score") + 0.02,
                row["candidate_id"],
                fontsize=7,
            )

    ax.set_xlabel("Mean event rate across apps (Hz/neuron)")
    ax.set_ylabel("Robustness score (lower is better)")
    ax.set_title("Robustness vs activity across priority tuning candidates")
    ax.grid(True, color="0.9", linewidth=0.8)

    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", color="#444444", label="LIF"),
        plt.Line2D([0], [0], marker="o", linestyle="", color="#d64f45", label="HyperLIF"),
        plt.Line2D([0], [0], marker="o", linestyle="", color="#5b5fc7", label="Adaptive"),
        plt.Line2D([0], [0], marker="s", linestyle="", color="0.5", label="static origin"),
    ]
    ax.legend(handles=handles, loc="best", fontsize=8)
    plt.tight_layout()
    save("fig_candidate_score_events")


def plot_rate_calibration(summary: list[dict[str, str]]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    for family, color, label in (
        ("hyperlif", "#d64f45", "HyperLIF"),
        ("adaptive", "#5b5fc7", "Adaptive"),
    ):
        rows = [
            row for row in summary
            if row["stage"] == "2_origin_aware_calibration" and row["family"] == family
        ]
        rows.sort(key=lambda row: as_float(row, "rate_to_current"))
        ax.plot(
            [as_float(row, "rate_to_current") for row in rows],
            [as_float(row, "robust_score") for row in rows],
            marker="o",
            lw=1.8,
            color=color,
            label=label,
        )
        for row in rows:
            ax.text(
                as_float(row, "rate_to_current"),
                as_float(row, "robust_score") + 0.04,
                row["candidate_id"],
                fontsize=7,
                ha="center",
            )

    ax.set_xlabel("rate_to_current")
    ax.set_ylabel("Robustness score (lower is better)")
    ax.set_title("Origin-aware build-time rate calibration")
    ax.grid(True, color="0.9", linewidth=0.8)
    ax.legend(loc="best")
    plt.tight_layout()
    save("fig_candidate_rate_calibration")


def main() -> None:
    if not SUMMARY_CSV.exists():
        raise FileNotFoundError(
            f"{SUMMARY_CSV} not found. Run experiments/11_origin_aware_calibration_sweep.py first."
        )
    configure()
    summary = load_rows(SUMMARY_CSV)
    summary.sort(key=lambda row: as_float(row, "rank", 1.0e6))
    plot_heatmap(summary)
    plot_score_events(summary)
    plot_rate_calibration(summary)


if __name__ == "__main__":
    main()
