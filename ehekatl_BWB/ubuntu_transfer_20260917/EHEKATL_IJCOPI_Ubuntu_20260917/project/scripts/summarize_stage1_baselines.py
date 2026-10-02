#!/usr/bin/env python3
"""Independently summarize and compare the three Stage-1 baseline CSV files."""

import argparse
import csv
from pathlib import Path
from statistics import fmean


FIELDS = (
    "alt_m", "ias_kts", "pitch_deg", "roll_deg", "p_deg_s", "q_deg_s",
    "r_deg_s", "vvi_m_s", "sent_ctrl_0", "sent_ctrl_1",
)


def read(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_files", nargs=3, type=Path)
    args = parser.parse_args()
    runs = [(path, read(path)) for path in args.csv_files]
    if any(len(rows) == 0 for _, rows in runs):
        raise SystemExit("FAIL: every baseline must contain rows")

    print("Stage-1 baseline comparison")
    print("============================")
    for path, rows in runs:
        times = [float(row["t_s"]) for row in rows]
        intervals = [b - a for a, b in zip(times, times[1:])]
        print(f"{path.name}: rows={len(rows)} elapsed_s={times[-1]-times[0]:.9f} max_gap_s={max(intervals):.9f}")
        print("  " + " ".join(
            f"{field}=[{min(float(row[field]) for row in rows):.6f},{max(float(row[field]) for row in rows):.6f}]"
            for field in FIELDS
        ))

    print("Cross-run mean ranges")
    for field in FIELDS:
        means = [fmean(float(row[field]) for row in rows) for _, rows in runs]
        print(f"  {field}: [{min(means):.9f},{max(means):.9f}] span={max(means)-min(means):.9f}")

    checks = {
        "three 600-row runs": all(len(rows) == 600 for _, rows in runs),
        "all engaged": all(all(row["engaged"].strip().lower() == "true" for row in rows) for _, rows in runs),
        "all start gates passed": all(all(row["start_allowed"].strip().lower() == "true" for row in rows) for _, rows in runs),
        "same metadata": all(len({row[field] for row in rows}) == 1 for _, rows in runs for field in ("aircraft_config", "payload", "fuel", "weather", "failures")),
        "no saturation": all(not any(row["ctrl_0_saturated"].strip().lower() == "true" or row["ctrl_1_saturated"].strip().lower() == "true" for row in rows) for _, rows in runs),
    }
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
