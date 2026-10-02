"""Aggregate ACC 2027 QLabs pendulum runs and build a compact paper figure."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_ORDER = [
    "classical",
    "fixed-residual",
    "adaptive-residual",
    "online-pes-fixed",
    "online-pes-adaptive",
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT / "results" / "acc2027_twin")
    p.add_argument("--label", default="closure_nominal")
    p.add_argument("--output", type=Path, default=ROOT / "analysis" / "acc2027_twin_closure")
    return p


def main() -> None:
    args = parser().parse_args()
    records: list[dict] = []
    for path in sorted(args.root.glob("*/summary.json")):
        if args.label not in path.parent.name:
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        record["run_directory"] = str(path.parent)
        records.append(record)
    if not records:
        raise SystemExit(f"No summaries containing label {args.label!r} under {args.root}")

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    baseline_values = [
        float(r["alpha_rms_tail_deg"])
        for r in records
        if r["controller"] == "classical" and r["alpha_rms_tail_deg"] is not None
    ]
    baseline_mean = float(np.mean(baseline_values))
    aggregate: list[dict] = []
    for controller in CONTROLLER_ORDER:
        group = [r for r in records if r["controller"] == controller]
        if not group:
            continue
        errors = np.asarray(
            [float(r["alpha_rms_tail_deg"]) for r in group if r["alpha_rms_tail_deg"] is not None]
        )
        residuals = np.asarray(
            [float(r["residual_rms_balance_v"]) for r in group if r["residual_rms_balance_v"] is not None]
        )
        row = {
            "controller": controller,
            "n": len(errors),
            "alpha_rms_tail_mean_deg": float(np.mean(errors)),
            "alpha_rms_tail_std_deg": float(np.std(errors, ddof=1)) if len(errors) > 1 else 0.0,
            "improvement_vs_classical_percent": 100.0 * (baseline_mean - float(np.mean(errors))) / baseline_mean,
            "residual_rms_balance_mean_v": float(np.mean(residuals)) if len(residuals) else 0.0,
            "all_tail_balanced": all(float(r["balance_fraction_tail_5s"]) == 1.0 for r in group),
            "fault_samples": sum(int(r["amplifier_fault_samples"]) for r in group),
            "stall_samples": sum(int(r["stall_samples"]) for r in group),
        }
        aggregate.append(row)

    with (output / "aggregate.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(aggregate[0]))
        writer.writeheader()
        writer.writerows(aggregate)

    lines = [
        "# ACC 2027 QLabs pendulum aggregate",
        "",
        f"Selection label: `{args.label}`. Metrics use the final five seconds of each run.",
        "",
        "| Controller | n | alpha RMS (deg) | Improvement | residual RMS (V) | Tail balanced | Faults/stalls |",
        "|---|---:|---:|---:|---:|:---:|---:|",
    ]
    for row in aggregate:
        lines.append(
            f"| {row['controller']} | {row['n']} | "
            f"{row['alpha_rms_tail_mean_deg']:.4f} +/- {row['alpha_rms_tail_std_deg']:.4f} | "
            f"{row['improvement_vs_classical_percent']:+.2f}% | "
            f"{row['residual_rms_balance_mean_v']:.4f} | "
            f"{'yes' if row['all_tail_balanced'] else 'no'} | "
            f"{row['fault_samples']}/{row['stall_samples']} |"
        )
    lines.extend(
        [
            "",
            "Interpret repeated-trial statistics only when n >= 3. Capture time is not a matched metric because the QLabs arm state is not reset between processes.",
        ]
    )
    (output / "aggregate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    labels = [r["controller"].replace("-", "\n") for r in aggregate]
    means = [r["alpha_rms_tail_mean_deg"] for r in aggregate]
    stds = [r["alpha_rms_tail_std_deg"] for r in aggregate]
    fig, ax = plt.subplots(figsize=(9.0, 4.8), constrained_layout=True)
    colors = ["#5B6573", "#2B7A78", "#3AAFA9", "#6C5CE7", "#A66DD4"]
    ax.bar(np.arange(len(means)), means, yerr=stds, capsize=4, color=colors[: len(means)])
    ax.set_xticks(np.arange(len(means)), labels)
    ax.set_ylabel("Final-5-s pendulum-angle RMS (deg)")
    ax.set_title("QUBE Servo 3 QLabs twin: bounded additive residual control")
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(output / "pendulum_tail_rms.png", dpi=220)
    fig.savefig(output / "pendulum_tail_rms.pdf")
    plt.close(fig)
    print((output / "aggregate.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
