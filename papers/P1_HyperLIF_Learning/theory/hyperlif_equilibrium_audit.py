"""Equilibrium and local-stability audit for HyperLIF/Adaptive HyperLIF.

The script treats input current J as constant, finds every equilibrium of the
coupled two-state ODE on r in [0, 1], evaluates the full 2x2 Jacobian, and
writes machine-readable evidence.  It deliberately does not infer oscillation
frequency from equilibria; limit cycles require a separate trajectory or
bifurcation analysis.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class Parameters:
    tau: float = 0.02
    tau_r: float = 0.002
    alpha: float = 100.0
    gamma: float = 0.2
    v_rest: float = 0.0
    v_reset: float = 0.0
    theta: float = 1.0
    event_threshold: float = 1.0
    fixed_gain: float = 100.0
    base_gain: float = 20.0
    adaptive_gain: float = 80.0


def logistic(x: float) -> float:
    x = float(np.clip(x, -700.0, 700.0))
    return float(1.0 / (1.0 + np.exp(-x)))


def gain_scale(current: float, adaptive: bool, p: Parameters) -> float:
    return p.base_gain + p.adaptive_gain * abs(current) if adaptive else p.fixed_gain


def voltage_equilibrium(gate: float, current: float, adaptive: bool,
                        p: Parameters) -> float:
    conductance = gain_scale(current, adaptive, p) * gate**2
    return float(
        (p.v_rest + current + p.tau * conductance * p.v_reset)
        / (1.0 + p.tau * conductance)
    )


def gate_balance(gate: float, current: float, adaptive: bool,
                 p: Parameters) -> float:
    voltage = voltage_equilibrium(gate, current, adaptive, p)
    target = logistic(p.alpha * (voltage - p.theta + p.gamma * gate))
    return target - gate


def _bisect(current: float, adaptive: bool, p: Parameters,
            left: float, right: float) -> float:
    f_left = gate_balance(left, current, adaptive, p)
    for _ in range(80):
        mid = 0.5 * (left + right)
        f_mid = gate_balance(mid, current, adaptive, p)
        if abs(f_mid) < 1e-13 or right - left < 1e-12:
            return mid
        if f_left * f_mid <= 0:
            right = mid
        else:
            left, f_left = mid, f_mid
    return 0.5 * (left + right)


def equilibrium_gates(current: float, adaptive: bool, p: Parameters,
                      grid_size: int = 4001) -> list[float]:
    grid = np.linspace(0.0, 1.0, grid_size)
    values = np.asarray([gate_balance(float(r), current, adaptive, p) for r in grid])
    roots: list[float] = []
    for i in range(grid_size - 1):
        if values[i] == 0.0:
            roots.append(float(grid[i]))
        elif values[i] * values[i + 1] < 0.0:
            roots.append(_bisect(current, adaptive, p, float(grid[i]), float(grid[i + 1])))
    if values[-1] == 0.0:
        roots.append(1.0)
    roots.sort()
    unique: list[float] = []
    for root in roots:
        if not unique or abs(root - unique[-1]) > 1e-7:
            unique.append(root)
    return unique


def jacobian(voltage: float, gate: float, current: float, adaptive: bool,
             p: Parameters) -> np.ndarray:
    scale = gain_scale(current, adaptive, p)
    conductance = scale * gate**2
    sigmoid_slope_factor = gate * (1.0 - gate)  # target == gate at equilibrium
    return np.asarray(
        [
            [-(1.0 / p.tau + conductance),
             -2.0 * scale * gate * (voltage - p.v_reset)],
            [p.alpha * sigmoid_slope_factor / p.tau_r,
             (p.alpha * p.gamma * sigmoid_slope_factor - 1.0) / p.tau_r],
        ],
        dtype=float,
    )


def audit(currents: np.ndarray, p: Parameters) -> list[dict]:
    rows: list[dict] = []
    for family, adaptive in (("HyperLIF", False), ("AdaptiveHyperLIF", True)):
        for current in currents:
            for branch, gate in enumerate(equilibrium_gates(float(current), adaptive, p)):
                voltage = voltage_equilibrium(gate, float(current), adaptive, p)
                eig = np.linalg.eigvals(jacobian(voltage, gate, float(current), adaptive, p))
                rows.append(
                    {
                        "family": family,
                        "current": float(current),
                        "branch": branch,
                        "voltage": voltage,
                        "gate": gate,
                        "conductance": gain_scale(float(current), adaptive, p) * gate**2,
                        "eig1_real": float(eig[0].real),
                        "eig1_imag": float(eig[0].imag),
                        "eig2_real": float(eig[1].real),
                        "eig2_imag": float(eig[1].imag),
                        "max_real_eigenvalue": float(np.max(eig.real)),
                        "locally_asymptotically_stable": bool(np.max(eig.real) < 0.0),
                        "above_event_threshold": bool(voltage >= p.event_threshold),
                    }
                )
    return rows


def summarize(rows: list[dict], p: Parameters) -> dict:
    summary: dict = {
        "parameter_contract": p.__dict__,
        "analytical_open_gate_db_current_fixed": (
            (p.theta - p.gamma) * (1.0 + p.tau * p.fixed_gain)
            - p.v_rest - p.tau * p.fixed_gain * p.v_reset
        ),
        "adaptive_positive_drive_open_gate_voltage_limit": (
            (1.0 + p.tau * p.adaptive_gain * p.v_reset)
            / (p.tau * p.adaptive_gain)
        ),
        "adaptive_open_gate_bound_condition_beta_gt": (
            1.0 / (p.tau * (p.theta - p.gamma - p.v_reset))
        ),
        "alpha_times_gamma": p.alpha * p.gamma,
        "simple_gate_self_feedback_bound_alpha_gamma_lt_4": (
            p.alpha * p.gamma < 4.0
        ),
        "warning": (
            "Open-gate formulas analyze the r=1 branch. The true coupled "
            "equilibria satisfy an implicit gate equation; equilibrium stability "
            "does not by itself establish or exclude a limit cycle."
        ),
    }
    root_counts: dict[tuple[str, float], int] = {}
    for row in rows:
        key = (row["family"], row["current"])
        root_counts[key] = root_counts.get(key, 0) + 1

    for family in ("HyperLIF", "AdaptiveHyperLIF"):
        subset = [row for row in rows if row["family"] == family]
        multi = sorted(
            current
            for (row_family, current), count in root_counts.items()
            if row_family == family and count > 1
        )
        stable_above = [row["current"] for row in subset
                        if row["locally_asymptotically_stable"] and row["above_event_threshold"]]
        unstable = [row["current"] for row in subset
                    if not row["locally_asymptotically_stable"]]
        summary[family] = {
            "equilibrium_rows": len(subset),
            "sampled_multi_equilibrium_current_range": (
                [min(multi), max(multi)] if multi else None
            ),
            "sampled_stable_above_event_current_range": (
                [min(stable_above), max(stable_above)] if stable_above else None
            ),
            "sampled_unstable_equilibrium_current_range": (
                [min(unstable), max(unstable)] if unstable else None
            ),
        }
    return summary


def write_outputs(rows: list[dict], summary: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with (output / "equilibria.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(2, 1, figsize=(9, 8), sharex=True)
    colors = {"HyperLIF": "#185FA5", "AdaptiveHyperLIF": "#1B9E77"}
    for family in colors:
        for stable, marker, alpha in ((True, ".", 0.9), (False, "x", 0.55)):
            selected = [row for row in rows if row["family"] == family and
                        row["locally_asymptotically_stable"] is stable]
            label = f"{family} {'stable' if stable else 'unstable'}"
            axes[0].scatter([row["current"] for row in selected],
                            [row["voltage"] for row in selected], s=9, marker=marker,
                            alpha=alpha, color=colors[family], label=label)
            axes[1].scatter([row["current"] for row in selected],
                            [row["gate"] for row in selected], s=9, marker=marker,
                            alpha=alpha, color=colors[family])
    axes[0].axhline(summary["parameter_contract"]["event_threshold"], color="black",
                    linestyle="--", linewidth=1, label="event threshold")
    axes[0].axhline(summary["parameter_contract"]["theta"] -
                    summary["parameter_contract"]["gamma"], color="#CC5500",
                    linestyle=":", linewidth=1, label="open-gate knee")
    axes[0].set_ylabel("equilibrium voltage")
    axes[1].set_ylabel("equilibrium gate")
    axes[1].set_xlabel("constant input current J")
    axes[0].legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "equilibrium_branches.png", dpi=180)
    plt.close(fig)


def self_check(p: Parameters) -> None:
    assert 0 < p.tau and 0 < p.tau_r and 0 < p.theta
    assert 0 <= p.gamma < p.theta - p.v_reset
    assert abs(voltage_equilibrium(1.0, 4.0, False, p) - 4.0 / 3.0) < 1e-12
    shifted = replace(p, v_reset=-0.6)
    assert voltage_equilibrium(0.0, 0.0, False, shifted) == 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--j-min", type=float, default=0.0)
    parser.add_argument("--j-max", type=float, default=6.0)
    parser.add_argument("--j-step", type=float, default=0.01)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parent / "results" / "default_equilibria")
    args = parser.parse_args()
    if args.j_step <= 0 or args.j_max < args.j_min:
        raise ValueError("require j_step > 0 and j_max >= j_min")
    p = Parameters()
    self_check(p)
    currents = np.arange(args.j_min, args.j_max + 0.5 * args.j_step, args.j_step)
    rows = audit(currents, p)
    summary = summarize(rows, p)
    write_outputs(rows, summary, args.output)
    print(json.dumps({"output": str(args.output), **summary}, indent=2))


if __name__ == "__main__":
    main()
