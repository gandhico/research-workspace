"""Create run_6dof_cascade_ff.py: the Option A cascade plus outer-loop
flatness feedforward. run_6dof_cascade.py itself is NOT modified.

The inner attitude loop already damps the rate error omega - omega_des. The
outer position loop does not: F0 = m g e_z - kp (p - p_ref) - kd v damps
absolute velocity, with no velocity or acceleration reference. On a moving
position reference (circle_xy, full6_stress) that leaves a velocity lag,
exactly the gap found in the attitude-only PD on 2026-09-10.

  --pos-ff none   (default)  canonical law, byte-identical expression
  --pos-ff fd                F0 = m (g e_z + a_ref) - kp (p - p_ref)
                                  - kd (v - v_ref) - ki * integral

v_ref, a_ref are central finite differences of position_reference. A mission
with jump discontinuities (waypoint_step) would feed an impulse forward on the
one sample that straddles a jump; such samples get zero feedforward, which is
what a flatness-based design does with a non-differentiable reference.

Run:  python patch_6dof_ff.py
"""
from __future__ import annotations

import io
import py_compile
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "run_6dof_cascade.py"
DST = HERE / "run_6dof_cascade_ff.py"

shutil.copyfile(SRC, DST)
s = io.open(DST, encoding="utf-8").read()
n = 0


def sub(old: str, new: str, tag: str) -> None:
    global s, n
    c = s.count(old)
    if c != 1:
        raise SystemExit(f"FAILED [{tag}]: found {c}, expected 1")
    s = s.replace(old, new, 1)
    n += 1
    print(f"  ok  {tag}")


s = "\n".join([
    "# Outer-loop feedforward variant of run_6dof_cascade.py (patch_6dof_ff.py).",
    "# --pos-ff none (default) reproduces the canonical cascade exactly.",
    "",
]) + s

sub("def rotmat_to_quat(R: np.ndarray) -> np.ndarray:",
    '''def position_rates(t: float, mission: str, duration: float,
                   h: float = 1e-4, v_max: float = 20.0, a_max: float = 50.0):
    """Reference velocity and acceleration by central differences of
    position_reference. A sample straddling a jump in the reference gives an
    impulse (|v| > v_max or |a| > a_max); it gets zero feedforward instead."""
    t0 = max(t - h, 0.0)
    pm = position_reference(t0, mission, duration)
    p0 = position_reference(t, mission, duration)
    pp = position_reference(t + h, mission, duration)
    v = (pp - pm) / ((t + h) - t0)
    a = (pp - 2.0 * p0 + pm) / (h * h) if t >= h else np.zeros(3)
    if (np.linalg.norm(v) > v_max or np.linalg.norm(a) > a_max
            or not np.all(np.isfinite(a))):
        return np.zeros(3), np.zeros(3)
    return v, a


def rotmat_to_quat(R: np.ndarray) -> np.ndarray:''',
    "position-rates")

sub("        actuator_scale: float = 1.0, authority_scale: float = 1.0) -> dict:",
    "        actuator_scale: float = 1.0, authority_scale: float = 1.0,\n"
    "        pos_ff: str = \"none\") -> dict:",
    "signature")

sub("""        F0 = np.clip(mass*gravity*np.array([0, 0, 1])-kp_pos*(p-p_ref)-kd_pos*v-ki_pos*pos_integral,
                     -force_limits, force_limits)
""",
    """        if pos_ff == "none":
            # Canonical outer law, byte-identical expression.
            F0 = np.clip(mass*gravity*np.array([0, 0, 1])-kp_pos*(p-p_ref)-kd_pos*v-ki_pos*pos_integral,
                         -force_limits, force_limits)
        else:
            v_ref, a_ref = position_rates(t, mission, duration)
            F0 = np.clip(mass*(gravity*np.array([0, 0, 1])+a_ref)-kp_pos*(p-p_ref)
                         -kd_pos*(v-v_ref)-ki_pos*pos_integral,
                         -force_limits, force_limits)
""",
    "outer-law")

sub('        "qerr_max_rad": float(qerr.max()),\n',
    '        "qerr_max_rad": float(qerr.max()),\n'
    '        "pos_ff": pos_ff, "actuator_scale": actuator_scale,\n'
    '        "authority_scale": authority_scale,\n',
    "summary")

sub('    p.add_argument("--authority-scale", type=float, default=1.0)\n',
    '    p.add_argument("--authority-scale", type=float, default=1.0)\n'
    '    p.add_argument("--pos-ff", choices=("none", "fd"), default="none",\n'
    '                   help="Outer-loop velocity/acceleration feedforward.")\n',
    "cli")

sub("            a.platform, a.wn_att, a.wn_pos, a.ki_pos, a.ki_att, a.actuator_scale, a.authority_scale)",
    "            a.platform, a.wn_att, a.wn_pos, a.ki_pos, a.ki_att, a.actuator_scale, a.authority_scale,\n"
    "            a.pos_ff)",
    "call")

io.open(DST, "w", encoding="utf-8").write(s)
py_compile.compile(str(DST), doraise=True)
print(f"\nwrote {DST.name} ({n} changes), compiles cleanly")
