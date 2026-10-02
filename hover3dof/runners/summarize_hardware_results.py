"""Pull every results\\hardware\\*\\summary.json into one comparison table.

Pure Python, reads local files only -- no hardware access. Run any time to
get an up-to-date table of every hardware run so far, optionally filtered
by --mission and grouped by controller for quick before/after comparison.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

HOVER_ROOT = Path(__file__).resolve().parents[1]
RESULTS = HOVER_ROOT/"results"/"hardware"


def load_all() -> list[dict]:
    rows = []
    for d in sorted(RESULTS.iterdir()):
        sp = d/"summary.json"
        if not sp.exists():
            continue
        s = json.loads(sp.read_text())
        s["run_dir"] = d.name
        tp = d/"trace.csv"
        if tp.exists():
            with tp.open() as f:
                trace_rows = list(csv.DictReader(f))
            if trace_rows and "residual_norm" in trace_rows[0]:
                res = np.array([float(r["residual_norm"]) for r in trace_rows])
                gate = np.array([float(r["gate_mean"]) for r in trace_rows])
                s["residual_norm_mean"] = float(res.mean())
                s["gate_mean_mean"] = float(gate.mean())
        rows.append(s)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mission", default=None,
                         choices=["hover", "roll", "full3", "hard45", "hardstep", "yaw360"])
    parser.add_argument("--armed-only", action="store_true")
    args = parser.parse_args()

    rows = load_all()
    if args.mission:
        rows = [r for r in rows if r.get("mission") == args.mission]
    if args.armed_only:
        rows = [r for r in rows if r.get("armed")]

    header = f"{'run_dir':<40} {'mission':<10} {'controller':<20} {'armed':<6} {'beta':<6} {'max_res_V':<10} {'mean_err_deg':<13} {'max_err_deg':<12} {'residual_mean':<14} {'gate_mean':<10}"
    print(header)
    print("-"*len(header))
    for r in rows:
        print(f"{r['run_dir']:<40} {r.get('mission','?'):<10} {r['controller']:<20} "
              f"{str(r['armed']):<6} {r.get('beta',0.0):<6} {r.get('max_residual_volts',0.0):<10} "
              f"{r['angle_err_mean_deg']:<13.3f} {r['angle_err_max_deg']:<12.3f} "
              f"{r.get('residual_norm_mean', 0.0):<14.4f} {r.get('gate_mean_mean', 0.0):<10.4f}")

    print()
    print("--- grouped by (mission, controller, beta, max_residual_volts), armed only ---")
    groups: dict[tuple, list[float]] = {}
    for r in rows:
        if not r.get("armed"):
            continue
        key = (r.get("mission", "?"), r["controller"], r.get("beta", 0.0), r.get("max_residual_volts", 0.0))
        groups.setdefault(key, []).append(r["angle_err_mean_deg"])
    for key, errs in sorted(groups.items()):
        errs_arr = np.array(errs)
        print(f"mission={key[0]:<8} controller={key[1]:<20} beta={key[2]:<5} max_res_V={key[3]:<5} "
              f"n={len(errs):<3} mean_err_deg={errs_arr.mean():.3f} (std={errs_arr.std():.3f}, "
              f"range=[{errs_arr.min():.2f}, {errs_arr.max():.2f}])")


if __name__ == "__main__":
    main()
