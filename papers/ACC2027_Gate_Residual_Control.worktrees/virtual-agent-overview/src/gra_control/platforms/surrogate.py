from __future__ import annotations

import csv
from pathlib import Path

import mujoco
import numpy as np

from gra_control.gate import CMGResidualAugmentor
from gra_control.math3d import euler_to_quat, quat_angle, quat_error, reference_quat
from gra_control.provenance import manifest, write_json


ROOT = Path(__file__).resolve().parents[3]
MODELS = {
    "pendulum": ROOT/"models/pendulum_surrogate.xml",
    "hover3dof": ROOT/"models/hover3dof_surrogate.xml",
    "qcar": ROOT/"models/qcar_surrogate.xml",
}


def _pendulum_lqr(model: mujoco.MjModel) -> np.ndarray:
    """Linearize the loaded MuJoCo model at upright and solve the discrete Riccati equation."""
    def transition(x: np.ndarray, u: float) -> np.ndarray:
        d = mujoco.MjData(model)
        d.qpos[:] = x[:2]
        d.qvel[:] = x[2:]
        d.ctrl[0] = u
        mujoco.mj_forward(model, d)
        mujoco.mj_step(model, d)
        return np.r_[d.qpos.copy(), d.qvel.copy()]

    x0 = np.zeros(4)
    eps = 1e-6
    A = np.column_stack([
        (transition(x0 + eps*np.eye(4)[i], 0.0)-transition(x0-eps*np.eye(4)[i], 0.0))/(2*eps)
        for i in range(4)
    ])
    B = ((transition(x0, eps)-transition(x0, -eps))/(2*eps)).reshape(4, 1)
    Q = np.diag([0.8, 120.0, 0.2, 5.0])
    R = np.array([[0.08]])
    P = Q.copy()
    for _ in range(20000):
        K = np.linalg.solve(R+B.T@P@B, B.T@P@A)
        next_p = Q+A.T@P@(A-B@K)
        if np.max(np.abs(next_p-P)) < 1e-10:
            P = next_p
            break
        P = next_p
    return np.linalg.solve(R+B.T@P@B, B.T@P@A).reshape(4)


def _augmentation(name: str, channels: int, limits: np.ndarray, beta: float):
    if name == "classical":
        return None
    mode = "blend" if name == "legacy-blend" else (
        "online_pes" if name in {"online-pes", "online-pes-fixed", "online-pes-adaptive"} else "residual"
    )
    adaptive = name not in {"fixed-residual", "online-pes-fixed"}
    return CMGResidualAugmentor(channels, limits, mode, adaptive, beta)


def run_surrogate(
    platform_name: str,
    controller_name: str,
    duration: float,
    dt: float,
    beta: float,
    output: Path,
) -> dict:
    model_path = MODELS[platform_name]
    model = mujoco.MjModel.from_xml_path(str(model_path))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    rows: list[dict] = []

    if platform_name == "pendulum":
        data.qpos[:] = [0.0, 0.10]
        limits = np.array([5.0])
        aug = _augmentation(controller_name, 1, limits, beta)
        lqr_gain = _pendulum_lqr(model)
        while data.time < duration:
            arm, alpha = data.qpos[:2]
            arm_rate, alpha_rate = data.qvel[:2]
            state = np.array([arm, alpha, arm_rate, alpha_rate])
            u0 = np.array([np.clip(-lqr_gain@state, -5, 5)])
            if aug:
                out = aug.step(u0, dt, np.array([-alpha-0.1*alpha_rate]))
                u, gate, residual = out.command, float(np.mean(out.gate)), out.residual
            else:
                u, gate, residual = u0, 0.0, np.zeros(1)
            data.ctrl[0] = u[0]
            mujoco.mj_step(model, data)
            rows.append({"t": float(data.time), "error": float(abs(alpha)), "command": float(u[0]),
                         "residual": float(residual[0]), "gate_mean": gate})

    elif platform_name == "hover3dof":
        data.qpos[:] = euler_to_quat(0.15, -0.10, 0.08)
        limits = np.array([0.30, 0.30, 0.22])
        aug = _augmentation(controller_name, 3, limits, beta)
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "hover_body")
        while data.time < duration:
            q = np.asarray(data.qpos[:4], dtype=float)
            omega = np.asarray(data.qvel[:3], dtype=float).copy()
            qref = reference_quat(float(data.time), "roll", duration)
            qe, eq = quat_error(qref, q)
            # qe = q_ref*conj(q), so +K*vec(qe) is corrective in this model.
            u0 = np.clip(1.1*eq-0.18*omega, -limits, limits)
            if aug:
                out = aug.step(u0, dt, np.clip(-1.5*eq-0.15*omega, -1, 1))
                u, gate, residual = out.command, float(np.mean(out.gate)), out.residual
            else:
                u, gate, residual = u0, 0.0, np.zeros(3)
            data.xfrc_applied[:] = 0.0
            R = np.asarray(data.xmat[body_id]).reshape(3, 3)
            data.xfrc_applied[body_id, 3:6] = R@u
            mujoco.mj_step(model, data)
            rows.append({"t": float(data.time), "error": quat_angle(qe), "command": float(np.linalg.norm(u)),
                         "residual": float(np.linalg.norm(residual)), "gate_mean": gate})

    elif platform_name == "qcar":
        data.qpos[:] = [0.0, 0.20, 0.0]
        limits = np.array([0.35])
        aug = _augmentation(controller_name, 1, limits, beta)
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "qcar")
        while data.time < duration:
            x, y, yaw = data.qpos[:3]
            vx, vy, yaw_rate = data.qvel[:3]
            yref = 0.35*np.sin(0.22*x)
            slope = 0.077*np.cos(0.22*x)
            error = y-yref
            heading_error = yaw-np.arctan(slope)
            steer0 = np.array([np.clip(-1.4*error-0.45*vy-0.9*heading_error-0.15*yaw_rate, -0.35, 0.35)])
            if aug:
                target = np.array([np.clip(-2.0*error-0.4*heading_error, -1, 1)])
                out = aug.step(steer0, dt, target)
                steer, gate, residual = out.command, float(np.mean(out.gate)), out.residual
            else:
                steer, gate, residual = steer0, 0.0, np.zeros(1)
            data.xfrc_applied[:] = 0.0
            force = 2.0*np.array([np.cos(yaw), np.sin(yaw), 0.0])
            data.xfrc_applied[body_id, :3] = force
            data.xfrc_applied[body_id, 5] = 1.2*steer[0]
            mujoco.mj_step(model, data)
            rows.append({"t": float(data.time), "error": float(abs(error)), "command": float(steer[0]),
                         "residual": float(residual[0]), "gate_mean": gate})
    else:
        raise ValueError(platform_name)

    output.mkdir(parents=True, exist_ok=True)
    csv_path = output/"trace.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summary = {
        "platform": platform_name, "model_fidelity": "integration-surrogate",
        "controller": controller_name, "duration": duration, "dt": dt,
        "beta": beta,
        "error_mean": float(np.mean([r["error"] for r in rows])),
        "error_max": float(np.max([r["error"] for r in rows])),
        "command_rms": float(np.sqrt(np.mean([r["command"]**2 for r in rows]))),
        "residual_rms": float(np.sqrt(np.mean([r["residual"]**2 for r in rows]))),
        "trace": str(csv_path),
    }
    args = {"platform": platform_name, "controller": controller_name, "duration": duration,
            "dt": dt, "beta": beta}
    write_json(output/"summary.json", summary)
    write_json(output/"manifest.json", manifest(ROOT, platform_name, controller_name, model_path, args))
    return summary
