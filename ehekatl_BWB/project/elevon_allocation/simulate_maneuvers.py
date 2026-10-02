"""Monte Carlo numerical study of EHEKATL distributed elevon allocation."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from elevon_allocation.allocator import BoxQPAllocator, EffectivenessModel, FixedMixer


HZ = 35.0
DT = 1.0 / HZ
DURATION = 10.0
N_STEPS = int(DURATION * HZ)
AXES = ("roll", "pitch", "yaw")
MANEUVERS = ("pitch_capture", "bank_capture", "coordinated_turn", "agile_reversal", "yaw_rejection")
SCENARIOS = ("nominal", "outer_elevon_jam", "left_rudder_failed", "degraded_outboard_pair")
METHODS = ("fixed_mixer", "constrained_qp", "covariance_aware_qp")


@dataclass
class TrialMetric:
    method: str
    maneuver: str
    scenario: str
    trial: int
    angle_rmse_deg: float
    peak_angle_error_deg: float
    allocation_rmse_deg_s2: float
    surface_rms_command: float
    total_variation: float
    saturation_fraction: float
    final_error_norm_deg: float


def smooth_step(t: np.ndarray, start: float, end: float, amplitude: float) -> np.ndarray:
    width = 0.22
    return 0.5 * amplitude * (np.tanh((t - start) / width) - np.tanh((t - end) / width))


def reference(maneuver: str, t: np.ndarray) -> np.ndarray:
    ref = np.zeros((len(t), 3))
    if maneuver == "pitch_capture":
        ref[:, 1] = smooth_step(t, 1.0, 8.0, 8.0)
    elif maneuver == "bank_capture":
        ref[:, 0] = smooth_step(t, 1.0, 8.0, 22.0)
    elif maneuver == "coordinated_turn":
        ref[:, 0] = smooth_step(t, 1.0, 8.5, 18.0)
        ref[:, 2] = smooth_step(t, 1.5, 8.5, 14.0)
    elif maneuver == "agile_reversal":
        ref[:, 0] = smooth_step(t, 0.8, 4.2, 24.0) - smooth_step(t, 4.2, 8.4, 24.0)
        ref[:, 1] = smooth_step(t, 1.2, 8.0, 6.0)
    elif maneuver == "yaw_rejection":
        ref[:, 2] = smooth_step(t, 1.0, 3.8, 16.0) - smooth_step(t, 5.0, 7.8, 16.0)
    else:
        raise ValueError(maneuver)
    return ref


def make_allocator(method: str, model: EffectivenessModel):
    if method == "fixed_mixer":
        return FixedMixer(model, DT)
    if method == "constrained_qp":
        return BoxQPAllocator(model, DT, covariance_weight=0.0)
    if method == "covariance_aware_qp":
        return BoxQPAllocator(model, DT, covariance_weight=20.0)
    raise ValueError(method)


def configure_scenario(allocator, scenario: str) -> None:
    if scenario == "nominal":
        return
    if scenario == "outer_elevon_jam":
        allocator.configure_failure("elevon_L4", 0.0)
    elif scenario == "left_rudder_failed":
        allocator.configure_failure("rudder_L", 0.0)
    elif scenario == "degraded_outboard_pair":
        allocator.configure_failure("elevon_L4", 0.55)
        allocator.configure_failure("elevon_R4", 0.55)
    else:
        raise ValueError(scenario)


def scenario_scale(model: EffectivenessModel, scenario: str) -> np.ndarray:
    scale = np.ones(model.matrix.shape[1])
    if scenario == "nominal":
        return scale
    if scenario == "outer_elevon_jam":
        scale[model.surface_names.index("elevon_L4")] = 0.0
    elif scenario == "left_rudder_failed":
        scale[model.surface_names.index("rudder_L")] = 0.0
    elif scenario == "degraded_outboard_pair":
        scale[model.surface_names.index("elevon_L4")] = 0.55
        scale[model.surface_names.index("elevon_R4")] = 0.55
    else:
        raise ValueError(scenario)
    return scale


def simulate(method: str, maneuver: str, scenario: str, trial: int, seed: int):
    model = EffectivenessModel.research_prior()
    allocator = make_allocator(method, model)
    # A fixed mixer is intentionally fault-unaware. The two optimization-based
    # allocators receive the detected effectiveness loss and can redistribute
    # control. This is the operational distinction under test.
    if method != "fixed_mixer":
        configure_scenario(allocator, scenario)
    rng = np.random.default_rng(seed + 100003 * trial)
    actual_b = model.sampled(rng) * scenario_scale(model, scenario)[np.newaxis, :]

    t = np.arange(N_STEPS) * DT
    ref = reference(maneuver, t)
    angles = np.zeros((N_STEPS, 3))
    rates = np.zeros((N_STEPS, 3))
    commands = np.zeros((N_STEPS, 10))
    virtual = np.zeros((N_STEPS, 3))
    achieved = np.zeros((N_STEPS, 3))
    saturated = np.zeros((N_STEPS, 10), dtype=bool)
    damping = np.array([0.95, 1.05, 0.85])
    kp = np.array([2.4, 2.9, 1.75])
    kd = np.array([2.15, 2.35, 1.8])

    for k in range(1, N_STEPS):
        virtual[k] = np.clip(kp * (ref[k] - angles[k - 1]) - kd * rates[k - 1], -55.0, 55.0)
        result = allocator.allocate(virtual[k])
        commands[k] = result.command
        saturated[k] = result.saturated
        achieved[k] = actual_b @ result.command
        disturbance = rng.normal(0.0, [0.10, 0.10, 0.08])
        rates[k] = rates[k - 1] + DT * (achieved[k] - damping * rates[k - 1] + disturbance)
        angles[k] = angles[k - 1] + DT * rates[k]

    error = ref - angles
    allocation_error = virtual - achieved
    metric = TrialMetric(
        method=method,
        maneuver=maneuver,
        scenario=scenario,
        trial=trial,
        angle_rmse_deg=float(np.sqrt(np.mean(error**2))),
        peak_angle_error_deg=float(np.max(np.abs(error))),
        allocation_rmse_deg_s2=float(np.sqrt(np.mean(allocation_error**2))),
        surface_rms_command=float(np.sqrt(np.mean(commands**2))),
        total_variation=float(np.sum(np.abs(np.diff(commands, axis=0)))),
        saturation_fraction=float(np.mean(saturated)),
        final_error_norm_deg=float(np.linalg.norm(error[-1])),
    )
    trace = {"time": t, "reference": ref, "angles": angles, "rates": rates, "commands": commands,
             "virtual": virtual, "achieved": achieved}
    return metric, trace


def summarize(metrics: list[TrialMetric]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for method in METHODS:
        for scenario in SCENARIOS:
            selected = [m for m in metrics if m.method == method and m.scenario == scenario]
            for field in ("angle_rmse_deg", "allocation_rmse_deg_s2", "total_variation", "saturation_fraction"):
                values = np.array([getattr(m, field) for m in selected])
                rows.append({
                    "method": method,
                    "scenario": scenario,
                    "metric": field,
                    "mean": float(values.mean()),
                    "median": float(np.median(values)),
                    "p95": float(np.quantile(values, 0.95)),
                    "n": int(values.size),
                })
    return rows


def make_plots(output: Path, metrics: list[TrialMetric], example_traces: dict[str, dict[str, np.ndarray]]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2), constrained_layout=True)
    colors = {"fixed_mixer": "#777777", "constrained_qp": "#1f77b4", "covariance_aware_qp": "#d97706"}
    x = np.arange(len(SCENARIOS))
    for j, method in enumerate(METHODS):
        means = []
        p95 = []
        for scenario in SCENARIOS:
            values = np.array([m.angle_rmse_deg for m in metrics if m.method == method and m.scenario == scenario])
            means.append(values.mean())
            p95.append(np.quantile(values, 0.95))
        axes[0].bar(x + (j - 1) * 0.24, means, width=0.22, color=colors[method], label=method.replace("_", " "))
        axes[1].bar(x + (j - 1) * 0.24, p95, width=0.22, color=colors[method])
    for ax, title, ylabel in zip(axes, ("Mean across five maneuvers", "95th percentile across five maneuvers"),
                                 ("attitude RMSE [deg]", "attitude RMSE [deg]")):
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xticks(x, [s.replace("_", "\n") for s in SCENARIOS], fontsize=8)
        ax.grid(axis="y", alpha=0.25)
    axes[0].legend(frameon=False, fontsize=8)
    fig.savefig(output / "monte_carlo_attitude_error.png", dpi=220)
    fig.savefig(output / "monte_carlo_attitude_error.pdf")
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(9.5, 8.5), sharex=True, constrained_layout=True)
    for method, trace in example_traces.items():
        for axis in range(3):
            axes[axis].plot(trace["time"], trace["angles"][:, axis], color=colors[method], lw=1.5,
                            label=method.replace("_", " "))
    trace0 = next(iter(example_traces.values()))
    for axis in range(3):
        axes[axis].plot(trace0["time"], trace0["reference"][:, axis], "k--", lw=1.1, label="reference")
        axes[axis].set_ylabel(f"{AXES[axis]} [deg]")
        axes[axis].grid(alpha=0.25)
    axes[0].legend(frameon=False, ncol=2, fontsize=8)
    axes[-1].set_xlabel("time [s]")
    fig.suptitle("Agile reversal with left outer elevon jam")
    fig.savefig(output / "agile_reversal_fault_trace.png", dpi=220)
    fig.savefig(output / "agile_reversal_fault_trace.pdf")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260917)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "results")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    metrics: list[TrialMetric] = []
    examples: dict[str, dict[str, np.ndarray]] = {}
    for method in METHODS:
        for maneuver in MANEUVERS:
            for scenario in SCENARIOS:
                for trial in range(args.trials):
                    metric, trace = simulate(method, maneuver, scenario, trial, args.seed)
                    metrics.append(metric)
                    if maneuver == "agile_reversal" and scenario == "outer_elevon_jam" and trial == 0:
                        examples[method] = trace
                print(json.dumps({"completed": [method, maneuver, scenario], "trials": args.trials}), flush=True)

    metric_rows = [asdict(metric) for metric in metrics]
    with (args.output / "trial_metrics.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(metric_rows[0]))
        writer.writeheader()
        writer.writerows(metric_rows)
    summary = summarize(metrics)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (args.output / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    make_plots(args.output, metrics, examples)
    print(json.dumps({"trials_total": len(metrics), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
