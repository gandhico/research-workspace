"""Regulation-under-disturbance benchmark on the QLabs Aero2 2DOF twin.

Holds theta=psi=0 while scheduled command pulses kick pitch/yaw; each controller
must reject them. Companion table to reference tracking. Setpoints are 0, so the
standard metrics (deviation from 0) are wrap-safe.
Requires QLabs Aero2 (helicopter 2DOF) open on localhost:18950.
"""
from __future__ import annotations

import csv
import os
import sys
import time
import traceback
from datetime import datetime

REPO = r"C:\Research\aero2"
QPY = r"C:\Users\gandhico\Documents\Quanser\0_libraries\python"
os.environ.setdefault("QUANSER_PYTHON", QPY)
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

import run_control as rc  # noqa: E402

OUT = os.path.join(REPO, "results_twin_campaign")
os.makedirs(OUT, exist_ok=True)

CTRLS = ["pd", "lqr", "lqg", "backstepping", "smc", "nmpc", "hyperlif", "qpd"]
rows = []
for c in CTRLS:
    print(f"disturbance: {c} ...", flush=True)
    cfg = dict(execution_mode="virtual_twin", model_variant="helicopter_2dof",
               controller=c, application="regulation_disturbance",
               duration_s=20.0, hz=200.0, estimator="passthrough",
               out="results_twin_campaign")
    try:
        rec, m = rc.run(cfg)
        row = {"controller": c}
        for k, v in m.items():
            try:
                row[k] = round(float(v), 4)
            except (TypeError, ValueError):
                pass
        rc.save_record(rec, m, cfg)
        rows.append(row)
        print("  ok:", row, flush=True)
    except Exception as e:
        print("  FAIL:", repr(e), flush=True)
        traceback.print_exc()
        rows.append({"controller": c, "error": str(e)})
    time.sleep(0.5)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
keys = ["controller"] + sorted({k for r in rows for k in r} - {"controller"})
p = os.path.join(OUT, f"disturbance_summary_{stamp}.csv")
with open(p, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
print("\n[Regulation under disturbance — deviation from 0]")
for r in rows:
    print(f"  {str(r.get('controller')):>12}: pitch_rms={r.get('pitch_rms')}  "
          f"yaw_rms={r.get('yaw_rms')}  pitch_sat={r.get('pitch_sat_frac')}")
print("DISTURBANCE DONE ->", p)
