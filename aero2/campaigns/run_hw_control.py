"""Run a controller on the PHYSICAL Aero2 (hardware). Conservative defaults.

Usage: python run_hw_control.py [controller] [application] [duration_s] [voltage_limit]
Requires the physical Aero 2 powered + USB-connected and full QUARC (HIL drivers).
SAFETY: keep voltage_limit modest; the rotors spin. Start with pd / short runs.
"""
from __future__ import annotations

import os
import sys

REPO = r"C:\Research\aero2"
QPY = r"C:\Users\gandhico\Documents\Quanser\0_libraries\python"
os.environ.setdefault("QUANSER_PYTHON", QPY)
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

import numpy as np  # noqa: E402
import run_control as rc  # noqa: E402

ctrl = sys.argv[1] if len(sys.argv) > 1 else "pd"
app = sys.argv[2] if len(sys.argv) > 2 else "reference_tracking"
dur = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
vlim = float(sys.argv[4]) if len(sys.argv) > 4 else 12.0

# extra "key=value" args -> controller_kwargs (e.g. kp_yaw=30 kd_yaw=12)
ckw = {}
for a in sys.argv[5:]:
    if "=" in a:
        k, v = a.split("=", 1)
        try:
            v = float(v)
        except ValueError:
            pass
        ckw[k] = v
if ckw:
    print("  controller_kwargs:", ckw, flush=True)

cfg = dict(execution_mode="hardware", model_variant="helicopter_2dof",
           controller=ctrl, application=app, duration_s=dur, hz=200.0,
           estimator="passthrough", voltage_limit=vlim, out="results_hardware",
           controller_kwargs=ckw)

print(f"HARDWARE run: {ctrl} on {app}, {dur}s, Vlim={vlim} ...", flush=True)
rec, m = rc.run(cfg)
rc.save_record(rec, m, cfg)
t = np.asarray(rec.t)
realized = (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 else 0.0
print(f"[HARDWARE | {ctrl} | {app}]", flush=True)
print(f"  samples={len(t)} duration={t[-1]-t[0]:.2f}s realized={realized:.1f} Hz", flush=True)
for k in ("pitch_rms", "yaw_rms", "tail_pitch_mae", "tail_yaw_mae", "pitch_sat_frac", "yaw_sat_frac"):
    if k in m:
        print(f"  {k} = {float(m[k]):.4f}", flush=True)
print("HW_CONTROL_DONE", flush=True)
