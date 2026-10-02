"""Seven-agent flexible-arm DILISIC reproduction experiment."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from dilisic.controllers import DILISICWrapper, DoubleIntegratorFormationController
from dilisic.controllers.lisic import LISICParameters
from dilisic.plants import FlexibleSingleLinkArm


def disturbance(t: float) -> float:
    return 6000.0 if 70.0 <= t < 75.0 else 0.0


def run(duration: float, dt: float, output: Path, plot: bool = False) -> dict[str, float]:
    output.mkdir(parents=True, exist_ok=True)
    n_agents = 7
    plant = FlexibleSingleLinkArm()
    outer = DoubleIntegratorFormationController(n_agents=n_agents)
    controllers = [DILISICWrapper() for _ in range(n_agents)]

    states = np.zeros((n_agents, 4), dtype=float)
    states[:, 0] = np.linspace(-0.64, 0.64, n_agents)
    ref_states = [controller.initialize(states[i]) for i, controller in enumerate(controllers)]

    steps = int(round(duration / dt))
    log_stride = max(1, steps // 5000)
    csv_path = output / "trajectory.csv"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["t"]
            + [f"q_{i}" for i in range(n_agents)]
            + [f"v_{i}" for i in range(n_agents)]
            + [f"u_{i}" for i in range(n_agents)]
            + ["s_0", "f_hat_0", "h_hat_0"]
        )

        last_info = [{"s": 0.0, "f_hat": 0.0, "h_hat": 0.0, "u_total": 0.0} for _ in range(n_agents)]
        controls = np.zeros(n_agents, dtype=float)
        # Initial condition is logged at t=0.  Earlier code integrated once at
        # every label in range(steps+1), so an advertised T-second run actually
        # advanced to T+dt and each CSV state was shifted one sample forward.
        writer.writerow(
            [0.0]
            + states[:, 0].tolist()
            + states[:, 1].tolist()
            + controls.tolist()
            + [last_info[0]["s"], last_info[0]["f_hat"], last_info[0]["h_hat"]]
        )
        for step in range(steps):
            t = step * dt
            u_di = outer.compute(t, states[:, 0], states[:, 1])
            for i, controller in enumerate(controllers):
                controls[i], last_info[i] = controller.step(states[i], ref_states[i], float(u_di[i]), dt)

            d = disturbance(t)
            for i in range(n_agents):
                states[i] = plant.rk4_step(states[i], controls[i], d, dt)

            completed = step + 1
            if completed % log_stride == 0 or completed == steps:
                writer.writerow(
                    [completed * dt]
                    + states[:, 0].tolist()
                    + states[:, 1].tolist()
                    + controls.tolist()
                    + [last_info[0]["s"], last_info[0]["f_hat"], last_info[0]["h_hat"]]
                )

    if plot:
        _plot(csv_path, output)

    q_ref, _, _ = outer.reference(duration)
    return {
        "csv": str(csv_path),
        "final_com_error": float(np.mean(states[:, 0]) - q_ref),
        "max_weight_norm": float(
            max(max(c.lisic.weight_norms().values()) for c in controllers)
        ),
    }


def _plot(csv_path: Path, output: Path) -> None:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:
        raise RuntimeError("Install matplotlib or run without --plot") from exc

    data = np.genfromtxt(csv_path, delimiter=",", names=True)
    t = data["t"]
    q_cols = [name for name in data.dtype.names or [] if name.startswith("q_")]
    v_cols = [name for name in data.dtype.names or [] if name.startswith("v_")]

    plt.figure(figsize=(10, 5))
    for col in q_cols:
        plt.plot(t, data[col], linewidth=1.0)
    plt.xlabel("time [s]")
    plt.ylabel("position [rad]")
    plt.tight_layout()
    plt.savefig(output / "positions.png", dpi=160)

    plt.figure(figsize=(10, 5))
    for col in v_cols:
        plt.plot(t, data[col], linewidth=1.0)
    plt.xlabel("time [s]")
    plt.ylabel("velocity [rad/s]")
    plt.tight_layout()
    plt.savefig(output / "velocities.png", dpi=160)
    plt.close("all")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--dt", type=float, default=1.0e-3)
    parser.add_argument("--output", type=Path, default=Path("runs/flexible_arm_mas"))
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()
    result = run(args.duration, args.dt, args.output, args.plot)
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
