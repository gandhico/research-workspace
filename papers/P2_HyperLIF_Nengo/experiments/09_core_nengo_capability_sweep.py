"""Core-Nengo capability sweep for HyperLIF readout variants.

This experiment is the next rung after the Phase-A integrator/oscillator smoke.
It tests whether HyperLIF and Adaptive HyperLIF can be placed in small canonical
Nengo/NEF applications using the practical readout threshold theta_event=0.95.

The custom neuron dynamics are unchanged. For speed, this sweep uses local
subclasses with an approximate build-time rate curve so that decoder solving
does not require settled simulation for every evaluation point. The parity
claim remains owned by experiment 07, where the exact shared stepping kernel is
tested directly.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from _common import CSV_DIR, ensure_results, write_log
from neurons.nengo_hyperlif import AdaptiveHyperLIFNengo, HyperLIFNengo
from simulation.metrics import rmse, write_rows

import nengo


DT = 0.001
WARMUP = 0.1


class FastReadoutHyperLIFNengo(HyperLIFNengo):
    """HyperLIF with approximate build-time rates for NEF smoke tests."""

    def rates(self, x, gain, bias):
        j = self.current(x, gain, bias)
        return np.maximum(0.0, self.rate_to_current * (j - self.event_threshold))

    def gain_bias(self, max_rates, intercepts):
        max_rates = np.asarray(np.atleast_1d(max_rates), dtype=float)
        intercepts = np.asarray(np.atleast_1d(intercepts), dtype=float)
        threshold_current = self.event_threshold - self.v_rest
        top_current = threshold_current + max_rates / self.rate_to_current
        gain = (threshold_current - top_current) / (intercepts - 1.0)
        bias = top_current - gain
        return gain, bias

    def max_rates_intercepts(self, gain, bias):
        gain = np.asarray(np.atleast_1d(gain), dtype=float)
        bias = np.asarray(np.atleast_1d(bias), dtype=float)
        threshold_current = self.event_threshold - self.v_rest
        intercepts = (threshold_current - bias) / gain
        top_current = gain + bias
        max_rates = np.maximum(0.0, top_current - threshold_current)
        return max_rates * self.rate_to_current, intercepts


class FastReadoutAdaptiveHyperLIFNengo(AdaptiveHyperLIFNengo):
    """Adaptive HyperLIF with approximate build-time rates for NEF smoke tests."""

    def rates(self, x, gain, bias):
        j = self.current(x, gain, bias)
        return np.maximum(0.0, self.rate_to_current * (j - self.event_threshold))

    def gain_bias(self, max_rates, intercepts):
        max_rates = np.asarray(np.atleast_1d(max_rates), dtype=float)
        intercepts = np.asarray(np.atleast_1d(intercepts), dtype=float)
        threshold_current = self.event_threshold - self.v_rest
        top_current = threshold_current + max_rates / self.rate_to_current
        gain = (threshold_current - top_current) / (intercepts - 1.0)
        bias = top_current - gain
        return gain, bias

    def max_rates_intercepts(self, gain, bias):
        gain = np.asarray(np.atleast_1d(gain), dtype=float)
        bias = np.asarray(np.atleast_1d(bias), dtype=float)
        threshold_current = self.event_threshold - self.v_rest
        intercepts = (threshold_current - bias) / gain
        top_current = gain + bias
        max_rates = np.maximum(0.0, top_current - threshold_current)
        return max_rates * self.rate_to_current, intercepts


@dataclass(frozen=True)
class Variant:
    name: str
    family: str
    event_threshold: float | str
    make: Callable[[], object]
    origin_policy: str = "baseline"
    v_reset: float | str = ""
    min_voltage: float | str = ""


def variants() -> list[Variant]:
    return [
        Variant("LIF", "lif", "native", lambda: nengo.LIF()),
        Variant(
            "HyperLIF_theta1.00",
            "hyperlif",
            1.00,
            lambda: FastReadoutHyperLIFNengo(event_threshold=1.00, rate_to_current=80.0),
        ),
        Variant(
            "HyperLIF_theta0.95",
            "hyperlif",
            0.95,
            lambda: FastReadoutHyperLIFNengo(event_threshold=0.95, rate_to_current=80.0),
        ),
        Variant(
            "HyperLIF_theta1.00_origin",
            "hyperlif",
            1.00,
            lambda: FastReadoutHyperLIFNengo(
                event_threshold=1.00,
                v_reset=-0.6,
                min_voltage=-2.0,
                rate_to_current=80.0,
            ),
            origin_policy="static_v_reset",
            v_reset=-0.6,
            min_voltage=-2.0,
        ),
        Variant(
            "HyperLIF_theta0.95_origin",
            "hyperlif",
            0.95,
            lambda: FastReadoutHyperLIFNengo(
                event_threshold=0.95,
                v_reset=-0.6,
                min_voltage=-2.0,
                rate_to_current=80.0,
            ),
            origin_policy="static_v_reset",
            v_reset=-0.6,
            min_voltage=-2.0,
        ),
        Variant(
            "Adaptive_theta1.00",
            "adaptive_hyperlif",
            1.00,
            lambda: FastReadoutAdaptiveHyperLIFNengo(event_threshold=1.00, rate_to_current=80.0),
        ),
        Variant(
            "Adaptive_theta0.95",
            "adaptive_hyperlif",
            0.95,
            lambda: FastReadoutAdaptiveHyperLIFNengo(event_threshold=0.95, rate_to_current=80.0),
        ),
        Variant(
            "Adaptive_theta1.00_origin",
            "adaptive_hyperlif",
            1.00,
            lambda: FastReadoutAdaptiveHyperLIFNengo(
                event_threshold=1.00,
                v_reset=-0.6,
                min_voltage=-2.0,
                rate_to_current=80.0,
            ),
            origin_policy="static_v_reset",
            v_reset=-0.6,
            min_voltage=-2.0,
        ),
        Variant(
            "Adaptive_theta0.95_origin",
            "adaptive_hyperlif",
            0.95,
            lambda: FastReadoutAdaptiveHyperLIFNengo(
                event_threshold=0.95,
                v_reset=-0.6,
                min_voltage=-2.0,
                rate_to_current=80.0,
            ),
            origin_policy="static_v_reset",
            v_reset=-0.6,
            min_voltage=-2.0,
        ),
    ]


def ensemble(n_neurons: int, dimensions: int, neuron_type, seed: int):
    return nengo.Ensemble(
        n_neurons,
        dimensions,
        neuron_type=neuron_type,
        seed=seed,
        max_rates=nengo.dists.Uniform(40.0, 120.0),
        intercepts=nengo.dists.Uniform(-0.5, 0.5),
    )


def _event_rate_hz(spikes: np.ndarray, runtime: float) -> float:
    return float(np.count_nonzero(spikes > 0.0) / (runtime * spikes.shape[1]))


def _target_values(sim, fn: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    return fn(sim.trange())


def communication_channel(variant: Variant) -> dict[str, object]:
    runtime = 0.7
    with nengo.Network(seed=10) as net:
        stim = nengo.Node(lambda t: np.sin(2.0 * np.pi * 2.0 * t))
        ens = ensemble(80, 1, variant.make(), seed=11)
        nengo.Connection(stim, ens, synapse=None)
        p_out = nengo.Probe(ens, synapse=0.02)
        p_spikes = nengo.Probe(ens.neurons)

    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(runtime)

    t = sim.trange()
    target = np.sin(2.0 * np.pi * 2.0 * t)
    mask = t >= WARMUP
    y = sim.data[p_out][:, 0]
    return {
        "app": "communication_channel",
        "metric_name": "decoded_rmse",
        "metric_value": rmse(y[mask], target[mask]),
        "event_rate_hz": _event_rate_hz(sim.data[p_spikes][mask], runtime - WARMUP),
    }


def function_square(variant: Variant) -> dict[str, object]:
    runtime = 0.7
    with nengo.Network(seed=20) as net:
        stim = nengo.Node(lambda t: 0.8 * np.sin(2.0 * np.pi * 1.5 * t))
        ens = ensemble(100, 1, variant.make(), seed=21)
        out = nengo.Node(size_in=1)
        nengo.Connection(stim, ens, synapse=None)
        nengo.Connection(ens, out, function=lambda x: x[0] ** 2, synapse=None)
        p_out = nengo.Probe(out, synapse=0.02)
        p_spikes = nengo.Probe(ens.neurons)

    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(runtime)

    t = sim.trange()
    x = 0.8 * np.sin(2.0 * np.pi * 1.5 * t)
    target = x**2
    mask = t >= WARMUP
    y = sim.data[p_out][:, 0]
    return {
        "app": "function_square",
        "metric_name": "function_rmse",
        "metric_value": rmse(y[mask], target[mask]),
        "event_rate_hz": _event_rate_hz(sim.data[p_spikes][mask], runtime - WARMUP),
    }


def transform_2d(variant: Variant) -> dict[str, object]:
    runtime = 0.7
    transform = np.array([[1.0, -0.5], [0.5, 1.0]])
    with nengo.Network(seed=30) as net:
        stim = nengo.Node(
            lambda t: [0.5 * np.sin(2.0 * np.pi * 1.5 * t), 0.5 * np.cos(2.0 * np.pi * 1.5 * t)]
        )
        pre = ensemble(100, 2, variant.make(), seed=31)
        post = ensemble(100, 2, variant.make(), seed=32)
        nengo.Connection(stim, pre, synapse=None)
        nengo.Connection(pre, post, transform=transform, synapse=0.02)
        p_out = nengo.Probe(post, synapse=0.02)
        p_spikes = nengo.Probe(post.neurons)

    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(runtime)

    t = sim.trange()
    x = np.column_stack([
        0.5 * np.sin(2.0 * np.pi * 1.5 * t),
        0.5 * np.cos(2.0 * np.pi * 1.5 * t),
    ])
    target = x @ transform.T
    mask = t >= WARMUP
    y = sim.data[p_out]
    return {
        "app": "transform_2d",
        "metric_name": "transform_rmse",
        "metric_value": rmse(y[mask], target[mask]),
        "event_rate_hz": _event_rate_hz(sim.data[p_spikes][mask], runtime - WARMUP),
    }


def working_memory(variant: Variant) -> dict[str, object]:
    runtime = 0.8
    tau = 0.1
    with nengo.Network(seed=40) as net:
        stim = nengo.Node(lambda t: 1.0 if 0.1 < t < 0.4 else 0.0)
        ens = ensemble(120, 1, variant.make(), seed=41)
        nengo.Connection(stim, ens, transform=tau, synapse=tau)
        nengo.Connection(ens, ens, synapse=tau)
        p_out = nengo.Probe(ens, synapse=0.05)
        p_spikes = nengo.Probe(ens.neurons)

    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(runtime)

    y = sim.data[p_out][:, 0]
    held = float(np.mean(y[-100:]))
    return {
        "app": "working_memory",
        "metric_name": "hold_error_to_0.3",
        "metric_value": abs(held - 0.3),
        "held_value": held,
        "event_rate_hz": _event_rate_hz(sim.data[p_spikes], runtime),
    }


def oscillator(variant: Variant) -> dict[str, object]:
    runtime = 1.2
    tau = 0.1
    omega = 2.0 * np.pi * 3.0
    with nengo.Network(seed=50) as net:
        kick = nengo.Node(lambda t: [1.0, 0.0] if t < 0.05 else [0.0, 0.0])
        ens = ensemble(160, 2, variant.make(), seed=51)
        nengo.Connection(kick, ens, synapse=None)
        nengo.Connection(ens, ens, synapse=tau, transform=[[1.0, -omega * tau], [omega * tau, 1.0]])
        p_out = nengo.Probe(ens[0], synapse=0.02)
        p_spikes = nengo.Probe(ens.neurons)

    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(runtime)

    t = sim.trange()
    mask = t >= 0.2
    y = sim.data[p_out][:, 0]
    amp = float(np.std(y[mask]))
    return {
        "app": "oscillator",
        "metric_name": "oscillator_std",
        "metric_value": amp,
        "oscillator_std": amp,
        "event_rate_hz": _event_rate_hz(sim.data[p_spikes][mask], runtime - 0.2),
    }


def pes_learning(variant: Variant) -> dict[str, object]:
    runtime = 1.0
    with nengo.Network(seed=60) as net:
        stim = nengo.Node(lambda t: np.sin(2.0 * np.pi * 1.0 * t))
        target = nengo.Node(lambda t: -np.sin(2.0 * np.pi * 1.0 * t))
        pre = ensemble(80, 1, variant.make(), seed=61)
        post = ensemble(80, 1, variant.make(), seed=62)
        error = nengo.Node(size_in=1)
        nengo.Connection(stim, pre, synapse=None)
        conn = nengo.Connection(
            pre,
            post,
            function=lambda x: [0.0],
            learning_rule_type=nengo.PES(learning_rate=1e-4),
        )
        nengo.Connection(post, error, synapse=0.02)
        nengo.Connection(target, error, transform=-1, synapse=None)
        nengo.Connection(error, conn.learning_rule)
        p_error = nengo.Probe(error, synapse=0.02)
        p_spikes = nengo.Probe(post.neurons)

    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(runtime)

    t = sim.trange()
    early = (t >= 0.2) & (t < 0.4)
    late = t >= 0.8
    err = sim.data[p_error][:, 0]
    early_rmse = float(np.sqrt(np.mean(err[early] ** 2)))
    late_rmse = float(np.sqrt(np.mean(err[late] ** 2)))
    return {
        "app": "pes_learning",
        "metric_name": "late_error_rmse",
        "metric_value": late_rmse,
        "early_error_rmse": early_rmse,
        "late_error_rmse": late_rmse,
        "event_rate_hz": _event_rate_hz(sim.data[p_spikes][late], float(np.sum(late)) * DT),
    }


APPS: list[Callable[[Variant], dict[str, object]]] = [
    communication_channel,
    function_square,
    transform_2d,
    working_memory,
    oscillator,
    pes_learning,
]


def run_app(app: Callable[[Variant], dict[str, object]], variant: Variant) -> dict[str, object]:
    try:
        row = app(variant)
        row["status"] = "ok"
    except Exception as exc:  # pragma: no cover - failures are part of the sweep output.
        row = {
            "app": app.__name__,
            "metric_name": "failure",
            "metric_value": np.nan,
            "event_rate_hz": np.nan,
            "status": f"FAIL {type(exc).__name__}: {exc}",
        }

    row["variant"] = variant.name
    row["family"] = variant.family
    row["event_threshold"] = variant.event_threshold
    row["origin_policy"] = variant.origin_policy
    row["v_reset"] = variant.v_reset
    row["min_voltage"] = variant.min_voltage
    return row


def main() -> None:
    ensure_results()
    rows: list[dict[str, object]] = []

    for variant in variants():
        for app in APPS:
            row = run_app(app, variant)
            rows.append(row)
            print(
                f"{row['app']:24s} {row['variant']:22s} "
                f"{row['status']:30s} {row['metric_name']}={row['metric_value']}"
            )

    preferred = [
        "app",
        "variant",
        "family",
        "event_threshold",
        "origin_policy",
        "v_reset",
        "min_voltage",
        "status",
        "metric_name",
        "metric_value",
        "event_rate_hz",
        "held_value",
        "oscillator_std",
        "early_error_rmse",
        "late_error_rmse",
    ]
    all_keys = preferred + sorted({key for row in rows for key in row if key not in preferred})
    normalized_rows = [{key: row.get(key, "") for key in all_keys} for row in rows]
    write_rows(CSV_DIR / "10_core_nengo_capability_sweep.csv", normalized_rows)

    lines = [
        "Core-Nengo capability sweep",
        "Approximate build-time rates are used for HyperLIF decoder solving; state dynamics are unchanged.",
        "",
    ]
    for row in rows:
        lines.append(
            f"{row['app']} | {row['variant']} | status={row['status']} | "
            f"{row['metric_name']}={row['metric_value']} | event_rate_hz={row['event_rate_hz']}"
        )
    write_log("10_core_nengo_capability_sweep.txt", "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
