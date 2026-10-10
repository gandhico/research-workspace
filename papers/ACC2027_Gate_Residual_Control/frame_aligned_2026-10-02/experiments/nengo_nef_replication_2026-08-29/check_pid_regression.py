"""Gate for the rebuilt run_mujoco_nef_pid.py. Exits non-zero on any mismatch.

  1. defaults on two Table V PD cells   -> must equal the stored values bit-for-bit
  2. --ki-factor 0.05 on one cell       -> must equal the earlier tuning run bit-for-bit
     (proves the new options did not change the torque-anti-windup PID path)
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
RES = HERE / "results"

CASES = [
    ("x2", "roll", "1.0", [],
     RES / "matched_45s/x2_roll_classical/summary.json"),
    ("cf2-rotor", "hardstep", "1.5", [],
     RES / "matched_45s/cf2_rotor_hardstep_classical/summary.json"),
    ("x2", "roll", "1.0", ["--ki-factor", "0.05"],
     RES / "pid_baseline_2026-09-10/tune/ki0.05/x2_roll_classical/summary.json"),
]

ok = True
with tempfile.TemporaryDirectory() as tmp:
    for k, (plat, mis, scale, extra, ref) in enumerate(CASES):
        out = Path(tmp) / f"c{k}"
        cmd = [PY, str(HERE / "run_mujoco_nef_pid.py"),
               "--platform", plat, "--controller", "classical", "--mission", mis,
               "--duration", "45", "--dt", "0.0005", "--beta", "0.5",
               "--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0",
               "--actuator-scale", scale, "--log-every", "10",
               "--no-neural-archive", "--output", str(out), *extra]
        subprocess.run(cmd, check=True, capture_output=True)
        a = json.loads(ref.read_text())["qerr_mean_rad"]
        b = json.loads((out / "summary.json").read_text())["qerr_mean_rad"]
        same = a == b
        ok &= same
        print(f"  {plat:10s}{mis:10s}{' '.join(extra) or 'defaults':18s}"
              f"{a:.17f}  {b:.17f}  {'exact' if same else 'MISMATCH'}")
print("regression", "PASSED" if ok else "FAILED")
sys.exit(0 if ok else 1)
