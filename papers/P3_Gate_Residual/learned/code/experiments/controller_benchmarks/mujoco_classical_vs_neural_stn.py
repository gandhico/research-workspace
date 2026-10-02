from __future__ import annotations

import argparse
# Local STN-PID/PES attitude controller
import sys
from pathlib import Path as _PathForSTN

_STN_DIR = _PathForSTN(__file__).resolve().parents[1] / "mujoco_stn_hyperlif_benchmark"
if str(_STN_DIR) not in sys.path:
    sys.path.insert(0, str(_STN_DIR))

from stn_pid_attitude_controller import STNPIDAttitudeController

import csv
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import mujoco

try:
    import mujoco.viewer as mujoco_viewer
except Exception:
    mujoco_viewer = None

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
THIS_DIR = Path(__file__).resolve().parent

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from neural_torque_controllers import make_controller
from benchmark_metrics import summarize_controller_run


MODEL_XMLS = {
    "skydio_x2": PROJECT_ROOT / "third_party" / "mujoco_menagerie" / "skydio_x2" / "scene.xml",
    "bitcraze_crazyflie_2": PROJECT_ROOT
    / "third_party"
    / "mujoco_menagerie"
    / "bitcraze_crazyflie_2"
    / "scene.xml",
}

LOGS_DIR = PROJECT_ROOT / "results" / "logs" / "controller_benchmarks"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures" / "controller_benchmarks"


def q_mul(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    p0, p1, p2, p3 = p
    q0, q1, q2, q3 = q
    return np.array(
        [
            p0 * q0 - p1 * q1 - p2 * q2 - p3 * q3,
            p0 * q1 + p1 * q0 + p2 * q3 - p3 * q2,
            p0 * q2 - p1 * q3 + p2 * q0 + p3 * q1,
            p0 * q3 + p1 * q2 - p2 * q1 + p3 * q0,
        ],
        dtype=float,
    )


def q_conj(q: np.ndarray) -> np.ndarray:
    return np.array([q[0], -q[1], -q[2], -q[3]], dtype=float)


def q_normalize(q: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(q)
    if n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    return q / n


def quat_continuous(q: np.ndarray, q_prev: np.ndarray | None) -> np.ndarray:
    """Return q or -q so quaternion traces remain visually continuous."""
    q = q_normalize(q)
    if q_prev is not None and np.linalg.norm(q + q_prev) < np.linalg.norm(q - q_prev):
        return -q
    return q


def euler_to_quat(phi: float, theta: float, psi: float) -> np.ndarray:
    cphi, sphi = np.cos(phi / 2.0), np.sin(phi / 2.0)
    cth, sth = np.cos(theta / 2.0), np.sin(theta / 2.0)
    cpsi, spsi = np.cos(psi / 2.0), np.sin(psi / 2.0)
    return q_normalize(
        np.array(
            [
                cphi * cth * cpsi + sphi * sth * spsi,
                sphi * cth * cpsi - cphi * sth * spsi,
                cphi * sth * cpsi + sphi * cth * spsi,
                cphi * cth * spsi - sphi * sth * cpsi,
            ],
            dtype=float,
        )
    )


def quat_to_euler(q: np.ndarray) -> np.ndarray:
    q = q_normalize(q)
    q0, q1, q2, q3 = q
    return np.array(
        [
            np.arctan2(2.0 * (q0 * q1 + q2 * q3), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3),
            np.arcsin(np.clip(2.0 * (q0 * q2 - q3 * q1), -1.0, 1.0)),
            np.arctan2(2.0 * (q0 * q3 + q1 * q2), q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3),
        ],
        dtype=float,
    )


def wrap_to_pi(x: np.ndarray) -> np.ndarray:
    return (x + np.pi) % (2.0 * np.pi) - np.pi


def quat_angle_error(q_err: np.ndarray) -> float:
    q_err = q_normalize(q_err)
    return float(2.0 * np.arctan2(np.linalg.norm(q_err[1:]), max(1e-12, abs(q_err[0]))))


def mujoco_quat_to_paper_quat(q_mj: np.ndarray) -> np.ndarray:
    return q_conj(q_normalize(q_mj))


def clip_norm(v: np.ndarray, vmax: float) -> np.ndarray:
    n = np.linalg.norm(v)
    if n <= vmax or n < 1e-12:
        return v
    return v * (vmax / n)


def reference_euler(t: float, mission: str, sim_time: float = 20.0) -> np.ndarray:
    if mission == "roll":
        return np.array([0.25 * np.sin(0.7 * t), 0.0, 0.0], dtype=float)

    if mission == "full3":
        return 0.5 * np.sin(t + np.array([0.0, np.pi / 2.0, np.pi], dtype=float))

    if mission == "step":
        return np.array(
            [
                1.0 if t >= 1.0 else 0.0,
                1.0 if t >= 5.0 else 0.0,
                1.0 if t >= 9.0 else 0.0,
            ],
            dtype=float,
        )

    if mission == "hard45":
        # Long aggressive smooth maneuver.
        # Uses mixed frequencies and phase shifts to avoid a simple periodic pattern.
        # Amplitudes are intentionally below the step mission to keep it physically realistic.
        phi = (
            0.55 * np.sin(0.75 * t)
            + 0.20 * np.sin(2.10 * t + 0.40)
        )
        theta = (
            0.45 * np.sin(0.95 * t + np.pi / 3.0)
            + 0.18 * np.sin(1.75 * t)
        )
        psi = (
            0.65 * np.sin(0.55 * t + np.pi)
            + 0.25 * np.sin(1.35 * t + 0.20)
        )
        return np.array([phi, theta, psi], dtype=float)


    elif mission == "yaw360":
        # 360-degree yaw rotation mission.
        # Purpose:
        #   - test quaternion behavior through a full rotation
        #   - expose Euler yaw wrapping
        #   - keep roll/pitch small while yaw completes 2*pi
        #
        # Reference:
        #   phi_ref   = 0
        #   theta_ref = 0
        #   psi_ref   = smooth ramp 0 -> 2*pi
        #
        # The smoothstep profile avoids a sharp acceleration at the beginning/end.
        Tspin = max(sim_time, 1e-9)
        s = np.clip(t / Tspin, 0.0, 1.0)
        smooth = 3.0*s**2 - 2.0*s**3
        phi_ref = 0.0
        theta_ref = 0.0
        psi_ref = 2.0*np.pi*smooth
        return np.array([phi_ref, theta_ref, psi_ref], dtype=float)


    if mission == "roll360":
        # Fast 360-degree roll / flip with a short pre-roll delay.
        #
        # Important:
        # A roll flip is much harder than yaw360 because the thrust vector rotates
        # away from vertical and can point downward during inversion. Therefore,
        # this mission should be run with a higher z reference, for example:
        #   --z-ref 3.0
        #
        # The mission:
        #   0 <= t < t_start: hold level
        #   t_start <= t <= t_start + Tflip: smooth 0 -> 2*pi roll
        #   after flip: hold equivalent final level attitude
        t_start = 1.0
        Tflip = 1.2

        if t < t_start:
            phi_ref = 0.0
        else:
            s = np.clip((t - t_start) / Tflip, 0.0, 1.0)
            smooth = 3.0 * s**2 - 2.0 * s**3
            phi_ref = 2.0 * np.pi * smooth

        theta_ref = 0.0
        psi_ref = 0.0
        return np.array([phi_ref, theta_ref, psi_ref], dtype=float)

    if mission == "hardstep":
        # Aggressive piecewise command for stress testing recovery behavior.
        if t < 5.0:
            return np.array([0.0, 0.0, 0.0], dtype=float)
        if t < 12.0:
            return np.array([0.75, -0.45, 0.55], dtype=float)
        if t < 20.0:
            return np.array([-0.65, 0.55, -0.70], dtype=float)
        if t < 30.0:
            return np.array([0.50, 0.50, 0.90], dtype=float)
        if t < 40.0:
            return np.array([-0.80, -0.35, 0.20], dtype=float)
        return np.array([0.0, 0.0, 0.0], dtype=float)

    # ---- aggressive / acrobatic suite (thrust-aware flips: run with higher --z-ref, e.g. 3.0) ----
    if mission == "pitch360":
        # Full 360-degree pitch LOOP (analogue of roll360 on the pitch axis).
        t_start, Tflip = 1.0, 1.2
        theta_ref = 0.0
        if t >= t_start:
            s = np.clip((t - t_start) / Tflip, 0.0, 1.0)
            theta_ref = 2.0 * np.pi * (3.0 * s**2 - 2.0 * s**3)
        return np.array([0.0, theta_ref, 0.0], dtype=float)

    if mission == "hard90":
        # Double-amplitude aggressive continuous tracking (~1.0-1.2 rad peaks, higher freq).
        phi = 1.05 * np.sin(0.90 * t) + 0.35 * np.sin(2.50 * t + 0.40)
        theta = 0.90 * np.sin(1.15 * t + np.pi / 3.0) + 0.32 * np.sin(2.10 * t)
        psi = 1.20 * np.sin(0.70 * t + np.pi) + 0.45 * np.sin(1.60 * t + 0.20)
        return np.array([phi, theta, psi], dtype=float)

    if mission == "tumble":
        # Sequential roll flip THEN pitch flip (a tumble).
        if t < 1.0:
            return np.array([0.0, 0.0, 0.0], dtype=float)
        if t < 2.5:
            s = np.clip((t - 1.0) / 1.5, 0.0, 1.0)
            return np.array([2.0 * np.pi * (3.0 * s**2 - 2.0 * s**3), 0.0, 0.0], dtype=float)
        if t < 3.0:
            return np.array([0.0, 0.0, 0.0], dtype=float)
        if t < 4.5:
            s = np.clip((t - 3.0) / 1.5, 0.0, 1.0)
            return np.array([0.0, 2.0 * np.pi * (3.0 * s**2 - 2.0 * s**3), 0.0], dtype=float)
        return np.array([0.0, 0.0, 0.0], dtype=float)

    if mission == "acro":
        # Acro medley: pitch loop -> roll flip -> yaw spin (the full routine).
        if t < 2.0:
            return np.array([0.0, 0.0, 0.0], dtype=float)
        if t < 3.5:
            s = np.clip((t - 2.0) / 1.5, 0.0, 1.0)
            return np.array([0.0, 2.0 * np.pi * (3.0 * s**2 - 2.0 * s**3), 0.0], dtype=float)
        if t < 4.0:
            return np.array([0.0, 0.0, 0.0], dtype=float)
        if t < 5.5:
            s = np.clip((t - 4.0) / 1.5, 0.0, 1.0)
            return np.array([2.0 * np.pi * (3.0 * s**2 - 2.0 * s**3), 0.0, 0.0], dtype=float)
        if t < 6.0:
            return np.array([0.0, 0.0, 0.0], dtype=float)
        s = np.clip((t - 6.0) / max(sim_time - 6.0, 1e-9), 0.0, 1.0)
        return np.array([0.0, 0.0, 2.0 * np.pi * (3.0 * s**2 - 2.0 * s**3)], dtype=float)

    raise ValueError(f"Unknown mission: {mission}")


def reference_quat(t: float, mission: str, sim_time: float = 20.0) -> np.ndarray:
    return euler_to_quat(*reference_euler(t, mission, sim_time))


def find_freejoint(model: mujoco.MjModel) -> int:
    for j in range(model.njnt):
        if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
            return j
    raise RuntimeError("No freejoint found in model.")


def build_scaled_gains(inertia: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    wn = np.array([4.0, 4.0, 3.5], dtype=float)
    zeta = np.array([0.95, 0.95, 0.95], dtype=float)
    alpha_max = np.array([12.0, 12.0, 10.0], dtype=float)

    kq = 2.0 * inertia * (wn**2)
    kw = 2.0 * zeta * wn * inertia
    tau_limit = np.maximum(inertia * alpha_max, np.array([0.03, 0.03, 0.02]))

    return kq, kw, tau_limit


def run(args: argparse.Namespace) -> tuple[Path, Path]:
    xml_path = MODEL_XMLS[args.quad]
    if not xml_path.exists():
        raise FileNotFoundError(f"MuJoCo XML not found: {xml_path}")

    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)
    model.opt.timestep = args.dt

    free_jid = find_freejoint(model)
    body_id = model.jnt_bodyid[free_jid]
    qpos_adr = model.jnt_qposadr[free_jid]
    qvel_adr = model.jnt_dofadr[free_jid]

    total_mass = float(np.sum(model.body_mass))
    gravity = float(abs(model.opt.gravity[2]))
    inertia = np.array(model.body_inertia[body_id], dtype=float)

    kq, kw, tau_limit = build_scaled_gains(inertia)

    stn_controller = None
    hyperlif_residual_controller = None

    if args.controller == "stn_pid":
        controller = make_controller(
            "classical",
            kq,
            kw,
            tau_limit,
            dt=args.dt,
            direct_blend=args.direct_blend,
            direct_activity_mode=args.direct_activity_mode,
            nengo_n_neurons=args.n_neurons,
            nengo_radius=args.radius,
            nengo_synapse=args.synapse,
            nengo_seed=args.seed,
            direct_scale=args.direct_scale,
            direct_gate_gain=args.direct_gate_gain,
        )
        stn_controller = STNPIDAttitudeController(
            mode="stn",
            tau_limit=float(np.max(tau_limit)),
        )

    elif args.controller == "stn_pid_pes":
        controller = make_controller(
            "classical",
            kq,
            kw,
            tau_limit,
            dt=args.dt,
            direct_blend=args.direct_blend,
            direct_activity_mode=args.direct_activity_mode,
            nengo_n_neurons=args.n_neurons,
            nengo_radius=args.radius,
            nengo_synapse=args.synapse,
            nengo_seed=args.seed,
            direct_scale=args.direct_scale,
            direct_gate_gain=args.direct_gate_gain,
        )
        stn_controller = STNPIDAttitudeController(
            mode="stn_pes",
            tau_limit=float(np.max(tau_limit)),
        )

    elif args.controller == "stn_pid_pes_direct":
        # Option A:
        # Direct STN-PID-PES torque controller.
        # This does NOT use the validated classical PD torque.
        # It is the closest transfer test to a stand-alone STN-PID-PES controller.
        controller = None
        stn_controller = STNPIDAttitudeController(
            mode="stn_pes",
            tau_limit=float(np.max(tau_limit)),
        )

    elif args.controller == "stn_pid_pes_gain":
        # Option B:
        # Gain-adaptive STN-PID-PES controller.
        # We still call the validated classical controller to preserve the correct
        # quaternion sign convention, then use STN-PES to modulate the effective gains.
        controller = make_controller(
            "classical",
            kq,
            kw,
            tau_limit,
            dt=args.dt,
            direct_blend=args.direct_blend,
            direct_activity_mode=args.direct_activity_mode,
            nengo_n_neurons=args.n_neurons,
            nengo_radius=args.radius,
            nengo_synapse=args.synapse,
            nengo_seed=args.seed,
            direct_scale=args.direct_scale,
            direct_gate_gain=args.direct_gate_gain,
        )
        stn_controller = STNPIDAttitudeController(
            mode="stn_pes",
            tau_limit=float(np.max(tau_limit)),
        )

    elif args.controller == "stn_pid_pes_hyperlif_residual":
        # Final verification branch:
        # frozen sign-corrected STN-PID-PES backbone + small direct HyperLIF residual.
        controller = make_controller(
            "classical",
            kq,
            kw,
            tau_limit,
            dt=args.dt,
            direct_blend=args.direct_blend,
            direct_activity_mode=args.direct_activity_mode,
            nengo_n_neurons=args.n_neurons,
            nengo_radius=args.radius,
            nengo_synapse=args.synapse,
            nengo_seed=args.seed,
            direct_scale=args.direct_scale,
            direct_gate_gain=args.direct_gate_gain,
        )
        stn_controller = STNPIDAttitudeController(
            mode="stn_pes",
            tau_limit=float(np.max(tau_limit)),
        )
        hyperlif_residual_controller = make_controller(
            "direct_hyperlif",
            kq,
            kw,
            tau_limit,
            dt=args.dt,
            direct_blend=args.direct_blend,
            direct_activity_mode=args.direct_activity_mode,
            nengo_n_neurons=args.n_neurons,
            nengo_radius=args.radius,
            nengo_synapse=args.synapse,
            nengo_seed=args.seed,
            direct_scale=args.direct_scale,
            direct_gate_gain=args.direct_gate_gain,
        )

    else:
        controller = make_controller(
            args.controller,
            kq,
            kw,
            tau_limit,
            dt=args.dt,
            direct_blend=args.direct_blend,
            direct_activity_mode=args.direct_activity_mode,
            nengo_n_neurons=args.n_neurons,
            nengo_radius=args.radius,
            nengo_synapse=args.synapse,
            nengo_seed=args.seed,
            direct_scale=args.direct_scale,
            direct_gate_gain=args.direct_gate_gain,
        )

    if model.nu > 0:
        data.ctrl[:] = 0.0

    data.qpos[qpos_adr : qpos_adr + 3] = np.array([0.0, 0.0, args.z_ref])
    data.qpos[qpos_adr + 3 : qpos_adr + 7] = np.array([1.0, 0.0, 0.0, 0.0])
    data.qvel[qvel_adr : qvel_adr + 6] = 0.0
    data.xfrc_applied[:] = 0.0
    mujoco.mj_forward(model, data)

    viewer = None
    if args.viewer:
        if mujoco_viewer is None:
            raise RuntimeError("MuJoCo viewer is not available in this Python environment.")
        viewer = mujoco_viewer.launch_passive(model, data)
        print("MuJoCo viewer launched. Close the viewer window or press Ctrl+C to stop.")

    step_count = 0

    rows: list[dict[str, float]] = []
    q_ref_prev_plot: np.ndarray | None = None
    q_meas_prev_plot: np.ndarray | None = None

    while data.time < args.sim_time:
        t = float(data.time)
        data.xfrc_applied[:] = 0.0

        pos = np.array(data.qpos[qpos_adr : qpos_adr + 3], dtype=float)
        vel = np.array(data.qvel[qvel_adr : qvel_adr + 3], dtype=float)

        q_mj = q_normalize(np.array(data.qpos[qpos_adr + 3 : qpos_adr + 7], dtype=float))
        omega = np.array(data.qvel[qvel_adr + 3 : qvel_adr + 6], dtype=float)

        q_meas = mujoco_quat_to_paper_quat(q_mj)
        q_ref = reference_quat(t, args.mission, args.sim_time)
        eul_ref = reference_euler(t, args.mission, args.sim_time)

        q_ref_plot = quat_continuous(q_ref.copy(), q_ref_prev_plot)
        q_meas_plot = quat_continuous(q_meas.copy(), q_meas_prev_plot)
        q_ref_prev_plot = q_ref_plot.copy()
        q_meas_prev_plot = q_meas_plot.copy()

        q_err = q_mul(q_ref, q_conj(q_meas))
        if q_err[0] < 0.0:
            q_err = -q_err

        axis_error = q_err[1:4]

        if args.controller in ("stn_pid", "stn_pid_pes", "stn_pid_pes_direct", "stn_pid_pes_gain", "stn_pid_pes_hyperlif_residual"):

            if args.controller in ("stn_pid", "stn_pid_pes"):
                # Existing successful controller:
                # validated classical PD backbone + sign-corrected STN-PES torque augmentation.
                ctrl = controller.step(axis_error, omega, args.dt)
                tau_pd = np.clip(ctrl.tau, -tau_limit, tau_limit)

                tau_stn, stn_info = stn_controller.step(
                    error=axis_error,
                    omega=omega,
                    dt=args.dt,
                    measure=axis_error,
                )

                # Sign-corrected augmentation. This is the result that worked well on Bitcraze.
                stn_correction_scale = -0.05
                tau_body = tau_pd + args.direct_blend * stn_correction_scale * tau_stn
                tau_body = np.clip(tau_body, -tau_limit, tau_limit)

                ctrl_info = {
                    "event_count_step": 0.0,
                    "activity_mean": float(np.linalg.norm(tau_stn)),
                    "activity_max": float(np.max(np.abs(tau_stn))),
                    **stn_info,
                }

            elif args.controller == "stn_pid_pes_direct":
                # Option A:
                # Direct stand-alone STN-PID-PES torque.
                # No classical PD backbone.
                # The negative sign follows the successful MuJoCo torque convention.
                tau_stn, stn_info = stn_controller.step(
                    error=axis_error,
                    omega=omega,
                    dt=args.dt,
                    measure=axis_error,
                )

                direct_torque_scale = -1.0
                tau_body = args.direct_blend * direct_torque_scale * tau_stn
                tau_body = np.clip(tau_body, -tau_limit, tau_limit)

                ctrl_info = {
                    "event_count_step": 0.0,
                    "activity_mean": float(np.linalg.norm(tau_stn)),
                    "activity_max": float(np.max(np.abs(tau_stn))),
                    **stn_info,
                }

            elif args.controller == "stn_pid_pes_gain":
                # Option B:
                # STN-PID-PES gain-adaptive controller.
                # Use the validated classical controller for the correct quaternion convention,
                # then apply a smooth per-axis gain multiplier learned from STN-PES.
                ctrl = controller.step(axis_error, omega, args.dt)
                tau_pd = np.clip(ctrl.tau, -tau_limit, tau_limit)

                _tau_stn_unused, stn_info = stn_controller.step(
                    error=axis_error,
                    omega=omega,
                    dt=args.dt,
                    measure=axis_error,
                )

                # Normalize relative to the initial gains in STNPIDAttitudeController:
                # Kp0 = 0.03, Kd0 = 0.002.
                kp = np.array(
                    [
                        stn_info.get("Kp_x", 0.03),
                        stn_info.get("Kp_y", 0.03),
                        stn_info.get("Kp_z", 0.03),
                    ],
                    dtype=float,
                )
                kd = np.array(
                    [
                        stn_info.get("Kd_x", 0.002),
                        stn_info.get("Kd_y", 0.002),
                        stn_info.get("Kd_z", 0.002),
                    ],
                    dtype=float,
                )

                kp_rel = kp / 0.03
                kd_rel = kd / 0.002

                # Conservative gain multiplier.
                # direct_blend controls how much of the STN gain adaptation is used.
                gain_adapt_scale = 0.25
                gain_mult = 1.0 + args.direct_blend * gain_adapt_scale * (0.8 * (kp_rel - 1.0) + 0.2 * (kd_rel - 1.0))
                gain_mult = np.clip(gain_mult, 0.25, 4.0)

                tau_body = gain_mult * tau_pd
                tau_body = np.clip(tau_body, -tau_limit, tau_limit)

                ctrl_info = {
                    "event_count_step": 0.0,
                    "activity_mean": float(np.mean(gain_mult)),
                    "activity_max": float(np.max(gain_mult)),
                    "gain_mult_x": float(gain_mult[0]),
                    "gain_mult_y": float(gain_mult[1]),
                    "gain_mult_z": float(gain_mult[2]),
                    **stn_info,
                }

            elif args.controller == "stn_pid_pes_hyperlif_residual":
                ctrl_pd = controller.step(axis_error, omega, args.dt)
                tau_pd = np.clip(ctrl_pd.tau, -tau_limit, tau_limit)

                tau_stn, stn_info = stn_controller.step(
                    error=axis_error,
                    omega=omega,
                    dt=args.dt,
                    measure=axis_error,
                )
                tau_stn = np.clip(np.asarray(tau_stn, dtype=float), -tau_limit, tau_limit)

                stn_correction_scale = -0.05
                tau_backbone = tau_pd + args.direct_blend * stn_correction_scale * tau_stn
                tau_backbone = np.clip(tau_backbone, -tau_limit, tau_limit)

                ctrl_hyperlif = hyperlif_residual_controller.step(axis_error, omega, args.dt)
                tau_hyperlif = np.clip(ctrl_hyperlif.tau, -tau_limit, tau_limit)

                tau_body = tau_backbone + args.custom_aug_correction_scale * tau_hyperlif
                tau_body = np.clip(tau_body, -tau_limit, tau_limit)

                ctrl_info = {
                    "event_count_step": float(ctrl_hyperlif.info.get("event_count_step", 0.0)),
                    "activity_mean": float(ctrl_hyperlif.info.get("activity_mean", 0.0)),
                    "activity_max": float(ctrl_hyperlif.info.get("activity_max", 0.0)),
                    "pd_tau_norm": float(np.linalg.norm(tau_pd)),
                    "stn_tau_norm": float(np.linalg.norm(tau_stn)),
                    "backbone_tau_norm": float(np.linalg.norm(tau_backbone)),
                    "hyperlif_tau_norm": float(np.linalg.norm(tau_hyperlif)),
                    "hyperlif_tau_max_abs": float(np.max(np.abs(tau_hyperlif))),
                    "total_tau_norm": float(np.linalg.norm(tau_body)),
                    "custom_aug_correction_scale": float(args.custom_aug_correction_scale),
                    **stn_info,
                }

        else:
            ctrl = controller.step(axis_error, omega, args.dt)
            tau_body = np.clip(ctrl.tau, -tau_limit, tau_limit)
            ctrl_info = ctrl.info

        r_wb = data.xmat[body_id].reshape(3, 3)
        body_z_world = r_wb[:, 2]

        tilt_cos = max(0.35, body_z_world[2])
        collective = total_mass * (
            gravity + 6.0 * (args.z_ref - pos[2]) + 4.0 * (0.0 - vel[2])
        ) / tilt_cos
        collective = np.clip(collective, 0.0, 2.5 * total_mass * max(gravity, 1.0))

        force_world = collective * body_z_world

        a_xy = -1.5 * pos[:2] - 2.2 * vel[:2]
        force_world[:2] += total_mass * clip_norm(a_xy, 3.0)

        data.xfrc_applied[body_id, 0:3] = force_world
        data.xfrc_applied[body_id, 3:6] = r_wb @ tau_body

        mujoco.mj_step(model, data)

        step_count += 1

        if viewer is not None:
            if not viewer.is_running():
                print("Viewer closed by user.")
                break

            if step_count % args.viewer_sync_every == 0:
                viewer.sync()
                if args.viewer_realtime:
                    time.sleep(args.dt * args.viewer_sync_every * args.viewer_slowdown)

        eul_meas = quat_to_euler(q_meas)
        eul_err = wrap_to_pi(eul_meas - eul_ref)

        rows.append(
            {
                "t": t,
                "phi_ref": eul_ref[0],
                "theta_ref": eul_ref[1],
                "psi_ref": eul_ref[2],
                "phi": eul_meas[0],
                "theta": eul_meas[1],
                "psi": eul_meas[2],
                "q_ref_w": q_ref_plot[0],
                "q_ref_x": q_ref_plot[1],
                "q_ref_y": q_ref_plot[2],
                "q_ref_z": q_ref_plot[3],
                "q_w": q_meas_plot[0],
                "q_x": q_meas_plot[1],
                "q_y": q_meas_plot[2],
                "q_z": q_meas_plot[3],
                "phi_err": eul_err[0],
                "theta_err": eul_err[1],
                "psi_err": eul_err[2],
                "qerr_angle": quat_angle_error(q_err),
                "z": pos[2],
                "tau_x": tau_body[0],
                "tau_y": tau_body[1],
                "tau_z": tau_body[2],
                "event_count_step": float(ctrl_info.get("event_count_step", 0.0)),
                "activity_mean": float(ctrl_info.get("activity_mean", 0.0)),
                "activity_max": float(ctrl_info.get("activity_max", 0.0)),
                "stn_Kp_x": float(ctrl_info.get("Kp_x", 0.0)),
                "stn_Kp_y": float(ctrl_info.get("Kp_y", 0.0)),
                "stn_Kp_z": float(ctrl_info.get("Kp_z", 0.0)),
                "stn_Ki_x": float(ctrl_info.get("Ki_x", 0.0)),
                "stn_Ki_y": float(ctrl_info.get("Ki_y", 0.0)),
                "stn_Ki_z": float(ctrl_info.get("Ki_z", 0.0)),
                "stn_Kd_x": float(ctrl_info.get("Kd_x", 0.0)),
                "stn_Kd_y": float(ctrl_info.get("Kd_y", 0.0)),
                "stn_Kd_z": float(ctrl_info.get("Kd_z", 0.0)),
                "stn_sens_x": float(ctrl_info.get("sens_x", 0.0)),
                "stn_sens_y": float(ctrl_info.get("sens_y", 0.0)),
                "stn_sens_z": float(ctrl_info.get("sens_z", 0.0)),
                "pd_tau_norm": float(ctrl_info.get("pd_tau_norm", 0.0)),
                "stn_tau_norm": float(ctrl_info.get("stn_tau_norm", 0.0)),
                "backbone_tau_norm": float(ctrl_info.get("backbone_tau_norm", 0.0)),
                "hyperlif_tau_norm": float(ctrl_info.get("hyperlif_tau_norm", 0.0)),
                "hyperlif_tau_max_abs": float(ctrl_info.get("hyperlif_tau_max_abs", 0.0)),
                "total_tau_norm": float(ctrl_info.get("total_tau_norm", 0.0)),
                "custom_aug_correction_scale": float(ctrl_info.get("custom_aug_correction_scale", 0.0)),
            }
        )

    if viewer is not None:
        viewer.close()

    if controller is not None and hasattr(controller, "close"):
        controller.close()

    summary = summarize_controller_run(rows, tau_limit)
    summary.update(
        {
            "controller": args.controller,
            "quad": args.quad,
            "mission": args.mission,
            "dt": args.dt,
            "sim_time": args.sim_time,
            "direct_blend": args.direct_blend,
            "direct_scale": args.direct_scale,
            "custom_aug_correction_scale": args.custom_aug_correction_scale,
        }
    )

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    stem = (
        f"mujoco_{args.quad}_{args.mission}_{args.controller}"
        f"_dt{args.dt:g}_T{args.sim_time:g}_scale{args.direct_scale}_act{args.direct_activity_mode}_gg{args.direct_gate_gain:g}_blend{args.direct_blend:g}"
    ).replace(".", "p")
    if args.controller == "stn_pid_pes_hyperlif_residual":
        stem = f"{stem}_caug{args.custom_aug_correction_scale:g}".replace(".", "p")

    csv_path = LOGS_DIR / f"{stem}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary_path = LOGS_DIR / f"{stem}_summary.txt"
    summary_path.write_text(
        "\n".join([f"{k}={v}" for k, v in summary.items()]),
        encoding="utf-8",
    )

    arr = {key: np.array([row[key] for row in rows]) for key in rows[0]}
    t = arr["t"]

    fig, axes = plt.subplots(5, 1, figsize=(10, 10), sharex=True)

    for i, name in enumerate(["phi", "theta", "psi"]):
        axes[i].plot(t, arr[f"{name}_ref"], "--", label="reference")
        axes[i].plot(t, arr[name], label="measured")
        axes[i].set_ylabel(f"{name} [rad]")
        axes[i].grid(True, alpha=0.3)

    axes[0].legend(fontsize=8)

    axes[3].plot(t, arr["qerr_angle"], color="tab:red")
    axes[3].set_ylabel("q error [rad]")
    axes[3].grid(True, alpha=0.3)

    axes[4].plot(t, arr["tau_x"], label="tau_x")
    axes[4].plot(t, arr["tau_y"], label="tau_y")
    axes[4].plot(t, arr["tau_z"], label="tau_z")
    axes[4].set_ylabel("torque [Nm]")
    axes[4].set_xlabel("Time [s]")
    axes[4].grid(True, alpha=0.3)
    axes[4].legend(fontsize=8)

    fig.suptitle(f"Controller benchmark: {args.controller}, {args.mission}, scale={args.direct_scale}, activity={args.direct_activity_mode}, blend={args.direct_blend}")
    fig.tight_layout()

    fig_path = FIGURES_DIR / f"{stem}.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(summary_path.read_text(encoding="utf-8"))
    print(f"Saved CSV: {csv_path}")
    print(f"Saved figure: {fig_path}")

    return csv_path, summary_path



def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--quad", choices=sorted(MODEL_XMLS), default="skydio_x2")
    parser.add_argument("--mission", choices=["roll", "full3", "step", "hard45", "hardstep", "yaw360", "roll360", "pitch360", "hard90", "tumble", "acro"], default="roll")

    parser.add_argument(
        "--controller",
        choices=[
            "classical",
            "direct_lif",
            "direct_hyperlif",
            "direct_adaptive_hyperlif",
            "direct_izhikevich",
            "nengo_lifrate",
            "nengo_lif",
            "nengo_rectified",
            "nengo_adaptive_lif",
            "nengo_izhikevich", "stn_pid", "stn_pid_pes", "stn_pid_pes_direct", "stn_pid_pes_gain",
            "stn_pid_pes_hyperlif_residual",
        ],
        default="classical",
    )

    parser.add_argument("--dt", type=float, default=0.0005)
    parser.add_argument("--sim-time", type=float, default=15.0)
    parser.add_argument("--z-ref", type=float, default=1.0)

    parser.add_argument("--viewer", action="store_true", help="Open MuJoCo passive viewer.")
    parser.add_argument("--viewer-sync-every", type=int, default=20, help="Viewer sync period in simulation steps.")
    parser.add_argument("--viewer-realtime", action="store_true", help="Slow simulation down to approximately real time.")
    parser.add_argument("--viewer-slowdown", type=float, default=1.0, help="Viewer real-time slowdown multiplier.")

    parser.add_argument("--direct-blend", type=float, default=0.20)
    parser.add_argument("--direct-scale", choices=["paper", "control"], default="paper")
    parser.add_argument("--direct-activity-mode", choices=["voltage", "gate", "events"], default="voltage")
    parser.add_argument("--direct-gate-gain", type=float, default=1.0, help="Gain applied to gate activity when --direct-activity-mode gate is used.")
    parser.add_argument(
        "--custom-aug-correction-scale",
        type=float,
        default=0.05,
        help="Scale applied to the HyperLIF residual in stn_pid_pes_hyperlif_residual.",
    )

    parser.add_argument("--n-neurons", type=int, default=400)
    parser.add_argument("--radius", type=float, default=1.5)
    parser.add_argument("--synapse", type=float, default=0.002)
    parser.add_argument("--seed", type=int, default=2)

    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()














