"""Aggregate the HPC array results ($HLL_RESULTS/_registry.csv) into per-dataset rankings and a
cross-dataset config x dataset table. Run after the SLURM array completes.

    python hpc/aggregate_hpc.py            # writes $HLL_RESULTS/HPC_RESULTS.md
"""

from __future__ import annotations

import csv
import os
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get("HLL_RESULTS", str(ROOT / "results" / "hpc")))
REG = RESULTS / "_registry.csv"


def _f(row, key, default=None):
    v = row.get(key)
    if v in (None, ""):
        return default
    try:
        return float(v)
    except ValueError:
        return default


def main():
    if not REG.exists():
        print(f"no registry yet: {REG}")
        return
    rows = list(csv.DictReader(open(REG, encoding="utf-8")))
    for r in rows:
        r["config"] = f"{r.get('arch', 'ff')}.{r['neuron']}.{r['readout']}"

    datasets = sorted({r["dataset"] for r in rows})
    configs = sorted({r["config"] for r in rows})

    lines = ["# HPC event-vision results — Adaptive HyperLIF (HyperLIF_Learning)", "",
             f"Registry: `{REG}` — {len(rows)} runs, {len(datasets)} datasets, {len(configs)} configs.",
             "",
             "Columns: accuracy = mean ± std over seeds; events = mean events/sample; "
             "stable = fraction of seeds with no NaN.", ""]
    cross = {c: {} for c in configs}
    for ds in datasets:
        drows = [r for r in rows if r["dataset"] == ds]
        prov = sorted({r.get("provenance", "") for r in drows if r.get("provenance")})
        agg = {}
        for c in configs:
            crows = [r for r in drows if r["config"] == c]
            accs = [_f(r, "accuracy") for r in crows if _f(r, "accuracy") is not None]
            if not accs:
                continue
            evs = [_f(r, "events_per_sample") for r in crows if _f(r, "events_per_sample") is not None]
            stables = [str(r.get("stable")).lower() in ("true", "1") for r in crows]
            agg[c] = (st.mean(accs), st.pstdev(accs) if len(accs) > 1 else 0.0, len(accs),
                      st.mean(evs) if evs else float("nan"),
                      sum(stables) / len(stables) if stables else float("nan"))
            cross[c][ds] = st.mean(accs)
        lines += [f"## {ds}", ""]
        if prov:
            lines += [f"_provenance: {', '.join(prov)}_", ""]
        lines += ["| config | accuracy | seeds | events/sample | stable |",
                  "|---|---:|---:|---:|---:|"]
        for c, (m, s, n, ev, stab) in sorted(agg.items(), key=lambda kv: kv[1][0], reverse=True):
            lines.append(f"| {c} | {m:.4f} ± {s:.4f} | {n} | {ev:.1f} | {stab:.0%} |")
        lines.append("")

    lines += ["## Cross-dataset (mean accuracy)", "",
              "| config | " + " | ".join(datasets) + " | mean |",
              "|---|" + "---:|" * (len(datasets) + 1)]
    table = []
    for c in configs:
        vals = [cross[c].get(ds) for ds in datasets]
        present = [v for v in vals if v is not None]
        mean = st.mean(present) if present else 0.0
        table.append((c, vals, mean))
    for c, vals, mean in sorted(table, key=lambda x: x[2], reverse=True):
        cells = " | ".join(f"{v:.4f}" if v is not None else "—" for v in vals)
        lines.append(f"| {c} | {cells} | {mean:.4f} |")

    out = RESULTS / "HPC_RESULTS.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
