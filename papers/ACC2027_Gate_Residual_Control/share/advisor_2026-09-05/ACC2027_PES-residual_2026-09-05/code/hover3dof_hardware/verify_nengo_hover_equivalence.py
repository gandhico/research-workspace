"""Offline numerical audit of direct CMG/PES versus the Nengo Hover decoder."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np



# --- portable paths (added for distribution) ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from acc2027_paths import ROOT  # noqa: E402

HERE = Path(__file__).resolve().parent
ACC_ROOT = ROOT
NENGO_ROOT = ACC_ROOT / "experiments" / "nengo_nef_replication_2026-08-29"
sys.path.insert(0, str(ACC_ROOT / "src"))
sys.path.insert(0, str(NENGO_ROOT))

from gra_control.gate import CMGResidualAugmentor  # noqa: E402
from nengo_cmg import NengoCMGPESAugmentor  # noqa: E402


def main() -> None:
    dt = 5e-4
    limits = np.array([0.12, 0.28, 0.28])
    direct = CMGResidualAugmentor(
        channels=3,
        limits=limits,
        mode="online_pes",
        adaptive_conductance=True,
        beta=0.5,
        learning_rate=8e-4,
    )
    nengo_controller = NengoCMGPESAugmentor(
        channels=3,
        limits=limits,
        dt=dt,
        beta=0.5,
        learning_rate=8e-4,
        adaptive_conductance=True,
    )
    maxima = {"residual": 0.0, "activity": 0.0, "gate": 0.0, "voltage": 0.0, "weights": 0.0}
    try:
        for k in range(2000):
            t = k * dt
            baseline = limits * np.array(
                [0.72 * np.sin(2.1 * t), -0.63 * np.cos(1.7 * t), 0.51 * np.sin(2.9 * t + 0.2)]
            )
            target = np.clip(
                np.array([np.sin(0.8 * t), -np.cos(0.6 * t), np.sin(1.2 * t + 0.4)]),
                -1.0,
                1.0,
            )
            out_direct = direct.step(baseline, dt, target)
            out_nengo = nengo_controller.step(baseline, target)
            maxima["residual"] = max(maxima["residual"], float(np.max(np.abs(out_direct.residual - out_nengo.residual))))
            maxima["activity"] = max(maxima["activity"], float(np.max(np.abs(out_direct.activity - out_nengo.activity))))
            maxima["gate"] = max(maxima["gate"], float(np.max(np.abs(direct.units.r - nengo_controller.r))))
            maxima["voltage"] = max(maxima["voltage"], float(np.max(np.abs(direct.units.v - nengo_controller.v))))
            maxima["weights"] = max(maxima["weights"], float(np.max(np.abs(direct.W - nengo_controller.W))))
    finally:
        nengo_controller.close()

    behavioral_tolerance = 2e-6
    # Nengo's PES operator publishes its learned transform on the following
    # simulator tick.  The state/output comparison is therefore the strict
    # equivalence test; the raw transform may differ by at most one direct PES
    # increment at the same observation instant.
    weight_temporal_skew_bound = 8.1e-4
    behavior_keys = ("residual", "activity", "gate", "voltage")
    status = "passed" if (
        max(maxima[key] for key in behavior_keys) <= behavioral_tolerance
        and maxima["weights"] <= weight_temporal_skew_bound
    ) else "failed"
    payload = {
        "status": status,
        "steps": 2000,
        "dt_s": dt,
        "behavioral_tolerance": behavioral_tolerance,
        "weight_temporal_skew_bound": weight_temporal_skew_bound,
        "maximum_absolute_differences": maxima,
        "interpretation": {
            "behavior": "Residual, CMG activity, gate, and membrane states must agree within the strict behavioral tolerance.",
            "weights": "Built-in Nengo PES exposes its transform with a one-neural-step scheduling skew; the bound is one direct learning increment and is not treated as a behavioral mismatch.",
        },
    }
    output = HERE / "results" / "offline_nengo_equivalence.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if status != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
