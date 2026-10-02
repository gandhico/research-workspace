"""Combine strict and frozen threshold-aware validation into the final report."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = HERE / "analysis" / "final"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
PLATFORMS = ("x2", "cf2-rotor")
FAMILIES = ("lif", "alif", "lifrate", "izhikevich")
STRICT_CONTROLLERS = ("cmg", *FAMILIES, "constant-one", "paired-current")
DISPLAY = {
    "cmg": "CMG",
    "lif": "LIF",
    "alif": "ALIF",
    "lifrate": "LIFRate",
    "izhikevich": "Izhikevich",
    "constant-one": "Constant",
    "paired-current": "Static paired",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def gmean(values):
    return math.exp(sum(math.log(v) for v in values) / len(values))


def strict_path(platform, mission, controller):
    return RESULTS / "strict_exact" / platform / mission / controller


def tuned_path(platform, mission, family):
    phase = "selected_confirm" if platform == "x2" and mission in ("roll", "hard45") else "selected_validate"
    return RESULTS / phase / platform / mission / family


def activity_stats(directory):
    archive_path = directory / "neural_trace_full_rate.npz"
    if not archive_path.exists():
        return 0.0, 0.0, 0.0
    with np.load(archive_path) as archive:
        activity = np.asarray(archive["activity"], dtype=float)
    return (
        float(np.mean(activity > 1e-6)),
        float(np.mean(activity >= 0.999)),
        float(np.mean(np.std(activity, axis=0))),
    )


def metric(summary):
    return summary["metrics"]["qerr_true_mean_rad"]


def effort(summary):
    return summary["metrics"]["gated_residual_normalized_rms"]


def aggregate(source):
    rows = []
    for platform in PLATFORMS:
        baseline = {m: metric(load(strict_path(platform, m, "classical") / "summary.json")) for m in MISSIONS}
        controllers = STRICT_CONTROLLERS if source == "strict" else FAMILIES
        for controller in controllers:
            directories = [
                strict_path(platform, m, controller) if source == "strict" else tuned_path(platform, m, controller)
                for m in MISSIONS
            ]
            summaries = [load(directory / "summary.json") for directory in directories]
            activities = [activity_stats(directory) for directory in directories]
            ratios = [metric(s) / baseline[m] for s, m in zip(summaries, MISSIONS)]
            heldout_indices = (
                [1, 3, 4] if source == "tuned" and platform == "x2" else list(range(5))
            )
            heldout_ratio = gmean([ratios[i] for i in heldout_indices])
            rows.append({
                "source": source,
                "platform": platform,
                "controller": controller,
                **{f"{m}_improvement_percent": 100.0 * (1.0-r) for m, r in zip(MISSIONS, ratios)},
                "geomean_error_ratio": gmean(ratios),
                "geomean_improvement_percent": 100.0 * (1.0-gmean(ratios)),
                "heldout_geomean_improvement_percent": 100.0 * (1.0-heldout_ratio),
                "mean_residual_nrms": float(np.mean([effort(s) for s in summaries])),
                "mean_activity_active_fraction": float(np.mean([a[0] for a in activities])),
                "mean_activity_rail_fraction": float(np.mean([a[1] for a in activities])),
                "mean_activity_temporal_std": float(np.mean([a[2] for a in activities])),
                "worst_mission_improvement_percent": min(100.0*(1.0-r) for r in ratios),
            })
    return rows


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_basis(strict_rows):
    controllers = ("cmg", "constant-one", "paired-current", "lif", "alif", "lifrate", "izhikevich")
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.2), constrained_layout=True)
    for ax, platform in zip(axes, PLATFORMS):
        rows = {(r["controller"]): r for r in strict_rows if r["platform"] == platform}
        vals = [rows[c]["geomean_improvement_percent"] for c in controllers]
        colors = ["#0072B2", "#777777", "#999999", "#E69F00", "#CC79A7", "#56B4E9", "#D55E00"]
        bars = ax.bar(range(len(controllers)), vals, color=colors)
        ax.axhline(0, color="0.25", lw=0.9)
        ax.set_xticks(range(len(controllers)), [DISPLAY[c] for c in controllers], rotation=28, ha="right")
        ax.set_ylabel("geometric-mean error reduction [%]")
        ax.set_title("Skydio X2" if platform == "x2" else "Crazyflie 2.0 (1.5x rotors)")
        ax.grid(axis="y", alpha=0.25)
        for bar, value in zip(bars, vals):
            ax.text(bar.get_x()+bar.get_width()/2, value, f"{value:+.1f}", ha="center", va="bottom" if value >= 0 else "top", fontsize=8)
    fig.savefig(OUT / "basis_mechanism_comparison.pdf", bbox_inches="tight")
    fig.savefig(OUT / "basis_mechanism_comparison.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def plot_tuning(strict_rows, tuned_rows):
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.3), constrained_layout=True)
    x = np.arange(len(FAMILIES))
    width = 0.36
    for ax, platform in zip(axes, PLATFORMS):
        strict = {r["controller"]: r for r in strict_rows if r["platform"] == platform}
        tuned = {r["controller"]: r for r in tuned_rows if r["platform"] == platform}
        sv = [strict[f]["geomean_improvement_percent"] for f in FAMILIES]
        tv = [tuned[f]["geomean_improvement_percent"] for f in FAMILIES]
        ax.bar(x-width/2, sv, width, label="strict shared map", color="#999999")
        ax.bar(x+width/2, tv, width, label="threshold-aware", color="#009E73")
        ax.axhline(0, color="0.25", lw=0.9)
        ax.set_xticks(x, [DISPLAY[f] for f in FAMILIES], rotation=20, ha="right")
        ax.set_ylabel("geometric-mean error reduction [%]")
        ax.set_title("Skydio X2" if platform == "x2" else "Crazyflie 2.0 (1.5x rotors)")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(frameon=False, fontsize=8)
    fig.savefig(OUT / "family_tuning_comparison.pdf", bbox_inches="tight")
    fig.savefig(OUT / "family_tuning_comparison.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def report(strict_rows, tuned_rows):
    strict = {(r["platform"], r["controller"]): r for r in strict_rows}
    tuned = {(r["platform"], r["controller"]): r for r in tuned_rows}
    settings = load(HERE / "analysis" / "development" / "selected_settings.json")
    lines = [
        "# Final conclusion: neuron family and no-neuron basis",
        "",
        "This report uses the mathematically corrected, equal normalized PES rate and the final rho=3 PD+desired-rate-feedforward baseline. Positive percentages denote lower mean quaternion-angle error.",
        "",
        "## Strict matched result",
        "",
        "| Basis | X2 geo. improvement | X2 effort | X2 active | CF2 geo. improvement | CF2 effort | CF2 active |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for controller in STRICT_CONTROLLERS:
        x = strict[("x2", controller)]
        c = strict[("cf2-rotor", controller)]
        lines.append(f"| {DISPLAY[controller]} | {x['geomean_improvement_percent']:+.2f}% | {x['mean_residual_nrms']:.3f} | {100*x['mean_activity_active_fraction']:.1f}% | {c['geomean_improvement_percent']:+.2f}% | {c['mean_residual_nrms']:.3f} | {100*c['mean_activity_active_fraction']:.1f}% |")
    lines += [
        "",
        "## Threshold-aware conventional families",
        "",
        "| Family | Frozen setting (bias, gain, filter) | X2 strict -> tuned all / held-out | CF2 strict -> tuned held-out | Tuned worst mission X2 / CF2 |",
        "|---|---|---:|---:|---:|",
    ]
    for family in FAMILIES:
        s = settings[family]
        xs, xt = strict[("x2", family)], tuned[("x2", family)]
        cs, ct = strict[("cf2-rotor", family)], tuned[("cf2-rotor", family)]
        lines.append(
            f"| {DISPLAY[family]} | ({s['current_bias']:.2f}, {s['current_gain']:.2f}, {1000*s['feature_tau_s']:.0f} ms) | {xs['geomean_improvement_percent']:+.2f}% -> {xt['geomean_improvement_percent']:+.2f}% / {xt['heldout_geomean_improvement_percent']:+.2f}% | {cs['geomean_improvement_percent']:+.2f}% -> {ct['heldout_geomean_improvement_percent']:+.2f}% | {xt['worst_mission_improvement_percent']:+.1f}% / {ct['worst_mission_improvement_percent']:+.1f}% |"
        )
    lines += [
        "",
        "## Mission-level tuned result",
        "",
        "X2 Roll and Hard45 are development missions (15 s selection, 45 s confirmation); X2 Full3/Hardstep/Yaw360 and every CF2 mission are held out. Therefore the X2 five-mission geometric mean is descriptive, while the three-mission held-out value in the preceding table is the validation statistic.",
        "",
        "| Platform | Family | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean | Activity |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for platform in PLATFORMS:
        for family in FAMILIES:
            item = tuned[(platform, family)]
            lines.append(
                f"| {platform} | {DISPLAY[family]} | "
                + " | ".join(f"{item[f'{m}_improvement_percent']:+.1f}%" for m in MISSIONS)
                + f" | {item['geomean_improvement_percent']:+.2f}% | {100*item['mean_activity_active_fraction']:.1f}% |"
            )
    lines += [
        "",
        "## Mechanistic reading",
        "",
        "- The untuned thresholded families are active on only a few percent of unit-samples and are nearly neutral. This is an operating-point failure, not proof that PES cannot work with them.",
        "- Threshold-aware LIF and ALIF become useful mainly on Full3 and Hard45; they still provide essentially no benefit on the tiny-error Yaw360 case.",
        "- Tuned LIFRate is active essentially continuously and is the strongest conventional alternative. Its persistent continuous feature supports the persistence hypothesis, yet CMG retains the larger cross-mission improvement at comparable residual effort.",
        "- Lowering Izhikevich bias removes the low-error residual floor: Roll and Yaw360 recover the baseline exactly. The cost is inactivity on those missions, so its gains are confined to larger-error trajectories.",
        "- CMG is nearly always active but only about half of its unit-samples are at the activity ceiling; it retains branch-dependent temporal variation. It substantially exceeds both a constant feature and an instantaneous paired feature. The supported mechanism is therefore persistent, bounded, temporally structured activity—not conductance modulation by itself.",
        "",
        "## Claim boundary",
        "",
        "1. The corrected result can establish whether CMG is a better activity basis under this residual interface; it cannot attribute the advantage specifically to current-dependent conductance because the prior chi ablation remains nearly inactive.",
        "2. A tuned standard family that improves demonstrates feasibility, not equality: it may require a different operating point and may have materially different spike/effort statistics.",
        "3. A no-neuron control that improves confirms that PES and bounded residual learning carry part of the benefit. Only the performance gap between CMG and those controls is evidence associated with CMG temporal state/activation.",
        "4. These simulation conclusions should precede—not be mixed with—the planned controller-family expansion and later hardware evidence.",
    ]
    (OUT / "FINAL_NEURON_BASIS_REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    strict_rows = aggregate("strict")
    tuned_rows = aggregate("tuned")
    write_csv(OUT / "strict_aggregate.csv", strict_rows)
    write_csv(OUT / "tuned_aggregate.csv", tuned_rows)
    plot_basis(strict_rows)
    plot_tuning(strict_rows, tuned_rows)
    report(strict_rows, tuned_rows)
    print(f"Final report written to {OUT}")


if __name__ == "__main__":
    main()
