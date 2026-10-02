"""MuJoCo hover + quaternion attitude validation against paper references.

This is the reproducible version of ``quaternion_mujoco_hover_roll.py``.  It
keeps the same useful hover-support idea, but makes the run configurable and
saves logs/figures for comparison with the validated pure ODE paper model.

Examples:

    python experiments/quaternion_quad/mujoco_hover_paper_validation.py --mission roll --viewer
    python experiments/quaternion_quad/mujoco_hover_paper_validation.py --mission full3 --gain-mode scaled
    python experiments/quaternion_quad/mujoco_hover_paper_validation.py --mission full3 --gain-mode paper --dt 0.0005
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import matplotlib.pyplot as plt
import mujoco
import mujoco.viewer
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
XML_PATH = PROJECT_ROOT / "third_party" / "mujoco_menagerie" / "skydio_x2" / "scene.xml"
LOGS_DIR = PROJECT_ROOT / "results" / "logs"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures" / "quaternion_quad" / "mujoco_hover_paper_validation"


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
    phi = np.arctan2(
        2.0 * (q0 * q1 + q2 * q3),
        q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3,
    )
    theta = np.arcsin(np.clip(2.0 * (q0 * q2 - q3 * q1), -1.0, 1.0))
    psi = np.arctan2(
        2.0 * (q0 * q3 + q1 * q2),
        q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3,
    )
    return np.array([phi, theta, psi], dtype=float)


def wrap_to_pi(x: np.ndarray) -> np.ndarray:
    return (x + np.pi) % (2.0 * np.pi) - np.pi


def quat_angle_error(q_err: np.ndarray) -> float:
    q_err = q_normalize(q_err)
    return float(2.0 * np.arctan2(np.linalg.norm(q_err[1:]), max(1e-12, abs(q_err[0]))))


def mujoco_quat_to_paper_quat(q_mj: np.ndarray) -> np.ndarray:
    # Keep the convention that made the original hover-roll script behave well.
    return q_conj(q_normalize(q_mj))


def clip_norm(v: np.ndarray, vmax: float) -> np.ndarray:
    n = np.linalg.norm(v)
    if n <= vmax or n < 1e-12:
        return v
    return v * (vmax / n)


def reference_euler(t: float, mission: str) -> np.ndarray:
    if mission == "roll":
        return np.array([0.25 * np.sin(0.7 * t), 0.0, 0.0], dtype=float)
    if mission == "full3":
        phase = np.array([0.0, np.pi / 2.0, np.pi], dtype=float)
        return 0.5 * np.sin(t + phase)
    if mission == "step":
        return np.array(
            [
                1.0 if t >= 1.0 else 0.0,
                1.0 if t >= 5.0 else 0.0,
                1.0 if t >= 9.0 else 0.0,
            ],
            dtype=float,
        )
    raise ValueError(f"Unknown mission: {mission}")


def reference_quat(t: float, mission: str) -> np.ndarray:
    phi, theta, psi = reference_euler(t, mission)
    return euler_to_quat(phi, theta, psi)


def find_freejoint(model: mujoco.MjModel) -> int:
    for j in range(model.njnt):
        if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
            return j
    raise RuntimeError("No freejoint found in model.")


def build_gains(gain_mode: str, inertia: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if gain_mode == "paper":
        return (
            np.array([20.0, 20.0, 20.0], dtype=float),
            np.array([4.0, 4.0, 4.0], dtype=float),
            np.array([4.0, 4.0, 4.0], dtype=float),
        )
    if gain_mode == "scaled":
        wn = np.array([4.0, 4.0, 3.5], dtype=float)
        zeta = np.array([0.95, 0.95, 0.95], dtype=float)
        alpha_max = np.array([12.0, 12.0, 10.0], dtype=float)
        kq = 2.0 * inertia * (wn**2)
        kw = 2.0 * zeta * wn * inertia
        tau_limit = np.maximum(inertia * alpha_max, np.array([0.03, 0.03, 0.02]))
        return kq, kw, tau_limit
    raise ValueError(f"Unknown gain mode: {gain_mode}")


def run(args: argparse.Namespace) -> tuple[Path, Path]:
    if not XML_PATH.exists():
        raise FileNotFoundError(XML_PATH)

    model = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data = mujoco.MjData(model)
    model.opt.timestep = args.dt

    free_jid = find_freejoint(model)
    body_id = model.jnt_bodyid[free_jid]
    body_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body_id)
    qpos_adr = model.jnt_qposadr[free_jid]
    qvel_adr = model.jnt_dofadr[free_jid]

    total_mass = float(np.sum(model.body_mass))
    gravity = float(abs(model.opt.gravity[2]))
    inertia = np.array(model.body_inertia[body_id], dtype=float)
    kq, kw, tau_limit = build_gains(args.gain_mode, inertia)

    if model.nu > 0:
        data.ctrl[:] = 0.0
    data.qpos[qpos_adr : qpos_adr + 3] = np.array([0.0, 0.0, args.z_ref])
    data.qpos[qpos_adr + 3 : qpos_adr + 7] = np.array([1.0, 0.0, 0.0, 0.0])
    data.qvel[qvel_adr : qvel_adr + 6] = 0.0
    data.xfrc_applied[:] = 0.0
    mujoco.mj_forward(model, data)

    rows: list[dict[str, float]] = []

    def step_controller() -> None:
        t = float(data.time)
        data.xfrc_applied[:] = 0.0

        pos = np.array(data.qpos[qpos_adr : qpos_adr + 3], dtype=float)
        q_mj = q_normalize(np.array(data.qpos[qpos_adr + 3 : qpos_adr + 7], dtype=float))
        vel = np.array(data.qvel[qvel_adr : qvel_adr + 3], dtype=float)
        omega = np.array(data.qvel[qvel_adr + 3 : qvel_adr + 6], dtype=float)
        q_meas = mujoco_quat_to_paper_quat(q_mj)
        q_ref = reference_quat(t, args.mission)
        eul_ref = reference_euler(t, args.mission)

        q_err = q_mul(q_ref, q_conj(q_meas))
        if q_err[0] < 0.0:
            q_err = -q_err
        tau_body = -kq * q_err[1:4] - kw * omega
        tau_body = np.clip(tau_body, -tau_limit, tau_limit)

        r_wb = data.xmat[body_id].reshape(3, 3)
        tau_world = r_wb @ tau_body

        body_z_world = r_wb[:, 2]
        tilt_cos = max(args.min_tilt_cos, body_z_world[2])
        collective = total_mass * (
            gravity + args.kz_acc * (args.z_ref - pos[2]) + args.dz_acc * (0.0 - vel[2])
        ) / tilt_cos
        collective = np.clip(collective, 0.0, args.max_collective_factor * total_mass * max(gravity, 1.0))
        force_world = args.thrust_sign * collective * body_z_world

        if args.xy_tether:
            a_xy = -args.kxy_acc * pos[:2] - args.dxy_acc * vel[:2]
            force_world[:2] += total_mass * clip_norm(a_xy, args.max_xy_acc)

        data.xfrc_applied[body_id, 0:3] = force_world
        data.xfrc_applied[body_id, 3:6] = tau_world
        mujoco.mj_step(model, data)

        eul_meas = quat_to_euler(q_meas)
        eul_err = wrap_to_pi(eul_meas - eul_ref)
        rows.append(
            {
                "t": t,
                "x": pos[0],
                "y": pos[1],
                "z": pos[2],
                "vx": vel[0],
                "vy": vel[1],
                "vz": vel[2],
                "phi_ref": eul_ref[0],
                "theta_ref": eul_ref[1],
                "psi_ref": eul_ref[2],
                "phi": eul_meas[0],
                "theta": eul_meas[1],
                "psi": eul_meas[2],
                "phi_err": eul_err[0],
                "theta_err": eul_err[1],
                "psi_err": eul_err[2],
                "qerr_angle": quat_angle_error(q_err),
                "wx": omega[0],
                "wy": omega[1],
                "wz": omega[2],
                "tau_x": tau_body[0],
                "tau_y": tau_body[1],
                "tau_z": tau_body[2],
                "force_x": force_world[0],
                "force_y": force_world[1],
                "force_z": force_world[2],
                "collective": collective,
            }
        )

    if args.viewer:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            while viewer.is_running() and data.time < args.sim_time:
                tic = time.time()
                step_controller()
                viewer.sync()
                sleep_time = model.opt.timestep - (time.time() - tic)
                if sleep_time > 0.0:
                    time.sleep(sleep_time)
    else:
        while data.time < args.sim_time:
            step_controller()

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"mujoco_hover_{args.mission}_{args.gain_mode}_dt{args.dt:g}".replace(".", "p")
    csv_path = LOGS_DIR / f"{stem}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    arr = {key: np.array([row[key] for row in rows]) for key in rows[0]}
    rmse = np.sqrt(np.mean(np.column_stack([arr["phi_err"], arr["theta_err"], arr["psi_err"]]) ** 2, axis=0))
    tau = np.column_stack([arr["tau_x"], arr["tau_y"], arr["tau_z"]])
    sat = np.any(np.isclose(np.abs(tau), tau_limit, atol=1e-9), axis=1)
    summary_path = LOGS_DIR / f"{stem}_summary.txt"
    summary_path.write_text(
        "\n".join(
            [
                "MuJoCo hover paper validation",
                f"body={body_name}",
                f"mission={args.mission}",
                f"gain_mode={args.gain_mode}",
                f"dt={args.dt}",
                f"sim_time={args.sim_time}",
                f"mass={total_mass}",
                f"inertia={inertia.tolist()}",
                f"KQ={kq.tolist()}",
                f"KW={kw.tolist()}",
                f"tau_limit={tau_limit.tolist()}",
                f"rmse_phi_theta_psi={rmse.tolist()}",
                f"qerr_mean={float(np.mean(arr['qerr_angle']))}",
                f"qerr_max={float(np.max(arr['qerr_angle']))}",
                f"tau_mean={float(np.mean(np.linalg.norm(tau, axis=1)))}",
                f"sat_fraction={float(np.mean(sat))}",
                f"z_mean={float(np.mean(arr['z']))}",
                f"z_std={float(np.std(arr['z']))}",
            ]
        ),
        encoding="utf-8",
    )

    t = arr["t"]
    fig, axes = plt.subplots(4, 1, figsize=(10, 9), sharex=True)
    for i, name in enumerate(["phi", "theta", "psi"]):
        axes[i].plot(t, arr[f"{name}_ref"], "--", label="reference")
        axes[i].plot(t, arr[name], label="measured")
        axes[i].set_ylabel(f"{name} [rad]")
        axes[i].grid(True, alpha=0.3)
    axes[0].legend(fontsize=8)
    axes[3].plot(t, arr["qerr_angle"], color="tab:red")
    axes[3].set_ylabel("q error [rad]")
    axes[3].set_xlabel("Time [s]")
    axes[3].grid(True, alpha=0.3)
    fig.suptitle(f"MuJoCo hover attitude validation: {args.mission}, {args.gain_mode}")
    fig.tight_layout()
    figure_path = FIGURES_DIR / f"{stem}_attitude.png"
    fig.savefig(figure_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
    for i, name in enumerate(["x", "y", "z"]):
        axes[i].plot(t, arr[name])
        if name == "z":
            axes[i].axhline(args.z_ref, linestyle="--", color="k", linewidth=0.8)
        axes[i].set_ylabel(f"{name} [m]")
        axes[i].grid(True, alpha=0.3)
    axes[-1].set_xlabel("Time [s]")
    fig.suptitle(f"MuJoCo hover position: {args.mission}, {args.gain_mode}")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"{stem}_position.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(summary_path.read_text(encoding="utf-8"))
    print(f"Saved CSV: {csv_path}")
    print(f"Saved figure: {figure_path}")
    return csv_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mission", choices=["roll", "full3", "step"], default="roll")
    parser.add_argument("--gain-mode", choices=["scaled", "paper"], default="scaled")
    parser.add_argument("--dt", type=float, default=0.0005)
    parser.add_argument("--sim-time", type=float, default=15.0)
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--z-ref", type=float, default=1.0)
    parser.add_argument("--thrust-sign", type=float, default=1.0)
    parser.add_argument("--xy-tether", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--kz-acc", type=float, default=6.0)
    parser.add_argument("--dz-acc", type=float, default=4.0)
    parser.add_argument("--max-collective-factor", type=float, default=2.5)
    parser.add_argument("--min-tilt-cos", type=float, default=0.35)
    parser.add_argument("--kxy-acc", type=float, default=1.5)
    parser.add_argument("--dxy-acc", type=float, default=2.2)
    parser.add_argument("--max-xy-acc", type=float, default=3.0)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
