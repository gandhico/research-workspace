"""Create a matched PD versus CMG-PES campaign comparison artifact."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


METRICS = ("position_RMSE_m", "attitude_RMSE_deg", "peak_position_error_m",
           "peak_attitude_error_deg", "max_abs_input_N", "saturation_fraction")


def load_campaign(path):
    path = Path(path).resolve()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    results = json.loads((path / "campaign.json").read_text(encoding="utf-8"))
    return path, manifest, {row["name"]: row for row in results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pd", type=Path)
    parser.add_argument("pes", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    pd_path, pd_manifest, pd = load_campaign(args.pd)
    pes_path, pes_manifest, pes = load_campaign(args.pes)
    if list(pd) != list(pes):
        raise ValueError("Campaign mission lists/order do not match")
    for key in ("model_xml_sha256", "mesh_sha256", "hover_py_sha256", "missions_py_sha256"):
        if pd_manifest.get(key) != pes_manifest.get(key):
            raise ValueError(f"Campaign provenance mismatch: {key}")

    output = args.output or pd_path.parent / datetime.now().strftime("comparison_pd_pes_%Y%m%d_%H%M%S")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name in pd:
        row = {"mission": name, "pd_status": pd[name]["status"], "pes_status": pes[name]["status"]}
        for metric in METRICS:
            row[f"pd_{metric}"] = pd[name].get(metric)
            row[f"pes_{metric}"] = pes[name].get(metric)
        row["peak_pes_residual_norm"] = pes[name].get("peak_pes_residual_norm", 0.)
        rows.append(row)
    with (output / "comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    aggregate = {
        "pd_campaign": str(pd_path), "pes_campaign": str(pes_path),
        "missions": len(rows),
        "pd_passed": sum(r["pd_status"] == "pass" for r in rows),
        "pes_passed": sum(r["pes_status"] == "pass" for r in rows),
    }
    for metric in METRICS:
        for mode in ("pd", "pes"):
            values = np.asarray([r[f"{mode}_{metric}"] for r in rows], dtype=float)
            aggregate[f"{mode}_mean_{metric}"] = float(np.mean(values))
            aggregate[f"{mode}_max_{metric}"] = float(np.max(values))
    (output / "comparison.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")

    x = np.arange(len(rows))
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True, constrained_layout=True)
    panels = (("position_RMSE_m", "Position RMSE [m]"),
              ("attitude_RMSE_deg", "Attitude RMSE [deg]"),
              ("max_abs_input_N", "Peak |rotor input| [N]"))
    for ax, (metric, ylabel) in zip(axes, panels):
        ax.plot(x, [r[f"pd_{metric}"] for r in rows], "o-", label="PD", linewidth=1)
        ax.plot(x, [r[f"pes_{metric}"] for r in rows], "s-", label="CMG-PES", linewidth=1)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=.3)
        ax.legend()
    axes[-1].set_xticks(x, [r["mission"] for r in rows], rotation=65, ha="right")
    fig.suptitle("Matched Omnicopter controller campaign")
    fig.savefig(output / "comparison.png", dpi=180)
    plt.close(fig)

    lines = ["# Matched PD and online-PES campaign", "",
             f"Both campaigns used the same model, mesh, mission script and {len(rows)} mission definitions.", "",
             f"- PD: {aggregate['pd_passed']}/{len(rows)} passed",
             f"- CMG-PES: {aggregate['pes_passed']}/{len(rows)} passed", "",
             "| Mission | PD pos RMSE m | PES pos RMSE m | PD att RMSE deg | PES att RMSE deg | PD peak N | PES peak N |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['mission']} | {r['pd_position_RMSE_m']:.6f} | {r['pes_position_RMSE_m']:.6f} | "
                     f"{r['pd_attitude_RMSE_deg']:.4f} | {r['pes_attitude_RMSE_deg']:.4f} | "
                     f"{r['pd_max_abs_input_N']:.3f} | {r['pes_max_abs_input_N']:.3f} |")
    lines += ["", "Passing establishes bounded stability/performance under these ideal-model gates; it does not establish that the learned residual outperforms PD or transfers safely to hardware."]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
