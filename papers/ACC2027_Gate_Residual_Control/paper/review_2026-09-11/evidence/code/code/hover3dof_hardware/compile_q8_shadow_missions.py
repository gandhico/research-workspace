"""Compile connected-Q8 zero-output Nengo mission diagnostics (not performance)."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ORDER = ("roll", "full3", "hard45", "hardstep", "yaw360")


def read_columns(path: Path, names: tuple[str, ...]):
    values = {name: [] for name in names}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            for name in names:
                values[name].append(float(row[name]))
    return {name: np.asarray(item) for name, item in values.items()}


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=here / "results" / "hardware_q8_shadow_missions_2026-08-31")
    parser.add_argument("--output-root", type=Path, default=here / "results" / "hardware_q8_shadow_compiled_2026-08-31")
    args = parser.parse_args(); args.output_root.mkdir(parents=True, exist_ok=True)
    records = []
    columns = (
        "Vf_computed", "Vb_computed", "Vl_computed", "Vr_computed",
        "Vf_dac_written", "Vb_dac_written", "Vl_dac_written", "Vr_dac_written",
        "raw_encoder_count_yaw", "raw_encoder_count_pitch", "raw_encoder_count_roll",
    )
    for summary_path in args.input_root.rglob("summary.json"):
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        trace = read_columns(Path(summary["trace"]), columns)
        computed = np.column_stack([trace[name] for name in columns[:4]])
        dac = np.column_stack([trace[name] for name in columns[4:8]])
        encoders = np.column_stack([trace[name] for name in columns[8:]])
        archive_path = Path(summary["neural_trace_2khz"])
        with np.load(archive_path, allow_pickle=False) as archive:
            activity = archive["activity"]
            gate = archive["gate"]
            weights = archive["weights"]
            residual = archive["residual_torque_ypr"]
            pes_error = archive["pes_error"]
            finite = all(np.all(np.isfinite(archive[name])) for name in archive.files)
            record = {
                "mission": summary["config"]["mission"],
                "duration_s": summary["config"]["duration"],
                "run_completed": summary["run_completed"],
                "abort_reason": summary["abort_reason"],
                "hardware_rows": summary["n_steps_logged"],
                "neural_samples": int(archive["t"].shape[0]),
                "neural_signals": len(archive.files),
                "all_neural_finite": finite,
                "deadline_miss_fraction": summary["deadline_miss_fraction"],
                "max_computed_motor_V": float(np.max(computed)),
                "computed_motor_limit_fraction": float(np.mean((computed <= 1e-12) | (computed >= 24.0 - 1e-12))),
                "max_abs_dac_written_V": float(np.max(np.abs(dac))),
                "encoder_yaw_span_counts": float(np.ptp(encoders[:, 0])),
                "encoder_pitch_span_counts": float(np.ptp(encoders[:, 1])),
                "encoder_roll_span_counts": float(np.ptp(encoders[:, 2])),
                "activity_mean": float(np.mean(activity)),
                "activity_max": float(np.max(activity)),
                "gate_mean": float(np.mean(gate)),
                "gate_max": float(np.max(gate)),
                "decoder_drift_fro": float(np.linalg.norm(weights[-1] - weights[0])),
                "pes_error_rms": float(np.sqrt(np.mean(pes_error ** 2))),
                "residual_torque_rms_Nm": float(np.sqrt(np.mean(residual ** 2))),
                "trace": summary["trace"],
                "neural_trace": str(archive_path),
            }
        if record["max_abs_dac_written_V"] != 0.0:
            raise RuntimeError(f"nonzero physical output in shadow run: {summary_path}")
        if record["neural_samples"] != 10 * record["hardware_rows"]:
            raise RuntimeError(f"sample-rate mismatch: {summary_path}")
        records.append(record)
    records.sort(key=lambda item: ORDER.index(item["mission"]))
    if [item["mission"] for item in records] != list(ORDER):
        raise RuntimeError("expected one complete shadow run for each nontrivial mission")
    fields = list(records[0])
    with (args.output_root / "q8_shadow_mission_diagnostics.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(records)
    (args.output_root / "q8_shadow_mission_diagnostics.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")

    x = np.arange(len(records)); labels = [item["mission"] for item in records]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    axes[0, 0].bar(x, [r["max_computed_motor_V"] for r in records], color="#0072B2", label="computed only")
    axes[0, 0].bar(x, [r["max_abs_dac_written_V"] for r in records], color="#D55E00", label="physical DAC")
    axes[0, 0].axhline(24, color="black", ls="--", lw=0.8); axes[0, 0].set_ylabel("voltage [V]")
    axes[0, 0].set_title("Computed controller voltage vs physical zero output"); axes[0, 0].legend()
    axes[0, 1].bar(x - 0.18, [r["gate_mean"] for r in records], width=0.36, label="mean gate")
    axes[0, 1].bar(x + 0.18, [r["gate_max"] for r in records], width=0.36, label="max gate")
    axes[0, 1].set_title("CMG gate activation"); axes[0, 1].legend()
    axes[1, 0].bar(x, [r["decoder_drift_fro"] for r in records], color="#009E73")
    axes[1, 0].set_title(r"Online decoder movement $\|W_T-W_0\|_F$")
    axes[1, 1].bar(x, [100*r["deadline_miss_fraction"] for r in records], color="#CC79A7")
    axes[1, 1].set_ylabel("deadline misses [%]"); axes[1, 1].set_title("200-Hz computation timing")
    for ax in axes.flat:
        ax.set_xticks(x, labels, rotation=20, ha="right"); ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Connected Q8 Nengo shadow missions — all physical DAC commands exactly zero")
    fig.savefig(args.output_root / "q8_shadow_mission_diagnostics.png", dpi=240)
    fig.savefig(args.output_root / "q8_shadow_mission_diagnostics.pdf")
    plt.close(fig)
    print(json.dumps({"status": "passed", "missions": len(records), "output": str(args.output_root)}, indent=2))


if __name__ == "__main__":
    main()
