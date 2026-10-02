"""Compare 45-s frozen RL replays with the paper's archived PD+ff baselines."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NOMINAL = ROOT / "experiments" / "final_robustness_gating_2026-09-20" / "results" / "final_nominal.csv"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")


def main():
    with NOMINAL.open(newline="", encoding="utf-8") as stream:
        source = list(csv.DictReader(stream))
    rows = []
    for platform in ("x2", "cf2-rotor"):
        out = HERE / "results" / f"full45_{'cf2' if platform == 'cf2-rotor' else 'x2'}_cmg_envelope" / "eval"
        if not all((out / mission / "summary.json").exists() for mission in MISSIONS):
            print(f"pending {platform}: incomplete 45-s replay")
            continue
        for mission in MISSIONS:
            matches = [r for r in source if r["platform"] == platform and r["mission"] == mission
                       and r["controller"] == "classical" and r["label"] == "pdff_rho3"
                       and r["campaign"] == "nominal" and r["status"] == "completed"]
            if len(matches) != 1:
                raise ValueError(f"Expected one archived PD+ff row for {platform}/{mission}: {len(matches)}")
            baseline = float(matches[0]["qerr_true_mean_rad"])
            rl = json.loads((out / mission / "summary.json").read_text())
            if rl["platform"] != platform or rl["mission"] != mission or rl["duration_s"] != 45 or rl["dt_s"] != 0.0005:
                raise ValueError(f"RL configuration mismatch: {platform}/{mission}")
            rows.append({"platform": platform, "mission": mission, "baseline_mean_rad": baseline,
                         "rl_mean_rad": rl["qerr_true_mean_rad"],
                         "reduction_pct": 100 * (1 - rl["qerr_true_mean_rad"] / baseline),
                         "rl_effort_rms": rl["realized_residual_normalized_rms"],
                         "rl_rotor_sat_frac": rl["rotor_saturation_fraction"]})
    if not rows:
        return
    analysis = HERE / "analysis" / "full45"
    analysis.mkdir(parents=True, exist_ok=True)
    with (analysis / "comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# Exploratory RL replay on the paper's 45-s missions", "",
             "Trained for six 10-s episodes on Full3/Hard45, then frozen. Positive is lower true-state mean quaternion error.",
             "Archived baseline: `experiments/final_robustness_gating_2026-09-20/results/final_nominal.csv`, classical `pdff_rho3` rows.",
             "", "| Platform | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for platform in ("x2", "cf2-rotor"):
        selected = [next((r for r in rows if r["platform"] == platform and r["mission"] == m), None) for m in MISSIONS]
        if any(r is None for r in selected):
            continue
        ratio = [r["rl_mean_rad"] / r["baseline_mean_rad"] for r in selected]
        geo = 100 * (1 - np.exp(np.mean(np.log(ratio))))
        lines.append("| {} | {} | {:+.2f}% |".format(
            platform, " | ".join(f"{r['reduction_pct']:+.2f}%" for r in selected), geo))
    lines += ["", "One training seed; descriptive only. Full3/Hard45 were used for training; Roll/Hardstep/Yaw360 were held out."]
    (analysis / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    platforms = [p for p in ("x2", "cf2-rotor") if any(r["platform"] == p for r in rows)]
    fig, axes = plt.subplots(len(platforms), 1,
                             figsize=(7.8, 2.8 * len(platforms)),
                             sharex=True, constrained_layout=True)
    axes = np.atleast_1d(axes)
    for ax, platform in zip(axes, platforms):
        selected = [next((r for r in rows if r["platform"] == platform and r["mission"] == m), None) for m in MISSIONS]
        if any(r is None for r in selected):
            continue
        values = [r["reduction_pct"] for r in selected]
        ax.bar(np.arange(5), values, color="#246A91", width=0.62)
        ax.axhline(0, color="black", linewidth=0.8)
        span = max(max(values) - min(values), 0.4)
        ax.set_ylim(min(values) - 0.18 * span, max(0.0, max(values)) + 0.18 * span)
        ax.set_ylabel(f"{platform}\nreduction (%)")
        ax.grid(axis="y", alpha=0.2)
        for i, v in enumerate(values):
            ax.annotate(f"{v:+.2f}%", (i, v), ha="center", va="bottom" if v >= 0 else "top",
                        xytext=(0, 3 if v >= 0 else -3), textcoords="offset points", fontsize=8)
    axes[-1].set_xticks(np.arange(5), ["Roll", "Full3", "Hard45", "Hardstep", "Yaw360"])
    axes[0].set_title("Exploratory CMG actor-critic replay | 45-s paper missions", pad=10)
    fig.savefig(analysis / "comparison.png", dpi=180)
    fig.savefig(analysis / "comparison.pdf")
    plt.close(fig)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
