"""MuJoCo hover validation with a Nengo attitude-torque controller.

This script keeps the stable hover shell from ``mujoco_hover_paper_validation``
and replaces the direct analytic torque command with a Nengo network:

    input  = [axis_error_x, axis_error_y, axis_error_z, wx, wy, wz]
    output = [tau_x, tau_y, tau_z]

The decoded function is the same scaled quaternion PD map used in the stable
MuJoCo run.  This makes the first Nengo controller a controlled replacement:
same plant, same reference, same gains, but neuralized torque computation.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import mujoco
import mujoco.viewer
import nengo
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

try:
    from nengo_neurons import AdaptiveHyperLIF_b20_gs80_rtc15, HyperLIF
except ImportError:  # Allows standard Nengo neurons even if custom package is not installed editable.
    AdaptiveHyperLIF_b20_gs80_rtc15 = None
    HyperLIF = None


MODEL_XMLS = {
    "skydio_x2": PROJECT_ROOT / "third_party" / "mujoco_menagerie" / "skydio_x2" / "scene.xml",
    "bitcraze_crazyflie_2": PROJECT_ROOT
    / "third_party"
    / "mujoco_menagerie"
    / "bitcraze_crazyflie_2"
    / "scene.xml",
}
LOGS_DIR = PROJECT_ROOT / "results" / "logs"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures" / "quaternion_quad" / "mujoco_hover_nengo_controller"


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


def reference_euler(t: float, mission: str) -> np.ndarray:
    if mission == "roll":
        return np.array([0.25 * np.sin(0.7 * t), 0.0, 0.0], dtype=float)
    if mission == "full3":
        return 0.5 * np.sin(t + np.array([0.0, np.pi / 2.0, np.pi], dtype=float))
    if mission == "step":
        return np.array([1.0 if t >= 1.0 else 0.0, 1.0 if t >= 5.0 else 0.0, 1.0 if t >= 9.0 else 0.0])
    raise ValueError(f"Unknown mission: {mission}")


def reference_quat(t: float, mission: str) -> np.ndarray:
    return euler_to_quat(*reference_euler(t, mission))


def find_freejoint(model: mujoco.MjModel) -> int:
    for j in range(model.njnt):
        if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
            return j
    raise RuntimeError("No freejoint found in model.")


def neuron_type(name: str) -> nengo.neurons.NeuronType:
    if name == "lif":
        return nengo.LIF()
    if name == "lifrate":
        return nengo.LIFRate()
    if name == "rectified":
        return nengo.RectifiedLinear()
    if name == "hyperlif":
        if HyperLIF is None:
            raise RuntimeError("HyperLIF is not importable. Install the project editable first.")
        return HyperLIF()
    if name == "adaptivehyperlif_tuned":
        if AdaptiveHyperLIF_b20_gs80_rtc15 is None:
            raise RuntimeError("AdaptiveHyperLIF_b20_gs80_rtc15 is not importable. Install the project editable first.")
        return AdaptiveHyperLIF_b20_gs80_rtc15()
    raise ValueError(f"Unknown neuron type: {name}")


def build_scaled_gains(inertia: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    wn = np.array([4.0, 4.0, 3.5], dtype=float)
    zeta = np.array([0.95, 0.95, 0.95], dtype=float)
    alpha_max = np.array([12.0, 12.0, 10.0], dtype=float)
    kq = 2.0 * inertia * (wn**2)
    kw = 2.0 * zeta * wn * inertia
    tau_limit = np.maximum(inertia * alpha_max, np.array([0.03, 0.03, 0.02]))
    return kq, kw, tau_limit


def build_nengo_controller(
    kq: np.ndarray,
    kw: np.ndarray,
    tau_limit: np.ndarray,
    dt: float,
    n_neurons: int,
    neuron_name: str,
    synapse: float,
    radius: float,
    seed: int,
    max_rate_low: float,
    max_rate_high: float,
    intercept_low: float,
    intercept_high: float,
) -> tuple[nengo.Simulator, np.ndarray, np.ndarray]:
    state = np.zeros(6, dtype=float)
    output = np.zeros(3, dtype=float)

    def stim_func(_t: float) -> np.ndarray:
        return state

    def capture_func(_t: float, x: np.ndarray) -> None:
        output[:] = np.clip(x, -tau_limit, tau_limit)

    def torque_func(x: np.ndarray) -> np.ndarray:
        axis_err = x[:3]
        omega = x[3:]
        return np.clip(-kq * axis_err - kw * omega, -tau_limit, tau_limit)

    with nengo.Network(label=f"MuJoCo {neuron_name} quaternion controller") as model:
        stim = nengo.Node(stim_func, size_out=6, label="axis_error_and_omega")
        ens = nengo.Ensemble(
            n_neurons=n_neurons,
            dimensions=6,
            neuron_type=neuron_type(neuron_name),
            radius=radius,
            max_rates=nengo.dists.Uniform(max_rate_low, max_rate_high),
            intercepts=nengo.dists.Uniform(intercept_low, intercept_high),
            seed=seed,
            label=f"{neuron_name}_controller",
        )
        torque = nengo.Node(capture_func, size_in=3, label="tau_body")
        nengo.Connection(stim, ens, synapse=None)
        nengo.Connection(ens, torque, function=torque_func, synapse=synapse)

    sim = nengo.Simulator(model, dt=dt, progress_bar=False)
    return sim, state, output


def run(args: argparse.Namespace) -> None:
    xml_path = Path(args.xml_path) if args.xml_path else MODEL_XMLS[args.quad]
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

    sim, ctrl_state, ctrl_output = build_nengo_controller(
        kq,
        kw,
        tau_limit,
        args.dt,
        args.n_neurons,
        args.neuron,
        args.synapse,
        args.radius,
        args.seed,
        args.max_rate_low,
        args.max_rate_high,
        args.intercept_low,
        args.intercept_high,
    )

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
        vel = np.array(data.qvel[qvel_adr : qvel_adr + 3], dtype=float)
        q_mj = q_normalize(np.array(data.qpos[qpos_adr + 3 : qpos_adr + 7], dtype=float))
        omega = np.array(data.qvel[qvel_adr + 3 : qvel_adr + 6], dtype=float)
        q_meas = mujoco_quat_to_paper_quat(q_mj)
        q_ref = reference_quat(t, args.mission)
        eul_ref = reference_euler(t, args.mission)
        q_err = q_mul(q_ref, q_conj(q_meas))
        if q_err[0] < 0.0:
            q_err = -q_err

        ctrl_state[:] = np.concatenate([q_err[1:4], omega])
        sim.step()
        tau_body = np.clip(ctrl_output.copy(), -tau_limit, tau_limit)

        r_wb = data.xmat[body_id].reshape(3, 3)
        body_z_world = r_wb[:, 2]
        tilt_cos = max(0.35, body_z_world[2])
        collective = total_mass * (gravity + 6.0 * (args.z_ref - pos[2]) + 4.0 * (0.0 - vel[2])) / tilt_cos
        collective = np.clip(collective, 0.0, 2.5 * total_mass * max(gravity, 1.0))
        force_world = collective * body_z_world
        a_xy = -1.5 * pos[:2] - 2.2 * vel[:2]
        force_world[:2] += total_mass * clip_norm(a_xy, 3.0)

        data.xfrc_applied[body_id, 0:3] = force_world
        data.xfrc_applied[body_id, 3:6] = r_wb @ tau_body
        mujoco.mj_step(model, data)

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
                "phi_err": eul_err[0],
                "theta_err": eul_err[1],
                "psi_err": eul_err[2],
                "qerr_angle": quat_angle_error(q_err),
                "z": pos[2],
                "tau_x": tau_body[0],
                "tau_y": tau_body[1],
                "tau_z": tau_body[2],
            }
        )

    if args.viewer:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            while viewer.is_running() and data.time < args.sim_time:
                tic = time.time()
                step_controller()
                viewer.sync()
                sleep_time = model.opt.timestep - (time.time() - tic)
                if sleep_time > 0:
                    time.sleep(sleep_time)
    else:
        while data.time < args.sim_time:
            step_controller()

    sim.close()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    stem = (
        f"mujoco_hover_nengo_{args.quad}_{args.mission}_{args.neuron}"
        f"_n{args.n_neurons}_r{args.radius:g}_syn{args.synapse:g}_seed{args.seed}_dt{args.dt:g}"
    ).replace(".", "p")
    csv_path = LOGS_DIR / f"{stem}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    arr = {key: np.array([row[key] for row in rows]) for key in rows[0]}
    tau = np.column_stack([arr["tau_x"], arr["tau_y"], arr["tau_z"]])
    rmse = np.sqrt(np.mean(np.column_stack([arr["phi_err"], arr["theta_err"], arr["psi_err"]]) ** 2, axis=0))
    summary_path = LOGS_DIR / f"{stem}_summary.txt"
    summary_path.write_text(
        "\n".join(
            [
                "MuJoCo hover Nengo controller",
                f"quad={args.quad}",
                f"xml_path={xml_path}",
                f"mission={args.mission}",
                f"neuron={args.neuron}",
                f"n_neurons={args.n_neurons}",
                f"dt={args.dt}",
                f"synapse={args.synapse}",
                f"radius={args.radius}",
                f"seed={args.seed}",
                f"max_rates=[{args.max_rate_low}, {args.max_rate_high}]",
                f"intercepts=[{args.intercept_low}, {args.intercept_high}]",
                f"KQ={kq.tolist()}",
                f"KW={kw.tolist()}",
                f"tau_limit={tau_limit.tolist()}",
                f"rmse_phi_theta_psi={rmse.tolist()}",
                f"qerr_mean={float(np.mean(arr['qerr_angle']))}",
                f"qerr_max={float(np.max(arr['qerr_angle']))}",
                f"tau_mean={float(np.mean(np.linalg.norm(tau, axis=1)))}",
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
    fig.suptitle(f"MuJoCo Nengo controller: {args.mission}, {args.neuron}")
    fig.tight_layout()
    figure_path = FIGURES_DIR / f"{stem}_attitude.png"
    fig.savefig(figure_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(summary_path.read_text(encoding="utf-8"))
    print(f"Saved CSV: {csv_path}")
    print(f"Saved figure: {figure_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quad", choices=sorted(MODEL_XMLS), default="skydio_x2")
    parser.add_argument("--xml-path", default="", help="Optional explicit MuJoCo XML path.")
    parser.add_argument("--mission", choices=["roll", "full3", "step"], default="roll")
    parser.add_argument(
        "--neuron",
        choices=["lif", "lifrate", "rectified", "hyperlif", "adaptivehyperlif_tuned"],
        default="lifrate",
    )
    parser.add_argument("--n-neurons", type=int, default=400)
    parser.add_argument("--radius", type=float, default=1.5)
    parser.add_argument("--seed", type=int, default=2)
    parser.add_argument("--max-rate-low", type=float, default=100.0)
    parser.add_argument("--max-rate-high", type=float, default=200.0)
    parser.add_argument("--intercept-low", type=float, default=-0.8)
    parser.add_argument("--intercept-high", type=float, default=0.8)
    parser.add_argument("--dt", type=float, default=0.0005)
    parser.add_argument("--sim-time", type=float, default=15.0)
    parser.add_argument("--synapse", type=float, default=0.002)
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--z-ref", type=float, default=1.0)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
