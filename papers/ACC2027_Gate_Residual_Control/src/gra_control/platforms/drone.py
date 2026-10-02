from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

import mujoco
import numpy as np

from gra_control.gate import CMGResidualAugmentor
from gra_control.math3d import (
    euler_to_quat, quat_angle, quat_conj, quat_error, quat_mul, reference_quat,
)
from gra_control.provenance import manifest, write_json


ROOT = Path(__file__).resolve().parents[3]


@dataclass
class DroneSpec:
    name: str
    model: Path
    body_name: str
    interface: str


SPECS = {
    "cf2": DroneSpec(
        "cf2",
        ROOT/"third_party/mujoco_menagerie/bitcraze_crazyflie_2/scene.xml",
        "cf2",
        "virtual_wrench",
    ),
    "x2": DroneSpec(
        "x2",
        ROOT/"third_party/mujoco_menagerie/skydio_x2/scene.xml",
        "x2",
        "rotor4",
    ),
    "cf2-rotor": DroneSpec(
        "cf2-rotor",
        ROOT/"models/cf2_rotor_design/scene.xml",
        "cf2",
        "rotor4",
    ),
}


def _name_id(model: mujoco.MjModel, obj, name: str) -> int:
    idx = mujoco.mj_name2id(model, obj, name)
    if idx < 0:
        raise RuntimeError(f"MuJoCo object not found: {name}")
    return int(idx)


def _free_joint(model: mujoco.MjModel) -> tuple[int, int, int, int]:
    for jid in range(model.njnt):
        if model.jnt_type[jid] == mujoco.mjtJoint.mjJNT_FREE:
            return (
                int(jid), int(model.jnt_bodyid[jid]),
                int(model.jnt_qposadr[jid]), int(model.jnt_dofadr[jid]),
            )
    raise RuntimeError("Drone model has no free joint")


def _mixer(model: mujoco.MjModel) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    names = [f"thrust{i}" for i in range(1, 5)]
    aids = np.array([_name_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in names])
    sids = np.array([_name_id(model, mujoco.mjtObj.mjOBJ_SITE, n) for n in names])
    pos = model.site_pos[sids]
    B = np.vstack([np.ones(4), pos[:, 1], -pos[:, 0], model.actuator_gear[aids, 5]])
    return aids, B, np.linalg.inv(B), model.actuator_ctrlrange[aids].copy()


def torque_limits(
    platform_name: str,
    inertia: np.ndarray,
    model: mujoco.MjModel,
    policy: str,
) -> np.ndarray:
    inertia_limit = np.maximum(inertia*np.array([12.0, 12.0, 10.0]), 1e-6)
    if policy == "inertia":
        return inertia_limit
    if policy == "legacy-learned":
        return np.maximum(inertia_limit, np.array([0.03, 0.03, 0.02]))
    if policy == "model":
        if platform_name == "cf2":
            names = ["x_moment", "y_moment", "z_moment"]
            aids = np.array([_name_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in names])
            gear = np.abs(np.array([
                model.actuator_gear[aids[0], 3], model.actuator_gear[aids[1], 4],
                model.actuator_gear[aids[2], 5],
            ]))
            ctrl = np.max(np.abs(model.actuator_ctrlrange[aids]), axis=1)
            return np.minimum(inertia_limit, gear*ctrl)
        return inertia_limit
    raise ValueError(f"Unknown torque policy: {policy}")


def _controller(
    name: str,
    limits: np.ndarray,
    beta: float,
    learning_rate: float,
) -> CMGResidualAugmentor | None:
    if name == "classical":
        return None
    if name == "fixed-residual":
        return CMGResidualAugmentor(3, limits, "residual", False, beta)
    if name == "adaptive-residual":
        return CMGResidualAugmentor(3, limits, "residual", True, beta)
    if name == "legacy-blend":
        return CMGResidualAugmentor(3, limits, "blend", True, beta)
    if name in {"online-pes", "online-pes-adaptive"}:
        return CMGResidualAugmentor(3, limits, "online_pes", True, beta, learning_rate=learning_rate)
    if name == "online-pes-fixed":
        return CMGResidualAugmentor(3, limits, "online_pes", False, beta, learning_rate=learning_rate)
    raise ValueError(f"Unknown controller: {name}")


def run_drone(
    platform_name: str,
    controller_name: str,
    mission: str,
    duration: float,
    dt: float,
    beta: float,
    torque_policy: str,
    learning_rate: float,
    k_error: float,
    k_rate: float,
    actuator_scale: float,
    initial_angle_deg: float,
    disturbance_torque: float,
    attitude_noise_std: float,
    rate_noise_std: float,
    seed: int,
    output: Path,
) -> dict:
    spec = SPECS[platform_name]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    inertia = model.body_inertia[body_id].copy()
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    limits = torque_limits(platform_name, inertia, model, torque_policy)
    wn = np.array([4.0, 4.0, 3.5])
    kq = 2.0*inertia*wn*wn
    kw = 2.0*0.95*wn*inertia
    augmentor = _controller(controller_name, limits, beta, learning_rate)

    data.qpos[qa:qa+3] = [0.0, 0.0, 1.0]
    initial_rad = np.deg2rad(initial_angle_deg)
    q_initial_body = euler_to_quat(initial_rad, -0.7*initial_rad, 0.5*initial_rad)
    data.qpos[qa+3:qa+7] = quat_conj(q_initial_body)
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0  # Critical: prevents the historical CF2 double-hover input.
    mujoco.mj_forward(model, data)

    if spec.interface == "rotor4":
        act_ids, _, B_inv, ctrl_range = _mixer(model)
        if actuator_scale <= 0:
            raise ValueError("actuator_scale must be positive")
        ctrl_range[:, 1] *= actuator_scale
        model.actuator_ctrlrange[act_ids, 1] = ctrl_range[:, 1]
    else:
        names = ["body_thrust", "x_moment", "y_moment", "z_moment"]
        act_ids = np.array([_name_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in names])
        ctrl_range = model.actuator_ctrlrange[act_ids].copy()
        gears = np.abs(np.array([
            model.actuator_gear[act_ids[1], 3], model.actuator_gear[act_ids[2], 4],
            model.actuator_gear[act_ids[3], 5],
        ]))

    rows: list[dict] = []
    rng = np.random.default_rng(seed)
    while data.time < duration:
        t = float(data.time)
        q_meas = quat_conj(np.asarray(data.qpos[qa+3:qa+7], dtype=float))
        omega = np.asarray(data.qvel[va+3:va+6], dtype=float).copy()
        if attitude_noise_std > 0:
            dq = euler_to_quat(*rng.normal(0.0, attitude_noise_std, size=3))
            q_meas = quat_mul(dq, q_meas)
        if rate_noise_std > 0:
            omega += rng.normal(0.0, rate_noise_std, size=3)
        qref = reference_quat(t, mission, duration)
        qe, eq = quat_error(qref, q_meas)
        tau0 = np.clip(-kq*eq-kw*omega, -limits, limits)
        if augmentor is None:
            tau = tau0
            residual = np.zeros(3)
            gate_mean = 0.0
        else:
            target = np.clip(-k_error*eq-k_rate*omega, -1.0, 1.0)
            is_online = controller_name in {"online-pes", "online-pes-fixed", "online-pes-adaptive"}
            out = augmentor.step(tau0, dt, target if is_online else None)
            tau, residual = out.command, out.residual
            gate_mean = float(np.mean(out.gate))

        R = np.asarray(data.xmat[body_id], dtype=float).reshape(3, 3)
        z, vz = float(data.qpos[qa+2]), float(data.qvel[va+2])
        tilt = max(float(R[2, 2]), 0.35)
        collective = mass*(gravity + 6.0*(1.0-z)-4.0*vz)/tilt
        collective = float(np.clip(collective, 0.0, 2.5*mass*max(gravity, 1.0)))

        data.ctrl[:] = 0.0
        data.xfrc_applied[:] = 0.0
        if disturbance_torque > 0:
            disturbance_body = disturbance_torque*np.array([
                np.sin(1.31*t+0.2), 0.8*np.sin(1.73*t+1.1), 0.6*np.sin(2.17*t+2.0),
            ])
            data.xfrc_applied[body_id, 3:6] = R@disturbance_body
        if spec.interface == "rotor4":
            motors = B_inv@np.r_[collective, tau]
            motors = np.clip(motors, ctrl_range[:, 0], ctrl_range[:, 1])
            data.ctrl[act_ids] = motors
            saturated = bool(np.any(np.isclose(motors, ctrl_range[:, 0], atol=1e-7)) or
                             np.any(np.isclose(motors, ctrl_range[:, 1], atol=1e-7)))
        else:
            cmd = np.r_[collective, -tau/np.maximum(gears, 1e-15)]
            cmd = np.clip(cmd, ctrl_range[:, 0], ctrl_range[:, 1])
            data.ctrl[act_ids] = cmd
            saturated = bool(np.any(np.isclose(cmd[1:], ctrl_range[1:, 0], atol=1e-7)) or
                             np.any(np.isclose(cmd[1:], ctrl_range[1:, 1], atol=1e-7)))

        mujoco.mj_step(model, data)
        rows.append({
            "t": t, "qerr": quat_angle(qe), "tau_x": tau[0], "tau_y": tau[1],
            "tau_z": tau[2], "residual_norm": float(np.linalg.norm(residual)),
            "gate_mean": gate_mean, "z": z, "saturated": int(saturated),
        })

    output.mkdir(parents=True, exist_ok=True)
    csv_path = output/"trace.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    qerr = np.array([r["qerr"] for r in rows])
    tau = np.array([[r["tau_x"], r["tau_y"], r["tau_z"]] for r in rows])
    summary = {
        "platform": platform_name, "model_interface": spec.interface,
        "controller": controller_name, "mission": mission, "duration": duration, "dt": dt,
        "beta": beta, "learning_rate": learning_rate, "k_error": k_error, "k_rate": k_rate,
        "actuator_scale": actuator_scale,
        "initial_angle_deg": initial_angle_deg, "disturbance_torque_Nm": disturbance_torque,
        "attitude_noise_std_rad": attitude_noise_std, "rate_noise_std_rad_s": rate_noise_std,
        "seed": seed,
        "torque_policy": torque_policy, "torque_limits_Nm": limits.tolist(),
        "qerr_mean_rad": float(np.mean(qerr)), "qerr_max_rad": float(np.max(qerr)),
        "tau_mean_Nm": float(np.mean(np.linalg.norm(tau, axis=1))),
        "saturation_fraction": float(np.mean([r["saturated"] for r in rows])),
        "z_std_m": float(np.std([r["z"] for r in rows])),
        "trace": str(csv_path),
    }
    args = {
        "platform": platform_name, "controller": controller_name, "mission": mission,
        "duration": duration, "dt": dt, "beta": beta, "torque_policy": torque_policy,
        "learning_rate": learning_rate, "k_error": k_error, "k_rate": k_rate,
        "actuator_scale": actuator_scale,
        "initial_angle_deg": initial_angle_deg, "disturbance_torque": disturbance_torque,
        "attitude_noise_std": attitude_noise_std, "rate_noise_std": rate_noise_std, "seed": seed,
    }
    prov = manifest(ROOT, platform_name, controller_name, spec.model, args)
    prov["derived"] = {"body_inertia_kgm2": inertia.tolist(), "torque_limits_Nm": limits.tolist()}
    write_json(output/"summary.json", summary)
    write_json(output/"manifest.json", prov)
    return summary
