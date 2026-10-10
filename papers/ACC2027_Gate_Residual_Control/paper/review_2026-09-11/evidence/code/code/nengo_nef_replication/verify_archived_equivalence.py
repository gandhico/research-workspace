"""Compare Nengo results with the archived direct CMG/PES summaries."""
from __future__ import annotations

import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW = HERE / "results" / "matched_45s"
OUT = HERE / "results" / "compiled" / "archived_equivalence.csv"


def main():
    rows = []
    for platform, prefix in (("cf2-rotor", "cf2"), ("x2", "x2")):
        for mission in ("roll", "full3", "hard45", "hardstep", "yaw360"):
            old_name = f"{prefix}_cmg" if mission == "hard45" else f"{prefix}_{mission}_cmg"
            new_name = f"{platform}_{mission}_nengo-nef-pes".replace("-", "_")
            old = json.loads(
                (REPO / "results" / "plots_data" / old_name / "summary.json").read_text()
            )
            new = json.loads((NEW / new_name / "summary.json").read_text())
            difference = abs(old["qerr_mean_rad"] - new["qerr_mean_rad"])
            ppm = 1e6 * difference / abs(old["qerr_mean_rad"])
            rows.append(
                {
                    "platform": platform,
                    "mission": mission,
                    "archived_direct_mean_rad": old["qerr_mean_rad"],
                    "nengo_mean_rad": new["qerr_mean_rad"],
                    "absolute_difference_rad": difference,
                    "relative_difference_ppm": ppm,
                }
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    worst = max(row["relative_difference_ppm"] for row in rows)
    print(OUT)
    print(f"worst relative difference: {worst:.6f} ppm")
    if worst >= 3.0:
        raise SystemExit("equivalence threshold exceeded")


if __name__ == "__main__":
    main()
