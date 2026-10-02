#!/usr/bin/env python3
"""Check Stage-1 baseline completeness, timing, metadata, and command equations."""

import argparse
import csv
import math
from pathlib import Path


RICH_FIELDS = (
    "p_deg_s", "q_deg_s", "r_deg_s", "p_dot_deg_s2", "q_dot_deg_s2", "r_dot_deg_s2",
    "ias_kts", "tas_m_s", "alpha_deg", "beta_deg", "body_vx_m_s", "body_vy_m_s",
    "body_vz_m_s", "g_axial", "g_side", "g_normal", "total_pitch_ratio",
    "total_roll_ratio", "total_yaw_ratio", "throttle_engine_0", "throttle_engine_1",
    "autopilot_on", "autopilot_servos_on", "autothrottle_on", "dynamic_pressure_pa",
)
METADATA_FIELDS = ("test_id", "aircraft_config", "payload", "fuel", "weather", "failures")


def expected_output(feedback, setpoint, control, k, ku, tau):
    error = feedback - setpoint
    desired = -k * error
    control_error = control - desired
    derivative = -k * (control_error - desired)
    return control + tau * (derivative - error - ku * control_error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--hz", type=float, default=10.0)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--min-sample-fraction", type=float, default=0.99)
    parser.add_argument("--max-gap-periods", type=float, default=2.5)
    engagement = parser.add_mutually_exclusive_group()
    engagement.add_argument("--expect-engaged", action="store_true", default=True)
    engagement.add_argument("--expect-observe-only", action="store_true")
    args = parser.parse_args()

    with args.csv_file.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise SystemExit("FAIL: log has no data rows")

    missing_columns = sorted((set(RICH_FIELDS) | set(METADATA_FIELDS)) - set(rows[0]))
    missing_values = sum(any(row.get(field, "") == "" for field in RICH_FIELDS) for row in rows)
    times = [float(row["t_s"]) for row in rows]
    intervals = [b - a for a, b in zip(times, times[1:])]
    expected_samples = args.duration * args.hz
    sample_fraction = len(rows) / expected_samples
    max_gap = max(intervals, default=0.0)
    engaged_fraction = sum(row["engaged"].strip().lower() == "true" for row in rows) / len(rows)
    start_allowed_fraction = sum(row.get("start_allowed", "").strip().lower() == "true" for row in rows) / len(rows)
    start_block_reasons = sorted({row.get("start_block_reason", "").strip() for row in rows if row.get("start_block_reason", "").strip()})
    metadata_variants = {
        field: sorted({row[field].strip() for row in rows if field in row})
        for field in METADATA_FIELDS
    }
    placeholder_metadata = {
        field: values for field, values in metadata_variants.items()
        if not values or any(not value or "UNKNOWN" in value.upper() for value in values)
    }

    max_roll_error = max_pitch_error = 0.0
    for row in rows:
        roll_expected = expected_output(
            float(row["roll_deg"]), float(row["roll_sp_deg"]), float(row["ctrl_before_0"]),
            0.001, 33.0, 0.03,
        )
        pitch_expected = expected_output(
            float(row["pitch_deg"]), float(row["pitch_sp_deg"]), float(row["ctrl_before_1"]),
            0.001, 39.0, 0.03,
        )
        max_roll_error = max(max_roll_error, abs(roll_expected - float(row["raw_roll_output"])))
        max_pitch_error = max(max_pitch_error, abs(pitch_expected - float(row["raw_pitch_output"])))

    expected_engaged_fraction = 0.0 if args.expect_observe_only else 1.0
    checks = {
        "rich columns present": not missing_columns,
        "rich values complete": missing_values == 0,
        "sample fraction": sample_fraction >= args.min_sample_fraction,
        "maximum timing gap": max_gap <= args.max_gap_periods / args.hz,
        "single metadata value per field": all(len(values) == 1 for values in metadata_variants.values()),
        "no placeholder metadata": not placeholder_metadata,
        "engagement state": math.isclose(engaged_fraction, expected_engaged_fraction),
        "start gate": math.isclose(start_allowed_fraction, 1.0),
        "no engaged start block": args.expect_observe_only or not start_block_reasons,
        "original equations preserved": max(max_roll_error, max_pitch_error) <= 1e-12,
    }

    print(f"file={args.csv_file}")
    print(f"rows={len(rows)} sample_fraction={sample_fraction:.6f} engaged_fraction={engaged_fraction:.6f} start_allowed_fraction={start_allowed_fraction:.6f}")
    print(f"elapsed_s={times[-1]-times[0]:.9f} max_gap_s={max_gap:.9f}")
    print(f"max_roll_equation_error={max_roll_error:.12g} max_pitch_equation_error={max_pitch_error:.12g}")
    if missing_columns:
        print("missing_columns=" + ",".join(missing_columns))
    if placeholder_metadata:
        print("placeholder_metadata=" + ",".join(sorted(placeholder_metadata)))
    if start_block_reasons:
        print("start_block_reasons=" + " | ".join(start_block_reasons))
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
