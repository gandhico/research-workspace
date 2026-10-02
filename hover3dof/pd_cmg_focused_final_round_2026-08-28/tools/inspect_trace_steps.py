"""Report largest single-sample angle changes without auto-excluding a run."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()
    for run_dir in args.run_dirs:
        with (run_dir / "trace.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        angles = np.array([[float(row[f"{axis}_deg"]) for axis in ("yaw", "pitch", "roll")] for row in rows])
        delta = np.abs(np.diff(angles, axis=0))
        flat_order = np.argsort(delta.ravel())[::-1][:args.top]
        events = []
        for flat in flat_order:
            sample, axis = np.unravel_index(flat, delta.shape)
            events.append({
                "t": float(rows[sample + 1]["t"]),
                "axis": ("yaw", "pitch", "roll")[axis],
                "absolute_step_deg": float(delta[sample, axis]),
            })
        print(json.dumps({
            "run": run_dir.name,
            "max_by_axis_deg_per_sample": dict(zip(("yaw", "pitch", "roll"), np.max(delta, axis=0).tolist())),
            "top_events": events,
        }, indent=2))


if __name__ == "__main__":
    main()

