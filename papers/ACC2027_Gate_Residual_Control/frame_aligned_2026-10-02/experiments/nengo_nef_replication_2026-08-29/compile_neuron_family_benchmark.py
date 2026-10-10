"""Compile neuron-family summaries and create paper/presentation figures."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
FAMILY_ORDER = ("cmg-fixed", "cmg-pes", "lif-fixed", "lif-pes", "alif-fixed", "alif-pes", "izhikevich-fixed", "izhikevich-pes", "lifrate-fixed", "lifrate-pes")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
COLORS = {"cmg": "#009E73", "lif": "#0072B2", "alif": "#E69F00", "izhikevich": "#CC79A7", "lifrate": "#56B4E9"}


def _heatmap(ax, matrix, title, colorbar_label, *, cmap="viridis", vmin=None, vmax=None, fmt=".2g"):
    image = ax.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(MISSIONS)), MISSIONS, rotation=20, ha="right")
    ax.set_yticks(range(len(FAMILY_ORDER)), FAMILY_ORDER)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]):
                ax.text(j, i, format(matrix[i, j], fmt), ha="center", va="center", fontsize=7)
    ax.set_title(title)
    ax.figure.colorbar(image, ax=ax, label=colorbar_label, shrink=0.86)
    return image


def label(controller: str):
    if controller == "nengo-nef-pes":
        return "cmg-pes"
    return controller.removeprefix("nengo-")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=HERE / "results" / "neuron_family_matched_45s")
    parser.add_argument("--output-root", type=Path, default=HERE / "results" / "neuron_family_compiled")
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    records = []
    summaries = {}
    for path in args.input_root.rglob("summary.json"):
        item = json.loads(path.read_text(encoding="utf-8"))
        summaries[(item["platform"], item["mission"], item["controller"])] = item
    for (platform, mission, controller), item in summaries.items():
        if controller == "classical":
            continue
        baseline = summaries.get((platform, mission, "classical"))
        if baseline is None:
            continue
        improvement = 100.0 * (baseline["qerr_mean_rad"] - item["qerr_mean_rad"]) / baseline["qerr_mean_rad"]
        record = {
            "platform": platform, "mission": mission, "controller": controller,
            "family_mode": label(controller),
            "baseline_qerr_mean_rad": baseline["qerr_mean_rad"],
            "qerr_mean_rad": item["qerr_mean_rad"],
            "qerr_max_rad": item["qerr_max_rad"],
            "improvement_pct": improvement,
            "residual_mean_Nm": item["residual_mean_Nm"],
            "tau_mean_Nm": item["tau_mean_Nm"],
            "saturation_fraction": item["saturation_fraction"],
            "z_std_m": item["z_std_m"],
            "torque_limit_norm_Nm": float(np.linalg.norm(item["torque_limits_Nm"])),
            "residual_mean_over_limit_norm": (
                item["residual_mean_Nm"] / float(np.linalg.norm(item["torque_limits_Nm"]))
            ),
            "improvement_per_mean_residual_pct_per_Nm": (
                improvement / item["residual_mean_Nm"] if item["residual_mean_Nm"] > 1e-12 else None
            ),
            "trace": item["trace"],
            "neural_trace": item.get("neural_trace_full_rate"),
        }
        neural_path = item.get("neural_trace_full_rate")
        if neural_path and Path(neural_path).exists():
            with np.load(neural_path, allow_pickle=False) as archive:
                activity = archive["activity"]
                weights = archive["weights"]
                updates = archive["weight_delta"]
                record.update({
                    "activity_mean": float(np.mean(activity)),
                    "activity_max": float(np.max(activity)),
                    "activity_occupancy_fraction": float(np.mean(np.abs(activity) > 1e-9)),
                    "decoder_drift_fro": float(np.linalg.norm(weights[-1] - weights[0])),
                    "decoder_final_fro": float(np.linalg.norm(weights[-1])),
                    "weight_update_rms": float(np.sqrt(np.mean(updates ** 2))),
                })
                if "residual_torque" in archive:
                    residual = archive["residual_torque"]
                    limits = np.asarray(item["torque_limits_Nm"], dtype=float)
                    normalized = residual / limits[None, :]
                    record["residual_utilization_rms"] = float(np.sqrt(np.mean(normalized ** 2)))
                    record["residual_utilization_peak"] = float(np.max(np.abs(normalized)))
                if "pes_error" in archive:
                    record["pes_error_rms"] = float(np.sqrt(np.mean(archive["pes_error"] ** 2)))
                if "decoded_raw" in archive and "decoded_clipped" in archive:
                    record["decoder_clip_fraction"] = float(
                        np.mean(np.abs(archive["decoded_raw"] - archive["decoded_clipped"]) > 1e-12)
                    )
                if "raw_output" in archive and any(name in controller for name in ("-lif-", "-alif-", "-izhikevich-")):
                    count = int(np.count_nonzero(archive["raw_output"] > 0))
                    record["spike_count"] = count
                    record["mean_spike_rate_hz_per_unit"] = count / (item["duration"] * 6)
        records.append(record)
    records.sort(key=lambda r: (r["platform"], MISSIONS.index(r["mission"]), FAMILY_ORDER.index(r["family_mode"])))
    csv_path = args.output_root / "neuron_family_results.csv"
    fieldnames = sorted({name for record in records for name in record})
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader(); writer.writerows(records)
    (args.output_root / "neuron_family_results.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")

    for platform in sorted({r["platform"] for r in records}):
        matrix = np.full((len(FAMILY_ORDER), len(MISSIONS)), np.nan)
        for r in records:
            if r["platform"] == platform:
                matrix[FAMILY_ORDER.index(r["family_mode"]), MISSIONS.index(r["mission"])] = r["improvement_pct"]
        fig, ax = plt.subplots(figsize=(11, 7), constrained_layout=True)
        image = ax.imshow(matrix, cmap="RdYlGn", vmin=-60, vmax=60, aspect="auto")
        ax.set_xticks(range(len(MISSIONS)), MISSIONS)
        ax.set_yticks(range(len(FAMILY_ORDER)), FAMILY_ORDER)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if np.isfinite(matrix[i, j]):
                    ax.text(j, i, f"{matrix[i,j]:+.1f}%", ha="center", va="center", fontsize=9)
        ax.set_title(f"Matched neuron-family change from quaternion PD — {platform}")
        ax.set_xlabel("mission"); ax.set_ylabel("natural observable + decoder mode")
        fig.colorbar(image, ax=ax, label="mean q-error improvement [%]")
        fig.savefig(args.output_root / f"{platform}_neuron_family_heatmap.png", dpi=240)
        fig.savefig(args.output_root / f"{platform}_neuron_family_heatmap.pdf")
        plt.close(fig)

        fig, axes = plt.subplots(1, len(MISSIONS), figsize=(17, 4.3), sharey=True, constrained_layout=True)
        families = ("cmg", "lif", "alif", "izhikevich", "lifrate")
        for ax, mission in zip(axes, MISSIONS):
            values = []
            for family in families:
                match = next(r for r in records if r["platform"] == platform and r["mission"] == mission and r["family_mode"] == f"{family}-pes")
                values.append(match["improvement_pct"])
            ax.bar(range(len(families)), values, color=[COLORS[f] for f in families])
            ax.axhline(0, color="black", lw=0.8)
            ax.set_xticks(range(len(families)), families, rotation=45, ha="right")
            ax.set_title(mission); ax.grid(axis="y", alpha=0.25)
        axes[0].set_ylabel("improvement over PD [%]")
        fig.suptitle(f"Online-PES neuron-family benchmark — {platform}")
        fig.savefig(args.output_root / f"{platform}_online_pes_bars.png", dpi=240)
        fig.savefig(args.output_root / f"{platform}_online_pes_bars.pdf")
        plt.close(fig)

        # Mechanism and fairness dashboard.  Every panel uses the exact same
        # family/mission ordering as the performance heatmap.
        metric_specs = (
            ("improvement_pct", "mean q-error improvement", "improvement [%]", "RdYlGn", -60, 60, "+.1f"),
            ("residual_utilization_rms", "normalized residual effort", "RMS residual / axis limits", "magma", 0, None, ".2f"),
            ("activity_occupancy_fraction", "neural feature occupancy", "fraction |activity| > 1e-9", "Blues", 0, 1, ".2f"),
            ("decoder_drift_fro", "decoder movement", r"$\|W_T-W_0\|_F$", "cividis", 0, None, ".2f"),
        )
        fig, axes = plt.subplots(2, 2, figsize=(18, 12), constrained_layout=True)
        for ax, (metric, title, cbar, cmap, vmin, vmax, fmt) in zip(axes.flat, metric_specs):
            values = np.full((len(FAMILY_ORDER), len(MISSIONS)), np.nan)
            for record in records:
                if record["platform"] == platform and metric in record:
                    values[FAMILY_ORDER.index(record["family_mode"]), MISSIONS.index(record["mission"])] = record[metric]
            _heatmap(ax, values, title, cbar, cmap=cmap, vmin=vmin, vmax=vmax, fmt=fmt)
        fig.suptitle(f"Matched Nengo benchmark: performance, effort, activation, and learning — {platform}", fontsize=16)
        fig.savefig(args.output_root / f"{platform}_mechanism_dashboard.png", dpi=240)
        fig.savefig(args.output_root / f"{platform}_mechanism_dashboard.pdf")
        plt.close(fig)

        # Effort/performance plane exposes cases that improve tracking only by
        # spending substantially more residual authority.
        fig, axes = plt.subplots(1, len(MISSIONS), figsize=(18, 4.5), sharey=True, constrained_layout=True)
        for ax, mission in zip(axes, MISSIONS):
            subset = [r for r in records if r["platform"] == platform and r["mission"] == mission]
            for record in subset:
                family, mode = record["family_mode"].rsplit("-", 1)
                x = record.get("residual_utilization_rms", np.nan)
                y = record["improvement_pct"]
                ax.scatter(x, y, s=55, marker="o" if mode == "pes" else "s", color=COLORS[family],
                           edgecolor="black", linewidth=0.4)
                ax.annotate(record["family_mode"], (x, y), xytext=(3, 3), textcoords="offset points", fontsize=6)
            ax.axhline(0, color="black", lw=0.8)
            ax.set_title(mission)
            ax.set_xlabel("normalized residual RMS")
            ax.grid(alpha=0.25)
        axes[0].set_ylabel("mean q-error improvement [%]")
        fig.suptitle(f"Accuracy–authority trade-off — {platform} (circle: PES; square: fixed)")
        fig.savefig(args.output_root / f"{platform}_accuracy_authority_tradeoff.png", dpi=240)
        fig.savefig(args.output_root / f"{platform}_accuracy_authority_tradeoff.pdf")
        plt.close(fig)
    print(json.dumps({"records": len(records), "csv": str(csv_path), "output": str(args.output_root)}, indent=2))


if __name__ == "__main__":
    main()
