"""ACC2027 CMG residual controller, mirrored live onto the QLabs QDrone2 actor.

This is a QLabs *kinematic-mirror* virtual twin, not a QLabs-native physics
twin: the rigid-body quadrotor dynamics are integrated in this process using
the exact canonical controller from the ACC2027 repository
(``gra_control.gate.CMGResidualAugmentor`` and ``gra_control.math3d``,
imported unmodified, not reimplemented), and only the resulting pose is
pushed into the running Quanser Interactive Labs QDrone2 actor via ``qvl``
for visualization. Mass/inertia/gravity are read directly from the same
Skydio X2 MuJoCo model the ACC2027 paper uses for its "x2" platform -- they
are NOT identified to the physical QDrone2 airframe. See
``docs/QLABS_TWIN_FIDELITY.md`` for the exact fidelity boundary.

The real QLabs-native physics path (QUARC real-time model + pal.products.qdrone2)
needs a local MATLAB/QUARC build of QDrone2_Workspace from
Documents/Quanser/5_research/autonomous_vehicles/qdrone2/virtual/position_control
and is tracked separately; it is not required for this script.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import mujoco
import numpy as np

ACC_ROOT = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
QDRONE_ROOT = Path(__file__).resolve().parents[1]

from gra_control.gate import CMGResidualAugmentor
from gra_control.math3d import (
    euler_to_quat, quat_angle, quat_conj, quat_error, quat_mul, quat_normalize,
    reference_quat,
)
from gra_control.provenance import manifest, write_json


def quat_to_rotmat(q: np.ndarray) -> np.ndarray:
    w, x, y, z = quat_normalize(q)
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
        [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
        [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)],
    ], dtype=float)


def quat_to_euler_zyx(q: np.ndarray) -> np.ndarray:
    """Inverse of gra_control.math3d.euler_to_quat (roll, pitch, yaw), radians."""
    w, x, y, z = quat_normalize(q)
    roll = np.arctan2(2*(w*x+y*z), 1-2*(x*x+y*y))
    sinp = 2*(w*y-z*x)
    pitch = np.arcsin(np.clip(sinp, -1.0, 1.0))
    yaw = np.arctan2(2*(w*z+x*y), 1-2*(y*y+z*z))
    return np.array([roll, pitch, yaw])


def _controller(name: str, limits: np.ndarray, beta: float, learning_rate: float):
    if name == "classical":
        return None
    if name == "fixed-residual":
        return CMGResidualAugmentor(3, limits, "residual", False, beta)
    if name == "adaptive-residual":
        return CMGResidualAugmentor(3, limits, "residual", True, beta)
    if name in {"online-pes", "online-pes-adaptive"}:
        return CMGResidualAugmentor(3, limits, "online_pes", True, beta, learning_rate=learning_rate)
    if name == "online-pes-fixed":
        return CMGResidualAugmentor(3, limits, "online_pes", False, beta, learning_rate=learning_rate)
    raise ValueError(f"Unknown controller: {name}")


@dataclass
class RigidBodyParams:
    mass: float
    inertia: np.ndarray  # body-frame diagonal-ish inertia (3,), from MuJoCo body_inertia
    gravity: float


def load_x2_rigid_body_params() -> RigidBodyParams:
    """Read mass/inertia/gravity from the exact MuJoCo model the ACC2027 x2
    platform uses, without stepping it. Keeps this twin's plant parameters
    from silently drifting away from the paper's own numbers."""
    model_path = ACC_ROOT / "third_party/mujoco_menagerie/skydio_x2/scene.xml"
    model = mujoco.MjModel.from_xml_path(str(model_path))
    for jid in range(model.njnt):
        if model.jnt_type[jid] == mujoco.mjtJoint.mjJNT_FREE:
            body_id = int(model.jnt_bodyid[jid])
            break
    else:
        raise RuntimeError("x2 model has no free joint")
    return RigidBodyParams(
        mass=float(np.sum(model.body_mass)),
        inertia=model.body_inertia[body_id].copy(),
        gravity=abs(float(model.opt.gravity[2])),
    )


def run_twin(
    controller_name: str,
    mission: str,
    duration: float,
    dt: float,
    beta: float,
    learning_rate: float,
    k_error: float,
    k_rate: float,
    initial_angle_deg: float,
    disturbance_torque: float,
    seed: int,
    visualize: bool,
    realtime: bool,
    speed: float,
    viz_every: int,
    output: Path,
) -> dict:
    params = load_x2_rigid_body_params()
    inertia, mass, gravity = params.inertia, params.mass, params.gravity

    limits = np.maximum(inertia*np.array([12.0, 12.0, 10.0]), 1e-6)
    wn = np.array([4.0, 4.0, 3.5])
    kq = 2.0*inertia*wn*wn
    kw = 2.0*0.95*wn*inertia
    augmentor = _controller(controller_name, limits, beta, learning_rate)

    pos = np.array([0.0, 0.0, 1.0])
    vel = np.zeros(3)
    initial_rad = np.deg2rad(initial_angle_deg)
    q_body_from_world = quat_conj(euler_to_quat(initial_rad, -0.7*initial_rad, 0.5*initial_rad))
    omega = np.zeros(3)  # body-frame angular velocity

    qlabs = None
    drone = None
    if visualize:
        from qvl.qlabs import QuanserInteractiveLabs
        from qvl.qdrone2 import QLabsQDrone2

        qlabs = QuanserInteractiveLabs()
        if not qlabs.open("localhost"):
            raise RuntimeError("Could not connect to QLabs - is Quanser Interactive Labs running?")
        drone = QLabsQDrone2(qlabs)
        drone.actorNumber = 0
        drone.destroy()
        status = drone.spawn_id_degrees(
            actorNumber=0, location=list(pos), rotation=[0, 0, 0],
            scale=[1, 1, 1], configuration=0, waitForConfirmation=True,
        )
        if status != 0:
            raise RuntimeError(f"QDrone2 spawn failed with status {status}")

    rows: list[dict] = []
    rng = np.random.default_rng(seed)
    n_steps = int(round(duration/dt))
    wall_start = time.perf_counter()

    try:
        for k in range(n_steps):
            t = k*dt
            qref = reference_quat(t, mission, duration)
            qe, eq = quat_error(qref, q_body_from_world)
            tau0 = np.clip(-kq*eq - kw*omega, -limits, limits)

            if augmentor is None:
                tau, residual, gate_mean = tau0, np.zeros(3), 0.0
            else:
                target = np.clip(-k_error*eq - k_rate*omega, -1.0, 1.0)
                is_online = controller_name in {"online-pes", "online-pes-fixed", "online-pes-adaptive"}
                out = augmentor.step(tau0, dt, target if is_online else None)
                tau, residual = out.command, out.residual
                gate_mean = float(np.mean(out.gate))

            R_wb = quat_to_rotmat(quat_conj(q_body_from_world))  # world-from-body
            z, vz = pos[2], vel[2]
            tilt = max(float(R_wb[2, 2]), 0.35)
            collective = mass*(gravity + 6.0*(1.0-z) - 4.0*vz)/tilt
            collective = float(np.clip(collective, 0.0, 2.5*mass*max(gravity, 1.0)))

            disturbance_body = np.zeros(3)
            if disturbance_torque > 0:
                disturbance_body = disturbance_torque*np.array([
                    np.sin(1.31*t+0.2), 0.8*np.sin(1.73*t+1.1), 0.6*np.sin(2.17*t+2.0),
                ])

            force_world = R_wb @ np.array([0.0, 0.0, collective]) - np.array([0.0, 0.0, mass*gravity])
            acc = force_world/mass
            vel = vel + dt*acc
            pos = pos + dt*vel
            pos[2] = max(pos[2], 0.05)

            net_torque = tau + disturbance_body
            omega_dot = (net_torque - np.cross(omega, inertia*omega))/np.maximum(inertia, 1e-9)
            omega = omega + dt*omega_dot
            qdot = -0.5*quat_mul(np.array([0.0, *omega]), q_body_from_world)
            q_body_from_world = quat_normalize(q_body_from_world + dt*qdot)

            rows.append({
                "t": t, "qerr": quat_angle(qe), "tau_x": tau[0], "tau_y": tau[1],
                "tau_z": tau[2], "residual_norm": float(np.linalg.norm(residual)),
                "gate_mean": gate_mean, "x": pos[0], "y": pos[1], "z": pos[2],
            })

            if visualize and (k % viz_every == 0):
                rpy = quat_to_euler_zyx(quat_conj(q_body_from_world))
                drone.set_transform_and_dynamics(
                    location=list(pos), rotation=list(rpy),
                    enableDynamics=False, waitForConfirmation=False,
                )

            if realtime:
                target_wall = wall_start + t/max(speed, 1e-9)
                sleep_for = target_wall - time.perf_counter()
                if sleep_for > 0:
                    time.sleep(sleep_for)
    finally:
        if qlabs is not None:
            qlabs.close()

    output.mkdir(parents=True, exist_ok=True)
    csv_path = output/"trace.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    qerr = np.array([r["qerr"] for r in rows])
    tau_arr = np.array([[r["tau_x"], r["tau_y"], r["tau_z"]] for r in rows])
    summary = {
        "platform": "qdrone2_qlabs_kinematic_mirror",
        "fidelity": "integration surrogate + QLabs kinematic-mirror visualization; "
                    "NOT a QLabs-native physics twin; mass/inertia read from the "
                    "ACC2027 x2 MuJoCo model, not identified to physical QDrone2",
        "controller": controller_name, "mission": mission, "duration": duration, "dt": dt,
        "beta": beta, "learning_rate": learning_rate, "k_error": k_error, "k_rate": k_rate,
        "initial_angle_deg": initial_angle_deg, "disturbance_torque_Nm": disturbance_torque,
        "seed": seed, "torque_limits_Nm": limits.tolist(),
        "qerr_mean_rad": float(np.mean(qerr)), "qerr_max_rad": float(np.max(qerr)),
        "tau_mean_Nm": float(np.mean(np.linalg.norm(tau_arr, axis=1))),
        "trace": str(csv_path),
    }
    args = {
        "controller": controller_name, "mission": mission, "duration": duration, "dt": dt,
        "beta": beta, "learning_rate": learning_rate, "k_error": k_error, "k_rate": k_rate,
        "initial_angle_deg": initial_angle_deg, "disturbance_torque": disturbance_torque,
        "seed": seed, "visualize": visualize,
    }
    prov = manifest(ACC_ROOT, "qdrone2_qlabs_kinematic_mirror", controller_name,
                     ACC_ROOT/"third_party/mujoco_menagerie/skydio_x2/scene.xml", args)
    prov["derived"] = {"body_inertia_kgm2": inertia.tolist(), "torque_limits_Nm": limits.tolist()}
    write_json(output/"summary.json", summary)
    write_json(output/"manifest.json", prov)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controller", default="online-pes-adaptive",
                         choices=["classical", "fixed-residual", "adaptive-residual",
                                  "online-pes", "online-pes-fixed", "online-pes-adaptive"])
    parser.add_argument("--mission", default="hard45",
                         choices=["hover", "roll", "full3", "hard45", "hardstep", "yaw360"])
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--dt", type=float, default=5e-4)
    parser.add_argument("--beta", type=float, default=0.5)
    parser.add_argument("--learning-rate", type=float, default=8e-4)
    parser.add_argument("--k-error", type=float, default=8.0)
    parser.add_argument("--k-rate", type=float, default=0.0)
    parser.add_argument("--initial-angle-deg", type=float, default=0.0)
    parser.add_argument("--disturbance-torque", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--no-visualize", action="store_true", help="skip QLabs, just run + log")
    parser.add_argument("--no-realtime", action="store_true", help="run as fast as possible")
    parser.add_argument("--speed", type=float, default=1.0, help="realtime playback speed multiplier")
    parser.add_argument("--viz-every", type=int, default=20, help="push a QLabs pose update every N control steps")
    args = parser.parse_args()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output = QDRONE_ROOT/"results"/"qlabs_twin"/f"{args.controller}_{args.mission}_{timestamp}"

    summary = run_twin(
        controller_name=args.controller, mission=args.mission, duration=args.duration,
        dt=args.dt, beta=args.beta, learning_rate=args.learning_rate,
        k_error=args.k_error, k_rate=args.k_rate,
        initial_angle_deg=args.initial_angle_deg, disturbance_torque=args.disturbance_torque,
        seed=args.seed, visualize=not args.no_visualize, realtime=not args.no_realtime,
        speed=args.speed, viz_every=args.viz_every, output=output,
    )
    print(f"qerr_mean_rad={summary['qerr_mean_rad']:.6f}  qerr_max_rad={summary['qerr_max_rad']:.6f}")
    print(f"trace: {summary['trace']}")


if __name__ == "__main__":
    main()
