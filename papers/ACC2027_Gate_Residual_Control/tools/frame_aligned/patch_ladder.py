"""Frame-aligned patch, site 5: the rho = 1 PD/PID+ff ladder law (run_mujoco_nef_pid.py, used by select_rate_ff.py and
run_ff_cmg.py -> Table II middle block). Applied to the sandbox copy only, with exact-match assertions.
    .venv\Scripts\python.exe tools\frame_aligned\patch_ladder.py
"""
from pathlib import Path

from build_sandbox import ROT, SB, patch

f = SB / "experiments" / "nengo_nef_replication_2026-08-29" / "run_mujoco_nef_pid.py"
patch(f, [
    ("\n\ndef _build_augmentor(", ROT + "\n\ndef _build_augmentor("),
    ("                tau0_unsat = -kq * eq - kw * (omega - omega_d) - ki * eq_integral\n",
     "                tau0_unsat = -kq * eq - kw * (omega - _rotT(qe) @ omega_d) - ki * eq_integral   # FRAME-ALIGNED\n"),
])
print("patched", f)
