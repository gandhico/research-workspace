"""Gain sweep for replicating the Fresk/Nikolakopoulos quaternion controller.

Run from the project root:

    python experiments/quaternion_quad/paper_gain_sweep_replication.py --preset quick

The script runs the paper's three attitude tests on the repo-local Skydio
MuJoCo model:

    step: 1 rad steps on roll, pitch, yaw at different times
    sine: 0.5 rad amplitude, 1 rad/s, phase shifted channels
    flip: 0 -> 2*pi roll ramp

It saves:

    results/logs/paper_gain_sweep_metrics.csv
    results/logs/paper_gain_sweep_summary.txt
    results/figures/quaternion_quad/paper_replication/

The sweep varies Pq and Pw around the paper values Pq=20 and Pw=4. Torque is
bounded at +/-4 Nm, matching the paper's simulation section.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import mujoco
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
XML_PATH = PROJECT_ROOT / "third_party" / "mujoco_menagerie" / "skydio_x2" / "scene.xml"
LOGS_DIR = PROJECT_ROOT / "results" / "logs"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures" / "quaternion_quad" / "paper_replication"

PAPER_PQ = 20.0
PAPER_PW = 4.0
PAPER_TAU_LIMIT = 4.0


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
    q0 = np.clip(q_err[0], -1.0, 1.0)
    return float(2.0 * np.arctan2(np.linalg.norm(q_err[1:]), max(1e-12, abs(q0))))


def mujoco_quat_to_paper_quat(q_mj: np.ndarray) -> np.ndarray:
    return q_conj(q_normalize(q_mj))


def find_freejoint(model: mujoco.MjModel) -> int:
    for j in range(model.njnt):
        if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
            return j
    raise RuntimeError("No freejoint found in model.")


def reference_euler(t: float, scenario: str) -> np.ndarray:
    if scenario == "step":
        return np.array(
            [
                1.0 if t >= 1.0 else 0.0,
                1.0 if t >= 5.0 else 0.0,
                1.0 if t >= 9.0 else 0.0,
            ],
            dtype=float,
        )
    if scenario == "sine":
        amp = np.array([0.5, 0.5, 0.5], dtype=float)
        phase = np.array([0.0, np.pi / 2.0, np.pi], dtype=float)
        return amp * np.sin(1.0 * t + phase)
    if scenario == "flip":
        phi = np.clip((2.0 * np.pi / 5.0) * t, 0.0, 2.0 * np.pi)
        return np.array([phi, 0.0, 0.0], dtype=float)
    raise ValueError(f"Unknown scenario: {scenario}")


def reference_quat(t: float, scenario: str) -> np.ndarray:
    phi, theta, psi = reference_euler(t, scenario)
    return euler_to_quat(phi, theta, psi)


def scenario_time(scenario: str) -> float:
    return 5.0 if scenario == "flip" else 15.0


def gain_grid(preset: str) -> list[tuple[float, float]]:
    if preset == "paper-only":
        return [(1.0, 1.0)]
    if preset == "quick":
        p_scales = [0.35, 0.5, 0.75, 1.0, 1.25]
        w_scales = [0.6, 0.8, 1.0, 1.2, 1.5]
    else:
        p_scales = [0.2, 0.35, 0.5, 0.65, 0.8, 1.0, 1.2, 1.5]
        w_scales = [0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0]
    return [(p, w) for p in p_scales for w in w_scales]


def simulate(
    scenario: str,
    p_scale: float,
    w_scale: float,
    dt: float,
    noise: float,
    seed: int,
) -> tuple[dict[str, float | str], dict[str, np.ndarray]]:
    model = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data = mujoco.MjData(model)
    model.opt.gravity[:] = np.array([0.0, 0.0, 0.0])
    model.opt.timestep = dt

    free_jid = find_freejoint(model)
    body_id = model.jnt_bodyid[free_jid]
    qpos_adr = model.jnt_qposadr[free_jid]
    qvel_adr = model.jnt_dofadr[free_jid]

    if model.nu > 0:
        data.ctrl[:] = 0.0
    data.qpos[qpos_adr : qpos_adr + 3] = 0.0
    data.qpos[qpos_adr + 3 : qpos_adr + 7] = np.array([1.0, 0.0, 0.0, 0.0])
    data.qvel[qvel_adr : qvel_adr + 6] = 0.0
    data.xfrc_applied[:] = 0.0
    mujoco.mj_forward(model, data)

    rng = np.random.default_rng(seed)
    pq = PAPER_PQ * p_scale
    pw = PAPER_PW * w_scale
    tau_limit = PAPER_TAU_LIMIT
    sim_time = scenario_time(scenario)

    logs: dict[str, list[np.ndarray | float]] = {
        "t": [],
        "eul_ref": [],
        "eul_meas": [],
        "q_ref": [],
        "q_meas": [],
        "q_err": [],
        "qerr_angle": [],
        "tau": [],
        "omega": [],
    }

    while data.time < sim_time:
        t = float(data.time)
        data.qpos[qpos_adr : qpos_adr + 3] = 0.0
        data.qvel[qvel_adr : qvel_adr + 3] = 0.0
        data.xfrc_applied[:] = 0.0

        q_mj = q_normalize(np.array(data.qpos[qpos_adr + 3 : qpos_adr + 7], dtype=float))
        q_meas = mujoco_quat_to_paper_quat(q_mj)
        omega = np.array(data.qvel[qvel_adr + 3 : qvel_adr + 6], dtype=float)

        if noise > 0.0:
            q_meas = q_normalize(q_meas + noise * rng.standard_normal(4))
            omega = omega + noise * rng.standard_normal(3)

        q_ref = reference_quat(t, scenario)
        eul_ref = reference_euler(t, scenario)
        q_err = q_mul(q_ref, q_conj(q_meas))

        if scenario != "flip" and q_err[0] < 0.0:
            q_err = -q_err

        tau_body = -pq * q_err[1:] - pw * omega
        tau_body = np.clip(tau_body, -tau_limit, tau_limit)
        tau_world = data.xmat[body_id].reshape(3, 3) @ tau_body
        data.xfrc_applied[body_id, 3:6] = tau_world
        mujoco.mj_step(model, data)

        logs["t"].append(t)
        logs["eul_ref"].append(eul_ref.copy())
        logs["eul_meas"].append(quat_to_euler(q_meas))
        logs["q_ref"].append(q_ref.copy())
        logs["q_meas"].append(q_meas.copy())
        logs["q_err"].append(q_err.copy())
        logs["qerr_angle"].append(quat_angle_error(q_err))
        logs["tau"].append(tau_body.copy())
        logs["omega"].append(omega.copy())

    arrays = {key: np.asarray(value, dtype=float) for key, value in logs.items()}
    eul_error = wrap_to_pi(arrays["eul_meas"] - arrays["eul_ref"])
    if scenario == "flip":
        phi_error = np.unwrap(arrays["eul_meas"][:, 0]) - arrays["eul_ref"][:, 0]
        eul_error[:, 0] = phi_error

    qerr = arrays["qerr_angle"]
    tau_norm = np.linalg.norm(arrays["tau"], axis=1)
    omega_norm = np.linalg.norm(arrays["omega"], axis=1)
    sat_fraction = float(np.mean(np.any(np.abs(arrays["tau"]) >= 0.98 * tau_limit, axis=1)))

    row: dict[str, float | str] = {
        "scenario": scenario,
        "p_scale": p_scale,
        "w_scale": w_scale,
        "Pq": pq,
        "Pw": pw,
        "tau_limit": tau_limit,
        "noise": noise,
        "rmse_phi": float(np.sqrt(np.mean(eul_error[:, 0] ** 2))),
        "rmse_theta": float(np.sqrt(np.mean(eul_error[:, 1] ** 2))),
        "rmse_psi": float(np.sqrt(np.mean(eul_error[:, 2] ** 2))),
        "rmse_euler_mean": float(np.mean(np.sqrt(np.mean(eul_error**2, axis=0)))),
        "qerr_mean": float(np.mean(qerr)),
        "qerr_max": float(np.max(qerr)),
        "tau_mean": float(np.mean(tau_norm)),
        "tau_max": float(np.max(tau_norm)),
        "omega_mean": float(np.mean(omega_norm)),
        "omega_max": float(np.max(omega_norm)),
        "sat_fraction": sat_fraction,
    }
    row["score"] = float(row["qerr_mean"] + 0.02 * row["tau_mean"] + 0.3 * row["sat_fraction"])
    arrays["eul_error"] = eul_error
    arrays["tau_norm"] = tau_norm
    arrays["omega_norm"] = omega_norm
    return row, arrays


def write_rows(rows: list[dict[str, float | str]]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    path = LOGS_DIR / "paper_gain_sweep_metrics.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved metrics: {path}")

    summary_path = LOGS_DIR / "paper_gain_sweep_summary.txt"
    lines = [
        "Paper quaternion controller gain sweep",
        "======================================",
        "",
        f"Paper gains: Pq={PAPER_PQ}, Pw={PAPER_PW}, tau_limit={PAPER_TAU_LIMIT}",
        "",
    ]
    for scenario in ["step", "sine", "flip"]:
        subset = [r for r in rows if r["scenario"] == scenario]
        ranked = sorted(subset, key=lambda r: float(r["score"]))
        lines.extend([scenario, "-" * len(scenario)])
        for r in ranked[:8]:
            lines.append(
                f"Pq={r['Pq']:.3f} Pw={r['Pw']:.3f} score={r['score']:.6f} "
                f"qerr_mean={r['qerr_mean']:.6f} qerr_max={r['qerr_max']:.6f} "
                f"tau_mean={r['tau_mean']:.3f} sat={r['sat_fraction']:.3f}"
            )
        lines.append("")
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved summary: {summary_path}")


def plot_paper_style(scenario: str, label: str, data: dict[str, np.ndarray]) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    t = data["t"]
    eul_ref = np.unwrap(data["eul_ref"], axis=0)
    eul_meas = np.unwrap(data["eul_meas"], axis=0)
    tau = data["tau"]
    q_ref = data["q_ref"]
    q_meas = data["q_meas"]

    if scenario in {"step", "sine"}:
        names = ["Phi [rad]", "Theta [rad]", "Psi [rad]"]
        fig, axes = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
        for i, ax in enumerate(axes):
            ax.plot(t, eul_ref[:, i], "--", linewidth=1.5, label="reference")
            ax.plot(t, eul_meas[:, i], linewidth=1.3, label="response")
            ax.set_ylabel(names[i])
            ax.grid(True, alpha=0.3)
        axes[-1].set_xlabel("Time [s]")
        axes[0].legend(fontsize=8)
        fig.suptitle(f"{scenario} attitude response ({label})")
        fig.tight_layout()
        path = FIGURES_DIR / f"{scenario}_{label}_attitude_response.png"
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"Saved figure: {path}")
        plt.close(fig)

        fig, axes = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
        names = ["Mx [Nm]", "My [Nm]", "Mz [Nm]"]
        for i, ax in enumerate(axes):
            ax.plot(t, tau[:, i], linewidth=1.3)
            ax.axhline(PAPER_TAU_LIMIT, linestyle="--", color="k", linewidth=0.8)
            ax.axhline(-PAPER_TAU_LIMIT, linestyle="--", color="k", linewidth=0.8)
            ax.set_ylabel(names[i])
            ax.grid(True, alpha=0.3)
        axes[-1].set_xlabel("Time [s]")
        fig.suptitle(f"{scenario} controller effort ({label})")
        fig.tight_layout()
        path = FIGURES_DIR / f"{scenario}_{label}_control_effort.png"
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"Saved figure: {path}")
        plt.close(fig)

    if scenario == "flip":
        fig, axes = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
        axes[0].plot(t, eul_ref[:, 0], "--", linewidth=1.5, label="reference")
        axes[0].plot(t, eul_meas[:, 0], linewidth=1.3, label="response")
        axes[0].set_ylabel("Phi [rad]")
        axes[0].grid(True, alpha=0.3)
        axes[0].legend(fontsize=8)
        axes[1].plot(t, tau[:, 0], linewidth=1.3)
        axes[1].axhline(PAPER_TAU_LIMIT, linestyle="--", color="k", linewidth=0.8)
        axes[1].axhline(-PAPER_TAU_LIMIT, linestyle="--", color="k", linewidth=0.8)
        axes[1].set_ylabel("Mx [Nm]")
        axes[1].set_xlabel("Time [s]")
        axes[1].grid(True, alpha=0.3)
        fig.suptitle(f"flip response and effort ({label})")
        fig.tight_layout()
        path = FIGURES_DIR / f"flip_{label}_phi_and_mx.png"
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"Saved figure: {path}")
        plt.close(fig)

        fig, axes = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
        for i, ax in enumerate(axes):
            ax.plot(t, q_ref[:, i], "--", linewidth=1.5, label=f"q{i} reference")
            ax.plot(t, q_meas[:, i], linewidth=1.3, label=f"q{i} response")
            ax.set_ylabel(f"q{i}")
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8)
        axes[-1].set_xlabel("Time [s]")
        fig.suptitle(f"flip quaternion components ({label})")
        fig.tight_layout()
        path = FIGURES_DIR / f"flip_{label}_q0_q1.png"
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"Saved figure: {path}")
        plt.close(fig)


def plot_gain_surface(rows: list[dict[str, float | str]], scenario: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    subset = [r for r in rows if r["scenario"] == scenario]
    p_vals = sorted({float(r["p_scale"]) for r in subset})
    w_vals = sorted({float(r["w_scale"]) for r in subset})
    matrix = np.full((len(w_vals), len(p_vals)), np.nan)
    for r in subset:
        i = w_vals.index(float(r["w_scale"]))
        j = p_vals.index(float(r["p_scale"]))
        matrix[i, j] = float(r["score"])
    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(matrix, origin="lower", aspect="auto", cmap="viridis")
    ax.set_xticks(np.arange(len(p_vals)))
    ax.set_xticklabels([f"{v:g}" for v in p_vals])
    ax.set_yticks(np.arange(len(w_vals)))
    ax.set_yticklabels([f"{v:g}" for v in w_vals])
    ax.set_xlabel("Pq scale relative to paper")
    ax.set_ylabel("Pw scale relative to paper")
    ax.set_title(f"Gain sweep score: {scenario}")
    fig.colorbar(im, ax=ax, label="lower is better")
    fig.tight_layout()
    path = FIGURES_DIR / f"{scenario}_gain_score_surface.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"Saved figure: {path}")
    plt.close(fig)


def run(args: argparse.Namespace) -> None:
    if not XML_PATH.exists():
        raise FileNotFoundError(f"MuJoCo XML not found: {XML_PATH}")

    scenarios = ["step", "sine", "flip"] if args.scenario == "all" else [args.scenario]
    rows: list[dict[str, float | str]] = []
    best_data: dict[tuple[str, str], dict[str, np.ndarray]] = {}
    grid = gain_grid(args.preset)

    for scenario in scenarios:
        print(f"Running {scenario} with {len(grid)} gain pairs")
        scenario_rows: list[dict[str, float | str]] = []
        scenario_data: dict[tuple[float, float], dict[str, np.ndarray]] = {}
        for p_scale, w_scale in grid:
            row, data = simulate(
                scenario=scenario,
                p_scale=p_scale,
                w_scale=w_scale,
                dt=args.dt,
                noise=args.noise,
                seed=args.seed,
            )
            rows.append(row)
            scenario_rows.append(row)
            scenario_data[(p_scale, w_scale)] = data
            print(
                f"  Pq={row['Pq']:.2f} Pw={row['Pw']:.2f} "
                f"score={row['score']:.4f} qerr={row['qerr_mean']:.4f} "
                f"tau={row['tau_mean']:.3f} sat={row['sat_fraction']:.3f}"
            )

        best = min(scenario_rows, key=lambda r: float(r["score"]))
        best_key = (float(best["p_scale"]), float(best["w_scale"]))
        best_data[(scenario, "best")] = scenario_data[best_key]

        paper_row = next(
            (r for r in scenario_rows if float(r["p_scale"]) == 1.0 and float(r["w_scale"]) == 1.0),
            None,
        )
        if paper_row is not None:
            paper_key = (float(paper_row["p_scale"]), float(paper_row["w_scale"]))
            best_data[(scenario, "paper")] = scenario_data[paper_key]

    write_rows(rows)
    for scenario in scenarios:
        plot_gain_surface(rows, scenario)
        if (scenario, "best") in best_data:
            plot_paper_style(scenario, "best", best_data[(scenario, "best")])
        if (scenario, "paper") in best_data:
            plot_paper_style(scenario, "paper", best_data[(scenario, "paper")])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=["paper-only", "quick", "full"], default="quick")
    parser.add_argument("--scenario", choices=["all", "step", "sine", "flip"], default="all")
    parser.add_argument("--dt", type=float, default=0.01)
    parser.add_argument("--noise", type=float, default=0.0, help="Optional measurement noise amplitude")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
