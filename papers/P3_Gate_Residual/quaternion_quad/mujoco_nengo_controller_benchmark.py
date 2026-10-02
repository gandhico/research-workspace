"""Batch benchmark for Nengo quaternion controllers in MuJoCo hover.

The script launches ``mujoco_hover_nengo_controller.py`` for a small grid of
neuron/controller settings, parses the generated summary files, and saves a
comparison CSV plus figures.

Recommended first run:

    python experiments/quaternion_quad/mujoco_nengo_controller_benchmark.py --preset quick --mission roll

Then try the paper-like mission:

    python experiments/quaternion_quad/mujoco_nengo_controller_benchmark.py --preset quick --mission full3
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = PROJECT_ROOT / "experiments" / "quaternion_quad" / "mujoco_hover_nengo_controller.py"
LOGS_DIR = PROJECT_ROOT / "results" / "logs"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures" / "quaternion_quad" / "mujoco_nengo_controller_benchmark"


def sanitize_float(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def expected_stem(
    quad: str,
    mission: str,
    neuron: str,
    n_neurons: int,
    radius: float,
    synapse: float,
    seed: int,
    dt: float,
) -> str:
    return (
        f"mujoco_hover_nengo_{quad}_{mission}_{neuron}"
        f"_n{n_neurons}_r{sanitize_float(radius)}_syn{sanitize_float(synapse)}_seed{seed}_dt{sanitize_float(dt)}"
    )


def parse_scalar(text: str, key: str) -> float:
    match = re.search(rf"^{re.escape(key)}=([^\n]+)", text, flags=re.MULTILINE)
    if not match:
        return float("nan")
    return float(match.group(1))


def parse_vector(text: str, key: str) -> list[float]:
    match = re.search(rf"^{re.escape(key)}=\[([^\]]+)\]", text, flags=re.MULTILINE)
    if not match:
        return [float("nan"), float("nan"), float("nan")]
    return [float(part.strip()) for part in match.group(1).split(",")]


def grid(preset: str, include_adaptive: bool, neuron_filter: list[str] | None) -> list[dict[str, float | int | str]]:
    if preset == "quick":
        neurons = ["lifrate", "lif", "rectified"]
        settings = [
            {"n_neurons": 400, "radius": 1.5, "synapse": 0.002, "seed": 2},
        ]
        if include_adaptive:
            neurons.append("adaptivehyperlif_tuned")
            settings.extend(
                [
                    {"n_neurons": 600, "radius": 0.75, "synapse": 0.005, "seed": 3},
                    {"n_neurons": 800, "radius": 0.5, "synapse": 0.01, "seed": 4},
                ]
            )
    else:
        neurons = ["lifrate", "lif", "rectified"]
        if include_adaptive:
            neurons.append("adaptivehyperlif_tuned")
        settings = [
            {"n_neurons": 400, "radius": 1.5, "synapse": 0.002, "seed": 2},
            {"n_neurons": 600, "radius": 1.0, "synapse": 0.003, "seed": 3},
            {"n_neurons": 800, "radius": 0.75, "synapse": 0.005, "seed": 4},
            {"n_neurons": 1000, "radius": 0.5, "synapse": 0.01, "seed": 5},
        ]
    if neuron_filter:
        wanted = set(neuron_filter)
        neurons = [neuron for neuron in neurons if neuron in wanted]
    return [{**setting, "neuron": neuron} for neuron in neurons for setting in settings]


def run_case(args: argparse.Namespace, case: dict[str, float | int | str]) -> dict[str, float | int | str]:
    cmd = [
        sys.executable,
        str(CONTROLLER),
        "--quad",
        args.quad,
        "--mission",
        args.mission,
        "--neuron",
        str(case["neuron"]),
        "--n-neurons",
        str(case["n_neurons"]),
        "--radius",
        str(case["radius"]),
        "--synapse",
        str(case["synapse"]),
        "--seed",
        str(case["seed"]),
        "--dt",
        str(args.dt),
        "--sim-time",
        str(args.sim_time),
        "--max-rate-low",
        str(args.max_rate_low),
        "--max-rate-high",
        str(args.max_rate_high),
        "--intercept-low",
        str(args.intercept_low),
        "--intercept-high",
        str(args.intercept_high),
    ]
    print("Running:", " ".join(cmd))
    if not args.dry_run:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)

    stem = expected_stem(
        args.quad,
        args.mission,
        str(case["neuron"]),
        int(case["n_neurons"]),
        float(case["radius"]),
        float(case["synapse"]),
        int(case["seed"]),
        args.dt,
    )
    summary_path = LOGS_DIR / f"{stem}_summary.txt"
    if args.dry_run:
        return {
            "mission": args.mission,
            **case,
            "summary": str(summary_path),
            "status": "dry-run",
        }
    text = summary_path.read_text(encoding="utf-8")
    rmse = parse_vector(text, "rmse_phi_theta_psi")
    return {
        "mission": args.mission,
        "quad": args.quad,
        **case,
        "dt": args.dt,
        "sim_time": args.sim_time,
        "rmse_phi": rmse[0],
        "rmse_theta": rmse[1],
        "rmse_psi": rmse[2],
        "qerr_mean": parse_scalar(text, "qerr_mean"),
        "qerr_max": parse_scalar(text, "qerr_max"),
        "tau_mean": parse_scalar(text, "tau_mean"),
        "z_mean": parse_scalar(text, "z_mean"),
        "z_std": parse_scalar(text, "z_std"),
        "summary": str(summary_path),
        "status": "ok",
    }


def write_rows(rows: list[dict[str, float | int | str]], args: argparse.Namespace) -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = LOGS_DIR / f"mujoco_nengo_controller_benchmark_{args.quad}_{args.mission}_{args.preset}.csv"
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def plot_rows(rows: list[dict[str, float | int | str]], args: argparse.Namespace) -> None:
    valid = [row for row in rows if row.get("status") == "ok"]
    if not valid:
        return
    import matplotlib.pyplot as plt

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    valid = sorted(valid, key=lambda r: float(r["qerr_mean"]))
    labels = [
        f"{r['neuron']}\nn={r['n_neurons']} r={r['radius']} s={r['synapse']}"
        for r in valid
    ]
    metrics = ["qerr_mean", "tau_mean", "z_std"]
    fig, axes = plt.subplots(3, 1, figsize=(max(10, 0.7 * len(valid)), 9), sharex=True)
    x = np.arange(len(valid))
    for ax, metric in zip(axes, metrics):
        vals = [float(r[metric]) for r in valid]
        ax.bar(x, vals)
        ax.set_ylabel(metric)
        ax.grid(True, axis="y", alpha=0.3)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, rotation=35, ha="right")
    fig.suptitle(f"MuJoCo Nengo controller benchmark: {args.quad}, {args.mission}, {args.preset}")
    fig.tight_layout()
    path = FIGURES_DIR / f"mujoco_nengo_controller_benchmark_{args.quad}_{args.mission}_{args.preset}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quad", choices=["skydio_x2", "bitcraze_crazyflie_2"], default="skydio_x2")
    parser.add_argument("--mission", choices=["roll", "full3", "step"], default="roll")
    parser.add_argument("--preset", choices=["quick", "full"], default="quick")
    parser.add_argument("--include-adaptive", action="store_true")
    parser.add_argument(
        "--neurons",
        default="",
        help="Optional comma-separated subset, e.g. rectified,lifrate,adaptivehyperlif_tuned",
    )
    parser.add_argument("--dt", type=float, default=0.0005)
    parser.add_argument("--sim-time", type=float, default=15.0)
    parser.add_argument("--max-rate-low", type=float, default=100.0)
    parser.add_argument("--max-rate-high", type=float, default=200.0)
    parser.add_argument("--intercept-low", type=float, default=-0.8)
    parser.add_argument("--intercept-high", type=float, default=0.8)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = []
    neuron_filter = [item.strip() for item in args.neurons.split(",") if item.strip()]
    for case in grid(args.preset, args.include_adaptive, neuron_filter):
        try:
            rows.append(run_case(args, case))
        except Exception as exc:
            print(f"Case failed: {case}: {exc}")
            rows.append({"mission": args.mission, **case, "status": f"failed: {exc}"})

    csv_path = write_rows(rows, args)
    plot_rows(rows, args)
    print(f"Saved benchmark CSV: {csv_path}")


if __name__ == "__main__":
    main()
