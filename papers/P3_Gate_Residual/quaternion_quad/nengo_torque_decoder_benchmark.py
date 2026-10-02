"""Offline Nengo torque-decoder benchmark for quaternion attitude control.

This script isolates the neural controller block from MuJoCo.  It samples:

    x = [axis_error_x, axis_error_y, axis_error_z, wx, wy, wz]

and asks a Nengo ensemble to approximate the scaled quaternion PD torque law:

    tau = clip(-KQ * axis_error - KW * omega, -tau_limit, tau_limit)

The goal is to separate representation/decoder quality from closed-loop plant
dynamics.  Run this before expensive MuJoCo sweeps, especially for
AdaptiveHyperLIF variants.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import nengo
from nengo.builder.ensemble import get_activities
import numpy as np

try:
    from nengo_neurons import AdaptiveHyperLIF_b20_gs80_rtc15, HyperLIF
except ImportError:
    AdaptiveHyperLIF_b20_gs80_rtc15 = None
    HyperLIF = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "results" / "logs"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures" / "quaternion_quad" / "nengo_torque_decoder_benchmark"

SKYDIO_INERTIA = np.array([0.060711294842784244, 0.0364684032704233, 0.025411698113207547])


def scaled_gains() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    wn = np.array([4.0, 4.0, 3.5], dtype=float)
    zeta = np.array([0.95, 0.95, 0.95], dtype=float)
    alpha_max = np.array([12.0, 12.0, 10.0], dtype=float)
    kq = 2.0 * SKYDIO_INERTIA * (wn**2)
    kw = 2.0 * zeta * wn * SKYDIO_INERTIA
    tau_limit = np.maximum(SKYDIO_INERTIA * alpha_max, np.array([0.03, 0.03, 0.02]))
    return kq, kw, tau_limit


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


def torque_function(x: np.ndarray, kq: np.ndarray, kw: np.ndarray, tau_limit: np.ndarray) -> np.ndarray:
    axis_err = x[..., :3]
    omega = x[..., 3:]
    return np.clip(-kq * axis_err - kw * omega, -tau_limit, tau_limit)


def sample_inputs(n: int, radius: float, seed: int, mode: str) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if mode == "uniform_box":
        axis_err = rng.uniform(-0.35, 0.35, size=(n, 3))
        omega = rng.uniform(-1.5, 1.5, size=(n, 3))
    elif mode == "roll_like":
        axis_err = np.zeros((n, 3))
        omega = np.zeros((n, 3))
        axis_err[:, 0] = rng.uniform(-0.18, 0.18, size=n)
        axis_err[:, 1:] = rng.normal(0.0, 0.02, size=(n, 2))
        omega[:, 0] = rng.uniform(-0.8, 0.8, size=n)
        omega[:, 1:] = rng.normal(0.0, 0.08, size=(n, 2))
    elif mode == "full3_like":
        axis_err = rng.uniform(-0.45, 0.45, size=(n, 3))
        omega = rng.uniform(-1.2, 1.2, size=(n, 3))
    else:
        raise ValueError(f"Unknown sample mode: {mode}")

    x = np.concatenate([axis_err, omega], axis=1)
    norms = np.linalg.norm(x, axis=1)
    mask = norms > radius
    x[mask] *= (radius / norms[mask])[:, None]
    return x


def setting_grid(preset: str, include_adaptive: bool, neuron_filter: list[str]) -> list[dict[str, float | int | str]]:
    neurons = ["lifrate", "lif", "rectified"]
    if include_adaptive:
        neurons.append("adaptivehyperlif_tuned")
    if neuron_filter:
        wanted = set(neuron_filter)
        neurons = [neuron for neuron in neurons if neuron in wanted]

    if preset == "smoke":
        settings = [
            {"n_neurons": 200, "radius": 1.0, "synapse": 0.005, "seed": 2},
        ]
    elif preset == "quick":
        settings = [
            {"n_neurons": 400, "radius": 1.5, "synapse": 0.002, "seed": 2},
            {"n_neurons": 600, "radius": 1.0, "synapse": 0.003, "seed": 3},
            {"n_neurons": 800, "radius": 0.75, "synapse": 0.005, "seed": 4},
        ]
    else:
        settings = [
            {"n_neurons": 400, "radius": 1.5, "synapse": 0.002, "seed": 2},
            {"n_neurons": 600, "radius": 1.0, "synapse": 0.003, "seed": 3},
            {"n_neurons": 800, "radius": 0.75, "synapse": 0.005, "seed": 4},
            {"n_neurons": 1000, "radius": 0.5, "synapse": 0.01, "seed": 5},
            {"n_neurons": 1200, "radius": 0.4, "synapse": 0.015, "seed": 6},
        ]
    return [{**setting, "neuron": neuron} for neuron in neurons for setting in settings]


def evaluate_case(
    case: dict[str, float | int | str],
    x_train: np.ndarray,
    x_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    args: argparse.Namespace,
) -> tuple[dict[str, float | int | str], np.ndarray]:
    neuron = str(case["neuron"])
    radius = float(case["radius"])
    n_neurons = int(case["n_neurons"])
    seed = int(case["seed"])
    synapse = float(case["synapse"])

    with nengo.Network(label=f"offline {neuron} torque decoder") as model:
        stim = nengo.Node(size_in=6)
        ens = nengo.Ensemble(
            n_neurons=n_neurons,
            dimensions=6,
            neuron_type=neuron_type(neuron),
            radius=radius,
            max_rates=nengo.dists.Uniform(args.max_rate_low, args.max_rate_high),
            intercepts=nengo.dists.Uniform(args.intercept_low, args.intercept_high),
            eval_points=x_train,
            seed=seed,
        )
        out = nengo.Node(size_in=3)
        nengo.Connection(stim, ens, synapse=None)
        nengo.Connection(
            ens,
            out,
            eval_points=x_train,
            function=y_train,
            solver=nengo.solvers.LstsqL2(reg=args.reg),
            synapse=synapse,
        )

    with nengo.Simulator(model, dt=args.dt, progress_bar=False) as sim:
        conn = model.connections[-1]
        built = sim.model.params[conn]
        activities = get_activities(sim.model.params[ens], ens, x_test)
        y_pred = activities @ built.weights.T

    err = y_pred - y_test
    rmse_axis = np.sqrt(np.mean(err**2, axis=0))
    mae_axis = np.mean(np.abs(err), axis=0)
    norm_err = np.linalg.norm(err, axis=1)
    norm_target = np.linalg.norm(y_test, axis=1)
    row = {
        **case,
        "sample_mode": args.sample_mode,
        "n_train": len(x_train),
        "n_test": len(x_test),
        "dt": args.dt,
        "rmse_tau_x": rmse_axis[0],
        "rmse_tau_y": rmse_axis[1],
        "rmse_tau_z": rmse_axis[2],
        "rmse_norm": float(np.sqrt(np.mean(norm_err**2))),
        "mae_norm": float(np.mean(norm_err)),
        "max_norm": float(np.max(norm_err)),
        "target_norm_mean": float(np.mean(norm_target)),
        "relative_rmse": float(np.sqrt(np.mean(norm_err**2)) / max(1e-12, np.sqrt(np.mean(norm_target**2)))),
        "status": "ok",
    }
    return row, y_pred


def write_rows(rows: list[dict[str, float | int | str]], args: argparse.Namespace) -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = LOGS_DIR / f"nengo_torque_decoder_benchmark_{args.sample_mode}_{args.preset}.csv"
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def plot_rows(rows: list[dict[str, float | int | str]], args: argparse.Namespace) -> None:
    valid = sorted([r for r in rows if r.get("status") == "ok"], key=lambda r: float(r["rmse_norm"]))
    if not valid:
        return
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    labels = [f"{r['neuron']}\nN={r['n_neurons']} r={r['radius']} s={r['synapse']}" for r in valid]
    x = np.arange(len(valid))
    fig, axes = plt.subplots(3, 1, figsize=(max(10, 0.7 * len(valid)), 9), sharex=True)
    for ax, metric in zip(axes, ["rmse_norm", "relative_rmse", "max_norm"]):
        ax.bar(x, [float(r[metric]) for r in valid])
        ax.set_ylabel(metric)
        ax.grid(True, axis="y", alpha=0.3)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, rotation=35, ha="right")
    fig.suptitle(f"Offline torque decoder benchmark: {args.sample_mode}, {args.preset}")
    fig.tight_layout()
    path = FIGURES_DIR / f"nengo_torque_decoder_benchmark_{args.sample_mode}_{args.preset}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure: {path}")


def plot_best_scatter(
    best: dict[str, float | int | str],
    y_test: np.ndarray,
    y_pred: np.ndarray,
    args: argparse.Namespace,
) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for i, name in enumerate(["tau_x", "tau_y", "tau_z"]):
        axes[i].scatter(y_test[:, i], y_pred[:, i], s=5, alpha=0.35)
        lo = min(float(np.min(y_test[:, i])), float(np.min(y_pred[:, i])))
        hi = max(float(np.max(y_test[:, i])), float(np.max(y_pred[:, i])))
        axes[i].plot([lo, hi], [lo, hi], "k--", linewidth=1.0)
        axes[i].set_xlabel(f"target {name}")
        axes[i].set_ylabel(f"decoded {name}")
        axes[i].grid(True, alpha=0.3)
    fig.suptitle(
        f"Best torque decoder: {best['neuron']}, N={best['n_neurons']}, "
        f"r={best['radius']}, syn={best['synapse']}"
    )
    fig.tight_layout()
    path = FIGURES_DIR / f"nengo_torque_decoder_best_scatter_{args.sample_mode}_{args.preset}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved scatter: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=["smoke", "quick", "full"], default="quick")
    parser.add_argument("--sample-mode", choices=["roll_like", "full3_like", "uniform_box"], default="roll_like")
    parser.add_argument("--include-adaptive", action="store_true")
    parser.add_argument("--neurons", default="")
    parser.add_argument("--n-train", type=int, default=600)
    parser.add_argument("--n-test", type=int, default=600)
    parser.add_argument("--dt", type=float, default=0.001)
    parser.add_argument("--reg", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--max-rate-low", type=float, default=100.0)
    parser.add_argument("--max-rate-high", type=float, default=200.0)
    parser.add_argument("--intercept-low", type=float, default=-0.8)
    parser.add_argument("--intercept-high", type=float, default=0.8)
    args = parser.parse_args()

    kq, kw, tau_limit = scaled_gains()
    neuron_filter = [item.strip() for item in args.neurons.split(",") if item.strip()]
    x_train = sample_inputs(args.n_train, radius=1.5, seed=args.seed, mode=args.sample_mode)
    x_test = sample_inputs(args.n_test, radius=1.5, seed=args.seed + 1, mode=args.sample_mode)
    y_train = torque_function(x_train, kq, kw, tau_limit)
    y_test = torque_function(x_test, kq, kw, tau_limit)

    rows = []
    predictions: dict[int, np.ndarray] = {}
    for idx, case in enumerate(setting_grid(args.preset, args.include_adaptive, neuron_filter)):
        print(f"Evaluating {case}")
        try:
            row, y_pred = evaluate_case(case, x_train, x_test, y_train, y_test, args)
            predictions[idx] = y_pred
        except Exception as exc:
            row = {**case, "sample_mode": args.sample_mode, "status": f"failed: {exc}"}
        rows.append(row)
        print(row)

    csv_path = write_rows(rows, args)
    plot_rows(rows, args)
    valid = [(idx, row) for idx, row in enumerate(rows) if row.get("status") == "ok"]
    if valid:
        best_idx, best = min(valid, key=lambda item: float(item[1]["rmse_norm"]))
        plot_best_scatter(best, y_test, predictions[best_idx], args)
    print(f"Saved benchmark CSV: {csv_path}")


if __name__ == "__main__":
    main()
