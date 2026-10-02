"""Constant-drive trajectory audit for HyperLIF and Adaptive HyperLIF.

The simulation uses the same frozen-target/frozen-conductance split map as the
validated implementations.  It reports two deliberately separate observables:

  occupancy[k] = 1[v[k] >= event_threshold]
  crossing[k]  = 1[v[k-1] < event_threshold <= v[k]]

The first reproduces the historical snnTorch architecture diagnostic.  Only
the second is a discrete upward-crossing event count.  Neither is a measured
hardware-energy quantity.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from hyperlif_equilibrium_audit import Parameters


def simulate(currents: np.ndarray, adaptive: bool, p: Parameters, dt: float,
             duration: float, transient: float) -> tuple[list[dict], dict[float, dict]]:
    voltage = np.full_like(currents, p.v_rest, dtype=float)
    gate = np.zeros_like(currents, dtype=float)
    crossing_count = np.zeros_like(currents, dtype=int)
    occupancy_count = np.zeros_like(currents, dtype=int)
    samples = np.zeros_like(currents, dtype=int)
    sum_voltage = np.zeros_like(currents, dtype=float)
    sum_voltage2 = np.zeros_like(currents, dtype=float)
    min_voltage = np.full_like(currents, np.inf, dtype=float)
    max_voltage = np.full_like(currents, -np.inf, dtype=float)

    trace_currents = (1.5, 4.0)
    trace_indices = {value: int(np.argmin(np.abs(currents - value))) for value in trace_currents}
    traces = {value: {"time": [], "voltage": [], "gate": []} for value in trace_currents}

    gate_decay = np.exp(-dt / p.tau_r)
    total_steps = int(round(duration / dt))
    transient_steps = int(round(transient / dt))
    for step in range(total_steps):
        previous = voltage.copy()
        argument = np.clip(p.alpha * (voltage - p.theta + p.gamma * gate), -700, 700)
        target = 1.0 / (1.0 + np.exp(-argument))
        gate = np.clip(target + (gate - target) * gate_decay, 0.0, 1.0)
        scale = (p.base_gain + p.adaptive_gain * np.abs(currents)
                 if adaptive else np.full_like(currents, p.fixed_gain))
        conductance = scale * gate**2
        decay = np.exp(-(1.0 / p.tau + conductance) * dt)
        equilibrium = (
            p.v_rest / p.tau + currents / p.tau + conductance * p.v_reset
        ) / (1.0 / p.tau + conductance)
        voltage = voltage * decay + equilibrium * (1.0 - decay)

        time = (step + 1) * dt
        for value, index in trace_indices.items():
            if step % max(1, int(round(0.0005 / dt))) == 0:
                traces[value]["time"].append(time)
                traces[value]["voltage"].append(float(voltage[index]))
                traces[value]["gate"].append(float(gate[index]))

        if step >= transient_steps:
            crossings = (previous < p.event_threshold) & (voltage >= p.event_threshold)
            occupancy = voltage >= p.event_threshold
            crossing_count += crossings
            occupancy_count += occupancy
            samples += 1
            sum_voltage += voltage
            sum_voltage2 += voltage**2
            min_voltage = np.minimum(min_voltage, voltage)
            max_voltage = np.maximum(max_voltage, voltage)

    observation_time = duration - transient
    mean_voltage = sum_voltage / samples
    variance = np.maximum(0.0, sum_voltage2 / samples - mean_voltage**2)
    rows = []
    for index, current in enumerate(currents):
        rows.append({
            "family": "AdaptiveHyperLIF" if adaptive else "HyperLIF",
            "current": float(current),
            "crossing_rate_hz": float(crossing_count[index] / observation_time),
            "threshold_occupancy_fraction": float(occupancy_count[index] / samples[index]),
            "voltage_mean": float(mean_voltage[index]),
            "voltage_std": float(np.sqrt(variance[index])),
            "voltage_min": float(min_voltage[index]),
            "voltage_max": float(max_voltage[index]),
        })
    return rows, traces


def write_outputs(rows: list[dict], traces_by_family: dict[str, dict], p: Parameters,
                  dt: float, duration: float, transient: float, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with (output / "constant_drive.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "parameters": asdict(p),
        "dt": dt,
        "duration": duration,
        "transient": transient,
        "event_definition": "upward sampled crossing v[k-1] < theta_e <= v[k]",
        "occupancy_definition": "sampled threshold occupancy v[k] >= theta_e",
        "warning": "Occupancy, crossing count, and measured hardware energy are distinct quantities.",
    }
    for family in ("HyperLIF", "AdaptiveHyperLIF"):
        subset = [row for row in rows if row["family"] == family]
        active = [row for row in subset if row["crossing_rate_hz"] > 0]
        blocked = [row for row in subset
                   if row["threshold_occupancy_fraction"] > 0.99
                   and row["crossing_rate_hz"] == 0]
        summary[family] = {
            "sampled_periodic_crossing_current_range": (
                [min(row["current"] for row in active), max(row["current"] for row in active)]
                if active else None
            ),
            "sampled_high_occupancy_zero_crossing_current_range": (
                [min(row["current"] for row in blocked), max(row["current"] for row in blocked)]
                if blocked else None
            ),
            "peak_crossing_rate_hz": max(row["crossing_rate_hz"] for row in subset),
        }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    colors = {"HyperLIF": "#185FA5", "AdaptiveHyperLIF": "#1B9E77"}
    fig, axes = plt.subplots(3, 1, figsize=(9, 10), sharex=True)
    for family, color in colors.items():
        subset = [row for row in rows if row["family"] == family]
        axes[0].plot([row["current"] for row in subset],
                     [row["crossing_rate_hz"] for row in subset], color=color, label=family)
        axes[1].plot([row["current"] for row in subset],
                     [row["threshold_occupancy_fraction"] for row in subset], color=color)
        axes[2].plot([row["current"] for row in subset],
                     [row["voltage_std"] for row in subset], color=color)
    axes[0].set_ylabel("up-crossings / s")
    axes[1].set_ylabel("threshold occupancy")
    axes[2].set_ylabel("voltage std")
    axes[2].set_xlabel("constant input current J")
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(output / "constant_drive_sweep.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex="col")
    for column, current in enumerate((1.5, 4.0)):
        for family, color in colors.items():
            trace = traces_by_family[family][current]
            axes[0, column].plot(trace["time"], trace["voltage"], color=color, label=family)
            axes[1, column].plot(trace["time"], trace["gate"], color=color)
        axes[0, column].axhline(p.event_threshold, color="black", linestyle="--", linewidth=1)
        axes[0, column].set_title(f"J = {current:g}")
        axes[0, column].set_ylabel("voltage")
        axes[1, column].set_ylabel("gate")
        axes[1, column].set_xlabel("time (s)")
    axes[0, 0].legend()
    fig.tight_layout()
    fig.savefig(output / "constant_drive_traces.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"output": str(output), **summary}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--j-min", type=float, default=0.0)
    parser.add_argument("--j-max", type=float, default=6.0)
    parser.add_argument("--j-step", type=float, default=0.01)
    parser.add_argument("--dt", type=float, default=1e-4)
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--transient", type=float, default=1.0)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parent / "results" / "constant_drive")
    args = parser.parse_args()
    if not (0 < args.dt and 0 <= args.transient < args.duration):
        raise ValueError("require dt > 0 and 0 <= transient < duration")
    p = Parameters()
    currents = np.arange(args.j_min, args.j_max + 0.5 * args.j_step, args.j_step)
    rows: list[dict] = []
    traces_by_family = {}
    for family, adaptive in (("HyperLIF", False), ("AdaptiveHyperLIF", True)):
        family_rows, traces = simulate(
            currents, adaptive, p, args.dt, args.duration, args.transient
        )
        rows.extend(family_rows)
        traces_by_family[family] = traces
    write_outputs(rows, traces_by_family, p, args.dt, args.duration,
                  args.transient, args.output)


if __name__ == "__main__":
    main()
