"""Measure the Aero2 MECHANICAL pitch range (hard stops) with the motors OFF.

Reads the pitch encoder live while YOU gently tilt the body by hand to each stop.
The encoder is incremental (zeroed at connect), so start with the body at a known
pose (e.g. horizontal) and the printed min/max are the down/up stops about that zero.

    theta = 360 * counts / 2880   (handled internally; printed in degrees)

USAGE (in the lab, Aero2 connected, QUARC installed):
    python measure_pitch_range.py
  1) let the script connect (body wherever it rests),
  2) SLOWLY rotate the pitch body fully DOWN to its stop, then fully UP to its stop,
  3) Ctrl-C -> it prints the total mechanical range and the two stop angles.

Safe: voltage_limit=0 and a zero command every cycle, so the motors never drive.
"""
import os, sys
REPO = r"C:\Research\aero2"
QPY  = r"C:\Users\gandhico\Documents\Quanser\0_libraries\python"
os.environ.setdefault("QUANSER_PYTHON", QPY)
sys.path.insert(0, REPO); sys.path.insert(0, QPY)
import numpy as np
from aero2.execution.hardware import HardwareBackend

d2r = 180.0 / np.pi
be = HardwareBackend(aero_id="0", frequency=100.0, output_mode="mixed",
                     voltage_limit=0.0, quanser_python=QPY)   # 0 V -> motors never drive
be.reset(np.zeros(4))
print("Motors OFF. Slowly tilt the PITCH body to BOTH hard stops. Ctrl-C when done.\n")
tmin = tmax = 0.0
try:
    while True:
        be.apply(np.zeros(2))                 # command 0 V every cycle (safety)
        th = float(be.read().theta) * d2r
        tmin = min(tmin, th); tmax = max(tmax, th)
        print(f"\rpitch = {th:+7.2f} deg    down-stop {tmin:+7.2f}    up-stop {tmax:+7.2f}    "
              f"RANGE = {tmax - tmin:6.2f} deg", end="", flush=True)
except KeyboardInterrupt:
    print(f"\n\n=== MECHANICAL PITCH RANGE = {tmax - tmin:.1f} deg "
          f"(from {tmin:.1f} deg to {tmax:.1f} deg about the connect pose) ===")
finally:
    be.close()
