"""Compile the strict matrix into audit CSV, figures, and a mechanism report."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results" / "strict_exact"
OUT = HERE / "analysis" / "strict"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
CONTROLLERS = (
    "classical",
    "cmg",
    "lif",
    "alif",
    "lifrate",
    "izhikevich",
    "constant-one",
    "paired-current",
)
DISPLAY = {
    "classical": "Baseline",
    "cmg": "CMG",
    "lif": "LIF",
    "alif": "ALIF",
    "lifrate": "LIFRate",
    "izhikevich": "Izhikevich",
    "constant-one": "Constant basis",
    "paired-current": "Static paired basis",
}


def geometric_mean(values):
    values = np.asarray(values, dtype=float)
    return float(np.exp(np.mean(np.log(values))))


def load_rows():
    rows = []
    for path in sorted(ROOT.rglob("summary.json")):
        summary = json.loads(path.read_text(encoding="utf-8"))
        controller = summary["controller"]
        row = {
            "platform": summary["platform"],
            "mission": summary["mission"],
            "controller": controller,
            "qerr_mean_rad": summary["metrics"]["qerr_true_mean_rad"],
            "qerr_mean_mrad": 1000.0 * summary["metrics"]["qerr_true_mean_rad"],
            "qerr_max_rad": summary["metrics"]["qerr_true_max_rad"],
            "residual_nrms": summary["metrics"]["gated_residual_normalized_rms"],
            "gate_blocked_fraction": summary["output_gate"]["blocked_fraction_any_axis"],
            "rotor_saturation_fraction": summary["actuation"]["rotor_saturation_fraction_any_rotor"],
            "run_id": summary["run_id"],
            "path": str(path.parent),
            "activity_mean": 0.0,
            "activity_active_fraction": 0.0,
            "activity_rail_fraction": 0.0,
            "activity_temporal_std": 0.0,
            "decoder_rail_fraction": 0.0,
        }
        archive_path = path.parent / "neural_trace_full_rate.npz"
        if archive_path.exists():
            with np.load(archive_path) as archive:
                activity = np.asarray(archive["activity"], dtype=float)
                decoded = np.asarray(archive["decoded_clipped"], dtype=float)
            row["activity_mean"] = float(np.mean(activity))
            row["activity_active_fraction"] = float(np.mean(activity > 1e-6))
            row["activity_rail_fraction"] = float(np.mean(activity >= 0.999))
            row["activity_temporal_std"] = float(np.mean(np.std(activity, axis=0)))
            row["decoder_rail_fraction"] = float(
                np.mean(np.any(np.abs(decoded) >= 0.999, axis=1))
            )
        rows.append(row)

    lookup = {(r["platform"], r["mission"], r["controller"]): r for r in rows}
    for row in rows:
        base = lookup[(row["platform"], row["mission"], "classical")]
        row["error_ratio_to_baseline"] = row["qerr_mean_rad"] / base["qerr_mean_rad"]
        row["improvement_percent"] = 100.0 * (
            1.0 - row["error_ratio_to_baseline"]
        )
    return rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def aggregate(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["platform"], row["controller"])].append(row)
    output = []
    for (platform, controller), values in grouped.items():
        values = sorted(values, key=lambda x: MISSIONS.index(x["mission"]))
        output.append(
            {
                "platform": platform,
                "controller": controller,
                "geomean_error_mrad": 1000.0
                * geometric_mean([v["qerr_mean_rad"] for v in values]),
                "geomean_error_ratio": geometric_mean(
                    [v["error_ratio_to_baseline"] for v in values]
                ),
                "geomean_improvement_percent": 100.0
                * (
                    1.0
                    - geometric_mean(
                        [v["error_ratio_to_baseline"] for v in values]
                    )
                ),
                "mean_residual_nrms": float(
                    np.mean([v["residual_nrms"] for v in values])
                ),
                "mean_activity_active_fraction": float(
                    np.mean([v["activity_active_fraction"] for v in values])
                ),
                "mean_activity_rail_fraction": float(
                    np.mean([v["activity_rail_fraction"] for v in values])
                ),
                "mean_activity_temporal_std": float(
                    np.mean([v["activity_temporal_std"] for v in values])
                ),
                "mean_decoder_rail_fraction": float(
                    np.mean([v["decoder_rail_fraction"] for v in values])
                ),
                "worst_mission_improvement_percent": float(
                    min(v["improvement_percent"] for v in values)
                ),
            }
        )
    return sorted(output, key=lambda x: (x["platform"], CONTROLLERS.index(x["controller"])))


def heatmap(rows):
    lookup = {(r["platform"], r["mission"], r["controller"]): r for r in rows}
    controllers = CONTROLLERS[1:]
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.7), constrained_layout=True)
    for ax, platform in zip(axes, ("x2", "cf2-rotor")):
        matrix = np.array(
            [
                [lookup[(platform, m, c)]["improvement_percent"] for m in MISSIONS]
                for c in controllers
            ]
        )
        vmax = max(25.0, float(np.nanpercentile(np.abs(matrix), 90)))
        im = ax.imshow(matrix, cmap="RdYlGn", vmin=-vmax, vmax=vmax, aspect="auto")
        ax.set_xticks(range(len(MISSIONS)), [m.capitalize() for m in MISSIONS], rotation=30, ha="right")
        ax.set_yticks(range(len(controllers)), [DISPLAY[c] for c in controllers])
        ax.set_title("Skydio X2" if platform == "x2" else "Crazyflie 2.0 (1.5x rotors)")
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix[i,j]:+.1f}%", ha="center", va="center", fontsize=8)
        fig.colorbar(im, ax=ax, shrink=0.8, label="tracking-error reduction")
    fig.savefig(OUT / "strict_improvement_heatmap.pdf", bbox_inches="tight")
    fig.savefig(OUT / "strict_improvement_heatmap.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def scatter(aggregates):
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.4), constrained_layout=True)
    colors = plt.cm.tab10(np.linspace(0, 1, len(CONTROLLERS) - 1))
    for ax, platform in zip(axes, ("x2", "cf2-rotor")):
        values = [a for a in aggregates if a["platform"] == platform and a["controller"] != "classical"]
        for color, item in zip(colors, values):
            ax.scatter(item["mean_residual_nrms"], item["geomean_improvement_percent"], s=65, color=color)
            ax.annotate(DISPLAY[item["controller"]], (item["mean_residual_nrms"], item["geomean_improvement_percent"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
        ax.axhline(0, color="0.35", lw=0.8)
        ax.set_xlabel("mean normalized residual RMS")
        ax.set_ylabel("five-mission geometric-mean improvement")
        ax.set_title("Skydio X2" if platform == "x2" else "Crazyflie 2.0 (1.5x rotors)")
        ax.grid(alpha=0.25)
    fig.savefig(OUT / "strict_error_effort.pdf", bbox_inches="tight")
    fig.savefig(OUT / "strict_error_effort.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fmt(value):
    return f"{value:.3f}"


def report(rows, aggregates):
    lookup = {(r["platform"], r["mission"], r["controller"]): r for r in rows}
    aggregate_lookup = {(a["platform"], a["controller"]): a for a in aggregates}
    lines = [
        "# Decisive neuron-family and non-neural basis result",
        "",
        "All rows use the final rho=3 PD+desired-rate-feedforward baseline, the same six signed channels, W0=[I3,-I3], PES target/update, beta, actuator limits, and saturation-opposition output gate. Only the activity basis changes.",
        "",
    ]
    for platform, platform_name in (("x2", "Skydio X2"), ("cf2-rotor", "Crazyflie 2.0, 1.5x rotors")):
        lines += [f"## {platform_name}", "", "| Basis | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean | Effort | Active | Rail |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for controller in CONTROLLERS:
            mission_values = [lookup[(platform, m, controller)] for m in MISSIONS]
            agg = aggregate_lookup[(platform, controller)]
            lines.append(
                "| " + DISPLAY[controller] + " | "
                + " | ".join(fmt(v["qerr_mean_mrad"]) for v in mission_values)
                + f" | {fmt(agg['geomean_error_mrad'])} | {fmt(agg['mean_residual_nrms'])} | {100*agg['mean_activity_active_fraction']:.1f}% | {100*agg['mean_decoder_rail_fraction']:.1f}% |"
            )
        lines += ["", "Improvements relative to the baseline (positive is better):", ""]
        for controller in CONTROLLERS[1:]:
            agg = aggregate_lookup[(platform, controller)]
            lines.append(
                f"- {DISPLAY[controller]}: {agg['geomean_improvement_percent']:+.2f}% geometric-mean; worst mission {agg['worst_mission_improvement_percent']:+.2f}%."
            )
        lines.append("")

    cmg = [aggregate_lookup[(p, "cmg")] for p in ("x2", "cf2-rotor")]
    constant = [aggregate_lookup[(p, "constant-one")] for p in ("x2", "cf2-rotor")]
    paired = [aggregate_lookup[(p, "paired-current")] for p in ("x2", "cf2-rotor")]
    lines += [
        "## Interpretation contract",
        "",
        "- If a conventional family improves after threshold-aware tuning, its original failure was an operating-point mismatch, not an impossibility result.",
        "- If the constant basis matches CMG, persistent PES features explain the result without neuron dynamics.",
        "- If the static paired basis matches CMG but the constant basis does not, input-dependent paired encoding matters while temporal neuron dynamics do not.",
        "- Only a consistent CMG advantage over both controls supports a dynamics-specific CMG claim.",
        "- These controls retain PES and the residual interface; they test the basis, not whether learning itself is needed.",
        "",
        "## Automatically computed comparison",
        "",
        f"CMG geometric-mean improvements: X2 {cmg[0]['geomean_improvement_percent']:+.2f}%, CF2 {cmg[1]['geomean_improvement_percent']:+.2f}%.",
        f"Constant-basis improvements: X2 {constant[0]['geomean_improvement_percent']:+.2f}%, CF2 {constant[1]['geomean_improvement_percent']:+.2f}%.",
        f"Static-paired improvements: X2 {paired[0]['geomean_improvement_percent']:+.2f}%, CF2 {paired[1]['geomean_improvement_percent']:+.2f}%.",
        "",
        "The scientific conclusion must be written after checking the full mission pattern and effort/rail metrics; a geometric mean alone is not sufficient.",
    ]
    (OUT / "STRICT_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    expected = 2 * len(MISSIONS) * len(CONTROLLERS)
    if len(rows) != expected:
        raise SystemExit(f"Expected {expected} summaries, found {len(rows)}")
    aggregates = aggregate(rows)
    write_csv(OUT / "strict_all_runs.csv", rows)
    write_csv(OUT / "strict_aggregate.csv", aggregates)
    heatmap(rows)
    scatter(aggregates)
    report(rows, aggregates)
    print(f"Compiled {len(rows)} runs into {OUT}")


if __name__ == "__main__":
    main()
