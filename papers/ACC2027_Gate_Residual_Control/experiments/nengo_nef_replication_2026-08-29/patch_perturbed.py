"""Add an intermittent disturbance schedule to run_mujoco_nef_perturbed.py.

The canonical runner applies a continuous multi-sine body torque that is
never silent. For a hold-equilibrium study we want bursts separated by quiet
intervals, so the controller is seen entering a disturbance, adapting inside
it, and -- the interesting part -- being left holding a decoder that was
learned under a disturbance which has just stopped.

run_mujoco_nef.py itself is NOT touched: it is hashed in the frozen audit and
produced the reported results.
"""
from __future__ import annotations

import io

DST = "run_mujoco_nef_perturbed.py"
s = io.open(DST, encoding="utf-8").read()
n = 0


def sub(old: str, new: str, tag: str) -> None:
    global s, n
    if s.count(old) != 1:
        raise SystemExit(f"FAILED [{tag}]: found {s.count(old)}, expected 1")
    s = s.replace(old, new, 1)
    n += 1
    print(f"  ok  {tag}")


# --- header note (prepended, docstring left intact) ---------------------------
HEADER = "\n".join([
    "# Variant of run_mujoco_nef.py adding an intermittent disturbance",
    "# schedule. With --disturbance-schedule continuous (the default) the",
    "# behaviour is identical to the canonical runner.",
    "",
])
if not s.startswith(HEADER):
    s = HEADER + s
    n += 1
    print("  ok  header")

# --- gating helper -----------------------------------------------------------
sub("""def _build_augmentor(name, limits, dt, beta, learning_rate, seed):""",
    '''def disturbance_gain(t: float, args) -> float:
    """Scale on the disturbance torque at time ``t``.

    ``continuous``   always 1.0 (canonical behaviour).
    ``intermittent`` 0.0 for the first ``--disturbance-warmup`` seconds, then
                     alternating ON for ``--disturbance-on`` and OFF for
                     ``--disturbance-off``. Each edge is smoothed over
                     ``--disturbance-ramp`` seconds with a raised cosine so
                     the plant sees a finite slew rather than an impulse.
    """
    if args.disturbance_schedule == "continuous":
        return 1.0

    warm = args.disturbance_warmup
    if t < warm:
        return 0.0

    period = args.disturbance_on + args.disturbance_off
    phase = (t - warm) % period
    ramp = max(args.disturbance_ramp, 1e-9)

    if phase < args.disturbance_on:
        # rising edge at phase 0, falling edge at phase = on
        if phase < ramp:
            return 0.5 * (1.0 - np.cos(np.pi * phase / ramp))
        if phase > args.disturbance_on - ramp:
            x = (args.disturbance_on - phase) / ramp
            return 0.5 * (1.0 - np.cos(np.pi * x))
        return 1.0
    return 0.0


def _build_augmentor(name, limits, dt, beta, learning_rate, seed):''',
    "gain-helper")

# --- apply the gate in the loop ---------------------------------------------
sub("""            if args.disturbance_torque > 0:
                disturbance_body = args.disturbance_torque * np.array(
                    [
                        np.sin(1.31 * t + 0.2),
                        0.8 * np.sin(1.73 * t + 1.1),
                        0.6 * np.sin(2.17 * t + 2.0),
                    ]
                )
                data.xfrc_applied[body_id, 3:6] = R @ disturbance_body""",
    """            disturbance_scale = disturbance_gain(t, args)
            if args.disturbance_torque > 0 and disturbance_scale > 0.0:
                disturbance_body = (
                    args.disturbance_torque * disturbance_scale * np.array(
                        [
                            np.sin(1.31 * t + 0.2),
                            0.8 * np.sin(1.73 * t + 1.1),
                            0.6 * np.sin(2.17 * t + 2.0),
                        ]
                    )
                )
                data.xfrc_applied[body_id, 3:6] = R @ disturbance_body""",
    "apply-gate")

# --- record the schedule in the summary --------------------------------------
sub('        "disturbance_torque_Nm": args.disturbance_torque,',
    '''        "disturbance_torque_Nm": args.disturbance_torque,
        "disturbance_schedule": args.disturbance_schedule,
        "disturbance_warmup_s": args.disturbance_warmup,
        "disturbance_on_s": args.disturbance_on,
        "disturbance_off_s": args.disturbance_off,
        "disturbance_ramp_s": args.disturbance_ramp,''',
    "summary-fields")

# --- CLI ---------------------------------------------------------------------
sub('    p.add_argument("--disturbance-torque", type=float, default=0.0)',
    '''    p.add_argument("--disturbance-torque", type=float, default=0.0)
    p.add_argument(
        "--disturbance-schedule",
        choices=("continuous", "intermittent"),
        default="continuous",
        help="continuous reproduces run_mujoco_nef.py exactly.",
    )
    p.add_argument("--disturbance-warmup", type=float, default=5.0,
                   help="Quiet interval before the first burst [s].")
    p.add_argument("--disturbance-on", type=float, default=5.0,
                   help="Burst duration [s].")
    p.add_argument("--disturbance-off", type=float, default=5.0,
                   help="Quiet duration between bursts [s].")
    p.add_argument("--disturbance-ramp", type=float, default=0.25,
                   help="Raised-cosine edge smoothing [s].")''',
    "cli")

io.open(DST, "w", encoding="utf-8").write(s)
print(f"\npatched {DST} ({n} changes)")

import py_compile
py_compile.compile(DST, doraise=True)
print("compiles cleanly")
