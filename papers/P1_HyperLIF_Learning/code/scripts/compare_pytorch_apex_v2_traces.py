"""Compare PyTorch and APEX-v2 first-batch trace summary CSVs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--pytorch", default=str(ROOT / "results" / "apex_v2" / "pytorch_first_batch_trace.csv"))
    p.add_argument("--apex-v2", required=True)
    p.add_argument("--output", default=None)
    return p.parse_args()


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def key(row):
    return (row["architecture"], row["neuron"], row["readout"], row.get("seed", "1"))


def f(row, name):
    return float(row[name])


def main():
    args = parse_args()
    pytorch_rows = {key(r): r for r in read_csv(args.pytorch)}
    apex_rows = {key(r): r for r in read_csv(args.apex_v2)}
    keys = sorted(set(pytorch_rows) & set(apex_rows))
    missing_py = sorted(set(apex_rows) - set(pytorch_rows))
    missing_apex = sorted(set(pytorch_rows) - set(apex_rows))

    out_dir = ROOT / "results" / "apex_v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = Path(args.output) if args.output else out_dir / "pytorch_vs_apex_v2_trace_compare.csv"

    rows = []
    structural_failures = 0
    for k in keys:
        py = pytorch_rows[k]
        ax = apex_rows[k]
        feature_dim_match = int(py["feature_dim"]) == int(ax["feature_dim"])
        logit_shape_match = int(py["logit_rows"]) == int(ax["logit_rows"]) and int(py["logit_cols"]) == int(ax["logit_cols"])
        finite_match = py["finite"].lower() == "true" and ax["finite"].lower() == "true"
        structural_ok = feature_dim_match and logit_shape_match and finite_match
        structural_failures += 0 if structural_ok else 1
        rows.append({
            "architecture": k[0],
            "neuron": k[1],
            "readout": k[2],
            "seed": k[3],
            "feature_dim_match": feature_dim_match,
            "logit_shape_match": logit_shape_match,
            "finite_both": finite_match,
            "structural_ok": structural_ok,
            "events_pytorch": f(py, "events_per_sample"),
            "events_apex_v2": f(ax, "events_per_sample"),
            "events_abs_delta": abs(f(py, "events_per_sample") - f(ax, "events_per_sample")),
            "gate_pytorch": f(py, "gate_mean"),
            "gate_apex_v2": f(ax, "gate_mean"),
            "gate_abs_delta": abs(f(py, "gate_mean") - f(ax, "gate_mean")),
            "voltage_pytorch": f(py, "voltage_mean"),
            "voltage_apex_v2": f(ax, "voltage_mean"),
            "conductance_pytorch": f(py, "conductance_mean"),
            "conductance_apex_v2": f(ax, "conductance_mean"),
        })

    with output.open("w", newline="", encoding="utf-8") as f_out:
        fieldnames = list(rows[0].keys()) if rows else [
            "architecture", "neuron", "readout", "seed", "structural_ok"
        ]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"matched={len(keys)} missing_pytorch={len(missing_py)} missing_apex={len(missing_apex)} structural_failures={structural_failures}")
    print(f"CSV={output}")
    if missing_py:
        print("MISSING_PYTORCH=" + repr(missing_py[:5]))
    if missing_apex:
        print("MISSING_APEX=" + repr(missing_apex[:5]))
    if structural_failures:
        raise SystemExit("Structural comparison failed.")
    print("PYTORCH_APEX_V2_TRACE_COMPARE_OK")


if __name__ == "__main__":
    main()

