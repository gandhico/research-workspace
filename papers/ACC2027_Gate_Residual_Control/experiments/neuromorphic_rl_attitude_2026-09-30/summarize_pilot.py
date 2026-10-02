"""Compare matched RL evaluations and save a clearly labeled pilot figure."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")


def read_arm(root: Path):
    return {mission: json.loads((root / "eval" / mission / "summary.json").read_text())
            for mission in MISSIONS}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--arm", action="append", required=True,
                   help="LABEL=directory; repeat for each evaluated arm")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    baseline = read_arm(args.baseline)
    arms = {}
    for item in args.arm:
        label, path = item.split("=", 1)
        arms[label] = read_arm(Path(path))
    rows = []
    for label, arm in arms.items():
        for mission in MISSIONS:
            a, b = arm[mission], baseline[mission]
            for key in ("platform", "mission", "duration_s", "dt_s", "policy_dt_s"):
                if a[key] != b[key]:
                    raise ValueError(f"{label}/{mission}: mismatch in {key}: {a[key]} vs {b[key]}")
            rows.append({
                "platform": a["platform"], "mission": mission, "label": label,
                "duration_s": a["duration_s"],
                "baseline_mean_deg": b["qerr_true_mean_deg"],
                "rl_mean_deg": a["qerr_true_mean_deg"],
                "reduction_pct": 100 * (1 - a["qerr_true_mean_rad"] / b["qerr_true_mean_rad"]),
                "rl_effort_rms": a["realized_residual_normalized_rms"],
                "rl_rotor_sat_frac": a["rotor_saturation_fraction"],
                "rl_gate_frac": a["output_gate_fraction"],
            })
    with (args.output / "comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# Exploratory RL pilot comparison", "",
             "Positive reduction means lower true-state quaternion-angle error.\n",
             "| Platform | Duration | Arm | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean |",
             "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for label in arms:
        selected = [next(r for r in rows if r["label"] == label and r["mission"] == m) for m in MISSIONS]
        ratio = np.array([r["rl_mean_deg"] / r["baseline_mean_deg"] for r in selected])
        geo = 100 * (1 - float(np.exp(np.mean(np.log(ratio)))))
        lines.append("| {} | {:.0f} s | {} | {} | {:+.2f}% |".format(
            selected[0]["platform"], selected[0]["duration_s"], label,
            " | ".join(f"{r['reduction_pct']:+.2f}%" for r in selected), geo))
    lines += ["", "Development missions: Full3 and Hard45. Held-out missions: Roll, Hardstep and Yaw360.",
              "This table is a pilot, not a paper comparison or statistical result."]
    (args.output / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    fig, axes = plt.subplots(len(arms), 1, figsize=(8.4, 2.8 * len(arms)),
                             sharex=True, constrained_layout=True)
    axes = np.atleast_1d(axes)
    x = np.arange(len(MISSIONS))
    for ax, (label, _) in zip(axes, arms.items()):
        values = [next(r for r in rows if r["label"] == label and r["mission"] == m)["reduction_pct"] for m in MISSIONS]
        ax.bar(x, values, 0.62, color="#246A91")
        ax.axhline(0, color="black", linewidth=0.8)
        span = max(max(values) - min(values), 1.0)
        ax.set_ylim(min(values) - 0.16 * span, max(0.0, max(values)) + 0.18 * span)
        for j, value in enumerate(values):
            ax.annotate(f"{value:+.1f}%", (j, value), ha="center", va="top" if value < 0 else "bottom",
                        xytext=(0, -3 if value < 0 else 3), textcoords="offset points", fontsize=8)
        ax.set_ylabel(f"{label}\nreduction (%)")
        ax.grid(axis="y", alpha=0.2)
    axes[-1].set_xticks(x, ["Roll", "Full3", "Hard45", "Hardstep", "Yaw360"])
    fig.suptitle(f"Exploratory RL pilot | {rows[0]['platform']} | {rows[0]['duration_s']:g}-s evaluations")
    fig.savefig(args.output / "comparison.png", dpi=180)
    fig.savefig(args.output / "comparison.pdf")
    plt.close(fig)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
