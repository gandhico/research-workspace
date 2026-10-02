"""Verify that every connected Q8 neuron-family shadow run wrote zero output."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\q8_neuron_family_shadow_2026-09-01")
EXPECTED = {
    "pd", "nengo-cmg-fixed", "nengo-nef-pes",
    "nengo-lif-fixed", "nengo-lif-pes",
    "nengo-alif-fixed", "nengo-alif-pes",
    "nengo-izhikevich-fixed", "nengo-izhikevich-pes",
    "nengo-lifrate-fixed", "nengo-lifrate-pes",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest().upper()


def main() -> None:
    records = []
    failures = []
    files = []
    for summary_path in sorted(ROOT.glob("*/summary.json")):
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        controller = summary["config"]["controller"]
        with (summary_path.parent / "trace.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        output_columns = [
            f"{channel}_{suffix}"
            for channel in ("Vf", "Vb", "Vl", "Vr")
            for suffix in ("written", "dac_written")
        ]
        max_abs_output = max(abs(float(row[column])) for row in rows for column in output_columns)
        archive = summary_path.parent / "neural_trace_2khz.npz"
        neural_samples = 0
        if controller != "pd":
            if not archive.exists():
                failures.append(f"{controller}: missing neural archive")
            else:
                with np.load(archive, allow_pickle=False) as loaded:
                    neural_samples = len(loaded["t"])
                    if neural_samples != 10 * summary["n_steps_logged"]:
                        failures.append(f"{controller}: neural sample mismatch")
                    if not all(np.isfinite(loaded[name]).all() for name in loaded.files):
                        failures.append(f"{controller}: nonfinite neural data")
        checks = {
            "hardware_q8": bool(summary["hardware"]),
            "armed_false": not summary["config"]["armed"],
            "completed": bool(summary["run_completed"]),
            "zero_written_output": max_abs_output == 0.0,
        }
        if not all(checks.values()):
            failures.append(f"{controller}: failed checks {checks}")
        records.append({
            "controller": controller,
            "checks": checks,
            "max_abs_written_or_dac_output": max_abs_output,
            "hardware_samples": summary["n_steps_logged"],
            "neural_samples": neural_samples,
            "raw_home_ypr_deg": summary["raw_home_ypr_deg"],
            "run_directory": str(summary_path.parent),
        })
        files.extend(path for path in summary_path.parent.iterdir() if path.is_file())
    found = {record["controller"] for record in records}
    if found != EXPECTED:
        failures.append(f"controller set mismatch: found={sorted(found)}")
    payload = {
        "status": "passed" if not failures else "failed",
        "scope": "connected Q8 sensor/telemetry shadow; never a motor-driving experiment",
        "expected_controllers": sorted(EXPECTED),
        "found_controllers": sorted(found),
        "all_four_dac_channels_zero_every_sample": all(
            record["max_abs_written_or_dac_output"] == 0.0 for record in records
        ),
        "failures": failures,
        "runs": records,
    }
    audit_path = ROOT / "SHADOW_AUDIT.json"
    audit_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema": 1,
        "files": [
            {"path": str(path), "size": path.stat().st_size, "sha256": digest(path)}
            for path in sorted(set(files + [audit_path]))
        ],
    }
    (ROOT / "FROZEN_SHA256_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
