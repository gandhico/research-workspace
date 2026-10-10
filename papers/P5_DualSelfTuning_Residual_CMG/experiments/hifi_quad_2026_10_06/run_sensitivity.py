"""Small sequential motor-lag sensitivity screen; no fitted motor parameters.

One Python process, no videos, 20 Hz traces. The lag values are declared
synthetic perturbations. The unchanged L0 run and the copied L1 zero-lag
runner are checked separately before interpreting these cells.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from run_l1_v5 import ACC, ROOT, run
from dual_controller import TunerConfig

OUT = ROOT / "results" / "l1_sensitivity_hover_init_2026-10-06"
V5 = ROOT / "results" / "v5_2026-09-25"


def e_ref(platform: str) -> float:
    p = V5 / "lqr" / platform / "hard45" / "base" / "summary.json"
    return json.loads(p.read_text(encoding="utf-8"))["qerr_mean_rad"]


def cells():
    for platform in ("cf2-rotor", "x2"):
        for arm in ("base", "res", "st", "dual"):
            for tau in (0.0, 0.03):
                yield platform, arm, tau
    # One larger synthetic perturbation for the CF2 negative-regression case.
    for arm in ("base", "dual"):
        yield "cf2-rotor", arm, 0.10


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for i, (platform, arm, tau) in enumerate(cells(), 1):
        label = f"{platform}/{arm}/tau_{tau:.3f}"
        print(f"[{i:02d}] {label}", flush=True)
        tuner = TunerConfig(v2_gating=True, e_ref=e_ref(platform)) if arm in ("st", "dual") else None
        summary = run(platform, "hardstep", "lqr", arm, OUT / label,
                      duration=8.0, log_every=100, tuner=tuner,
                      sat_gate_axes=True, rotor_tau_s=tau)
        trace = OUT / label / "trace.csv"
        with trace.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        first_large = next((float(r["t"]) for r in rows if float(r["qerr"]) > 1.2), None)
        rec = {k: summary[k] for k in ("platform", "arm", "rotor_tau_s", "qerr_mean_rad",
                "qerr_max_rad", "z_min_m", "saturation_fraction", "motor_force_mismatch_rms_N",
                "diverged", "wall_s")}
        rec["first_qerr_gt_1p2_s_decimated"] = first_large
        rec["min_alpha_decimated"] = min(float(r["alpha"]) for r in rows)
        records.append(rec)
        print(f"     qerr={rec['qerr_mean_rad']:.4f} zmin={rec['z_min_m']:.4f} "
              f"sat={rec['saturation_fraction']:.3f} first>1.2={first_large}", flush=True)
    (OUT / "screen.json").write_text(json.dumps({
        "interpretation": "synthetic rotor-lag sensitivity; not X2/CF2 physical identification",
        "duration_s": 8.0, "mission": "hardstep", "family": "lqr", "cells": records,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
