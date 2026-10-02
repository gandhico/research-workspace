"""
Main runner for HyperLIF gate-state residual quadrotor control.
Supports both Skydio X2 (rotor-level) and Crazyflie 2 (virtual wrench).

Usage examples:
    python runners/run_rotor_level.py --quad skydio_x2 --controller classical --mission hover --sim-time 20 --viewer --dashboard --save-csv

    python runners/run_rotor_level.py --quad skydio_x2 --controller rotor_residual_adaptive_hyperlif --mission hard45 --sim-time 45 --residual-blend 0.10 --gate-gain 100000 --viewer --dashboard --save-csv --save-figures

    python runners/run_rotor_level.py --quad bitcraze_crazyflie_2 --controller direct_adaptive_hyperlif --mission hard45 --sim-time 45 --blend 0.50 --gate-gain 100000 --activity-mode gate --direct-scale control --viewer --save-csv

Control architecture (rotor-level, Skydio X2):
    q_err → ClassicalPD → tau → wrench → B_inv → u_nominal
                                                    |
    HyperLIF gate residual → delta_u ──────────────+
                                                    |
                                              clip(u_min, u_max) → MuJoCo actuators

Control architecture (body-torque, CF2):
    q_err → DirectNeuronController → tau → xfrc_applied OR CF2 virtual wrench actuators
    Hover support:  external collective force + lateral tether (applied via xfrc_applied)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

# Add project src to path
_RUNNER_DIR = Path(__file__).resolve().parent
_PROJECT    = _RUNNER_DIR.parent
if str(_PROJECT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT / "src"))

import mujoco
try:
    import mujoco.viewer as mujoco_viewer
except Exception:
    mujoco_viewer = None

from quad.models import load_drone, KNOWN_QUADS
from quad.reference import reference_euler, reference_quat, KNOWN_MISSIONS
from quad.math_utils import quat_angle_error, quat_to_euler, wrap_to_pi
from quad.bridge import (
    get_state, compute_hover_force,
    apply_body_torque, apply_rotor_commands, apply_cf2_wrench,
)
from rotor.mixer import wrench_to_motors, hover_wrench, saturation_flags
from controllers.factory import make_controller
from controllers.classical import ClassicalPD
from controllers.neural_controllers import RotorResidualController
from logging_utils.logger import (
    make_stem, save_csv, save_summary, save_npz,
    save_run_config, compute_summary,
)
from viz.dashboard import Dashboard, DashState


RESULTS_DIR = _PROJECT / "results"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="HyperLIF gate-state residual quadrotor controller",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ---- Simulation target ----
    p.add_argument("--quad", choices=sorted(KNOWN_QUADS), default="skydio_x2",
                   help="Quadrotor model")
    p.add_argument("--mission", choices=KNOWN_MISSIONS, default="hover",
                   help="Reference trajectory")
    p.add_argument("--controller", default="classical",
                   help="Controller name (classical, direct_hyperlif, rotor_residual_adaptive_hyperlif, ...)")
    p.add_argument("--sim-time", type=float, default=20.0)
    p.add_argument("--dt", type=float, default=0.0005)
    p.add_argument("--z-ref", type=float, default=1.0)
    p.add_argument("--seed", type=int, default=1)

    # ---- Direct-neuron body-torque options ----
    p.add_argument("--blend", type=float, default=0.20,
                   help="Blend factor for direct-neuron body-torque controllers")
    p.add_argument("--activity-mode", choices=["voltage","gate","events"], default="voltage")
    p.add_argument("--direct-scale", choices=["paper","control"], default="paper")
    p.add_argument("--gate-gain", type=float, default=1.0,
                   help="Gate activity scaling factor")

    # ---- Rotor-residual options ----
    p.add_argument("--residual-blend", type=float, default=0.10,
                   help="Blend factor for rotor-residual controllers")
    p.add_argument("--u-scale", type=float, default=None,
                   help="Rotor residual scale [N]. Default: 5%% of motor range")

    # ---- Nengo options ----
    p.add_argument("--n-neurons", type=int, default=400)
    p.add_argument("--radius", type=float, default=1.5)
    p.add_argument("--synapse", type=float, default=0.002)

    # ---- Viewer / visualization ----
    p.add_argument("--viewer", action="store_true", help="Open MuJoCo 3D viewer")
    p.add_argument("--viewer-sync-every", type=int, default=20)
    p.add_argument("--viewer-follow", action="store_true")
    p.add_argument("--viewer-distance", type=float, default=3.0)
    p.add_argument("--viewer-elevation", type=float, default=-20.0)
    p.add_argument("--viewer-azimuth", type=float, default=90.0)
    p.add_argument("--realtime", action="store_true", help="Slow to real-time during viewer")

    p.add_argument("--dashboard", action="store_true", help="Show live matplotlib dashboard")
    p.add_argument("--dashboard-update-every", type=int, default=100)
    p.add_argument("--dashboard-window", type=float, default=10.0,
                   help="Time window shown in dashboard [s]")

    # ---- Output options ----
    p.add_argument("--save-csv", action="store_true")
    p.add_argument("--save-figures", action="store_true")
    p.add_argument("--save-npz", action="store_true")
    p.add_argument("--no-save", action="store_true", help="Suppress all file output")
    p.add_argument("--output-dir", type=Path, default=None)

    return p.parse_args()


def _find_follow_body(model) -> int:
    keywords = ["crazyflie","cf2","skydio","x2","base","chassis","quad","drone","body"]
    names = [(i, (mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i) or "").lower())
             for i in range(model.nbody)]
    for kw in keywords:
        for bid, nm in names:
            if bid > 0 and kw in nm:
                return bid
    for j in range(model.njnt):
        if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
            return int(model.jnt_bodyid[j])
    return 1 if model.nbody > 1 else 0


def _update_camera(viewer, data, body_id, distance, elevation, azimuth):
    try:
        with viewer.lock():
            viewer.cam.type = 0
            viewer.cam.lookat[:] = data.xpos[body_id]
            viewer.cam.distance = distance
            viewer.cam.elevation = elevation
            viewer.cam.azimuth = azimuth
    except Exception:
        viewer.cam.type = 0
        viewer.cam.lookat[:] = data.xpos[body_id]
        viewer.cam.distance = distance
        viewer.cam.elevation = elevation
        viewer.cam.azimuth = azimuth


def run(args: argparse.Namespace) -> dict:
    np.random.seed(args.seed)

    # --- Load drone model ---
    params = load_drone(args.quad)
    mj_model = mujoco.MjModel.from_xml_path(str(params.xml_path))
    mj_data  = mujoco.MjData(mj_model)
    mj_model.opt.timestep = args.dt

    # --- Build controller ---
    ctrl = make_controller(
        name=args.controller, params=params, dt=args.dt,
        blend=args.blend,
        activity_mode=args.activity_mode,
        scale=args.direct_scale,
        gate_gain=args.gate_gain,
        residual_blend=args.residual_blend,
        u_scale=args.u_scale,
        n_neurons=args.n_neurons, radius=args.radius,
        synapse=args.synapse, seed=args.seed,
    )

    # --- Initial state ---
    pa = params.qpos_adr
    mj_data.qpos[pa:pa+3]   = [0.0, 0.0, args.z_ref]
    mj_data.qpos[pa+3:pa+7] = [1.0, 0.0, 0.0, 0.0]
    mj_data.qvel[:]          = 0.0
    mj_data.xfrc_applied[:]  = 0.0
    if mj_model.nu > 0:
        mj_data.ctrl[:] = params.hover_cmd_vector()
    mujoco.mj_forward(mj_model, mj_data)

    is_rotor_residual = isinstance(ctrl, RotorResidualController)
    is_classical      = isinstance(ctrl, ClassicalPD)
    use_rotor_acts    = params.actuator_mode == "rotor4" and is_rotor_residual

    # --- Viewer ---
    viewer = None
    follow_body_id = _find_follow_body(mj_model)
    if args.viewer and mujoco_viewer is not None:
        viewer = mujoco_viewer.launch_passive(mj_model, mj_data)
        if args.viewer_follow:
            _update_camera(viewer, mj_data, follow_body_id,
                           args.viewer_distance, args.viewer_elevation, args.viewer_azimuth)
        print("MuJoCo viewer launched.")

    # --- Dashboard ---
    dash = Dashboard(
        enabled=args.dashboard,
        update_every=args.dashboard_update_every,
        max_t_shown=args.dashboard_window,
    )
    if args.dashboard:
        title = f"{args.quad} | {args.mission} | {args.controller}"
        dash.setup(has_rotors=use_rotor_acts, title=title)

    # --- Simulation loop ---
    rows: list[dict] = []
    step_count = 0

    # For classical+rotor body: compute T using hover_wrench each step
    # For rotor_residual: RotorResidualController handles everything

    while mj_data.time < args.sim_time:
        t = float(mj_data.time)
        mj_data.xfrc_applied[:] = 0.0

        state   = get_state(mj_model, mj_data, params)
        q_ref   = reference_quat(t, args.mission, args.sim_time)
        eul_ref = reference_euler(t, args.mission, args.sim_time)

        # ---- Control computation ----
        if use_rotor_acts:
            # Rotor-level: RotorResidualController → 4 motor commands
            T = hover_wrench(params, state.pos, state.vel, state.R_wb, args.z_ref)
            u_final, u_nominal, info = ctrl.step(q_ref, state.q, state.omega, T, args.dt)
            apply_rotor_commands(mj_model, mj_data, params, u_final)

            tau_body  = info["tau_pd"]
            motors    = u_final
            delta_u   = info["delta_u"]
            sat_flags = saturation_flags(u_final, params)
            q_err     = info["q_err"]
            e_q       = info["e_q"]
            collective = T

        elif params.actuator_mode == "rotor4" and not use_rotor_acts:
            # Classical or direct-neuron body-torque on X2: still use actuators
            # Compute body torques then mix to motors
            out = ctrl.step(q_ref, state.q, state.omega, args.dt)
            tau_body = out.tau
            T = hover_wrench(params, state.pos, state.vel, state.R_wb, args.z_ref)
            u_final = wrench_to_motors(T, tau_body, params, clip=True)
            apply_rotor_commands(mj_model, mj_data, params, u_final)

            motors    = u_final
            sat_flags = saturation_flags(u_final, params)
            q_err     = out.q_err
            e_q       = out.e_q
            info      = out.info
            delta_u   = np.zeros(4)
            collective = T

        elif params.actuator_mode == "wrench4":
            # CF2: use xfrc_applied for both hover and attitude torques.
            # The CF2 virtual wrench actuators have max torque ±1e-5 Nm — far below
            # the inertia-scaled kq/kw torques needed for attitude control.
            # xfrc_applied bypasses this limit (consistent with legacy benchmark approach).
            hover_f = compute_hover_force(state, params, z_ref=args.z_ref)
            out = ctrl.step(q_ref, state.q, state.omega, args.dt)
            tau_body = out.tau
            apply_body_torque(mj_data, params, tau_body, hover_f)

            motors    = None
            sat_flags = None
            q_err     = out.q_err
            e_q       = out.e_q
            info      = out.info
            delta_u   = np.zeros(3)
            collective = float(np.linalg.norm(hover_f))

        mujoco.mj_step(mj_model, mj_data)
        step_count += 1

        # ---- Viewer sync ----
        if viewer is not None:
            if not viewer.is_running():
                print("Viewer closed.")
                break
            if step_count % args.viewer_sync_every == 0:
                if args.viewer_follow:
                    _update_camera(viewer, mj_data, follow_body_id,
                                   args.viewer_distance, args.viewer_elevation, args.viewer_azimuth)
                viewer.sync()
                if args.realtime:
                    time.sleep(args.dt * args.viewer_sync_every)

        # ---- Logging ----
        eul_meas = quat_to_euler(state.q)
        eul_err  = wrap_to_pi(eul_meas - eul_ref)

        row: dict = {
            "t":         t,
            "phi_ref":   eul_ref[0], "theta_ref": eul_ref[1], "psi_ref": eul_ref[2],
            "phi":       eul_meas[0], "theta": eul_meas[1], "psi": eul_meas[2],
            "phi_err":   eul_err[0], "theta_err": eul_err[1], "psi_err": eul_err[2],
            "q0": state.q[0], "q1": state.q[1], "q2": state.q[2], "q3": state.q[3],
            "q0_ref": q_ref[0], "q1_ref": q_ref[1], "q2_ref": q_ref[2], "q3_ref": q_ref[3],
            "qerr_angle": quat_angle_error(q_err),
            "wx": state.omega[0], "wy": state.omega[1], "wz": state.omega[2],
            "tau_x": tau_body[0], "tau_y": tau_body[1], "tau_z": tau_body[2],
            "collective": collective,
            "z":   state.pos[2],
            "x":   state.pos[0], "y": state.pos[1],
            "event_count":  float(info.get("event_count", 0.0)),
            "activity_mean": float(info.get("activity_mean", 0.0)),
            "gate_mean":    float(info.get("gate_mean", 0.0)),
            "gate_max":     float(info.get("gate_max", 0.0)),
            "voltage_mean": float(info.get("voltage_mean", 0.0)),
        }

        if motors is not None:
            for i, u in enumerate(motors):
                row[f"motor_{i+1}"] = float(u)
            row["rotor_sat_flag"] = float(np.sum(sat_flags)) if sat_flags is not None else 0.0
            for i, du in enumerate(delta_u):
                row[f"delta_u_{i+1}"] = float(du)

        rows.append(row)

        # ---- Dashboard update ----
        if args.dashboard:
            gate_arr    = np.zeros(8)
            volt_arr    = np.zeros(8)
            events_arr  = np.zeros(8)
            nr = getattr(ctrl, "_last_result", None) or getattr(getattr(ctrl, "neuron", None), "_last", None)
            if nr is None and hasattr(ctrl, "_last_result"):
                nr = ctrl._last_result
            if nr is not None:
                n = len(nr.gate)
                gate_arr[:n]   = nr.gate
                volt_arr[:n]   = nr.voltage
                events_arr[:n] = nr.events

            ds = DashState(
                t=t, q=state.q, q_ref=q_ref,
                euler=eul_meas, euler_ref=eul_ref,
                omega=state.omega, tau=tau_body,
                collective=collective,
                motors=motors,
                qerr_angle=row["qerr_angle"],
                z=state.pos[2],
                gate=gate_arr, voltage=volt_arr, events=events_arr,
                residual=delta_u,
                rotor_sat_flags=sat_flags,
            )
            dash.update(ds)

    # ---- Cleanup ----
    if viewer is not None:
        viewer.close()
    if hasattr(ctrl, "close"):
        ctrl.close()

    # ---- Summary ----
    tau_lim = params.tau_limit
    run_config = vars(args)
    run_config.update({
        "quad_mass":    params.total_mass,
        "quad_inertia": params.body_inertia.tolist(),
        "actuator_mode": params.actuator_mode,
        "kq": params.kq.tolist(),
        "kw": params.kw.tolist(),
        "tau_limit": tau_lim.tolist(),
    })

    summary = compute_summary(rows, tau_lim, {
        "controller": args.controller,
        "quad": args.quad,
        "mission": args.mission,
        "dt": args.dt,
        "sim_time": args.sim_time,
    })

    if not args.no_save and (args.save_csv or args.save_figures or args.save_npz):
        stem = make_stem(args.quad, args.mission, args.controller,
                         args.dt, args.sim_time, args.seed)
        out_dir = args.output_dir or RESULTS_DIR
        logs_dir = out_dir / "logs"
        figs_dir = out_dir / "figures"

        if args.save_csv:
            csv_path = logs_dir / f"{stem}.csv"
            save_csv(rows, csv_path)
            summary_path = logs_dir / f"{stem}_summary.json"
            save_summary(summary, summary_path)
            config_path  = logs_dir / f"{stem}_config.json"
            save_run_config(run_config, config_path)
            print(f"CSV: {csv_path}")
            print(f"Summary: {summary_path}")

        if args.save_npz:
            npz_path = logs_dir / f"{stem}.npz"
            save_npz(rows, npz_path)
            print(f"NPZ: {npz_path}")

        if args.save_figures:
            _save_figures(rows, params, summary, args, figs_dir, stem)
            dash.save_figures(figs_dir, stem=stem)

    dash.close()

    # Print summary to console
    print("\n" + "="*60)
    print(f"Run summary: {args.quad} | {args.mission} | {args.controller}")
    print("="*60)
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"  {k:30s} = {v:.6g}")
        else:
            print(f"  {k:30s} = {v}")
    print("="*60 + "\n")

    return summary


def _save_figures(rows: list[dict], params, summary: dict,
                  args, figs_dir: Path, stem: str) -> None:
    """Generate and save standard result plots."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    arr = {k: np.array([r[k] for r in rows], dtype=float) for k in rows[0]}
    t = arr["t"]
    figs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Euler angles
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for i, (c, cr, lb) in enumerate([("phi","phi_ref","roll"),
                                      ("theta","theta_ref","pitch"),
                                      ("psi","psi_ref","yaw")]):
        axes[i].plot(t, np.degrees(arr[cr]), "--", label="ref", linewidth=1.5)
        axes[i].plot(t, np.degrees(arr[c]),  "-",  label="meas", linewidth=1.5)
        axes[i].set_ylabel(f"{lb} [deg]"); axes[i].grid(True, alpha=0.3)
    axes[0].legend(fontsize=8)
    axes[-1].set_xlabel("t [s]")
    fig.suptitle(f"Euler angles — {args.controller} | {args.mission}")
    fig.savefig(figs_dir / f"{stem}_euler.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    # 2. Quaternion error + altitude
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(t, arr["qerr_angle"], "r-", linewidth=1.5)
    axes[0].set_ylabel("qerr_angle [rad]"); axes[0].grid(True, alpha=0.3)
    axes[0].set_title(f"qerr_mean={summary['qerr_mean']:.4f} rad | score={summary['score']:.4f}")
    axes[1].plot(t, arr["z"], "b-", linewidth=1.5)
    axes[1].axhline(args.z_ref, linestyle="--", color="gray", label="z_ref")
    axes[1].set_ylabel("z [m]"); axes[1].set_xlabel("t [s]"); axes[1].grid(True, alpha=0.3)
    fig.suptitle(f"Tracking — {args.controller} | {args.mission}")
    fig.savefig(figs_dir / f"{stem}_tracking.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    # 3. Motor commands (if available)
    motor_keys = [k for k in arr if k.startswith("motor_")]
    if motor_keys:
        fig, ax = plt.subplots(figsize=(10, 4))
        for k in sorted(motor_keys):
            ax.plot(t, arr[k], linewidth=1.0, label=k)
        ax.set_ylabel("Motor cmd [N]"); ax.set_xlabel("t [s]")
        ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
        ax.set_title(f"Motor commands — {args.controller}")
        fig.savefig(figs_dir / f"{stem}_motors.png", dpi=180, bbox_inches="tight")
        plt.close(fig)

    # 4. Neural gate state
    if np.max(arr.get("gate_max", np.zeros(len(rows)))) > 1e-8:
        fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
        axes[0].plot(t, arr["gate_mean"], label="gate_mean")
        axes[0].plot(t, arr["gate_max"], "--", label="gate_max")
        axes[0].set_ylabel("Gate state"); axes[0].grid(True, alpha=0.3); axes[0].legend(fontsize=8)
        axes[1].plot(t, arr["voltage_mean"], color="C1")
        axes[1].set_ylabel("Voltage mean"); axes[1].grid(True, alpha=0.3)
        axes[2].plot(t, arr["event_count"], "k.", markersize=1)
        axes[2].set_ylabel("Events/step"); axes[2].set_xlabel("t [s]"); axes[2].grid(True, alpha=0.3)
        fig.suptitle(f"Neural state — {args.controller}")
        fig.savefig(figs_dir / f"{stem}_neural.png", dpi=180, bbox_inches="tight")
        plt.close(fig)

    print(f"Figures saved to: {figs_dir}")


def main() -> None:
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()
