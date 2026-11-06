"""Generate the ArduPilot 6DoF Lua mixer (FRAME_CLASS 16) from the MuJoCo twin.

The 6x8 wrench matrix is taken from the canonical XML through control/hover.py,
so the mixer uses the same verified rotor frames and COM moment arms as the
simulation controller.  Nothing is hand-copied.

ArduPilot conventions (AP_MotorsMatrix_6DoF_Scripting.cpp):
  * body frame is FRD: x forward, y right, z down;
  * per-motor normalized thrust t_i in [-1, 1] (1 = full forward thrust);
  * t_i = roll*R_i + pitch*P_i + yaw*Y_i + throttle*T_i + forward*F_i + right*L_i
    where throttle is UP force, roll/pitch/yaw are torques about +x/+y/+z (FRD);
  * forward/right are multiplied by throttle in the mixer, so throttle, forward
    and right factors must share one force scale (enforced here).

The AP body frame is defined as level at the twin's hover attitude (the XML
initial pose), with "forward" along a chosen world axis.  The Cube's physical
mounting relative to that frame is a separate calibration (AHRS_ORIENTATION).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]          # omnicopter
sys.path.insert(0, str(ROOT / "twin" / "control"))
from hover import XML, make_sim  # noqa: E402  (canonical model + verified B matrix)

AXES = ("roll", "pitch", "yaw", "throttle", "forward", "right")
WORLD_AXES = {"x": (1, 0, 0), "-x": (-1, 0, 0), "y": (0, 1, 0), "-y": (0, -1, 0)}


def ap_frame_in_body(world_from_body, world_forward):
    """Rows: AP forward, right, down axes expressed in MuJoCo body coordinates."""
    forward = np.asarray(world_forward, float)
    down = np.array([0.0, 0.0, -1.0])
    right = np.cross(down, forward)
    world_rows = np.vstack([forward, right, down])            # FRD axes in world
    return world_rows @ world_from_body                        # = (R^T v)^T per row


def effectiveness(matrix_body, ap_from_body):
    """6x8 map from rotor thrust [N] to AP inputs order (tau_x, tau_y, tau_z, F_up, F_fwd, F_right)."""
    force = ap_from_body @ matrix_body[:3]
    torque = ap_from_body @ matrix_body[3:]
    return np.vstack([torque[0], torque[1], torque[2], -force[2], force[0], force[1]])


def mujoco_check(model, data, controls_by_axis, world_from_body, ap_rows_world, tmax, inertia_body):
    """Apply each mixer column through MuJoCo's actuator pipeline with gravity off.

    Force columns must accelerate the COM along the matching world axis with no
    angular acceleration; torque columns must produce a COM torque (J*alpha at
    zero rate) about the matching body axis with no COM acceleration.  Torque,
    not alpha, is checked because the inertia is not exactly isotropic.
    Returns the off-axis ratio per column.
    """
    saved_gravity = model.opt.gravity.copy()
    model.opt.gravity[:] = 0
    bid = model.body("drone").id
    com = model.body_ipos[bid]
    report = {}
    try:
        for k, axis in enumerate(AXES):
            # Probe below actuator saturation (forward/right factors can exceed 1), then
            # report the response per unit AP input.
            probe = 0.5 / max(1.0, float(np.max(np.abs(controls_by_axis[:, k]))))
            mujoco.mj_resetData(model, data)
            data.ctrl[:] = probe * tmax * controls_by_axis[:, k]
            mujoco.mj_forward(model, data)
            alpha_body = data.qacc[3:6].copy()
            alpha_world = world_from_body @ alpha_body
            torque_world = world_from_body @ (inertia_body @ alpha_body)
            accel_com = data.qacc[:3] + world_from_body @ np.cross(alpha_body, com)
            if k < 3:   # torque about AP body x/y/z == ap_rows_world[k] in world
                wanted, unwanted = torque_world, accel_com
                direction = ap_rows_world[k]
            else:       # throttle=up, forward, right
                wanted, unwanted = accel_com, alpha_world
                direction = {3: -ap_rows_world[2], 4: ap_rows_world[0], 5: ap_rows_world[1]}[k]
            along = float(wanted @ direction)
            off = float(np.linalg.norm(wanted - along * direction) + np.linalg.norm(unwanted))
            report[axis] = {"along_axis_per_unit_input": along / probe, "off_axis_ratio": off / abs(along)}
    finally:
        model.opt.gravity[:] = saved_gravity
        mujoco.mj_resetData(model, data)
        mujoco.mj_forward(model, data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world-forward", choices=WORLD_AXES, default="x",
                        help="World axis that ArduPilot calls 'forward' at the hover attitude (default x)")
    parser.add_argument("--motor-map", default="1,2,3,4,5,6,7,8",
                        help="Twin rotor number driven by ArduPilot Motor1..Motor8 (SERVOn_FUNCTION 33..40). "
                             "Confirm on hardware before flight.")
    parser.add_argument("--tmax-n", type=float,
                        help="Full-command thrust per rotor [N] used only for the printed physical scales "
                             "(default: XML ctrlrange upper bound, unverified)")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "generated")
    args = parser.parse_args()

    motor_map = [int(v) for v in args.motor_map.split(",")]
    if sorted(motor_map) != list(range(1, 9)):
        parser.error("--motor-map must be a permutation of 1..8")

    model, data, controller = make_sim()
    bid = model.body("drone").id
    world_from_body = data.xmat[bid].reshape(3, 3).copy()
    tmax = args.tmax_n if args.tmax_n else float(model.actuator_ctrlrange[0, 1])

    ap_from_body = ap_frame_in_body(world_from_body, WORLD_AXES[args.world_forward])
    ap_rows_world = ap_from_body @ world_from_body.T           # FRD axes in world
    if not np.isclose(np.linalg.det(ap_from_body), 1.0):
        raise RuntimeError("AP frame is not right-handed")

    a = effectiveness(controller.matrix, ap_from_body)         # 6x8, N or N*m per N of rotor thrust
    if np.linalg.matrix_rank(a) != 6:
        raise RuntimeError("Wrench map is not rank six")
    pinv = np.linalg.pinv(a)                                   # 8x6, N of rotor thrust per unit wrench

    # Torque: one common scale keeps roll/pitch/yaw physically equal (same gains per axis).
    torque_scale = 1.0 / np.max(np.abs(pinv[:, :3]))
    # Force: one common scale for throttle/forward/right (the AP mixer multiplies forward/right
    # by throttle).  Normalized on the throttle column, as on a normal copter: throttle 1.0 drives
    # the most-loaded motor to full thrust.  Forward/right factors may then exceed 1; the AP mixer
    # scales horizontal demand back (horz_ratio) when motors saturate.
    force_scale = 1.0 / np.max(np.abs(pinv[:, 3]))
    factors = pinv.copy()                                      # rows = twin rotors 1..8
    factors[:, :3] *= torque_scale
    factors[:, 3:] *= force_scale

    # Per unit AP input, the rotor thrust is t*tmax, giving these physical wrenches:
    newton_per_throttle = force_scale * tmax
    nm_per_rpy = torque_scale * tmax
    mass = float(model.body_mass[bid])
    hover_throttle = mass * 9.81 / newton_per_throttle
    check = mujoco_check(model, data, factors, world_from_body, ap_rows_world, tmax, controller.inertia)
    worst = max(v["off_axis_ratio"] for v in check.values())

    xml_hash = hashlib.sha256(Path(XML).read_bytes()).hexdigest()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    args.output.mkdir(parents=True, exist_ok=True)

    lines = [
        "-- Omnidrone 6DoF mixer for ArduPilot Copter (FRAME_CLASS 16, SCR_ENABLE 1)",
        f"-- Generated {stamp} by omnicopter/flight/make_6dof_mixer.py",
        f"-- Twin XML sha256 {xml_hash}",
        f"-- AP forward = world {args.world_forward} at the twin hover attitude; FRD axes in MuJoCo body coords:",
        *[f"--   {n:7s} = ({r[0]: .6f}, {r[1]: .6f}, {r[2]: .6f})" for n, r in zip(("forward", "right", "down"), ap_from_body)],
        "-- Motor map: ArduPilot MotorK (SERVO function 32+K) -> twin rotor_N. CONFIRM ON HARDWARE.",
        "-- Reversible motors: ESCs must run bidirectional/3D (1500 us = stop). MOT_YAW_HEADROOM/1000 sets",
        "-- the reversal deadzone (capped at 0.25) in this mixer.",
        f"-- Physical scale at Tmax={tmax:.3f} N/rotor: throttle 1.0 = {newton_per_throttle:.3f} N up; "
        f"roll/pitch/yaw 1.0 = {nm_per_rpy:.4f} N*m",
        f"-- Twin hover throttle estimate (mass {mass:.3f} kg, unverified): {hover_throttle:.3f}",
        "--                         Roll        Pitch       Yaw         Throttle    Forward     Right     Rev  Order",
    ]
    for k, rotor in enumerate(motor_map):
        f = factors[rotor - 1]
        lines.append(f"Motors_6DoF:add_motor({k}, " + ", ".join(f"{v: .6f}" for v in f)
                     + f", true, {k + 1})  -- Motor{k + 1} = twin rotor_{rotor}")
    lines += [
        "",
        "assert(Motors_6DoF:init(8), 'unable to setup 8 motors')",
        "",
        "-- First flights: translate by tilting like a normal copter (standard position-controller",
        "-- assumptions). Switch both to true later for attitude-independent translation.",
        "attitude_control:set_forward_enable(false)",
        "attitude_control:set_lateral_enable(false)",
        "",
        'motors:set_frame_string("Omnidrone 6DoF (twin-derived)")',
        'gcs:send_text(6, "Omnidrone 6DoF mixer loaded")',
        "",
    ]
    lua = args.output / "omnidrone_6dof_mixer.lua"
    lua.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "generated_utc": stamp, "twin_xml": XML.relative_to(ROOT).as_posix(), "twin_xml_sha256": xml_hash,
        "mujoco_version": mujoco.__version__, "world_forward": args.world_forward,
        "ap_frd_axes_in_mujoco_body": ap_from_body.tolist(),
        "motor_map_ap_motor_to_twin_rotor": {f"Motor{k + 1}": r for k, r in enumerate(motor_map)},
        "factor_columns": list(AXES),
        "factors_by_ap_motor": {f"Motor{k + 1}": factors[r - 1].tolist() for k, r in enumerate(motor_map)},
        "tmax_N_assumed": tmax, "tmax_status": "XML ctrlrange, unverified" if not args.tmax_n else "user supplied",
        "newton_up_per_unit_throttle": newton_per_throttle, "newton_m_per_unit_rpy": nm_per_rpy,
        "twin_mass_kg": mass, "hover_throttle_estimate": hover_throttle,
        "mujoco_pure_axis_check": check, "worst_off_axis_ratio": worst,
    }
    (args.output / "omnidrone_6dof_mixer.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(lua.read_text(encoding="utf-8"))
    print("MuJoCo pure-axis check (gravity off, each column applied through data.ctrl):")
    for axis, v in check.items():
        unit = "N*m" if axis in AXES[:3] else "m/s^2"
        print(f"  {axis:8s} per unit input={v['along_axis_per_unit_input']: .4f} {unit:5s}"
              f"  off-axis ratio={v['off_axis_ratio']:.2e}")
    status = "PASS" if worst < 1e-6 else "FAIL"
    print(f"Mixer decoupling: {status} (worst off-axis ratio {worst:.2e})")
    print(f"Wrote {lua}")
    if status != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
