"""Six-unit yaw/pitch/roll CMG neuron and decoder diagnostic plot."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AXES = ("yaw", "pitch", "roll")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with (args.run_dir / "trace.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    data = {key: np.array([float(row[key]) for row in rows]) for key in rows[0]}
    summary = json.loads((args.run_dir / "summary.json").read_text(encoding="utf-8"))
    if "neuron_v_0" not in data:
        raise SystemExit("Trace has no neuron state columns")

    fig, axes = plt.subplots(8, 1, figsize=(10.5, 19), sharex=True)
    for branch, branch_name in enumerate(("positive", "negative")):
        for index, axis_name in enumerate(AXES):
            unit = branch * 3 + index
            axes[branch].plot(data["t"], data[f"neuron_v_{unit}"], lw=.9, label=axis_name)
            axes[branch + 2].plot(data["t"], data[f"neuron_r_{unit}"], lw=.9, label=axis_name)
            axes[branch + 4].plot(data["t"], data[f"neuron_activity_{unit}"], lw=.9, label=axis_name)
        axes[branch].set_ylabel(f"v ({branch_name})")
        axes[branch + 2].set_ylabel(f"r ({branch_name})")
        axes[branch + 2].set_ylim(-.05, 1.05)
        axes[branch + 4].set_ylabel(f"a ({branch_name})")
        axes[branch + 4].set_ylim(-.05, 1.05)
    for ax in axes[:6]:
        ax.grid(alpha=.25)
        ax.legend(ncol=3, fontsize=8)

    for axis_name in AXES:
        axes[6].plot(data["t"], data[f"requested_delta_tau_{axis_name}"], lw=.9, label=f"requested {axis_name}")
        axes[6].plot(data["t"], data[f"realized_delta_tau_{axis_name}"], lw=.8, ls="--", label=f"realized {axis_name}")
    axes[6].set_ylabel("delta tau [Nm]")
    axes[6].grid(alpha=.25)
    axes[6].legend(ncol=3, fontsize=7)

    if "decoder_w_0" in data:
        weights = np.column_stack([data[f"decoder_w_{index}"] for index in range(18)]).reshape(-1, 3, 6)
        for row, axis_name in enumerate(AXES):
            axes[7].plot(data["t"], np.linalg.norm(weights[:, row, :], axis=1), label=f"{axis_name} decoder row")
        axes[7].set_ylabel("||W row||2")
        axes[7].legend(ncol=3, fontsize=8)
    axes[7].set_xlabel("time [s]")
    axes[7].grid(alpha=.25)
    fig.suptitle(
        f"3DOF Hover torque-space CMG activity — {summary['mission']}\n"
        "6 units = yaw/pitch/roll x positive/negative branch; v, r, activity a, residual torque, decoder evolution",
        fontsize=12,
    )
    fig.tight_layout(rect=[0, 0, 1, .95])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    print(args.out)


if __name__ == "__main__":
    main()
