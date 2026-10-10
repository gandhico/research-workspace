"""Compile matched Hover disturbance runs and create presentation figures."""
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
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
EVENTS = ((4.0, 0.25), (9.0, 0.25), (14.0, 0.25), (19.0, 0.35))


def load_trace(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return {name: np.asarray([float(row[name]) for row in rows]) for name in rows[0]}


def recovery_metrics(t, error_deg, start, width):
    before = (t >= max(0, start - 0.5)) & (t < start)
    window = (t >= start) & (t <= start + 3.0)
    threshold = (float(np.median(error_deg[before])) if np.any(before) else 0.0) + 2.0
    indices = np.flatnonzero((t >= start + width) & (t <= start + 3.0))
    recovery = None
    for index in indices:
        if index + 10 <= len(t) and np.all(error_deg[index:index + 10] <= threshold):
            recovery = float(t[index] - (start + width))
            break
    return {
        "peak_qerr_deg_3s": float(np.max(error_deg[window])) if np.any(window) else None,
        "recovery_threshold_deg": threshold,
        "recovery_time_s": recovery,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=HERE / "results" / "disturbance_campaign_2026-08-31")
    parser.add_argument("--output-root", type=Path, default=HERE / "results" / "disturbance_compiled_2026-08-31")
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    runs = {}
    for path in args.input_root.rglob("summary.json"):
        summary = json.loads(path.read_text(encoding="utf-8"))
        config = summary["config"]
        if config.get("disturbance") != "hard-pulses" or config.get("io_mode") != "emulated":
            continue
        key = (config["mission"], config["controller"])
        if key not in runs or path.stat().st_mtime > runs[key][0].stat().st_mtime:
            runs[key] = (path, summary)
    records = []
    for mission in MISSIONS:
        if (mission, "pd") not in runs or (mission, "nengo-pes") not in runs:
            continue
        traces = {}
        for controller in ("pd", "nengo-pes"):
            _, summary = runs[(mission, controller)]
            trace = load_trace(Path(summary["trace"]))
            traces[controller] = trace
            qerr_deg = np.rad2deg(trace["qerr_rad"])
            record = {
                "mission": mission,
                "controller": controller,
                "completed": summary["run_completed"],
                "abort_reason": summary["abort_reason"],
                "qerr_mean_deg": float(np.mean(qerr_deg)),
                "qerr_peak_deg": float(np.max(qerr_deg)),
                "qerr_iae_deg_s": float(np.trapezoid(qerr_deg, trace["t"])),
                "deadline_miss_fraction": summary["deadline_miss_fraction"],
                "disturbance_scale": summary["config"]["disturbance_scale"],
                "trace": summary["trace"],
                "neural_trace": summary.get("neural_trace_2khz"),
            }
            for event_index, (start, width) in enumerate(EVENTS, 1):
                result = recovery_metrics(trace["t"], qerr_deg, start, width)
                for name, value in result.items():
                    record[f"pulse{event_index}_{name}"] = value
            records.append(record)

        baseline = next(r for r in records if r["mission"] == mission and r["controller"] == "pd")
        neural = next(r for r in records if r["mission"] == mission and r["controller"] == "nengo-pes")
        neural["mean_improvement_pct"] = 100 * (baseline["qerr_mean_deg"] - neural["qerr_mean_deg"]) / baseline["qerr_mean_deg"]
        neural["iae_improvement_pct"] = 100 * (baseline["qerr_iae_deg_s"] - neural["qerr_iae_deg_s"]) / baseline["qerr_iae_deg_s"]

        fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True, constrained_layout=True)
        fields = (("yaw_deg", "yaw_ref_deg", "yaw [deg]"), ("pitch_deg", "pitch_ref_deg", "pitch [deg]"), ("roll_deg", "roll_ref_deg", "roll [deg]"))
        for ax, (measured, reference, ylabel) in zip(axes[:3], fields):
            for controller, color, label in (("pd", "#0072B2", "PD"), ("nengo-pes", "#009E73", "PD + CMG-PES")):
                ax.plot(traces[controller]["t"], traces[controller][measured], color=color, lw=1.1, label=label)
            ax.plot(traces["pd"]["t"], traces["pd"][reference], color="black", ls="--", lw=0.9, label="reference")
            ax.set_ylabel(ylabel); ax.grid(True, alpha=0.25)
        for controller, color, label in (("pd", "#0072B2", "PD"), ("nengo-pes", "#009E73", "PD + CMG-PES")):
            axes[3].plot(traces[controller]["t"], np.rad2deg(traces[controller]["qerr_rad"]), color=color, lw=1.2, label=label)
        axes[3].set_ylabel("q-error [deg]"); axes[3].set_xlabel("time [s]"); axes[3].grid(True, alpha=0.25)
        for ax in axes:
            for start, width in EVENTS:
                ax.axvspan(start, start + width, color="#D55E00", alpha=0.15)
            ax.legend(loc="best", fontsize=8, ncol=3)
        completion = "complete pair" if baseline["completed"] and neural["completed"] else "partial / safety-aborted pair"
        fig.suptitle(
            f"3DOF Hover hard-pulse rejection — {mission} | "
            f"mean q-error {baseline['qerr_mean_deg']:.2f}° → {neural['qerr_mean_deg']:.2f}° "
            f"({neural['mean_improvement_pct']:+.2f}%), {completion}"
        )
        fig.savefig(args.output_root / f"hover_{mission}_hard_pulses.png", dpi=240)
        fig.savefig(args.output_root / f"hover_{mission}_hard_pulses.pdf")
        plt.close(fig)

    if not records:
        raise SystemExit("no complete matched run pairs found")
    fieldnames = sorted({name for record in records for name in record})
    with (args.output_root / "hover_disturbance_results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader(); writer.writerows(records)
    (args.output_root / "hover_disturbance_results.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "output": str(args.output_root)}, indent=2))


if __name__ == "__main__":
    main()
