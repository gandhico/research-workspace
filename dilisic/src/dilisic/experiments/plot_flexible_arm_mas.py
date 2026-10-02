"""Plot and summarize DILISIC flexible-arm MAS trajectories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def load_trajectory(csv_path: Path) -> np.ndarray:
    data = np.genfromtxt(csv_path, delimiter=",", names=True)
    if data.size == 0:
        raise ValueError(f"No trajectory rows found in {csv_path}")
    return np.atleast_1d(data)


def summarize(csv_path: Path) -> dict[str, float]:
    data = load_trajectory(csv_path)
    names = data.dtype.names or ()
    q_cols = [name for name in names if name.startswith("q_")]
    v_cols = [name for name in names if name.startswith("v_")]
    u_cols = [name for name in names if name.startswith("u_")]
    if not q_cols or not v_cols or not u_cols:
        raise ValueError("CSV must contain q_*, v_*, and u_* columns")

    q = np.column_stack([data[col] for col in q_cols])
    v = np.column_stack([data[col] for col in v_cols])
    u = np.column_stack([data[col] for col in u_cols])
    com = np.mean(q, axis=1)
    q_ref = -np.pi * np.sin(data["t"]) / 10.0

    return {
        "duration": float(data["t"][-1] - data["t"][0]),
        "samples": float(data.size),
        "final_com": float(com[-1]),
        "final_com_error": float(com[-1] - q_ref[-1]),
        "rms_com_error": float(np.sqrt(np.mean((com - q_ref) ** 2))),
        "max_position_spread": float(np.max(np.ptp(q, axis=1))),
        "max_velocity_spread": float(np.max(np.ptp(v, axis=1))),
        "max_abs_control": float(np.max(np.abs(u))),
        "max_abs_s_agent0": float(np.max(np.abs(data["s_0"]))) if "s_0" in names else float("nan"),
        "final_f_hat_agent0": float(data["f_hat_0"][-1]) if "f_hat_0" in names else float("nan"),
        "final_h_hat_agent0": float(data["h_hat_0"][-1]) if "h_hat_0" in names else float("nan"),
    }


def plot(csv_path: Path, output_dir: Path) -> list[Path]:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - depends on local optional GUI stack
        raise RuntimeError("matplotlib is required for plotting") from exc

    data = load_trajectory(csv_path)
    names = data.dtype.names or ()
    t = data["t"]
    q_cols = [name for name in names if name.startswith("q_")]
    v_cols = [name for name in names if name.startswith("v_")]
    u_cols = [name for name in names if name.startswith("u_")]
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    written.append(_line_plot(output_dir / "positions.png", t, data, q_cols, "Position", "rad", plt))
    written.append(_line_plot(output_dir / "velocities.png", t, data, v_cols, "Velocity", "rad/s", plt))
    written.append(_line_plot(output_dir / "controls.png", t, data, u_cols, "Control input", "input units", plt))

    q = np.column_stack([data[col] for col in q_cols])
    com = np.mean(q, axis=1)
    q_ref = -np.pi * np.sin(t) / 10.0
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(t, q_ref, "k--", linewidth=1.3, label="reference")
    axes[0].plot(t, com, linewidth=1.2, label="center of mass")
    axes[0].axvspan(30.0, 45.0, color="tab:orange", alpha=0.12, label="obstacle active")
    axes[0].axvspan(70.0, 75.0, color="tab:red", alpha=0.10, label="disturbance")
    axes[0].set_ylabel("angle [rad]")
    axes[0].legend(ncol=2, fontsize=8)
    axes[1].plot(t, com - q_ref, color="tab:blue", linewidth=1.0)
    axes[1].axhline(0.0, color="black", linewidth=0.7)
    axes[1].set_ylabel("CoM error [rad]")
    axes[1].set_xlabel("time [s]")
    fig.tight_layout()
    path = output_dir / "center_of_mass_tracking.png"
    fig.savefig(path, dpi=160)
    written.append(path)
    plt.close(fig)

    if {"s_0", "f_hat_0", "h_hat_0"}.issubset(names):
        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        axes[0].plot(t, data["s_0"], linewidth=1.0)
        axes[0].set_ylabel("s")
        axes[0].set_title("Agent 0 LISIC signals")
        axes[1].plot(t, data["f_hat_0"], linewidth=1.0)
        axes[1].set_ylabel("f_hat")
        axes[2].plot(t, data["h_hat_0"], linewidth=1.0)
        axes[2].set_ylabel("h_hat")
        axes[2].set_xlabel("time [s]")
        fig.tight_layout()
        path = output_dir / "agent0_lisic_estimates.png"
        fig.savefig(path, dpi=160)
        written.append(path)
        plt.close(fig)

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summarize(csv_path), indent=2), encoding="utf-8")
    written.append(summary_path)
    return written


def _line_plot(path: Path, t: np.ndarray, data: np.ndarray, columns: list[str], title: str, ylabel: str, plt) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5))
    for col in columns:
        ax.plot(t, data[col], linewidth=1.0, label=col)
    ax.set_title(title)
    ax.set_xlabel("time [s]")
    ax.set_ylabel(ylabel)
    if len(columns) <= 10:
        ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path, help="Path to trajectory.csv")
    parser.add_argument("--output", type=Path, default=None, help="Directory for plots and summary")
    parser.add_argument("--summary-only", action="store_true", help="Print summary without creating plots")
    args = parser.parse_args()

    if args.summary_only:
        print(json.dumps(summarize(args.csv), indent=2))
        return

    output = args.output or args.csv.parent / "plots"
    written = plot(args.csv, output)
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
