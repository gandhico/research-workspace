"""Create run_mujoco_nef_pid.py: the canonical runner plus baseline options.

run_mujoco_nef.py is NOT modified -- it is hashed in the frozen audit and
produced Table V. This writes a copy and adds three baseline options:

  --ki-factor F        integral gain ki = F * kq per axis   (default 0)
  --antiwindup MODE    torque | rotor                        (default torque)
  --rate-ff MODE       none | left | right | left-neg | right-neg
                                                             (default none)

Integral gain is scaled by kq rather than given absolutely: kq = 2 J wn^2
depends on inertia, and the airframes differ in inertia by about three orders
of magnitude, so one absolute ki cannot be fair to both.

Anti-windup is conditional integration. "torque" freezes an axis while the
baseline torque box clips it. "rotor" additionally freezes all axes while any
rotor command sat at its ctrl_range bound on the previous step. The rotor
bound, after allocation, is where saturation actually binds in this runner;
the torque box alone can miss it.

Rate feedforward replaces the damping term -kw*omega by -kw*(omega - omega_d),
the rate error of the paper's eq. (6). omega_d comes from a central finite
difference of reference_quat. Frame (left/right product) and sign are left as
explicit modes because this codebase uses a passive quaternion convention and
a silent convention mismatch has broken a controller here before; the correct
mode is selected empirically by select_rate_ff.py.

With all three at their defaults the torque is the canonical expression, so
every Table V PD number reproduces bit-for-bit. Existing PID results (torque
anti-windup, no feedforward) also reproduce, since omega - 0.0 == omega
exactly in IEEE arithmetic.

Run:  python patch_pid.py
"""
from __future__ import annotations

import io
import py_compile
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "run_mujoco_nef.py"
DST = HERE / "run_mujoco_nef_pid.py"

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


# --- header -------------------------------------------------------------------
s = "\n".join([
    "# PID / rate-feedforward variant of run_mujoco_nef.py (patch_pid.py).",
    "# Defaults reproduce the canonical PD runner exactly.",
    "",
]) + s
n += 1
print("  ok  header")

# --- reference rate by finite difference ---------------------------------------
sub("def _build_augmentor(name, limits, dt, beta, learning_rate, seed):",
    '''def reference_rate(t, mission, duration, mode, h=1e-4):
    """Reference angular rate from a central difference of reference_quat.

    'left'  uses vec(q(t+h) q(t-h)^-1); 'right' uses vec(q(t-h)^-1 q(t+h));
    the '-neg' variants flip the sign. Which one matches this codebase's
    passive convention is decided empirically by select_rate_ff.py.
    """
    t0 = max(t - h, 0.0)
    qa = reference_quat(t0, mission, duration)
    qb = reference_quat(t + h, mission, duration)
    base = mode.replace("-neg", "")
    if base == "left":
        dq = quat_mul(qb, quat_conj(qa))
    else:
        dq = quat_mul(quat_conj(qa), qb)
    if dq[0] < 0.0:
        dq = -dq
    w = 2.0 * dq[1:] / ((t + h) - t0)
    return -w if mode.endswith("-neg") else w


def _build_augmentor(name, limits, dt, beta, learning_rate, seed):''',
    "reference-rate")

# --- gains and accumulators ----------------------------------------------------
sub("    kw = 2.0 * 0.95 * wn * inertia\n",
    "    kw = 2.0 * 0.95 * wn * inertia\n"
    "    # Integral action, scaled per axis by kq so one factor is fair to both\n"
    "    # airframes. ki_factor = 0 makes the integral term identically zero.\n"
    "    ki = args.ki_factor * kq\n"
    "    eq_integral = np.zeros(3)\n"
    "    integral_frozen_steps = np.zeros(3, dtype=int)\n"
    "    rotor_sat_prev = False\n",
    "ki-definition")

# --- baseline torque law -------------------------------------------------------
sub("            tau0 = np.clip(-kq * eq - kw * omega, -limits, limits)\n",
    "            if args.ki_factor == 0.0 and args.rate_ff == 'none':\n"
    "                # Canonical PD, byte-identical expression.\n"
    "                tau0 = np.clip(-kq * eq - kw * omega, -limits, limits)\n"
    "            else:\n"
    "                if args.rate_ff == 'none':\n"
    "                    omega_d = np.zeros(3)\n"
    "                else:\n"
    "                    omega_d = reference_rate(t, args.mission, args.duration,\n"
    "                                             args.rate_ff)\n"
    "                tau0_unsat = -kq * eq - kw * (omega - omega_d) - ki * eq_integral\n"
    "                tau0 = np.clip(tau0_unsat, -limits, limits)\n"
    "                if args.ki_factor > 0.0:\n"
    "                    # Conditional-integration anti-windup.\n"
    "                    free = np.isclose(tau0, tau0_unsat, rtol=0.0, atol=1e-12)\n"
    "                    if args.antiwindup == 'rotor' and rotor_sat_prev:\n"
    "                        free = np.zeros(3, dtype=bool)\n"
    "                    eq_integral += np.where(free, eq, 0.0) * args.dt\n"
    "                    integral_frozen_steps += (~free).astype(int)\n",
    "baseline-law")

# --- remember rotor saturation for the next step's anti-windup ----------------
sub("            qerr_value = quat_angle(qe)\n",
    "            rotor_sat_prev = saturated\n"
    "            qerr_value = quat_angle(qe)\n",
    "rotor-sat-memory")

# --- summary ------------------------------------------------------------------
sub('        "seed": args.seed,\n',
    '        "seed": args.seed,\n'
    '        "ki_factor": args.ki_factor,\n'
    '        "ki": [float(v) for v in ki],\n'
    '        "antiwindup": args.antiwindup,\n'
    '        "rate_ff": args.rate_ff,\n'
    '        "baseline": ("PD" if args.ki_factor == 0.0 else "PID")\n'
    '                    + ("" if args.rate_ff == "none" else "+ff"),\n'
    '        "integral_final": [float(v) for v in eq_integral],\n'
    '        "integral_frozen_fraction": [\n'
    '            float(v) / max(step_index, 1) for v in integral_frozen_steps\n'
    '        ],\n',
    "summary-fields")

# --- CLI ----------------------------------------------------------------------
sub('    p.add_argument("--seed", type=int, default=1)\n',
    '    p.add_argument("--seed", type=int, default=1)\n'
    '    p.add_argument("--ki-factor", type=float, default=0.0,\n'
    '                   help="Integral gain as a multiple of kq, per axis. 0 = PD.")\n'
    '    p.add_argument("--antiwindup", choices=("torque", "rotor"),\n'
    '                   default="torque",\n'
    '                   help="Freeze integration on torque-box clip only, or also "\n'
    '                        "while any rotor was at its bound last step.")\n'
    '    p.add_argument("--rate-ff",\n'
    '                   choices=("none", "left", "right", "left-neg", "right-neg"),\n'
    '                   default="none",\n'
    '                   help="Damp omega - omega_d instead of omega.")\n',
    "cli")

io.open(DST, "w", encoding="utf-8").write(s)
py_compile.compile(str(DST), doraise=True)
print(f"\nwrote {DST.name} ({n} changes), compiles cleanly")
