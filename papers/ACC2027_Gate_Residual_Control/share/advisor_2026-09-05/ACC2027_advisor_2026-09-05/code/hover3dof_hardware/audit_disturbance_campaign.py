"""Audit paired configuration, telemetry integrity, and labels of the emulated study."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
PAIR_FIELDS = (
    "io_mode", "armed", "mission", "duration", "reference_scale",
    "hardstep_transition_s", "allocation_policy", "motor_floor_volts",
    "disturbance", "disturbance_scale", "max_abs_pitch_deg", "max_abs_roll_deg",
)
TRACE_PAIR_FIELDS = (
    "t", "yaw_ref_deg", "pitch_ref_deg", "roll_ref_deg",
    "disturbance_yaw_Nm", "disturbance_pitch_Nm", "disturbance_roll_Nm",
)


def trace_columns(path: Path):
    values = {name: [] for name in TRACE_PAIR_FIELDS}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            for name in values:
                values[name].append(float(row[name]))
    return {name: np.asarray(item) for name, item in values.items()}


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=here / "results" / "disturbance_campaign_profiled_2026-08-31")
    parser.add_argument("--output", type=Path, default=here / "results" / "disturbance_compiled_profiled_2026-08-31" / "campaign_integrity_audit.json")
    args = parser.parse_args()
    summaries = []
    for path in args.root.rglob("summary.json"):
        item = json.loads(path.read_text(encoding="utf-8")); item["_path"] = str(path)
        summaries.append(item)
    failures = []
    pairs = []
    if len(summaries) != 10:
        failures.append(f"expected 10 summaries, found {len(summaries)}")
    for mission in MISSIONS:
        group = [s for s in summaries if s["config"]["mission"] == mission]
        by_controller = {s["config"]["controller"]: s for s in group}
        if set(by_controller) != {"pd", "nengo-pes"}:
            failures.append(f"controller pair missing for {mission}: {sorted(by_controller)}")
            continue
        pd = by_controller["pd"]; cmg = by_controller["nengo-pes"]
        mismatches = [name for name in PAIR_FIELDS if pd["config"].get(name) != cmg["config"].get(name)]
        if mismatches:
            failures.append(f"config mismatch {mission}: {mismatches}")
        pd_trace = trace_columns(Path(pd["trace"])); cmg_trace = trace_columns(Path(cmg["trace"]))
        common = min(len(pd_trace["t"]), len(cmg_trace["t"]))
        for name in TRACE_PAIR_FIELDS:
            if not np.allclose(pd_trace[name][:common], cmg_trace[name][:common], atol=1e-12, rtol=0):
                failures.append(f"paired reference/disturbance mismatch {mission}/{name}")
        if pd.get("neural_trace_2khz") is not None:
            failures.append(f"PD unexpectedly has neural archive: {mission}")
        archive_path = Path(cmg["neural_trace_2khz"])
        with np.load(archive_path, allow_pickle=False) as archive:
            expected = cmg["n_steps_logged"] * 10
            lengths = {archive[name].shape[0] for name in archive.files}
            if lengths != {expected}:
                failures.append(f"neural sample mismatch {mission}: {lengths}, expected {expected}")
            for name in archive.files:
                if not np.all(np.isfinite(archive[name])):
                    failures.append(f"nonfinite {mission}/{name}")
            if not np.allclose(np.diff(archive["t"]), 0.0005, atol=2e-12, rtol=0):
                failures.append(f"neural timing mismatch: {mission}")
        analysis = archive_path.parent / "analysis"
        for suffix in ("neural.png", "neural.pdf", "neural_equation_terms.png", "neural_equation_terms.pdf", "neural_statistics.json", "neural.csv"):
            if not (analysis / suffix).exists():
                failures.append(f"missing analysis {mission}/{suffix}")
        pairs.append({
            "mission": mission,
            "common_compared_steps": common,
            "pd_completed": pd["run_completed"],
            "cmg_completed": cmg["run_completed"],
            "pd_abort_reason": pd["abort_reason"],
            "cmg_abort_reason": cmg["abort_reason"],
            "emulation_realtime": cmg["config"]["emulation_realtime"],
        })
    payload = {
        "status": "passed" if not failures else "failed",
        "summaries": len(summaries),
        "pairs": pairs,
        "failures": failures,
        "timing_note": "emulation_realtime=false; deadline_miss_fraction is not hardware timing evidence",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
