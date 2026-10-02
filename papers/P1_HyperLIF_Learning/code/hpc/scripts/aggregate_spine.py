"""Cross-dataset aggregation: combine all results/<mode>_<dataset>/ranking.csv into one view.

Builds a config x dataset accuracy matrix + a cross-dataset mean accuracy and mean rank
(the 'cross-dataset consistency' criterion from the triage decision rule). Writes
results/spine_summary.md and prints the table.

    python scripts/aggregate_spine.py --mode tiny
"""

from __future__ import annotations

import argparse
import csv
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="tiny")
    args = ap.parse_args()
    results = ROOT / "results"

    datasets = {}
    for d in sorted(results.glob(f"{args.mode}_*")):
        rk = d / "ranking.csv"
        if not rk.exists():
            continue
        name = d.name[len(args.mode) + 1:]
        with open(rk, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        datasets[name] = {r["config"]: float(r["acc_mean"]) for r in rows}
        # per-dataset rank (1 = best)
        order = sorted(rows, key=lambda r: float(r["acc_mean"]), reverse=True)
        datasets[name + "__rank"] = {r["config"]: i + 1 for i, r in enumerate(order)}

    ds_names = [k for k in datasets if not k.endswith("__rank")]
    if not ds_names:
        print(f"no {args.mode}_* ranking.csv found yet")
        return
    configs = sorted(set().union(*[set(datasets[n]) for n in ds_names]))

    table = []
    for c in configs:
        accs = [datasets[n].get(c) for n in ds_names if datasets[n].get(c) is not None]
        ranks = [datasets[n + "__rank"].get(c) for n in ds_names if datasets[n + "__rank"].get(c) is not None]
        table.append({
            "config": c,
            **{n: datasets[n].get(c) for n in ds_names},
            "mean_acc": st.mean(accs) if accs else 0.0,
            "mean_rank": st.mean(ranks) if ranks else 99,
        })
    table.sort(key=lambda r: r["mean_acc"], reverse=True)

    # print
    hdr = f"{'config':26s} " + " ".join(f"{n:>10s}" for n in ds_names) + f" {'mean':>7s} {'mrank':>6s}"
    print(hdr)
    for r in table:
        cells = " ".join(f"{(r[n] if r[n] is not None else float('nan')):10.3f}" for n in ds_names)
        print(f"{r['config']:26s} {cells} {r['mean_acc']:7.3f} {r['mean_rank']:6.2f}")

    # markdown
    lines = [f"# Spine cross-dataset summary ({args.mode})", "",
             "| config | " + " | ".join(ds_names) + " | mean acc | mean rank |",
             "|---|" + "---:|" * (len(ds_names) + 2)]
    for r in table:
        cells = " | ".join(f"{r[n]:.3f}" if r[n] is not None else "—" for n in ds_names)
        lines.append(f"| {r['config']} | {cells} | {r['mean_acc']:.3f} | {r['mean_rank']:.2f} |")
    (results / "spine_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {results / 'spine_summary.md'}  ({len(ds_names)} datasets: {', '.join(ds_names)})")


if __name__ == "__main__":
    main()
