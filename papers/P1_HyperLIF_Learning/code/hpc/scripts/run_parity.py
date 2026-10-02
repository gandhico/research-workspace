"""Parity gate: PyTorch neuron vs the vendored validated reference.

Proves the PyTorch HyperLIF / Adaptive HyperLIF reproduces the validated ``stable`` reference
(which is itself proven == the Nengo port) to machine precision, across several stimulus
protocols. No benchmark number in this project is trustworthy until this passes.

Run:
    python scripts/run_parity.py
Outputs:
    results/parity/parity_metrics.csv
    results/parity/parity_metrics.json
    docs/PARITY.md   (regenerated)
Exit code 0 if all protocols/models pass (max|dv|,max|dr| < 1e-9 and zero event mismatch).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import torch  # noqa: E402

from adhyperlif_triage.neurons import reference_numpy as ref  # noqa: E402
from adhyperlif_triage.neurons.hyperlif_torch import HyperLIFConfig, simulate_torch  # noqa: E402

DT = 1e-4
TOL = 1e-9


def protocol_step(n_pre=300, n_on=1700, n_post=1000, level=1.4):
    return np.concatenate([np.zeros(n_pre), np.full(n_on, level), np.zeros(n_post)])


def protocol_stress():
    seg = lambda v, n: np.full(n, v)  # noqa: E731
    return np.concatenate([seg(0.0, 300), seg(1.4, 1500), seg(2.5, 1500), seg(4.0, 1700), seg(0.0, 1000)])


def protocol_db_drive(level=3.3, n=3000):
    return np.full(n, level)


PROTOCOLS = {"step": protocol_step(), "stress": protocol_stress(), "db_drive": protocol_db_drive()}


def compare(ref_out, torch_out):
    v_ref, v_t = ref_out["voltage"], torch_out["voltage"]
    r_ref, r_t = ref_out["reset_gate"], torch_out["reset_gate"]
    e_ref = (ref_out["events"] > 0).astype(int)
    e_t = (torch_out["events"] > 0).astype(int)
    return {
        "voltage_rmse": float(np.sqrt(np.mean((v_ref - v_t) ** 2))),
        "gate_rmse": float(np.sqrt(np.mean((r_ref - r_t) ** 2))),
        "max_abs_v": float(np.max(np.abs(v_ref - v_t))),
        "max_abs_r": float(np.max(np.abs(r_ref - r_t))),
        "events_ref": int(e_ref.sum()),
        "events_torch": int(e_t.sum()),
        "event_mismatch": int(np.sum(e_ref != e_t)),
    }


def run():
    rows = []
    for proto_name, current in PROTOCOLS.items():
        # HyperLIF
        ro = ref.simulate_hyperlif(current, DT, ref.HyperLIFParams())
        to = simulate_torch(current, HyperLIFConfig(model="hyperlif"), DT, dtype=torch.float64)
        rows.append({"model": "hyperlif", "protocol": proto_name, **compare(ro, to)})
        # Adaptive HyperLIF
        ro = ref.simulate_adaptive_hyperlif(current, DT, ref.AdaptiveHyperLIFParams())
        to = simulate_torch(current, HyperLIFConfig(model="adaptive_hyperlif"), DT, dtype=torch.float64)
        rows.append({"model": "adaptive_hyperlif", "protocol": proto_name, **compare(ro, to)})

    passed = all(r["max_abs_v"] < TOL and r["max_abs_r"] < TOL and r["event_mismatch"] == 0 for r in rows)

    out_dir = ROOT / "results" / "parity"
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["model", "protocol", "voltage_rmse", "gate_rmse", "max_abs_v", "max_abs_r",
            "events_ref", "events_torch", "event_mismatch"]
    with open(out_dir / "parity_metrics.csv", "w", encoding="utf-8") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(f"{r[c]:.3e}" if isinstance(r[c], float) else str(r[c]) for c in cols) + "\n")
    with open(out_dir / "parity_metrics.json", "w", encoding="utf-8") as f:
        json.dump({"passed": passed, "tol": TOL, "dt": DT, "rows": rows,
                   "torch": torch.__version__, "numpy": np.__version__}, f, indent=2)

    write_parity_md(rows, passed)

    print(f"\n{'PASS' if passed else 'FAIL'}  (tol={TOL:g}, dt={DT:g}, torch {torch.__version__}, numpy {np.__version__})")
    print(f"{'model':18} {'protocol':9} {'max|dv|':>10} {'max|dr|':>10} {'ev_mismatch':>11}")
    for r in rows:
        print(f"{r['model']:18} {r['protocol']:9} {r['max_abs_v']:10.2e} {r['max_abs_r']:10.2e} {r['event_mismatch']:11d}")
    return 0 if passed else 1


def write_parity_md(rows, passed):
    lines = [
        "# Parity Gate — PyTorch neuron vs validated reference",
        "",
        f"**Status: {'PASS ✅' if passed else 'FAIL ❌'}**  ·  tolerance `max|Δ| < 1e-9`, zero event mismatch  ·  `dt = 1e-4`, float64",
        "",
        "The PyTorch `HyperLIFLayer` (`src/adhyperlif_triage/neurons/hyperlif_torch.py`) is checked",
        "against the vendored `reference_numpy.py` — a frozen copy of the `04_Adaptive_HyperLIF_Nengo`",
        "`stable` stepping that is itself proven equal (RMSE = 0) to the Nengo `NeuronType` port",
        "(`05_Adaptive_HyperLIF_Nengo_Paper/RESULTS_AUDIT.md`, result #1). Passing here means the",
        "PyTorch model **is** the validated continuous-reset neuron, not an approximation of it.",
        "",
        "| Model | Protocol | voltage RMSE | gate RMSE | max\\|Δv\\| | max\\|Δr\\| | events (ref/torch) | event mismatch |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['model']} | {r['protocol']} | {r['voltage_rmse']:.2e} | {r['gate_rmse']:.2e} | "
            f"{r['max_abs_v']:.2e} | {r['max_abs_r']:.2e} | {r['events_ref']}/{r['events_torch']} | {r['event_mismatch']} |"
        )
    lines += [
        "",
        "Protocols: **step** (J=1.4 pulse), **stress** (staircase ramp to J=4, exercises the",
        "depolarization-block / adaptive-rescue regime), **db_drive** (sustained J=3.3 above J_DB).",
        "",
        "> Regenerate with `python scripts/run_parity.py`. The origin extension (`delta_reset`) is",
        "> inert here (`delta_reset=0`), so this gate validates the base dynamics shared by every variant.",
    ]
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "PARITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(run())
