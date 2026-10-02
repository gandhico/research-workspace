"""Paper data-acquisition campaign — 2DOF helicopter, missions x controllers.

Saves EVERY run (full .npz/.json record via run_control.save_record) plus a master
summary CSV, into results_paper/<backend>/, so all data is captured for later
analysis. Token-light by design: acquire + save now, analyze later.

Usage:  python run_paper_campaign.py <offline|twin|hardware> [max_volt]
  offline  : all controllers x all missions (fast, no device)
  twin     : all controllers x all missions (needs QLabs Aero2 open on :18950)
  hardware : SAFE subset x safe missions (physical device; moderate voltage)
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

BACKEND = sys.argv[1] if len(sys.argv) > 1 else "offline"
MODE = {"offline": "offline", "twin": "virtual_twin", "hardware": "hardware"}[BACKEND]
MAXV = float(sys.argv[2]) if len(sys.argv) > 2 else (12.0 if BACKEND == "hardware" else 15.0)
DUR = 10.0 if BACKEND == "hardware" else 18.0
OUT = os.path.join(REPO, "results_paper", BACKEND)
os.makedirs(OUT, exist_ok=True)

MISSIONS_FULL = ["reference_tracking", "regulation_disturbance",
                 "pitch_reference_tracking", "yaw_reference_tracking"]
MISSIONS_HW = ["reference_tracking", "regulation_disturbance", "pitch_reference_tracking"]
MISSIONS = MISSIONS_HW if BACKEND == "hardware" else MISSIONS_FULL

# (label, controller, controller_kwargs)
FULL = [
    ("pd", "pd", {}), ("lqr", "lqr", {}), ("lqg", "lqg", {}), ("mpc", "mpc", {}),
    ("backstepping", "backstepping", {}), ("backstepping_yb", "backstepping", {"yawboost": True}),
    ("smc", "smc", {}), ("smc_yb", "smc", {"yawboost": True}), ("nmpc", "nmpc", {}),
    ("hyperlif", "hyperlif", {}),
    ("gate_res_fixed", "gate_residual", {"neuron": "hyperlif", "aug": "residual"}),
    ("gate_res_adapt", "gate_residual", {"neuron": "adaptive_hyperlif", "aug": "residual"}),
    ("gate_gain_adapt", "gate_residual", {"neuron": "adaptive_hyperlif", "aug": "gain"}),
    ("qpd", "qpd", {}),
]
# hardware: safe subset (skip aggressive smc/nmpc/backstepping — they saturate/spin)
HW_SAFE = [
    ("pd", "pd", {}), ("lqr", "lqr", {}), ("hyperlif", "hyperlif", {}),
    ("gate_res_adapt", "gate_residual", {"neuron": "adaptive_hyperlif", "aug": "residual"}),
    ("gate_gain_adapt", "gate_residual", {"neuron": "adaptive_hyperlif", "aug": "gain"}),
    ("qpd", "qpd", {}),
]
CTRLS = HW_SAFE if BACKEND == "hardware" else FULL

print(f"=== PAPER CAMPAIGN: backend={BACKEND} mode={MODE} Vlim={MAXV} dur={DUR}s ===", flush=True)
print(f"    missions={MISSIONS}", flush=True)
print(f"    controllers={[c[0] for c in CTRLS]}", flush=True)

rows = []
for mission in MISSIONS:
    for label, ctrl, kw in CTRLS:
        print(f"[{BACKEND}] {mission} / {label} ...", flush=True)
        cfg = dict(execution_mode=MODE, model_variant="helicopter_2dof", controller=ctrl,
                   controller_kwargs=kw, application=mission, duration_s=DUR, hz=200.0,
                   estimator="passthrough", voltage_limit=MAXV,
                   out=os.path.join("results_paper", BACKEND))
        try:
            rec, m = rc.run(cfg)
            row = {"backend": BACKEND, "mission": mission, "label": label}
            for k, v in m.items():
                try:
                    row[k] = round(float(v), 5)
                except (TypeError, ValueError):
                    pass
            rc.save_record(rec, m, cfg)
            rows.append(row)
            print("   ok:", {k: row.get(k) for k in ("pitch_rms", "yaw_rms", "realized_hz")}, flush=True)
        except Exception as e:
            print("   FAIL:", repr(e), flush=True)
            traceback.print_exc()
            rows.append({"backend": BACKEND, "mission": mission, "label": label, "error": str(e)})
        time.sleep(0.4)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
keys = ["backend", "mission", "label"] + sorted({k for r in rows for k in r} - {"backend", "mission", "label"})
csvp = os.path.join(OUT, f"campaign_{BACKEND}_{stamp}.csv")
with open(csvp, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    w.writerows(rows)
print(f"SAVED {len(rows)} runs -> {csvp}", flush=True)
print(f"PAPER_CAMPAIGN_DONE ({BACKEND})", flush=True)
