"""Phase 1 validation gates: new harness vs archived strict_exact X2 Hard45 runs."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ARCH = HERE.parents[0] / "neuron_basis_decisive_2026-09-24" / "results" / "strict_exact" / "x2" / "hard45"
GATES = HERE / "results" / "gates"
KEYS = ("activity", "gate", "voltage", "weights", "decoded_raw", "qerr_true_rad", "q_true", "tau_command")
CASES = {
    "G1 NumPy CMG (Nengo PES order) vs archived Nengo CMG": ("g1_cmg_numpy", "cmg"),
    "G2 Nengo CMG via new wrapper vs archived Nengo CMG": ("g2_cmg_nengo_wrapper", "cmg"),
    "G3 constant-one rerun vs archived constant-one": ("g3_constant_one_rerun", "constant-one"),
}


def main() -> None:
    report = {}
    for label, (new, old) in CASES.items():
        a = np.load(GATES / new / "neural_trace_full_rate.npz")
        b = np.load(ARCH / old / "neural_trace_full_rate.npz")
        diffs = {k: float(np.max(np.abs(a[k] - b[k]))) for k in KEYS}
        ma = json.loads((GATES / new / "summary.json").read_text())["metrics"]
        mb = json.loads((ARCH / old / "summary.json").read_text())["metrics"]
        rel = abs(ma["qerr_true_mean_rad"] - mb["qerr_true_mean_rad"]) / mb["qerr_true_mean_rad"]
        worst = max(diffs.values())
        report[label] = {"max_abs_trace_diff": diffs, "qerr_mean_new": ma["qerr_true_mean_rad"],
                         "qerr_mean_archived": mb["qerr_true_mean_rad"], "qerr_mean_rel_diff": rel,
                         "pass": bool(worst < 1e-9 and rel < 1e-9)}
        print(f"{label}\n  worst trace diff {worst:.3e}  qerr_mean rel diff {rel:.3e}  -> {'PASS' if report[label]['pass'] else 'FAIL'}")
        for k, v in diffs.items():
            print(f"    {k:15s} {v:.3e}")
    (GATES / "GATES.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
