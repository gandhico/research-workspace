"""Gate-state residual augmented controller benchmark on the QLabs Aero2 2DOF twin.

Compares the classical PD baseline against the MuJoCo-quadrotor gate-residual
architecture ported to Aero2, in all four forms:
    fixed / adaptive  x  residual / gain
on both reference tracking and regulation-under-disturbance.
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

# (controller, controller_kwargs, label)
VARIANTS = [
    ("pd", {}, "pd_baseline"),
    ("gate_residual", {"neuron": "hyperlif", "aug": "residual"}, "gate_res_fixed"),
    ("gate_residual", {"neuron": "adaptive_hyperlif", "aug": "residual"}, "gate_res_adapt"),
    ("gate_residual", {"neuron": "hyperlif", "aug": "gain"}, "gate_gain_fixed"),
    ("gate_residual", {"neuron": "adaptive_hyperlif", "aug": "gain"}, "gate_gain_adapt"),
]
APPS = [("reference_tracking", 18.0), ("regulation_disturbance", 20.0)]

rows = []
for app, dur in APPS:
    for ctrl, kwargs, label in VARIANTS:
        print(f"[{app}] {label} ...", flush=True)
        cfg = dict(execution_mode="virtual_twin", model_variant="helicopter_2dof",
                   controller=ctrl, controller_kwargs=kwargs, application=app,
                   duration_s=dur, hz=200.0, estimator="passthrough", out="results_twin_campaign")
        try:
            rec, m = rc.run(cfg)
            row = {"app": app, "label": label}
            for k, v in m.items():
                try:
                    row[k] = round(float(v), 4)
                except (TypeError, ValueError):
                    pass
            rc.save_record(rec, m, cfg)
            rows.append(row)
            print("  ok:", {k: row.get(k) for k in ("pitch_rms", "yaw_rms", "tail_yaw_mae")}, flush=True)
        except Exception as e:
            print("  FAIL:", repr(e), flush=True)
            traceback.print_exc()
            rows.append({"app": app, "label": label, "error": str(e)})
        time.sleep(0.5)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
keys = ["app", "label"] + sorted({k for r in rows for k in r} - {"app", "label"})
p = os.path.join(OUT, f"gate_residual_summary_{stamp}.csv")
with open(p, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)

# vs-PD comparison per app
print("\n[Gate-residual vs PD — pitch_rms / yaw_rms (Δ% vs PD)]")
for app, _ in APPS:
    base = next((r for r in rows if r["app"] == app and r["label"] == "pd_baseline"), None)
    print(f"  == {app} ==")
    for r in [x for x in rows if x["app"] == app]:
        if "error" in r:
            print(f"    {r['label']:>16}: FAIL"); continue
        dp = dy = ""
        if base and base.get("pitch_rms"):
            dp = f"({100*(r['pitch_rms']-base['pitch_rms'])/base['pitch_rms']:+.0f}%)"
            dy = f"({100*(r['yaw_rms']-base['yaw_rms'])/base['yaw_rms']:+.0f}%)"
        print(f"    {r['label']:>16}: pitch={r.get('pitch_rms')} {dp}  yaw={r.get('yaw_rms')} {dy}")
print("GATE RESIDUAL DONE ->", p)
