"""Pure ODE replication of the quaternion attitude-control paper.

Run from the project root:

    python experiments/quaternion_quad/paper_ode_replication.py --solver rk4

The model is intentionally independent of MuJoCo.  It uses the paper's
attitude-only rigid-body equations, inertia, gains, torque bounds, and
reference tests:

    q_dot = -0.5 * [0, omega] * q
    w_dot = I^{-1} (tau - omega x I omega)
    tau   = -Pq * vec(q_ref * conj(q)) - Pw * omega

The script can compare fixed-step solvers and can optionally compare its CSV
output against a Julia-generated CSV with compatible column names.
"""

from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "results" / "logs"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures" / "quaternion_quad" / "paper_ode_replication"

PAPER_I = np.diag([6.5e-4, 6.5e-4, 1.2e-3])
PAPER_PQ = 20.0
PAPER_PW = 4.0
PAPER_TAU_LIMIT = 4.0


@dataclass(frozen=True)
class Params:
    inertia: np.ndarray
    pq: float
    pw: float
    tau_limit: float
    shortest_path: bool


def q_normalize(q: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(q)
    if n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    return q / n


def q_conj(q: np.ndarray) -> np.ndarray:
    return np.array([q[0], -q[1], -q[2], -q[3]], dtype=float)


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
        phases = np.array([0.0, np.pi / 2.0, np.pi], dtype=float)
        return 0.5 * np.sin(t + phases)
    if scenario == "flip":
        phi = np.clip((2.0 * np.pi / 5.0) * t, 0.0, 2.0 * np.pi)
        return np.array([phi, 0.0, 0.0], dtype=float)
    raise ValueError(f"Unknown scenario: {scenario}")


def reference_quat(t: float, scenario: str) -> np.ndarray:
    phi, theta, psi = reference_euler(t, scenario)
    return euler_to_quat(phi, theta, psi)


def scenario_time(scenario: str) -> float:
    return 5.0 if scenario == "flip" else 15.0


def control_law(t: float, x: np.ndarray, scenario: str, params: Params) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    q_meas = q_normalize(x[:4])
    omega = x[4:7]
    q_ref = reference_quat(t, scenario)
    q_err = q_mul(q_ref, q_conj(q_meas))

    if params.shortest_path and q_err[0] < 0.0:
        q_err = -q_err

    tau = -params.pq * q_err[1:4] - params.pw * omega
    tau = np.clip(tau, -params.tau_limit, params.tau_limit)
    return tau, q_ref, q_normalize(q_err)


def rhs(t: float, x: np.ndarray, scenario: str, params: Params) -> np.ndarray:
    q = q_normalize(x[:4])
    omega = x[4:7]
    tau, _, _ = control_law(t, x, scenario, params)

    omega_quat = np.array([0.0, omega[0], omega[1], omega[2]], dtype=float)
    q_dot = -0.5 * q_mul(omega_quat, q)
    w_dot = np.linalg.solve(params.inertia, tau - np.cross(omega, params.inertia @ omega))

    dx = np.zeros(7, dtype=float)
    dx[:4] = q_dot
    dx[4:7] = w_dot
    return dx


def step_fixed(t: float, x: np.ndarray, dt: float, scenario: str, params: Params, solver: str) -> np.ndarray:
    if solver == "euler":
        x_next = x + dt * rhs(t, x, scenario, params)
    elif solver == "midpoint":
        k1 = rhs(t, x, scenario, params)
        x_next = x + dt * rhs(t + 0.5 * dt, x + 0.5 * dt * k1, scenario, params)
    elif solver == "rk4":
        k1 = rhs(t, x, scenario, params)
        k2 = rhs(t + 0.5 * dt, x + 0.5 * dt * k1, scenario, params)
        k3 = rhs(t + 0.5 * dt, x + 0.5 * dt * k2, scenario, params)
        k4 = rhs(t + dt, x + dt * k3, scenario, params)
        x_next = x + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    else:
        raise ValueError(f"Unsupported fixed-step solver: {solver}")

    x_next[:4] = q_normalize(x_next[:4])
    return x_next


def simulate_fixed(scenario: str, solver: str, dt: float, params: Params) -> dict[str, np.ndarray | float | str]:
    sim_time = scenario_time(scenario)
    n_steps = int(np.floor(sim_time / dt)) + 1
    t = np.arange(n_steps, dtype=float) * dt
    if t[-1] < sim_time:
        t = np.append(t, sim_time)

    x = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
    states = np.zeros((len(t), 7), dtype=float)
    tic = time.perf_counter()
    states[0] = x
    for k in range(1, len(t)):
        local_dt = t[k] - t[k - 1]
        x = step_fixed(t[k - 1], x, local_dt, scenario, params, solver)
        states[k] = x
    runtime = time.perf_counter() - tic
    return reconstruct(scenario, solver, dt, t, states, runtime, params)


def simulate_scipy(scenario: str, dt: float, params: Params) -> dict[str, np.ndarray | float | str]:
    try:
        from scipy.integrate import solve_ivp
    except ImportError as exc:
        raise RuntimeError("SciPy is not installed. Use --solver rk4, midpoint, or euler.") from exc

    tf = scenario_time(scenario)
    t_eval = np.arange(0.0, tf + 0.5 * dt, dt)
    t_eval = t_eval[t_eval <= tf + 1e-12]
    if t_eval[-1] < tf:
        t_eval = np.append(t_eval, tf)
    x0 = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
    tic = time.perf_counter()
    sol = solve_ivp(
        lambda t, x: rhs(t, x, scenario, params),
        (0.0, tf),
        x0,
        t_eval=t_eval,
        method="RK45",
        rtol=1e-8,
        atol=1e-10,
        max_step=dt,
    )
    runtime = time.perf_counter() - tic
    if not sol.success:
        raise RuntimeError(sol.message)
    states = sol.y.T.copy()
    for row in states:
        row[:4] = q_normalize(row[:4])
    return reconstruct(scenario, "scipy-rk45", dt, sol.t, states, runtime, params)


def reconstruct(
    scenario: str,
    solver: str,
    dt: float,
    t: np.ndarray,
    states: np.ndarray,
    runtime: float,
    params: Params,
) -> dict[str, np.ndarray | float | str]:
    q = np.array([q_normalize(row[:4]) for row in states])
    omega = states[:, 4:7]
    eul_ref = np.array([reference_euler(ti, scenario) for ti in t])
    q_ref = np.array([reference_quat(ti, scenario) for ti in t])
    eul_meas = np.array([quat_to_euler(qi) for qi in q])
    tau = []
    q_err = []
    for ti, xi in zip(t, states):
        tau_i, _, q_err_i = control_law(float(ti), xi, scenario, params)
        tau.append(tau_i)
        q_err.append(q_err_i)
    tau = np.asarray(tau)
    q_err = np.asarray(q_err)
    qerr_angle = np.array([quat_angle_error(qi) for qi in q_err])
    eul_err = wrap_to_pi(eul_meas - eul_ref)
    sat = np.any(np.isclose(np.abs(tau), params.tau_limit, atol=1e-9), axis=1)

    return {
        "scenario": scenario,
        "solver": solver,
        "dt": dt,
        "runtime": runtime,
        "t": t,
        "state": states,
        "q": q,
        "omega": omega,
        "eul_ref": eul_ref,
        "eul_meas": eul_meas,
        "eul_err": eul_err,
        "q_ref": q_ref,
        "q_err": q_err,
        "qerr_angle": qerr_angle,
        "tau": tau,
        "rmse_phi": float(np.sqrt(np.mean(eul_err[:, 0] ** 2))),
        "rmse_theta": float(np.sqrt(np.mean(eul_err[:, 1] ** 2))),
        "rmse_psi": float(np.sqrt(np.mean(eul_err[:, 2] ** 2))),
        "qerr_mean": float(np.mean(qerr_angle)),
        "qerr_max": float(np.max(qerr_angle)),
        "tau_mean": float(np.mean(np.linalg.norm(tau, axis=1))),
        "tau_max": float(np.max(np.linalg.norm(tau, axis=1))),
        "sat_fraction": float(np.mean(sat)),
        "qnorm_max_error": float(np.max(np.abs(np.linalg.norm(q, axis=1) - 1.0))),
    }


def simulate(scenario: str, solver: str, dt: float, params: Params) -> dict[str, np.ndarray | float | str]:
    if solver == "scipy-rk45":
        return simulate_scipy(scenario, dt, params)
    return simulate_fixed(scenario, solver, dt, params)


def write_csv(result: dict[str, np.ndarray | float | str]) -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    scenario = str(result["scenario"])
    solver = str(result["solver"])
    dt_label = f"{float(result['dt']):.4f}".replace(".", "p")
    path = LOGS_DIR / f"paper_ode_{scenario}_{solver}_dt{dt_label}.csv"

    t = result["t"]
    q = result["q"]
    omega = result["omega"]
    eul_ref = result["eul_ref"]
    eul_meas = result["eul_meas"]
    eul_err = result["eul_err"]
    q_ref = result["q_ref"]
    q_err = result["q_err"]
    tau = result["tau"]
    qerr_angle = result["qerr_angle"]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "t",
                "q0",
                "q1",
                "q2",
                "q3",
                "wx",
                "wy",
                "wz",
                "phi_ref",
                "theta_ref",
                "psi_ref",
                "phi",
                "theta",
                "psi",
                "phi_err",
                "theta_err",
                "psi_err",
                "qref0",
                "qref1",
                "qref2",
                "qref3",
                "qerr0",
                "qerr1",
                "qerr2",
                "qerr3",
                "qerr_angle",
                "tau_x",
                "tau_y",
                "tau_z",
            ]
        )
        for i in range(len(t)):
            writer.writerow(
                [
                    t[i],
                    *q[i],
                    *omega[i],
                    *eul_ref[i],
                    *eul_meas[i],
                    *eul_err[i],
                    *q_ref[i],
                    *q_err[i],
                    qerr_angle[i],
                    *tau[i],
                ]
            )
    return path


def write_summary(rows: list[dict[str, np.ndarray | float | str]], julia_rows: list[dict[str, float | str]]) -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = LOGS_DIR / "paper_ode_replication_summary.csv"
    fields = [
        "source",
        "scenario",
        "solver",
        "dt",
        "runtime",
        "rmse_phi",
        "rmse_theta",
        "rmse_psi",
        "qerr_mean",
        "qerr_max",
        "tau_mean",
        "tau_max",
        "sat_fraction",
        "qnorm_max_error",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({field: r.get(field, "python") if field == "source" else r.get(field, "") for field in fields})
        for r in julia_rows:
            writer.writerow(r)
    return path


def plot_response(result: dict[str, np.ndarray | float | str]) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    scenario = str(result["scenario"])
    solver = str(result["solver"])
    t = result["t"]
    eul_ref = np.unwrap(result["eul_ref"], axis=0)
    eul_meas = np.unwrap(result["eul_meas"], axis=0)
    tau = result["tau"]
    q = result["q"]
    q_ref = result["q_ref"]
    qerr_angle = result["qerr_angle"]
    label = f"{scenario}_{solver}"

    if scenario in {"step", "sine"}:
        fig, axes = plt.subplots(4, 1, figsize=(9, 8), sharex=True)
        names = ["Phi [rad]", "Theta [rad]", "Psi [rad]"]
        for i in range(3):
            axes[i].plot(t, eul_ref[:, i], "--", linewidth=1.5, label="reference")
            axes[i].plot(t, eul_meas[:, i], linewidth=1.2, label="response")
            axes[i].set_ylabel(names[i])
            axes[i].grid(True, alpha=0.3)
        axes[3].plot(t, qerr_angle, color="tab:red", linewidth=1.2)
        axes[3].set_ylabel("q error [rad]")
        axes[3].set_xlabel("Time [s]")
        axes[3].grid(True, alpha=0.3)
        axes[0].legend(fontsize=8)
        fig.suptitle(f"Pure ODE attitude response: {scenario}, {solver}")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / f"{label}_attitude_response.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

        fig, axes = plt.subplots(3, 1, figsize=(9, 6), sharex=True)
        for i, name in enumerate(["Mx [Nm]", "My [Nm]", "Mz [Nm]"]):
            axes[i].plot(t, tau[:, i], linewidth=1.2)
            axes[i].axhline(PAPER_TAU_LIMIT, color="k", linestyle="--", linewidth=0.8)
            axes[i].axhline(-PAPER_TAU_LIMIT, color="k", linestyle="--", linewidth=0.8)
            axes[i].set_ylabel(name)
            axes[i].grid(True, alpha=0.3)
        axes[-1].set_xlabel("Time [s]")
        fig.suptitle(f"Pure ODE control effort: {scenario}, {solver}")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / f"{label}_control_effort.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    if scenario == "flip":
        fig, axes = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
        axes[0].plot(t, eul_ref[:, 0], "--", linewidth=1.5, label="reference")
        axes[0].plot(t, eul_meas[:, 0], linewidth=1.2, label="response")
        axes[0].set_ylabel("Phi [rad]")
        axes[0].legend(fontsize=8)
        axes[0].grid(True, alpha=0.3)
        axes[1].plot(t, tau[:, 0], linewidth=1.2)
        axes[1].axhline(PAPER_TAU_LIMIT, color="k", linestyle="--", linewidth=0.8)
        axes[1].axhline(-PAPER_TAU_LIMIT, color="k", linestyle="--", linewidth=0.8)
        axes[1].set_ylabel("Mx [Nm]")
        axes[1].grid(True, alpha=0.3)
        axes[2].plot(t, qerr_angle, color="tab:red", linewidth=1.2)
        axes[2].set_ylabel("q error [rad]")
        axes[2].set_xlabel("Time [s]")
        axes[2].grid(True, alpha=0.3)
        fig.suptitle(f"Pure ODE flip response: {solver}")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / f"{label}_phi_mx_error.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

        fig, axes = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
        for i, ax in enumerate(axes):
            ax.plot(t, q_ref[:, i], "--", linewidth=1.5, label=f"q{i} reference")
            ax.plot(t, q[:, i], linewidth=1.2, label=f"q{i} response")
            ax.set_ylabel(f"q{i}")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        axes[-1].set_xlabel("Time [s]")
        fig.suptitle(f"Pure ODE flip quaternion components: {solver}")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / f"{label}_q0_q1.png", dpi=300, bbox_inches="tight")
        plt.close(fig)


def plot_solver_comparison(rows: list[dict[str, np.ndarray | float | str]]) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = sorted({str(r["scenario"]) for r in rows})
    solvers = sorted({str(r["solver"]) for r in rows})
    metrics = ["qerr_mean", "tau_mean", "sat_fraction", "runtime"]
    for scenario in scenarios:
        subset = [r for r in rows if str(r["scenario"]) == scenario]
        fig, axes = plt.subplots(2, 2, figsize=(10, 7))
        axes = axes.ravel()
        for ax, metric in zip(axes, metrics):
            vals = [float(next(r[metric] for r in subset if str(r["solver"]) == s)) for s in solvers]
            ax.bar(solvers, vals)
            ax.set_title(metric)
            ax.grid(True, axis="y", alpha=0.3)
            ax.tick_params(axis="x", rotation=25)
        fig.suptitle(f"Pure ODE solver comparison: {scenario}")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / f"{scenario}_solver_comparison.png", dpi=300, bbox_inches="tight")
        plt.close(fig)


def compare_to_julia(path: Path) -> list[dict[str, float | str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows: list[dict[str, float | str]] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out: dict[str, float | str] = {
                "source": "julia",
                "scenario": row.get("scenario", ""),
                "solver": row.get("solver", "julia"),
            }
            for key in [
                "dt",
                "runtime",
                "rmse_phi",
                "rmse_theta",
                "rmse_psi",
                "qerr_mean",
                "qerr_max",
                "tau_mean",
                "tau_max",
                "sat_fraction",
                "qnorm_max_error",
            ]:
                value = row.get(key, "")
                out[key] = float(value) if value not in {"", None} else ""
            rows.append(out)
    return rows


def run(args: argparse.Namespace) -> None:
    solvers = ["euler", "midpoint", "rk4"] if args.solver == "all-fixed" else [args.solver]
    scenarios = ["step", "sine", "flip"] if args.scenario == "all" else [args.scenario]
    params = Params(
        inertia=PAPER_I,
        pq=args.pq,
        pw=args.pw,
        tau_limit=args.tau_limit,
        shortest_path=not args.long_flip,
    )
    rows: list[dict[str, np.ndarray | float | str]] = []

    for scenario in scenarios:
        for solver in solvers:
            print(f"Running pure ODE scenario={scenario} solver={solver} dt={args.dt}")
            result = simulate(scenario, solver, args.dt, params)
            rows.append(result)
            csv_path = write_csv(result)
            if args.plots:
                plot_response(result)
            print(
                "  "
                f"qerr_mean={result['qerr_mean']:.5f} "
                f"qerr_max={result['qerr_max']:.5f} "
                f"tau_mean={result['tau_mean']:.3f} "
                f"sat={result['sat_fraction']:.3f} "
                f"runtime={result['runtime']:.3f}s "
                f"csv={csv_path}"
            )

    julia_rows = compare_to_julia(Path(args.julia_csv)) if args.julia_csv else []
    summary_path = write_summary(rows, julia_rows)
    if args.plots and len(solvers) > 1:
        plot_solver_comparison(rows)
    print(f"Saved summary: {summary_path}")
    print(f"Saved figures: {FIGURES_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["all", "step", "sine", "flip"], default="all")
    parser.add_argument(
        "--solver",
        choices=["euler", "midpoint", "rk4", "scipy-rk45", "all-fixed"],
        default="rk4",
        help="ODE solver to use. all-fixed runs Euler, midpoint, and RK4.",
    )
    parser.add_argument("--dt", type=float, default=0.002)
    parser.add_argument("--pq", type=float, default=PAPER_PQ)
    parser.add_argument("--pw", type=float, default=PAPER_PW)
    parser.add_argument("--tau-limit", type=float, default=PAPER_TAU_LIMIT)
    parser.add_argument(
        "--long-flip",
        action="store_true",
        help="Disable shortest-path quaternion correction. Useful for the paper's 0 to 2*pi flip plot.",
    )
    parser.add_argument("--julia-csv", default="", help="Optional Julia summary CSV with compatible metric columns.")
    parser.add_argument("--no-plots", dest="plots", action="store_false")
    parser.set_defaults(plots=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
