"""Parity gate for the snnTorch HyperLIF port vs the validated reference.

Same machine-precision check as the native PyTorch neuron, so the snnTorch implementation is
proven to be the validated model before any event-vision benchmark. Run:
    python scripts/run_parity_snntorch.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import torch  # noqa: E402

from adhyperlif_triage.neurons import reference_numpy as ref  # noqa: E402
from adhyperlif_triage.neurons.snntorch_hyperlif import simulate_snntorch  # noqa: E402

DT = 1e-4
TOL = 1e-9


def protocols():
    step = np.concatenate([np.zeros(300), np.full(1700, 1.4), np.zeros(1000)])
    stress = np.concatenate([np.full(300, 0.0), np.full(1500, 1.4), np.full(1500, 2.5),
                             np.full(1700, 4.0), np.full(1000, 0.0)])
    db = np.full(3000, 3.3)
    return {"step": step, "stress": stress, "db_drive": db}


def compare(ro, to):
    return {
        "voltage_rmse": float(np.sqrt(np.mean((ro["voltage"] - to["voltage"]) ** 2))),
        "gate_rmse": float(np.sqrt(np.mean((ro["reset_gate"] - to["reset_gate"]) ** 2))),
        "max_abs_v": float(np.max(np.abs(ro["voltage"] - to["voltage"]))),
        "max_abs_r": float(np.max(np.abs(ro["reset_gate"] - to["reset_gate"]))),
        "event_mismatch": int(np.sum((ro["events"] > 0).astype(int) != (to["events"] > 0).astype(int))),
    }


def main():
    rows = []
    for name, cur in protocols().items():
        ro = ref.simulate_hyperlif(cur, DT, ref.HyperLIFParams())
        to = simulate_snntorch(cur, DT, model="hyperlif", dtype=torch.float64)
        rows.append(("hyperlif", name, compare(ro, to)))
        ro = ref.simulate_adaptive_hyperlif(cur, DT, ref.AdaptiveHyperLIFParams())
        to = simulate_snntorch(cur, DT, model="adaptive_hyperlif", base_gain=20.0, gain_scaling=80.0, dtype=torch.float64)
        rows.append(("adaptive_hyperlif", name, compare(ro, to)))

    passed = all(m["max_abs_v"] < TOL and m["max_abs_r"] < TOL and m["event_mismatch"] == 0 for _, _, m in rows)
    print(f"\n{'PASS' if passed else 'FAIL'}  snnTorch HyperLIF vs reference (tol={TOL:g}, dt={DT:g})")
    print(f"{'model':18s} {'protocol':9s} {'max|dv|':>10s} {'max|dr|':>10s} {'ev_mismatch':>11s}")
    for model, proto, m in rows:
        print(f"{model:18s} {proto:9s} {m['max_abs_v']:10.2e} {m['max_abs_r']:10.2e} {m['event_mismatch']:11d}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
