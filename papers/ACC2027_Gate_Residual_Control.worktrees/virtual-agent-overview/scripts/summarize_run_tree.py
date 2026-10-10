from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path, help="Run directory containing summary.json files")
    args = ap.parse_args()
    summaries = []
    for path in sorted(args.root.rglob("summary.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        row["relative_path"] = str(path.parent.relative_to(args.root))
        summaries.append(row)
    if not summaries:
        raise SystemExit(f"No summary.json files found under {args.root}")
    keys = sorted({key for row in summaries for key in row if key != "trace"})
    output = args.root/"aggregate.csv"
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys, extrasaction="ignore")
        writer.writeheader(); writer.writerows(summaries)
    print(output)


if __name__ == "__main__":
    main()

