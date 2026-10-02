"""Like-for-like EHEKATL mission comparison for grouped and allocated ACS.

The baseline represents the thesis convention: two inner elevon pairs act as
elevators, two outer pairs act as ailerons, and the two rudders share a single
directional command.  The extension keeps the same attitude controller and
plant, but allocates the requested angular acceleration independently across
eight elevons and two rudders.

The effectiveness matrix is the transparent research prior in ``allocator``;
it is not an identified X-Plane or wind-tunnel model.  Results therefore show
the expected allocation mechanism and its fault-reconfiguration benefit, not
physical-aircraft performance.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from elevon_allocation.allocator import BoxQPAllocator, EffectivenessModel


HZ = 35.0
DT = 1.0 / HZ
DURATION = 70.0
FAULT_TIME = 32.0
AXES = ("roll", "pitch", "yaw")


@dataclass(frozen=True)
class MissionMetric:
    architecture: str
    attitude_rmse_deg: float
    peak_attitude_error_deg: float
    post_fault_rmse_deg: float
    allocation_rmse_deg_s2: float
    surface_rms_command: float
    total_variation: float
    saturation_fraction: float


class ThesisGroupedACS:
    """Three thesis-style commands routed to fixed surface groups.

    Logical commands are elevator, aileron and rudder.  The grouping is fixed
    and fault-unaware, matching the conventional primary-input abstraction
    used by the thesis controller derivation.
    """

    def __init__(self, model: EffectivenessModel, dt: float) -> None:
        self.model = model
        self.dt = float(dt)
        # Surface order: L1..L4, R1..R4, rudder L/R.
        self.grouping = np.zeros((10, 3))
        self.grouping[[0, 1, 4, 5], 0] = 1.0  # two inner elevator pairs
        self.grouping[[2, 3], 1] = -1.0       # left outer aileron pairs
        self.grouping[[6, 7], 1] = 1.0        # right outer aileron pairs
        self.grouping[[8, 9], 2] = 1.0        # paired rudders
        self.logical_effectiveness = model.matrix @ self.grouping
        self.previous = np.zeros(3)
        self.command_limits = np.ones(3)
        self.rate_limits = np.array([60.0 / 30.0, 60.0 / 30.0, 80.0 / 30.0])

    def allocate(self, virtual_command: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        desired = np.asarray(virtual_command, dtype=float)
        logical = np.linalg.solve(self.logical_effectiveness, desired)
        lower = np.maximum(-self.command_limits, self.previous - self.rate_limits * self.dt)
        upper = np.minimum(self.command_limits, self.previous + self.rate_limits * self.dt)
        logical = np.clip(logical, lower, upper)
        self.previous = logical.copy()
        surface = self.grouping @ logical
        achieved = self.model.matrix @ surface
        saturated = np.isclose(logical, lower, atol=2e-6) | np.isclose(logical, upper, atol=2e-6)
        return surface, achieved, saturated


def mission_reference(time: np.ndarray) -> np.ndarray:
    """Smooth attitude programme resembling climb, survey, return and landing."""
    knots = np.array([0, 5, 12, 18, 27, 35, 42, 50, 57, 63, 70], dtype=float)
    targets = np.array([
        [0, 0, 0],       # ground/trim
        [0, 8, 0],       # climb
        [0, 8, 0],
        [22, 3, 0],      # right survey turn
        [22, 3, 28],
        [0, 2, 28],      # level survey leg
        [-18, 3, 5],     # reversing turn
        [-18, -4, -18],
        [0, -5, -18],    # descent
        [0, 4, 0],       # flare/level
        [0, 2, 0],
    ], dtype=float)
    raw = np.column_stack([np.interp(time, knots, targets[:, axis]) for axis in range(3)])
    # First-order command shaping avoids artificial acceleration impulses.
    shaped = np.zeros_like(raw)
    alpha = DT / (0.55 + DT)
    for k in range(1, len(time)):
        shaped[k] = shaped[k - 1] + alpha * (raw[k] - shaped[k - 1])
    return shaped


def common_disturbance(time: float) -> np.ndarray:
    """Deterministic gust moments shared by both architectures."""
    gust_1 = np.exp(-0.5 * ((time - 23.0) / 0.65) ** 2)
    gust_2 = np.exp(-0.5 * ((time - 46.0) / 0.85) ** 2)
    return np.array([5.5 * gust_1 - 4.0 * gust_2, -2.0 * gust_1 + 3.0 * gust_2, 2.8 * gust_1 + 3.6 * gust_2])


def simulate_architecture(architecture: str, seed: int = 20260917) -> tuple[MissionMetric, dict[str, np.ndarray]]:
    model = EffectivenessModel.research_prior()
    rng = np.random.default_rng(seed)
    actual_nominal = model.sampled(rng, common_scale_sigma=0.035)
    if architecture == "thesis_grouped_acs":
        allocator = ThesisGroupedACS(model, DT)
    elif architecture == "distributed_elevon_qp":
        allocator = BoxQPAllocator(model, DT, covariance_weight=0.0, delta_weight=0.06)
    else:
        raise ValueError(architecture)

    time = np.arange(int(DURATION * HZ) + 1) * DT
    reference = mission_reference(time)
    angles = np.zeros((len(time), 3))
    rates = np.zeros_like(angles)
    commands = np.zeros((len(time), 10))
    virtual = np.zeros_like(angles)
    achieved = np.zeros_like(angles)
    saturation = np.zeros((len(time), 10), dtype=bool)
    allocation_residual = np.zeros_like(angles)

    damping = np.array([1.00, 1.10, 0.90])
    kp = np.array([2.65, 3.00, 1.85])
    kd = np.array([2.25, 2.45, 1.90])
    failed_index = model.surface_names.index("elevon_L4")
    fault_configured = False

    for k in range(1, len(time)):
        virtual[k] = np.clip(kp * (reference[k] - angles[k - 1]) - kd * rates[k - 1], -58.0, 58.0)
        if architecture == "distributed_elevon_qp":
            if time[k] >= FAULT_TIME and not fault_configured:
                allocator.configure_failure("elevon_L4", 0.0)
                fault_configured = True
            result = allocator.allocate(virtual[k])
            surface = result.command
            saturation[k] = result.saturated
        else:
            surface, _, logical_saturated = allocator.allocate(virtual[k])
            saturation[k] = np.repeat(logical_saturated, [4, 4, 2])

        effective = actual_nominal.copy()
        if time[k] >= FAULT_TIME:
            effective[:, failed_index] = 0.0
        commands[k] = surface
        achieved[k] = effective @ surface
        allocation_residual[k] = virtual[k] - achieved[k]
        noise = rng.normal(0.0, [0.055, 0.055, 0.045])
        acceleration = achieved[k] - damping * rates[k - 1] + common_disturbance(time[k]) + noise
        rates[k] = rates[k - 1] + DT * acceleration
        angles[k] = angles[k - 1] + DT * rates[k]

    error = reference - angles
    post_fault = time >= FAULT_TIME
    metric = MissionMetric(
        architecture=architecture,
        attitude_rmse_deg=float(np.sqrt(np.mean(error**2))),
        peak_attitude_error_deg=float(np.max(np.abs(error))),
        post_fault_rmse_deg=float(np.sqrt(np.mean(error[post_fault] ** 2))),
        allocation_rmse_deg_s2=float(np.sqrt(np.mean(allocation_residual**2))),
        surface_rms_command=float(np.sqrt(np.mean(commands**2))),
        total_variation=float(np.sum(np.abs(np.diff(commands, axis=0)))),
        saturation_fraction=float(np.mean(saturation)),
    )
    trace = {
        "time": time,
        "reference": reference,
        "angles": angles,
        "rates": rates,
        "commands": commands,
        "virtual": virtual,
        "achieved": achieved,
        "allocation_residual": allocation_residual,
    }
    return metric, trace


def save_outputs(output: Path, metrics: list[MissionMetric], traces: dict[str, dict[str, np.ndarray]]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    summary = [metric.__dict__ for metric in metrics]
    (output / "mission_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output / "mission_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    display_names = {
        "thesis_grouped_acs": "Thesis grouped ACS",
        "distributed_elevon_qp": "Distributed elevon QP",
    }
    table_lines = [
        "# Representative paired mission metrics",
        "",
        "Same seed, uncertainty draw, gusts, reference, controller and actuator limits.",
        "The left outer elevon is jammed at zero at 32 s.",
        "",
        "| Architecture | Attitude RMSE [deg] | Peak error [deg] | Post-fault RMSE [deg] | Allocation RMSE [deg/s^2] | Surface RMS [-] | Total variation [-] |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for metric in metrics:
        table_lines.append(
            f"| {display_names[metric.architecture]} | {metric.attitude_rmse_deg:.4f} | "
            f"{metric.peak_attitude_error_deg:.4f} | {metric.post_fault_rmse_deg:.4f} | "
            f"{metric.allocation_rmse_deg_s2:.4f} | {metric.surface_rms_command:.5f} | "
            f"{metric.total_variation:.4f} |"
        )
    table_lines += [
        "",
        "> Evidence boundary: the control-effectiveness matrix is a synthetic research prior,",
        "> not an identified EHEKATL, X-Plane, wind-tunnel or flight-test model.",
        "",
    ]
    (output / "mission_metrics_table.md").write_text("\n".join(table_lines), encoding="utf-8")

    fields = ["time_s", "architecture"]
    fields += [f"{name}_reference_deg" for name in AXES]
    fields += [f"{name}_deg" for name in AXES]
    fields += [f"{name}_rate_deg_s" for name in AXES]
    fields += [f"surface_{name}" for name in EffectivenessModel.research_prior().surface_names]
    fields += ["allocation_residual_norm_deg_s2"]
    with (output / "mission_timeseries.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for architecture, trace in traces.items():
            for k, time in enumerate(trace["time"]):
                row: dict[str, object] = {"time_s": float(time), "architecture": architecture}
                row.update({f"{name}_reference_deg": float(trace["reference"][k, axis]) for axis, name in enumerate(AXES)})
                row.update({f"{name}_deg": float(trace["angles"][k, axis]) for axis, name in enumerate(AXES)})
                row.update({f"{name}_rate_deg_s": float(trace["rates"][k, axis]) for axis, name in enumerate(AXES)})
                row.update({f"surface_{name}": float(trace["commands"][k, index]) for index, name in enumerate(EffectivenessModel.research_prior().surface_names)})
                row["allocation_residual_norm_deg_s2"] = float(np.linalg.norm(trace["allocation_residual"][k]))
                writer.writerow(row)


def make_figures(output: Path, traces: dict[str, dict[str, np.ndarray]]) -> None:
    colors = {"thesis_grouped_acs": "#d97706", "distributed_elevon_qp": "#1f77b4"}
    labels = {"thesis_grouped_acs": "thesis grouped ACS", "distributed_elevon_qp": "distributed elevon QP"}
    reference = next(iter(traces.values()))["reference"]
    time = next(iter(traces.values()))["time"]

    fig, axes = plt.subplots(3, 1, figsize=(10.5, 8.2), sharex=True, constrained_layout=True)
    for axis, name in enumerate(AXES):
        axes[axis].plot(time, reference[:, axis], "k--", lw=1.2, label="mission reference")
        for architecture, trace in traces.items():
            axes[axis].plot(time, trace["angles"][:, axis], color=colors[architecture], lw=1.45, label=labels[architecture])
        axes[axis].axvline(FAULT_TIME, color="#b91c1c", lw=1.0, ls=":")
        axes[axis].set_ylabel(f"{name} [deg]")
        axes[axis].grid(alpha=0.25)
    axes[0].legend(frameon=False, ncol=3, fontsize=8)
    axes[-1].set_xlabel("mission time [s]")
    fig.suptitle("Same EHEKATL mission: thesis grouped ACS vs independent elevon allocation\nleft outer elevon jam at 32 s; common gusts at 23 s and 46 s")
    fig.savefig(output / "mission_attitude_comparison.png", dpi=240)
    fig.savefig(output / "mission_attitude_comparison.pdf")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(10.5, 6.6), sharex=True, constrained_layout=True)
    for architecture, trace in traces.items():
        residual = np.linalg.norm(trace["allocation_residual"], axis=1)
        axes[0].plot(trace["time"], residual, color=colors[architecture], lw=1.35, label=labels[architecture])
        axes[1].plot(trace["time"], np.max(np.abs(trace["commands"]), axis=1), color=colors[architecture], lw=1.35)
    for axis in axes:
        axis.axvline(FAULT_TIME, color="#b91c1c", lw=1.0, ls=":")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("allocation residual norm [deg/s²]")
    axes[1].set_ylabel("maximum |surface command| [-]")
    axes[1].set_xlabel("mission time [s]")
    axes[0].legend(frameon=False)
    fig.suptitle("Allocation accuracy and actuator demand")
    fig.savefig(output / "mission_allocation_comparison.png", dpi=240)
    fig.savefig(output / "mission_allocation_comparison.pdf")
    plt.close(fig)

    surface_names = EffectivenessModel.research_prior().surface_names
    vmax = max(float(np.max(np.abs(trace["commands"]))) for trace in traces.values())
    fig, axes = plt.subplots(2, 1, figsize=(11.2, 7.3), sharex=True, constrained_layout=True)
    image = None
    for axis, architecture in zip(axes, ("thesis_grouped_acs", "distributed_elevon_qp")):
        trace = traces[architecture]
        image = axis.imshow(
            trace["commands"].T,
            aspect="auto",
            origin="lower",
            extent=[time[0], time[-1], -0.5, len(surface_names) - 0.5],
            cmap="RdBu_r",
            vmin=-vmax,
            vmax=vmax,
            interpolation="nearest",
        )
        axis.axvline(FAULT_TIME, color="#111827", lw=1.25, ls="--")
        axis.axhspan(2.5, 3.5, facecolor="none", edgecolor="#facc15", lw=1.5)
        axis.set_yticks(np.arange(len(surface_names)), surface_names, fontsize=8)
        axis.set_title(labels[architecture], loc="left", fontsize=10, weight="bold")
        axis.set_ylabel("commanded effector")
    axes[-1].set_xlabel("mission time [s]")
    axes[0].text(FAULT_TIME + 0.8, 8.8, "L4 jam", color="#111827", fontsize=8,
                 bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"})
    if image is not None:
        colorbar = fig.colorbar(image, ax=axes, shrink=0.92, pad=0.02)
        colorbar.set_label("normalized surface command [-]")
    fig.suptitle(
        "Actuator use and post-fault redistribution\n"
        "yellow outline: failed elevon_L4; dashed line: detected jam at 32 s"
    )
    fig.savefig(output / "mission_surface_redistribution.png", dpi=240)
    fig.savefig(output / "mission_surface_redistribution.pdf")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260917)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "results" / "mission_comparison")
    args = parser.parse_args()
    traces: dict[str, dict[str, np.ndarray]] = {}
    metrics: list[MissionMetric] = []
    for architecture in ("thesis_grouped_acs", "distributed_elevon_qp"):
        metric, trace = simulate_architecture(architecture, args.seed)
        metrics.append(metric)
        traces[architecture] = trace
    save_outputs(args.output, metrics, traces)
    make_figures(args.output, traces)
    print(json.dumps({"metrics": [metric.__dict__ for metric in metrics], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
