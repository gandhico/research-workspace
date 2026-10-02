"""Push hardware yaw to its MAX range while a PD holds pitch at horizontal (0 deg).

Holding pitch horizontal isolates yaw and maximizes yaw authority (cos(theta)=1),
and keeps the device in a safe orientation. Sustained yaw command + a permissive
window-stall detector (stop only if yaw advances < 2 deg over 2 s => true plateau).

Usage: python run_yaw_max_hold_pitch.py [yaw_volts] [dur_s]
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
from aero2.config import gains  # noqa: E402
from aero2.execution.hardware import HardwareBackend  # noqa: E402

OUT = os.path.join(REPO, "results_hardware")
os.makedirs(OUT, exist_ok=True)
V = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
HZ, VLIM = 200.0, 15.0
KpP, KdP = gains.PD_KP_PITCH, gains.PD_KD_PITCH


def push(be, sign):
    be.reset(np.zeros(4)); be.apply(np.zeros(2)); be.read()
    rows, hist = [], []
    t0 = time.perf_counter(); nextT = t0
    while True:
        t = time.perf_counter() - t0
        if t > DUR:
            break
        m = be.read()
        th = float(m.theta); thd = float(m.theta_dot or 0.0); psi = float(m.psi)
        u_p = float(np.clip(KpP * (0.0 - th) - KdP * thd, -VLIM, VLIM))  # hold pitch = 0
        be.apply(np.array([u_p, sign * V]))                             # sustained yaw push
        rows.append((t, psi, th, u_p))
        hist.append((t, psi))
        while hist and hist[0][0] < t - 2.0:
            hist.pop(0)
        if t > 3.0 and abs(psi - hist[0][1]) < np.deg2rad(2.0):
            print(f"  yaw plateau at {np.rad2deg(psi):+.1f} deg (pitch held {np.rad2deg(th):+.1f})", flush=True)
            break
        nextT += 1.0 / HZ
        while time.perf_counter() < nextT and (time.perf_counter() - t0) <= DUR:
            pass
    be.apply(np.zeros(2)); time.sleep(0.3)
    ps = np.array([r[1] for r in rows]); pit = np.array([r[2] for r in rows])
    return rows, float(np.rad2deg(ps.max())), float(np.rad2deg(ps.min())), \
        float(np.rad2deg(ps[-1])), float(np.rad2deg(np.mean(np.abs(pit))))


print(f"=== yaw-MAX with pitch held horizontal, yaw={V} V ===", flush=True)
be = HardwareBackend(aero_id="0", frequency=HZ, output_mode="mixed", voltage_limit=VLIM, quanser_python=QPY)
try:
    r1, mx1, _, end1, ph1 = push(be, +1)
    print(f"  +yaw: max={mx1:+.1f} deg (end {end1:+.1f}) | avg|pitch|={ph1:.1f} deg", flush=True)
    time.sleep(0.5)
    r2, _, mn2, end2, ph2 = push(be, -1)
    print(f"  -yaw: min={mn2:+.1f} deg (end {end2:+.1f}) | avg|pitch|={ph2:.1f} deg", flush=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(OUT, f"yaw_max_pitchheld_{stamp}.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["dir", "t", "psi_deg", "theta_deg", "u_pitch"])
        for tag, rr in (("+", r1), ("-", r2)):
            for t, psi, th, up in rr:
                w.writerow([tag, round(t, 4), round(np.rad2deg(psi), 2), round(np.rad2deg(th), 2), round(up, 2)])
    print(f"  YAW MAX RANGE (pitch-held): {mn2:+.1f} .. {mx1:+.1f} deg (span {mx1 - mn2:.1f} deg)", flush=True)
finally:
    be.close()
print("YAW_MAX_DONE", flush=True)
