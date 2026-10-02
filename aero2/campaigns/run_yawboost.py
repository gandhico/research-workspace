"""Yaw-authority fix: compare stock vs `yawboost` gains on the 2DOF twin.

Backstepping and SMC expose a `yawboost=True` kwarg (higher-authority yaw
retunes from the hardware experiments). This runs both stock and boosted on the
reference-tracking benchmark to quantify the yaw improvement on the digital twin.
Requires QLabs Aero2 (helicopter 2DOF) open on localhost:18950.
"""
from __future__ import annotations

import os
import sys
import time

REPO = r"C:\Research\aero2"
QPY = r"C:\Users\gandhico\Documents\Quanser\0_libraries\python"
os.environ.setdefault("QUANSER_PYTHON", QPY)
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

import run_control as rc  # noqa: E402

rows = []
for ctrl in ("backstepping", "smc"):
    for boost in (False, True):
        cfg = dict(
            execution_mode="virtual_twin", model_variant="helicopter_2dof",
            controller=ctrl, application="reference_tracking",
            duration_s=18.0, hz=200.0, estimator="passthrough",
            out="results_twin_campaign", controller_kwargs={"yawboost": boost},
        )
        try:
            rec, m = rc.run(cfg)
            row = {"controller": ctrl, "yawboost": boost}
            for k, v in m.items():
                try:
                    row[k] = round(float(v), 4)
                except (TypeError, ValueError):
                    pass
            rc.save_record(rec, m, cfg)
            rows.append(row)
            print("ok:", row, flush=True)
        except Exception as e:
            print("FAIL:", ctrl, boost, repr(e), flush=True)
            rows.append({"controller": ctrl, "yawboost": boost, "error": str(e)})
        time.sleep(0.5)

print("\n[yawboost comparison — yaw_rms / tail_yaw_mae]")
for r in rows:
    print(f"  {r.get('controller'):>12} boost={str(r.get('yawboost')):>5}: "
          f"yaw_rms={r.get('yaw_rms')}  tail_yaw_mae={r.get('tail_yaw_mae')}  "
          f"pitch_rms={r.get('pitch_rms')}")
print("YAWBOOST DONE")
