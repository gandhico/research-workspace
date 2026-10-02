"""Generic single-mission runner via rc.run (works with all registered controllers/apps).
Usage: python run_mission.py <offline|twin|hardware> <controller> <application> <dur> [vlim] [k=v ...]
Saves the full record to results_paper/<backend>/.
"""
from __future__ import annotations
import os, sys
REPO = r"C:\Research\aero2"
QPY = r"C:\Users\gandhico\Documents\Quanser\0_libraries\python"
os.environ.setdefault("QUANSER_PYTHON", QPY); os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "runners"))
import numpy as np  # noqa
import run_control as rc  # noqa

be = sys.argv[1]; mode = {"offline": "offline", "twin": "virtual_twin", "hardware": "hardware"}[be]
ctrl, app, dur = sys.argv[2], sys.argv[3], float(sys.argv[4])
vlim = float(sys.argv[5]) if len(sys.argv) > 5 else 15.0
ckw = {}
for a in sys.argv[6:]:
    if "=" in a:
        k, v = a.split("=", 1)
        try:
            v = float(v)
        except ValueError:
            pass
        ckw[k] = v
cfg = dict(execution_mode=mode, model_variant="helicopter_2dof", controller=ctrl, controller_kwargs=ckw,
           application=app, duration_s=dur, hz=200.0, estimator="passthrough", voltage_limit=vlim,
           out=os.path.join("results_paper", be))
print(f"{be}/{ctrl}/{app} kwargs={ckw} ...", flush=True)
rec, m = rc.run(cfg)
rc.save_record(rec, m, cfg)
t = np.asarray(rec.t)
print(f"SAVED -> results_paper/{be} | samples={len(t)} realized={((len(t)-1)/(t[-1]-t[0])):.1f}Hz "
      f"pitch_rms={m.get('pitch_rms')}", flush=True)
