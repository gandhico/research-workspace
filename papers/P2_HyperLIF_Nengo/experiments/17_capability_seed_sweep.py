"""Seed sweep for the calibrated HyperLIF Nengo capability suite.

This is a follow-up to experiment 13. It keeps the same six core Nengo apps
used for candidate selection, but repeats them over multiple network seeds for
the key candidates:

- T001: native LIF reference
- T002: uncalibrated HyperLIF theta=1.00
- T023: calibrated HyperLIF theta=0.95 + origin + rate_to_current=140
- T033: calibrated Adaptive HyperLIF theta=0.95 + origin + rate_to_current=140

Default run: 1 seed for an interactive smoke.
Preflight run: add --preflight for 3 seeds.
Paper-grade run: add --paper for 5 seeds.
"""

from __future__ import annotations

import argparse
import csv
import sys
import traceback
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import nengo  # noqa: E402
from src.neurons.nengo_hyperlif import AdaptiveHyperLIFNengo, HyperLIFNengo  # noqa: E402


def candidates():
    return {
        "T001_LIF": lambda: nengo.LIF(),
        "T002_HyperLIF_theta1": lambda: HyperLIFNengo(rate_to_current=80.0),
        "T023_HyperLIF_theta095_origin_r2c140": lambda: HyperLIFNengo(
            event_threshold=0.95,
            v_reset=-0.6,
            min_voltage=-2.0,
            rate_to_current=140.0,
            reset_gain=100.0,
        ),
        "T033_Adaptive_theta095_origin_r2c140": lambda: AdaptiveHyperLIFNengo(
            event_threshold=0.95,
            v_reset=-0.6,
            min_voltage=-2.0,
            rate_to_current=140.0,
        ),
    }


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def _rate(sim, probe):
    return float(np.mean(sim.data[probe])) if probe is not None else float("nan")


def app_comm_channel(nt, seed):
    with nengo.Network(seed=seed) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: np.sin(2 * np.pi * t))
        a = nengo.Ensemble(200, 1)
        b = nengo.Ensemble(200, 1)
        nengo.Connection(stim, a)
        nengo.Connection(a, b, synapse=0.01)
        p_in = nengo.Probe(stim)
        p_b = nengo.Probe(b, synapse=0.03)
        p_s = nengo.Probe(a.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.0)
    m = sim.trange() > 0.3
    return "decode_rmse", rmse(sim.data[p_b][m], sim.data[p_in][m]), _rate(sim, p_s)


def app_function_square(nt, seed):
    with nengo.Network(seed=seed) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: np.sin(2 * np.pi * t))
        a = nengo.Ensemble(200, 1)
        out = nengo.Node(size_in=1)
        nengo.Connection(stim, a)
        nengo.Connection(a, out, function=lambda x: x**2, synapse=0.01)
        p_in = nengo.Probe(stim)
        p_o = nengo.Probe(out, synapse=0.03)
        p_s = nengo.Probe(a.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.0)
    m = sim.trange() > 0.3
    return "function_rmse", rmse(sim.data[p_o][m], sim.data[p_in][m] ** 2), _rate(sim, p_s)


def app_transform_2d(nt, seed):
    transform = np.array([[0.0, -1.0], [1.0, 0.0]])
    with nengo.Network(seed=seed) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: [np.sin(2 * np.pi * t), np.cos(2 * np.pi * t)])
        a = nengo.Ensemble(300, 2)
        b = nengo.Ensemble(300, 2)
        nengo.Connection(stim, a)
        nengo.Connection(a, b, transform=transform, synapse=0.01)
        p_in = nengo.Probe(stim)
        p_b = nengo.Probe(b, synapse=0.03)
        p_s = nengo.Probe(a.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.0)
    m = sim.trange() > 0.3
    ideal = (transform @ sim.data[p_in][m].T).T
    return "transform_rmse", rmse(sim.data[p_b][m], ideal), _rate(sim, p_s)


def app_integrator(nt, seed):
    with nengo.Network(seed=seed) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: 1.0 if t < 0.3 else 0.0)
        a = nengo.Ensemble(300, 1)
        nengo.Connection(a, a, synapse=0.1)
        nengo.Connection(stim, a, transform=0.1, synapse=0.1)
        p = nengo.Probe(a, synapse=0.03)
        p_s = nengo.Probe(a.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.0)
    held = float(np.mean(sim.data[p][sim.trange() > 0.7]))
    return "hold_err_to_0.3", abs(held - 0.3), _rate(sim, p_s)


def app_oscillator(nt, seed):
    w = 2 * np.pi * 2.0
    with nengo.Network(seed=seed) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        a = nengo.Ensemble(300, 2)
        nengo.Connection(a, a, transform=[[1.0, -w * 0.1], [w * 0.1, 1.0]], synapse=0.1)
        kick = nengo.Node(lambda t: [1.0, 0.0] if t < 0.1 else [0.0, 0.0])
        nengo.Connection(kick, a)
        p = nengo.Probe(a, synapse=0.02)
        p_s = nengo.Probe(a.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.5)
    amp = float(np.std(sim.data[p][sim.trange() > 0.5]))
    return "osc_amp_err", abs(amp - 0.5), _rate(sim, p_s)


def app_working_memory(nt, seed):
    with nengo.Network(seed=seed) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        mem = nengo.networks.InputGatedMemory(300, 1)
        val = nengo.Node(lambda t: 0.6 if t < 0.3 else 0.0)
        gate = nengo.Node(lambda t: 0.0 if t < 0.3 else 1.0)
        nengo.Connection(val, mem.input)
        nengo.Connection(gate, mem.gate)
        p = nengo.Probe(mem.output, synapse=0.03)
        p_s = nengo.Probe(mem.mem.ea_ensembles[0].neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.0)
    held = float(np.mean(sim.data[p][sim.trange() > 0.7]))
    return "hold_err_to_0.6", abs(held - 0.6), _rate(sim, p_s)


def app_pes_learning(nt, seed):
    with nengo.Network(seed=seed) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: np.sin(2 * np.pi * t))
        pre = nengo.Ensemble(200, 1)
        post = nengo.Ensemble(200, 1)
        err = nengo.Ensemble(200, 1)
        nengo.Connection(stim, pre)
        conn = nengo.Connection(
            pre,
            post,
            function=lambda x: 0.0,
            learning_rule_type=nengo.PES(learning_rate=2e-4),
        )
        nengo.Connection(post, err)
        nengo.Connection(stim, err, transform=-1)
        nengo.Connection(err, conn.learning_rule)
        p_err = nengo.Probe(err, synapse=0.03)
        p_s = nengo.Probe(pre.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(4.0)
    late = float(np.sqrt(np.mean(sim.data[p_err][sim.trange() > 3.0] ** 2)))
    return "pes_late_rmse", late, _rate(sim, p_s)


APPS = {
    "comm_channel": ("NEF repr", app_comm_channel),
    "function_square": ("NEF repr", app_function_square),
    "transform_2d": ("NEF repr", app_transform_2d),
    "integrator": ("NEF dyn", app_integrator),
    "oscillator": ("NEF dyn", app_oscillator),
    "working_memory": ("memory", app_working_memory),
    "pes_learning": ("online learn", app_pes_learning),
}


def run(seeds):
    rows = []
    for seed in seeds:
        for app_index, (app_name, (capability, fn)) in enumerate(APPS.items(), start=1):
            app_seed = seed * 100 + app_index
            for candidate, make_neuron in candidates().items():
                try:
                    metric, error, rate = fn(make_neuron(), app_seed)
                    status = "ok"
                except Exception as exc:
                    traceback.print_exc(limit=1)
                    metric, error, rate = "-", float("nan"), float("nan")
                    status = f"FAIL:{type(exc).__name__}"
                row = {
                    "seed": seed,
                    "capability": capability,
                    "app": app_name,
                    "candidate": candidate,
                    "metric": metric,
                    "error": error,
                    "rate_hz": rate,
                    "status": status,
                }
                rows.append(row)
                print(
                    f"seed={seed:<2d} {app_name:16s} {candidate:38s} "
                    f"{metric:18s} error={error:8.4f} rate={rate:7.2f} {status}"
                )
    return rows


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["capability"], row["app"], row["candidate"], row["metric"])].append(row)

    summary = []
    for (capability, app, candidate, metric), group in sorted(grouped.items()):
        ok = [r for r in group if r["status"] == "ok" and np.isfinite(float(r["error"]))]
        errors = np.asarray([float(r["error"]) for r in ok], dtype=float)
        rates = np.asarray([float(r["rate_hz"]) for r in ok if np.isfinite(float(r["rate_hz"]))], dtype=float)
        summary.append(
            {
                "capability": capability,
                "app": app,
                "candidate": candidate,
                "metric": metric,
                "n_ok": len(ok),
                "n_fail": len(group) - len(ok),
                "error_mean": float(np.mean(errors)) if len(errors) else float("nan"),
                "error_std": float(np.std(errors, ddof=1)) if len(errors) > 1 else 0.0,
                "rate_mean_hz": float(np.mean(rates)) if len(rates) else float("nan"),
                "rate_std_hz": float(np.std(rates, ddof=1)) if len(rates) > 1 else 0.0,
            }
        )
    return summary


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true", help="Run 3 seeds instead of the default 1.")
    parser.add_argument("--paper", action="store_true", help="Run 5 seeds instead of the default 1.")
    parser.add_argument("--seeds", default=None, help="Comma-separated integer seeds, overriding defaults.")
    args = parser.parse_args()

    if args.seeds:
        seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    else:
        if args.paper:
            seeds = [1, 2, 3, 4, 5]
        elif args.preflight:
            seeds = [1, 2, 3]
        else:
            seeds = [1]

    rows = run(seeds)
    summary = summarize(rows)

    csv_dir = ROOT / "results" / "csv"
    raw_path = csv_dir / "17_capability_seed_sweep.csv"
    summary_path = csv_dir / "17_capability_seed_sweep_summary.csv"
    write_csv(raw_path, rows)
    write_csv(summary_path, summary)

    print(f"\nwrote {raw_path}")
    print(f"wrote {summary_path}")
    print("\nSummary:")
    for row in summary:
        print(
            f"{row['app']:16s} {row['candidate']:38s} "
            f"{row['metric']:18s} {row['error_mean']:.4f} +/- {row['error_std']:.4f} "
            f"rate={row['rate_mean_hz']:.1f} n={row['n_ok']} fail={row['n_fail']}"
        )


if __name__ == "__main__":
    main()
