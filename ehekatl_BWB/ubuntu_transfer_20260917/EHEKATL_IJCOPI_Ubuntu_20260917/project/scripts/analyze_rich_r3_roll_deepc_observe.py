#!/usr/bin/env python3
"""Audit R3 DeePC observe-only timing, history, runtime, safety, and replay."""

import argparse
import csv
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from deepc.src.r3_roll_runtime import R3RollDeePCRuntime
from run_rich_r3_roll_dualrate_xp12 import start_reasons


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    with args.csv.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) < 2:
        raise SystemExit("log has fewer than two samples")

    t = np.array([float(row["t_s"]) for row in rows])
    dt = np.diff(t)
    commands = np.array([float(row["deepc_command"]) for row in rows])
    runtimes = np.array([float(row["runtime_ms"]) for row in rows])
    runtime = R3RollDeePCRuntime()
    maximum_replay_error = 0.0
    maximum_history_error = 0.0
    for row in rows:
        pre_u = np.array([float(row[f"pre_u_history_{i}"]) for i in range(5)])
        pre_p = np.array([float(row[f"pre_p_history_{i}"]) for i in range(5)])
        maximum_history_error = max(
            maximum_history_error,
            float(np.max(np.abs(pre_u - runtime.u_history))),
            float(np.max(np.abs(pre_p - runtime.p_history))),
        )
        expected = runtime.update(float(row["p_error_deg_s"]))
        maximum_replay_error = max(maximum_replay_error, abs(expected["command"] - float(row["deepc_command"])))
        post_u = np.array([float(row[f"post_u_history_{i}"]) for i in range(5)])
        post_p = np.array([float(row[f"post_p_history_{i}"]) for i in range(5)])
        maximum_history_error = max(
            maximum_history_error,
            float(np.max(np.abs(post_u - runtime.u_history))),
            float(np.max(np.abs(post_p - runtime.p_history))),
        )

    first = {key: float(rows[0][key]) for key in (
        "altitude_m", "ias_kts", "pitch_deg", "roll_deg", "p_deg_s", "q_deg_s", "r_deg_s",
        "art_stab_on", "override_roll", "override_pitch", "paused", "sim_speed", "replay",
    )}
    reasons = start_reasons(first)
    checks = {
        "completeness": len(rows) >= 1040,
        "maximum_gap": float(dt.max()) <= 0.071428572,
        "mean_rate": 34.0 <= 1.0 / float(dt.mean()) <= 36.0,
        "start_gate": not reasons,
        "observe_only": all(row["engaged"] == "0" and row["controls_sent"] == "0" and row["ownership_requested"] == "0" for row in rows),
        "ownership_clear": all(float(row["override_roll"]) == 0 and float(row["override_pitch"]) == 0 for row in rows),
        "live_state": all(float(row["paused"]) == 0 and float(row["sim_speed"]) == 1 and float(row["replay"]) == 0 for row in rows),
        "safety": all(abs(float(row["pitch_deg"])) <= 10 and abs(float(row["roll_deg"])) <= 10 and max(abs(float(row[key])) for key in ("p_deg_s", "q_deg_s", "r_deg_s")) <= 20 for row in rows),
        "no_safety_latch": all(row["safety_latched"] == "0" and not row["safety_reason"] for row in rows),
        "optimizer_convergence": all(row["deepc_converged"] == "1" and row["deepc_fallback_required"] == "0" and not row["deepc_fallback_reason"] for row in rows),
        "command_bound": float(np.max(np.abs(commands))) <= 0.0002 + 1e-15,
        "slew_bound": float(np.max(np.abs(np.diff(commands)))) <= 0.00005 + 1e-15,
        "runtime_deadline": float(runtimes.max()) < 1000.0 / 35.0,
        "exact_runtime_replay": maximum_replay_error <= 1e-15,
        "exact_history": maximum_history_error <= 1e-15,
        "finite": all(math.isfinite(float(row[key])) for row in rows for key in ("runtime_ms", "deepc_command", "p_error_deg_s")),
    }
    checks = {key: bool(value) for key, value in checks.items()}
    result = {
        "file": str(args.csv),
        "rows": len(rows),
        "effective_hz": 1.0 / float(dt.mean()),
        "maximum_gap_s": float(dt.max()),
        "runtime_ms_median": float(np.median(runtimes)),
        "runtime_ms_p95": float(np.percentile(runtimes, 95)),
        "runtime_ms_max": float(runtimes.max()),
        "peak_abs_command": float(np.max(np.abs(commands))),
        "maximum_slew": float(np.max(np.abs(np.diff(commands)))),
        "maximum_runtime_replay_error": maximum_replay_error,
        "maximum_history_error": maximum_history_error,
        "start_gate_reasons": reasons,
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": "Observe-only integration evidence; no controls sent and no X-Plane performance claim.",
    }
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
