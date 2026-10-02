"""Motor-position identification for the Aero2 2DOF config (pitch/yaw).

Low-voltage open-loop excitation on a chosen backend (virtual_twin or hardware):
  - collective (both rotors same sign) -> should drive PITCH
  - differential (rotors opposite)     -> should drive YAW
  - motor0 / motor1 alone              -> front/rear rotor identity
Reports the pitch/yaw angular range for each, to identify + verify the motor map
and compare digital-twin vs hardware.

Usage: python run_motor_id.py [twin|hardware] [volts]
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

import numpy as np  # noqa: E402
from aero2.execution.virtual_twin import VirtualTwinBackend  # noqa: E402
from aero2.execution.hardware import HardwareBackend  # noqa: E402

KIND = sys.argv[1] if len(sys.argv) > 1 else "twin"
VOLTS = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0

# (label, output_mode, virtual command axis)
TESTS = [
    ("collective->pitch", "mixed", np.array([1.0, 0.0])),
    ("differential->yaw", "mixed", np.array([0.0, 1.0])),
    ("motor0 (front?)", "direct", np.array([1.0, 0.0])),
    ("motor1 (rear?)", "direct", np.array([0.0, 1.0])),
]


def make_backend(kind):
    cls = HardwareBackend if kind == "hardware" else VirtualTwinBackend
    return cls(aero_id="0", frequency=200.0, output_mode="mixed",
              voltage_limit=15.0, quanser_python=QPY)


def run_test(be, output_mode, axis, volts, dur=3.0, hz=200.0):
    be.output_mode = output_mode
    be.reset(np.zeros(4))
    be.apply(np.zeros(2)); be.read()             # warm-up throwaway
    th, ps = [], []
    t0 = time.perf_counter(); nextT = t0
    while True:
        t = time.perf_counter() - t0
        if t > dur:
            break
        u = axis * (volts if (0.5 < t < dur - 0.5) else 0.0)   # centered pulse
        be.apply(u)
        m = be.read()
        th.append(m.theta); ps.append(m.psi)
        nextT += 1.0 / hz
        while time.perf_counter() < nextT and (time.perf_counter() - t0) <= dur:
            pass
    be.apply(np.zeros(2)); time.sleep(0.2)
    th, ps = np.array(th), np.array(ps)
    return float(np.rad2deg(th.max() - th.min())), float(np.rad2deg(ps.max() - ps.min()))


print(f"=== Motor-ID on {KIND} at {VOLTS} V (open loop, 2DOF) ===", flush=True)
be = make_backend(KIND)
try:
    for label, om, axis in TESTS:
        dp, dy = run_test(be, om, axis, VOLTS)
        dom = "PITCH" if dp > dy else "YAW"
        print(f"  {label:>20}: pitch_range={dp:6.1f} deg  yaw_range={dy:6.1f} deg  -> {dom}-dominant", flush=True)
finally:
    be.close()
print(f"MOTOR_ID_DONE ({KIND})", flush=True)
