#!/usr/bin/env python3
"""Freeze the guarded R3 DeePC design-pilot protocol from accepted offline evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = json.loads((ROOT / "configs/rich_R3_deepc_uncertainty_replay.json").read_text())
if not source["pass"] or source["held_out_response_files_opened"]:
    raise SystemExit("accepted isolated offline replay is required")
result = {
    "status": "frozen_guarded_design_pilot",
    "source_artifact": "configs/rich_R3_deepc_uncertainty_replay.json",
    "sample_rate_hz": 35.0,
    "fallback_rate_hz": 10.0,
    "duration_s": 30.0,
    "disturbance": {"starts_s": [10.0, 12.0], "duration_s": 0.2, "signs": [1, -1], "amplitude": 0.00005},
    "limits": {"command": 0.0002, "slew_per_sample": 0.00005, "pitch_deg": 10.0, "roll_deg": 10.0, "body_rate_deg_s": 20.0},
    "pilot_gates": {
        "minimum_rows": 1040,
        "maximum_gap_s": 0.071428572,
        "minimum_rate_hz": 34.0,
        "maximum_rate_hz": 36.0,
        "maximum_runtime_ms": 28.571428571428573,
        "minimum_peak_abs_delta_p_deg_s": 0.0015,
        "maximum_final_5s_abs_delta_p_deg_s": 0.02,
        "minimum_sent_to_realized_lag1_correlation": 0.95,
        "maximum_restoration_error": 0.000001,
    },
    "offline_summary": source["summary"],
    "held_out_response_files_opened": [],
    "claim_boundary": "Frozen guarded design-pilot protocol only; no X-Plane control-performance claim.",
}
out = ROOT / "deepc/configs/rich_R3_deepc_pilot.json"
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
