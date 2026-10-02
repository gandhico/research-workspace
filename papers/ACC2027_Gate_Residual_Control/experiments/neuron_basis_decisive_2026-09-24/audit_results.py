"""Audit completeness, telemetry length, and recorded output hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
EXPECTED = {
    "strict_exact": 80,
    "development": 64,
    "development_baseline": 2,
    "selected_confirm": 8,
    "selected_validate": 32,
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    failures = []
    records = []
    for group, expected in EXPECTED.items():
        summaries = sorted((RESULTS / group).rglob("summary.json"))
        if len(summaries) != expected:
            failures.append(f"{group}: expected {expected} summaries, found {len(summaries)}")
        for summary_path in summaries:
            directory = summary_path.parent
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            manifest_path = directory / "manifest.json"
            trace_path = directory / "trace.csv"
            if not manifest_path.exists() or not trace_path.exists():
                failures.append(f"{directory}: missing manifest or trace")
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if summary.get("run_id") != manifest.get("run_id"):
                failures.append(f"{directory}: run_id mismatch")
            if summary.get("configuration_sha256") != manifest.get("configuration_sha256"):
                failures.append(f"{directory}: configuration hash mismatch")
            for filename, recorded in manifest.get("output_sha256", {}).items():
                path = directory / filename
                if not path.exists() or sha256(path) != recorded:
                    failures.append(f"{directory}: output hash mismatch for {filename}")
            residual = summary["controller"] != "classical"
            archive_path = directory / "neural_trace_full_rate.npz"
            schema_path = directory / "neural_trace_schema.json"
            if residual and (not archive_path.exists() or not schema_path.exists()):
                failures.append(f"{directory}: residual run missing neural archive/schema")
            if archive_path.exists():
                with np.load(archive_path) as archive:
                    n = int(archive["t"].shape[0])
                    required = {
                        "activity", "weights", "decoded_clipped", "pes_error",
                        "raw_residual_torque", "output_gate_mask", "tau_realized",
                        "rotor_saturation_mask",
                    }
                    missing = required - set(archive.files)
                if missing:
                    failures.append(f"{directory}: missing neural signals {sorted(missing)}")
                if n != summary["n_steps"]:
                    failures.append(f"{directory}: archive samples {n} != n_steps {summary['n_steps']}")
            records.append({
                "group": group,
                "controller": summary["controller"],
                "platform": summary["platform"],
                "mission": summary["mission"],
                "run_id": summary["run_id"],
                "n_steps": summary["n_steps"],
                "has_full_rate_neural_archive": archive_path.exists(),
            })
    report = {
        "status": "PASS" if not failures else "FAIL",
        "expected_runs": sum(EXPECTED.values()),
        "audited_runs": len(records),
        "groups": EXPECTED,
        "failures": failures,
        "full_rate_neural_archives": sum(r["has_full_rate_neural_archive"] for r in records),
    }
    output = HERE / "analysis" / "AUDIT_RESULTS.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
