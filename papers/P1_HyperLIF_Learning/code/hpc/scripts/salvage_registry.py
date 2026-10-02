"""Recover a ranking.csv + summary.md from a (possibly interrupted/contaminated) _registry.csv.

A run that died before its final aggregation step still has every completed run logged in the
registry. This dedups to the *real* run per (config, seed) — keeping the longest wall_s, which
drops short cache-building validation rows — then aggregates per config.

    python scripts/salvage_registry.py --dir results/phase1b_shd
"""

from __future__ import annotations

import argparse
import csv
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="results/<tag>_<dataset> dir with _registry.csv")
    args = ap.parse_args()
    base = (ROOT / args.dir) if not Path(args.dir).is_absolute() else Path(args.dir)
    reg = base / "_registry.csv"
    rows = list(csv.DictReader(open(reg, encoding="utf-8")))

    # keep the real (longest) run per (config, seed) -> drops short validation rows
    best = {}
    for r in rows:
        key = (r["config"], r["seed"])
        if key not in best or float(r.get("wall_s", 0) or 0) > float(best[key].get("wall_s", 0) or 0):
            best[key] = r
    by_cfg = {}
    for (cfg, seed), r in best.items():
        by_cfg.setdefault(cfg, []).append(r)

    table = []
    for cfg, rs in by_cfg.items():
        accs = [float(r["accuracy"]) for r in rs if r.get("accuracy") not in (None, "")]
        table.append({
            "config": cfg, "n_seeds": len(accs),
            "acc_mean": round(st.mean(accs), 4) if accs else 0.0,
            "acc_std": round(st.pstdev(accs), 4) if len(accs) > 1 else 0.0,
            "events_per_sample": round(st.mean([float(r["events_per_sample"]) for r in rs]), 2),
            "stable_frac": round(st.mean([1.0 if str(r.get("stable")) == "True" else 0.0 for r in rs]), 2),
        })
    table.sort(key=lambda r: r["acc_mean"], reverse=True)

    with open(base / "ranking.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys()))
        w.writeheader(); w.writerows(table)
    lines = [f"# Salvaged ranking — {base.name}", "",
             "| config | acc | n_seeds | events/sample | stable |", "|---|---:|---:|---:|---:|"]
    for r in table:
        lines.append(f"| {r['config']} | {r['acc_mean']:.3f} ± {r['acc_std']:.3f} | {r['n_seeds']} | "
                     f"{r['events_per_sample']:.2f} | {r['stable_frac']:.2f} |")
    (base / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"salvaged {len(table)} configs from {sum(r['n_seeds'] for r in table)} real runs -> {base/'ranking.csv'}")
    for r in table:
        print(f"  {r['config']:26s} {r['acc_mean']:.3f} ± {r['acc_std']:.3f}  (n={r['n_seeds']})")


if __name__ == "__main__":
    main()
