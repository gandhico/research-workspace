"""Tracking/input comparison for explicit PD versus torque-space PD-CMG."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def load(run_dir: Path) -> tuple[dict[str, np.ndarray], dict]:
    with (run_dir / "trace.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    trace = {key: np.array([float(row[key]) for row in rows]) for key in rows[0]}
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    return trace, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pd", type=Path, required=True)
    parser.add_argument("--pd-cmg", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    pd, ps = load(args.pd)
    cmg, cs = load(args.pd_cmg)
    if ps["mission"] != cs["mission"] or ps["duration"] != cs["duration"]:
        raise SystemExit("Refusing mismatched mission/duration plot")

    fig, axes = plt.subplots(7, 1, figsize=(10.5, 16), sharex=True)
    for index, axis in enumerate(("yaw", "pitch", "roll")):
        ax = axes[index]
        ax.plot(pd["t"], pd[f"{axis}_ref_deg"], "k--", lw=1.1, label="reference")
        ax.plot(pd["t"], pd[f"{axis}_deg"], lw=1.0, label="explicit PD")
        ax.plot(cmg["t"], cmg[f"{axis}_deg"], lw=1.0, label="PD + torque-space CMG-PES")
        ax.set_ylabel(f"{axis} [deg]")
        ax.grid(alpha=.25)
        ax.legend(fontsize=8, ncol=3)

    for trace, label, color in ((pd, "PD", "tab:blue"), (cmg, "PD-CMG", "tab:orange")):
        if "wrapped_euler_error_norm_deg" in trace:
            error = trace["wrapped_euler_error_norm_deg"]
        else:
            components = np.column_stack([
                trace[f"{axis}_ref_deg"] - trace[f"{axis}_deg"] for axis in ("yaw", "pitch", "roll")
            ])
            components[:, 0] = np.rad2deg(np.arctan2(
                np.sin(np.deg2rad(components[:, 0])),
                np.cos(np.deg2rad(components[:, 0])),
            ))
            error = np.linalg.norm(components, axis=1)
        axes[3].plot(trace["t"], error, label=label, color=color, lw=1.0)
    axes[3].set_ylabel("|error| [deg]")
    axes[3].grid(alpha=.25)
    axes[3].legend()

    for channel in ("Vf", "Vb", "Vl", "Vr"):
        axes[4].plot(pd["t"], pd[channel], lw=.8, label=channel)
        axes[5].plot(cmg["t"], cmg[channel], lw=.8, label=channel)
    axes[4].set_ylabel("PD motor [V]")
    axes[5].set_ylabel("PD-CMG motor [V]")
    axes[4].legend(ncol=4, fontsize=8)
    axes[5].legend(ncol=4, fontsize=8)
    axes[4].grid(alpha=.25)
    axes[5].grid(alpha=.25)

    axes[6].plot(cmg["t"], cmg["requested_residual_torque_norm"], label="requested")
    axes[6].plot(cmg["t"], cmg["realized_residual_torque_norm"], label="realized")
    axes[6].set_ylabel("residual |tau| [Nm]")
    axes[6].set_xlabel("time [s]")
    axes[6].grid(alpha=.25)
    axes[6].legend()

    improvement = 100.0 * (ps["angle_err_mean_deg"] - cs["angle_err_mean_deg"]) / ps["angle_err_mean_deg"]
    fig.suptitle(
        f"3DOF Hover explicit PD experiment — {ps['mission']}\n"
        f"mean combined error: PD {ps['angle_err_mean_deg']:.3f} deg -> "
        f"PD-CMG {cs['angle_err_mean_deg']:.3f} deg ({improvement:+.2f}%)",
        fontsize=12,
    )
    fig.tight_layout(rect=[0, 0, 1, .955])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    print(args.out)


if __name__ == "__main__":
    main()
