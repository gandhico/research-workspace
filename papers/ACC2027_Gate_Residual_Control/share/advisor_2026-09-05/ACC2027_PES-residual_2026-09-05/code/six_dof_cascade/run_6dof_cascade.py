"""Option A: realistic underactuated 6-DOF CMG-PES on X2 -- position PD
decomposed into desired thrust + attitude (standard differential-flatness
quadrotor control), inner quaternion-PD attitude loop, real rotor mixer.
Closer to hardware than Option B: real 4-actuator authority, real
saturation, no assumption of independently-commandable lateral force.

CMG-PES still spans 6 channels (3 position, 3 attitude) via the same
unmodified CMGResidualAugmentor(channels=6) -- the position-residual
corrects the desired-thrust/attitude command, the attitude-residual
corrects body torque, matching Option B's channel split but through the
cascade instead of a flat wrench.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import mujoco
import numpy as np

from gra_control.gate import CMGResidualAugmentor
from gra_control.math3d import quat_angle, quat_conj, quat_error, quat_mul, quat_normalize
from gra_control.platforms.drone import SPECS, _free_joint, _mixer, torque_limits

from run_6dof_wrench import position_reference, MASS_FORCE_LIMIT_SCALE  # reuse, not reimplement

MIN_THRUST_FRACTION = 0.05  # of hover thrust -- floor to avoid the R_des singularity at F=0
ATT_CMD_LPF_ALPHA = 0.02    # low-pass coefficient on the outer loop's commanded attitude, see run()


def rotmat_to_quat(R: np.ndarray) -> np.ndarray:
    """Shepperd's method, standard and numerically stable. R columns = body
    axes expressed in world frame (matching the convention already used by
    data.xmat[body_id].reshape(3,3) elsewhere in this codebase)."""
    m00, m01, m02 = R[0]
    m10, m11, m12 = R[1]
    m20, m21, m22 = R[2]
    tr = m00+m11+m22
    if tr > 0:
        s = 0.5/np.sqrt(tr+1.0)
        w = 0.25/s
        x = (m21-m12)*s
        y = (m02-m20)*s
        z = (m10-m01)*s
    elif m00 > m11 and m00 > m22:
        s = 2.0*np.sqrt(1.0+m00-m11-m22)
        w = (m21-m12)/s
        x = 0.25*s
        y = (m01+m10)/s
        z = (m02+m20)/s
    elif m11 > m22:
        s = 2.0*np.sqrt(1.0+m11-m00-m22)
        w = (m02-m20)/s
        x = (m01+m10)/s
        y = 0.25*s
        z = (m12+m21)/s
    else:
        s = 2.0*np.sqrt(1.0+m22-m00-m11)
        w = (m10-m01)/s
        x = (m02+m20)/s
        y = (m12+m21)/s
        z = 0.25*s
    return quat_normalize(np.array([w, x, y, z]))


def thrust_vector_to_attitude(F_world: np.ndarray, yaw_des: float, min_thrust: float) -> tuple[np.ndarray, float]:
    """Mellinger-Kumar style decomposition: desired body z-axis along the
    commanded force, x-axis picked to match desired yaw as closely as the
    tilt allows. Returns (q_des, collective_thrust_magnitude)."""
    thrust_mag = float(np.linalg.norm(F_world))
    if thrust_mag < min_thrust:
        F_world = np.array([0.0, 0.0, min_thrust])
        thrust_mag = min_thrust
    zb = F_world/thrust_mag
    xc = np.array([np.cos(yaw_des), np.sin(yaw_des), 0.0])
    yb = np.cross(zb, xc)
    n = np.linalg.norm(yb)
    if n < 1e-6:  # xc nearly parallel to zb (near-vertical singularity edge case)
        xc = np.array([1.0, 0.0, 0.0]) if abs(zb[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        yb = np.cross(zb, xc)
        n = np.linalg.norm(yb)
    yb = yb/n
    xb = np.cross(yb, zb)
    R_des = np.stack([xb, yb, zb], axis=1)
    return rotmat_to_quat(R_des), thrust_mag


def run(mission: str, duration: float, dt: float, controller: str, beta: float,
        learning_rate: float, k_error_pos: float, k_rate_pos: float,
        k_error_att: float, k_rate_att: float, output: Path,
        platform: str = "x2", wn_att: np.ndarray | None = None,
        wn_pos: np.ndarray | None = None,
        ki_pos: np.ndarray | None = None, ki_att: np.ndarray | None = None,
        actuator_scale: float = 1.0, authority_scale: float = 1.0) -> dict:
    spec = SPECS[platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    inertia = model.body_inertia[body_id].copy()
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    act_ids, _, B_inv, ctrl_range = _mixer(model)
    if actuator_scale != 1.0:
        # Same mechanism as drone.py's run_drone: raise each rotor's max
        # commandable thrust (ctrl_range upper bound) by this factor -- a
        # "more powerful rotor" design, not a gear/mass change. B_inv is
        # geometry-only (rotor positions), unaffected.
        if actuator_scale <= 0:
            raise ValueError("actuator_scale must be positive")
        ctrl_range[:, 1] *= actuator_scale
        model.actuator_ctrlrange[act_ids, 1] = ctrl_range[:, 1]

    wn = np.array([4.0, 4.0, 3.5]) if wn_att is None else np.asarray(wn_att, dtype=float)
    kq = 2.0*inertia*wn*wn
    kw = 2.0*0.95*wn*inertia
    # authority_scale raises the DESIGN force/torque ceiling the controller is
    # allowed to request -- a separate knob from actuator_scale (motor
    # headroom). A genuinely "more powerful rotor" redesign needs both raised
    # together: actuator_scale alone gives the motors more headroom but the
    # controller never asks for it while force_limits/tau_limits still cap
    # the request below what the old motors could already deliver.
    tau_limits = authority_scale*torque_limits(platform, inertia, model, "model")
    force_limits = authority_scale*np.array([MASS_FORCE_LIMIT_SCALE*mass*gravity]*2+[1.8*mass*gravity])
    limits6 = np.concatenate([force_limits, tau_limits])
    # Cascade time-scale separation: the outer position loop must be substantially
    # slower than the inner attitude loop (wn=[4,4,3.5] rad/s) for the cascade to
    # be stable at all -- a standard cascade-control requirement. An earlier
    # version used wn_pos~3 rad/s (kp_pos=mass*9), nearly as fast as the attitude
    # loop; confirmed unstable empirically (hover3d held exact equilibrium for
    # >10s then diverged exponentially from floating-point noise -- the classic
    # signature of a genuine closed-loop pole in the right half-plane, not an
    # external disturbance). wn_pos=1.0 rad/s (x/y), 1.2 rad/s (z) gives ~4x
    # separation from the attitude loop.
    wn_pos = np.array([1.0, 1.0, 1.2]) if wn_pos is None else np.asarray(wn_pos, dtype=float)
    kp_pos = mass*wn_pos*wn_pos
    kd_pos = mass*2.0*0.75*wn_pos
    ki_pos = np.zeros(3) if ki_pos is None else np.asarray(ki_pos, dtype=float)
    ki_att = np.zeros(3) if ki_att is None else np.asarray(ki_att, dtype=float)
    min_thrust = MIN_THRUST_FRACTION*mass*gravity
    # Anti-windup: clamp each integral accumulator so its contribution alone
    # cannot exceed a fraction of that channel's own force/torque limit.
    pos_integral_limit = np.divide(0.3*force_limits, ki_pos, out=np.full(3, np.inf), where=ki_pos > 1e-12)
    att_integral_limit = np.divide(0.3*tau_limits, ki_att, out=np.full(3, np.inf), where=ki_att > 1e-12)

    augmentor = None
    if controller != "classical":
        adaptive = controller in {"adaptive-residual", "online-pes-adaptive"}
        mode = "online_pes" if "online-pes" in controller else "residual"
        augmentor = CMGResidualAugmentor(6, limits6, mode, adaptive, beta, learning_rate=learning_rate)

    data.qpos[qa:qa+3] = position_reference(0.0, mission, duration)
    data.qpos[qa+3:qa+7] = quat_conj(np.array([1.0, 0.0, 0.0, 0.0]))
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)

    rows: list[dict] = []
    q_des_prev = np.array([1.0, 0.0, 0.0, 0.0])
    pos_integral = np.zeros(3)
    att_integral = np.zeros(3)
    while data.time < duration:
        t = float(data.time)
        p = np.asarray(data.qpos[qa:qa+3], dtype=float)
        v = np.asarray(data.qvel[va:va+3], dtype=float)
        q_meas = quat_conj(np.asarray(data.qpos[qa+3:qa+7], dtype=float))
        omega = np.asarray(data.qvel[va+3:va+6], dtype=float)

        p_ref = position_reference(t, mission, duration)
        pos_integral = np.clip(pos_integral+(p-p_ref)*dt, -pos_integral_limit, pos_integral_limit)
        F0 = np.clip(mass*gravity*np.array([0, 0, 1])-kp_pos*(p-p_ref)-kd_pos*v-ki_pos*pos_integral,
                     -force_limits, force_limits)

        if augmentor is None:
            F_cmd, tau_att_residual = F0, np.zeros(3)
            residual_norm, gate_mean, activity_mean, decoder_norm = 0.0, 0.0, 0.0, 0.0
        else:
            pos_target = np.clip(-k_error_pos*(p-p_ref)/max(1e-9, np.linalg.norm(force_limits))-k_rate_pos*v, -1.0, 1.0)
            # This step's tau0 depends on q_des, which depends on this step's F_cmd,
            # which is the augmentor's own output -- circular. Break it with a one-step
            # delay (same pattern as eq_for_target below): use last step's tau0/eq as the
            # attitude half of both the gate-drive baseline and the learning target. Do
            # NOT zero this out -- that starves the attitude gate of any reactive signal
            # (confirmed bug on the Hover hardware controller, see PROGRESS_2026-08-27.md
            # Bug 4 -- gate_mean pinned at exactly 0.0000 when baseline=0).
            tau0_prev = rows[-1]["_tau0"] if rows else np.zeros(3)
            eq_prev = rows[-1]["_eq_for_target"] if rows else np.zeros(3)
            att_target = np.clip(-k_error_att*eq_prev-k_rate_att*omega, -1.0, 1.0)
            target6 = np.concatenate([pos_target, att_target])
            wrench0_for_gate = np.concatenate([F0, tau0_prev])
            out_pos = augmentor.step(wrench0_for_gate, dt, target6)
            F_cmd = out_pos.command[0:3]
            tau_att_residual = out_pos.residual[3:6]
            residual_norm = float(np.linalg.norm(out_pos.residual))
            gate_mean = float(np.mean(out_pos.gate))
            activity_mean = float(np.mean(out_pos.activity))
            decoder_norm = float(np.linalg.norm(augmentor.W))

        yaw_des = 0.0
        q_des, thrust_mag = thrust_vector_to_attitude(F_cmd, yaw_des, min_thrust)
        # ROOT CAUSE of the instability below (found by direct ground-truth check,
        # not more hand-derivation): q_meas is built as quat_conj(data.qpos) to put
        # the raw MuJoCo attitude into this codebase's own quaternion convention.
        # q_des, built fresh from a geometric rotation matrix via rotmat_to_quat,
        # never went through that same correction. Verified exactly: set the plant
        # to a real tilt a, read its ACTUAL body-z direction via xmat (ground
        # truth), feed that exact direction back into thrust_vector_to_attitude --
        # the resulting q_des reproduces quat_conj(q_meas), not q_meas, for every
        # angle tested (0.05, -0.05, 0.15 rad, all exact to 1e-4). So q_des and
        # q_meas were being compared in opposite conventions the entire time --
        # quat_error(q_des, q_meas) was computing roughly *twice* the true error
        # with a sign that turns the restoring torque into a driving one, which is
        # exactly the runaway-from-floating-point-noise signature seen empirically.
        q_des = quat_conj(q_des)
        # Angular-rate feedforward for the inner loop: q_des is state-dependent (it
        # comes from the position loop, unlike drone.py's original missions where the
        # attitude reference is a pure function of time only, with no feedback path
        # back through the plant). Comparing omega against a fixed zero target (as
        # drone.py's validated formula does for an externally-driven reference) is
        # provably wrong here -- confirmed empirically: hover3d at exact equilibrium
        # held exact zero error for >10s then grew exponentially (right-half-plane-
        # pole signature); slowing the outer loop only delayed onset; low-pass
        # filtering q_des reduced but did not eliminate the growth. Diagnostic
        # logging pinned it precisely: Fcmd_y and eq_x (roll) grow in lockstep --
        # the y-position/roll cascade loop itself is unstable without feedforward.
        # Fix: estimate omega_des from the actual rotation q_des underwent this
        # step (standard small-angle quaternion-derivative-to-angular-velocity
        # relation: omega ~= 2*vec(conj(q_prev) (x) q_new)/dt), and drive the inner
        # loop toward zero RELATIVE rate (omega - omega_des), not zero absolute rate.
        _, dq_vec = quat_error(q_des, q_des_prev)
        omega_des = 2.0*dq_vec/dt
        q_des_prev = q_des
        qe, eq = quat_error(q_des, q_meas)
        att_integral = np.clip(att_integral+eq*dt, -att_integral_limit, att_integral_limit)
        # Matches the proportional term's sign convention (-kq*eq): both scale
        # the same error quantity eq in the same direction.
        tau0 = np.clip(-kq*eq-kw*(omega-omega_des)-ki_att*att_integral, -tau_limits, tau_limits)
        tau = np.clip(tau0+tau_att_residual, -tau_limits, tau_limits)

        motors = B_inv@np.r_[thrust_mag, tau]
        motors = np.clip(motors, ctrl_range[:, 0], ctrl_range[:, 1])
        data.ctrl[:] = 0.0
        data.ctrl[act_ids] = motors
        data.xfrc_applied[:] = 0.0
        mujoco.mj_step(model, data)

        rows.append({
            "t": t, "pos_err": float(np.linalg.norm(p-p_ref)), "qerr": quat_angle(qe),
            "x": p[0], "y": p[1], "z": p[2], "x_ref": p_ref[0], "y_ref": p_ref[1], "z_ref": p_ref[2],
            "thrust": thrust_mag, "tau_x": tau[0], "tau_y": tau[1], "tau_z": tau[2],
            "residual_norm": residual_norm, "gate_mean": gate_mean,
            "activity_mean": activity_mean, "decoder_norm": decoder_norm,
            "eq_x": eq[0], "eq_y": eq[1], "eq_z": eq[2],
            "qdes_w": q_des[0], "qdes_x": q_des[1], "qdes_y": q_des[2], "qdes_z": q_des[3],
            "Fcmd_x": F_cmd[0], "Fcmd_y": F_cmd[1], "Fcmd_z": F_cmd[2],
            "omega_x": omega[0], "omega_y": omega[1], "omega_z": omega[2],
            "_eq_for_target": eq, "_tau0": tau0,
        })

    for r in rows:
        del r["_eq_for_target"]
        del r["_tau0"]
    output.mkdir(parents=True, exist_ok=True)
    with (output/"trace.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    pos_err = np.array([r["pos_err"] for r in rows])
    qerr = np.array([r["qerr"] for r in rows])
    summary = {
        "platform": f"{platform}-6dof-cascade", "controller": controller, "mission": mission,
        "duration": duration, "dt": dt, "pos_err_mean_m": float(pos_err.mean()),
        "pos_err_max_m": float(pos_err.max()), "qerr_mean_rad": float(qerr.mean()),
        "qerr_max_rad": float(qerr.max()),
    }
    (output/"summary.json").write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mission", required=True, choices=["hover3d", "waypoint_step", "circle_xy", "full6_stress"])
    p.add_argument("--duration", type=float, default=10.0)
    p.add_argument("--dt", type=float, default=0.0005)
    p.add_argument("--controller", default="classical",
                    choices=["classical", "fixed-residual", "adaptive-residual", "online-pes-adaptive"])
    p.add_argument("--beta", type=float, default=0.5)
    p.add_argument("--learning-rate", type=float, default=0.0008)
    p.add_argument("--k-error-pos", type=float, default=8.0)
    p.add_argument("--k-rate-pos", type=float, default=0.0)
    p.add_argument("--k-error-att", type=float, default=8.0)
    p.add_argument("--k-rate-att", type=float, default=0.0)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--platform", default="x2", choices=["x2", "cf2-rotor"])
    p.add_argument("--wn-att", type=float, nargs=3, default=None)
    p.add_argument("--wn-pos", type=float, nargs=3, default=None)
    p.add_argument("--ki-pos", type=float, nargs=3, default=None)
    p.add_argument("--ki-att", type=float, nargs=3, default=None)
    p.add_argument("--actuator-scale", type=float, default=1.0)
    p.add_argument("--authority-scale", type=float, default=1.0)
    a = p.parse_args()
    s = run(a.mission, a.duration, a.dt, a.controller, a.beta, a.learning_rate,
            a.k_error_pos, a.k_rate_pos, a.k_error_att, a.k_rate_att, a.output,
            a.platform, a.wn_att, a.wn_pos, a.ki_pos, a.ki_att, a.actuator_scale, a.authority_scale)
    print(f"pos_err_mean={s['pos_err_mean_m']:.4f}m  qerr_mean={np.rad2deg(s['qerr_mean_rad']):.3f}deg")
