"""Find the physical Aero2 yaw range: sustained differential push +/- with stall
detection (stops if yaw stops moving while commanded -> a limit/stall), moderate
voltage. Records the trace + reports the observed yaw span.

Usage: python run_yaw_limit.py [volts] [dur_s]
"""
from __future__ import annotations

import csv
import os
import sys
import time
from datetime import datetime

REPO = r"C:\Research\aero2"
QPY = r"C:\Users\gandhico\Documents\Quanser\0_libraries\python"
os.environ.setdefault("QUANSER_PYTHON", QPY)
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.path.insert(0, REPO)

import numpy as np  # noqa: E402
from aero2.execution.hardware import HardwareBackend  # noqa: E402

OUT = os.path.join(REPO, "results_hardware")
os.makedirs(OUT, exist_ok=True)
V = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
HZ = 200.0


def push(be, sign):
    be.reset(np.zeros(4)); be.apply(np.zeros(2)); be.read()
    rows, last_psi, stalled = [], 0.0, 0
    t0 = time.perf_counter(); nextT = t0
    while True:
        t = time.perf_counter() - t0
        if t > DUR:
            break
        be.apply(np.array([0.0, sign * V]))       # differential -> yaw
        m = be.read(); psi = float(m.psi)
        rows.append((t, psi, float(m.theta)))
        if t > 1.0 and abs(psi - last_psi) < np.deg2rad(0.3):
            stalled += 1
        else:
            stalled = 0
        last_psi = psi
        if stalled > int(0.8 * HZ):               # yaw stuck while commanded -> limit
            print(f"  stall/limit at psi={np.rad2deg(psi):+.1f} deg", flush=True)
            break
        nextT += 1.0 / HZ
        while time.perf_counter() < nextT and (time.perf_counter() - t0) <= DUR:
            pass
    be.apply(np.zeros(2)); time.sleep(0.3)
    ps = np.array([r[1] for r in rows])
    return rows, float(np.rad2deg(ps.max())), float(np.rad2deg(ps.min())), float(np.rad2deg(ps[-1]))


print(f"=== HARDWARE yaw-limit test at {V} V (differential) ===", flush=True)
be = HardwareBackend(aero_id="0", frequency=HZ, output_mode="mixed", voltage_limit=15.0, quanser_python=QPY)
try:
    r1, mx1, _, end1 = push(be, +1)
    print(f"  +yaw push: max={mx1:+.1f} deg (end {end1:+.1f})", flush=True)
    time.sleep(0.5)
    r2, _, mn2, end2 = push(be, -1)
    print(f"  -yaw push: min={mn2:+.1f} deg (end {end2:+.1f})", flush=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(OUT, f"yaw_limit_{stamp}.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["dir", "t", "psi_deg", "theta_deg"])
        for t, psi, th in r1:
            w.writerow(["+", round(t, 4), round(np.rad2deg(psi), 2), round(np.rad2deg(th), 2)])
        for t, psi, th in r2:
            w.writerow(["-", round(t, 4), round(np.rad2deg(psi), 2), round(np.rad2deg(th), 2)])
    print(f"  YAW RANGE observed: {mn2:+.1f} .. {mx1:+.1f} deg (span {mx1 - mn2:.1f} deg)", flush=True)
finally:
    be.close()
print("YAW_LIMIT_DONE", flush=True)
