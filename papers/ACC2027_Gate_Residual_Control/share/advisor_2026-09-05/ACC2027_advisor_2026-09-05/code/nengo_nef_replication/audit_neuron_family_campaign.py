"""Audit completeness, numerical integrity, timing, and bounds of the full matrix."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
CONTROLLERS = (
    "classical", "nengo-cmg-fixed", "nengo-nef-pes",
    "nengo-lif-fixed", "nengo-lif-pes",
    "nengo-alif-fixed", "nengo-alif-pes",
    "nengo-izhikevich-fixed", "nengo-izhikevich-pes",
    "nengo-lifrate-fixed", "nengo-lifrate-pes",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    parser.add_argument("--root", type=Path, default=here / "results" / "neuron_family_matched_45s")
    parser.add_argument("--output", type=Path, default=here / "results" / "neuron_family_compiled" / "campaign_integrity_audit.json")
    args = parser.parse_args()
    failures = []
    checked_archives = 0
    checked_signals = 0
    for platform in PLATFORMS:
        for mission in MISSIONS:
            for controller in CONTROLLERS:
                directory = args.root / platform / mission / controller
                summary_path = directory / "summary.json"
                if not summary_path.exists():
                    failures.append(f"missing summary: {platform}/{mission}/{controller}")
                    continue
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                if summary.get("n_steps") != 90000:
                    failures.append(f"wrong n_steps: {platform}/{mission}/{controller}")
                if not Path(summary["trace"]).exists():
                    failures.append(f"missing trace: {platform}/{mission}/{controller}")
                if controller == "classical":
                    if summary.get("neural_trace_full_rate") is not None:
                        failures.append(f"classical has neural archive: {platform}/{mission}")
                    continue
                archive_path = Path(summary["neural_trace_full_rate"])
                schema_path = Path(summary["neural_trace_schema"])
                if not archive_path.exists() or not schema_path.exists():
                    failures.append(f"missing neural artifact: {platform}/{mission}/{controller}")
                    continue
                with np.load(archive_path, allow_pickle=False) as archive:
                    checked_archives += 1
                    lengths = {archive[name].shape[0] for name in archive.files}
                    checked_signals += len(archive.files)
                    if lengths != {90000}:
                        failures.append(f"sample-length mismatch {lengths}: {platform}/{mission}/{controller}")
                    for name in archive.files:
                        if not np.all(np.isfinite(archive[name])):
                            failures.append(f"nonfinite {name}: {platform}/{mission}/{controller}")
                    t = archive["t"]
                    if not np.allclose(np.diff(t), 0.0005, atol=2e-12, rtol=0):
                        failures.append(f"timing mismatch: {platform}/{mission}/{controller}")
                    if archive["weights"].shape != (90000, 3, 6):
                        failures.append(f"weight shape: {platform}/{mission}/{controller}")
                    if controller.endswith("-fixed"):
                        drift = np.linalg.norm(archive["weights"][-1] - archive["weights"][0])
                        if drift > 1e-12:
                            failures.append(f"fixed decoder drift {drift}: {platform}/{mission}/{controller}")
                    if np.max(np.abs(archive["decoded_clipped"])) > 1.0 + 1e-12:
                        failures.append(f"decoded clip violation: {platform}/{mission}/{controller}")
                    limits = np.asarray(summary["torque_limits_Nm"], dtype=float)
                    residual_ratio = np.abs(archive["residual_torque"]) / limits[None, :]
                    if np.max(residual_ratio) > summary["beta"] + 1e-9:
                        failures.append(f"residual authority violation: {platform}/{mission}/{controller}")
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                if abs(schema.get("sample_rate_hz", 0) - 2000.0) > 1e-9:
                    failures.append(f"schema rate: {platform}/{mission}/{controller}")
                prefix = directory / "analysis" / "family_diagnostics"
                if not prefix.with_suffix(".png").exists() or not prefix.with_suffix(".pdf").exists():
                    failures.append(f"missing diagnostic figure: {platform}/{mission}/{controller}")
    payload = {
        "status": "passed" if not failures else "failed",
        "expected_cells": len(PLATFORMS) * len(MISSIONS) * len(CONTROLLERS),
        "checked_archives": checked_archives,
        "checked_signals": checked_signals,
        "failures": failures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
