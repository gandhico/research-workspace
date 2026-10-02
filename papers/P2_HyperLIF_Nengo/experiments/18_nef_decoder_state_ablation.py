"""Experiment 18: NEF state-decoder ablation for calibrated HyperLIF neurons.

This is a bounded preflight that asks whether internal HyperLIF state variables
carry useful ensemble-level decoding information in Nengo. It compares the
normal decoded ensemble output with offline linear decoders trained from:

- filtered spikes,
- membrane voltage,
- reset gate, when available,
- combined state features.

The result is diagnostic evidence only until it is repeated at the desired
paper-grade seed/neuron budget.
"""

from __future__ import annotations

import argparse
from collections import defaultdict

import nengo
import numpy as np

from _common import CSV_DIR, ensure_results, write_log
from neurons.nengo_hyperlif import AdaptiveHyperLIFNengo, HyperLIFNengo
from simulation.metrics import rmse, write_rows


def candidates():
    return {
        "T001_LIF": lambda: nengo.LIF(),
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


def stimulus_value(t: float) -> float:
    value = 0.65 * np.sin(2 * np.pi * 1.0 * t) + 0.25 * np.sin(2 * np.pi * 3.0 * t + 0.2)
    return float(np.clip(value, -0.9, 0.9))


def lowpass_matrix(x: np.ndarray, dt: float, tau: float = 0.03) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x, dtype=float)
    decay = np.exp(-dt / tau)
    for k in range(1, x.shape[0]):
        y[k] = decay * y[k - 1] + (1.0 - decay) * x[k]
    return y


def fit_linear_decoder(
    features: np.ndarray,
    target: np.ndarray,
    train_fraction: float = 0.7,
    ridge: float = 1e-2,
    min_feature_scale: float = 0.05,
    clip_z: float = 20.0,
) -> tuple[float, float]:
    x = np.asarray(features, dtype=float)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    y = np.asarray(target, dtype=float).reshape(-1)

    n = min(x.shape[0], y.size)
    x = x[:n]
    y = y[:n]
    split = max(2, min(n - 1, int(train_fraction * n)))

    mean = np.mean(x[:split], axis=0, keepdims=True)
    scale = np.std(x[:split], axis=0, keepdims=True)
    scale = np.maximum(scale, min_feature_scale)
    x = np.clip((x - mean) / scale, -clip_z, clip_z)

    design = np.column_stack([x, np.ones(n)])
    xtx = design[:split].T @ design[:split]
    reg = ridge * np.eye(xtx.shape[0])
    reg[-1, -1] = 0.0
    rhs = design[:split].T @ y[:split]

    try:
        weights = np.linalg.solve(xtx + reg, rhs)
    except np.linalg.LinAlgError:
        weights, *_ = np.linalg.lstsq(design[:split], y[:split], rcond=None)

    pred = design @ weights
    return rmse(pred[:split], y[:split]), rmse(pred[split:], y[split:])


def probe_reset_gate(ensemble) -> nengo.Probe | None:
    neuron_type = ensemble.neuron_type
    probeable = getattr(neuron_type, "probeable", ())
    if "reset_gate" not in probeable:
        return None
    return nengo.Probe(ensemble.neurons, "reset_gate")


def run_one(
    candidate_name: str,
    make_neuron,
    seed: int,
    n_neurons: int,
    duration: float,
    dt: float,
    ridge: float,
    min_feature_scale: float,
    clip_z: float,
):
    with nengo.Network(seed=seed) as net:
        stim = nengo.Node(stimulus_value)
        ens = nengo.Ensemble(n_neurons, 1, neuron_type=make_neuron())
        nengo.Connection(stim, ens)

        p_stim = nengo.Probe(stim)
        p_decoded = nengo.Probe(ens, synapse=0.03)
        p_spikes = nengo.Probe(ens.neurons)
        p_voltage = nengo.Probe(ens.neurons, "voltage")
        p_gate = probe_reset_gate(ens)

    with nengo.Simulator(net, dt=dt, progress_bar=False) as sim:
        sim.run(duration)

    t = sim.trange()
    warm = t > max(0.2, 0.2 * duration)
    target = sim.data[p_stim][warm, 0]
    decoded = sim.data[p_decoded][warm, 0]
    spikes = sim.data[p_spikes][warm]
    voltage = sim.data[p_voltage][warm]
    filtered_spikes = lowpass_matrix(spikes, dt)
    gate = sim.data[p_gate][warm] if p_gate is not None else None

    feature_sets = {
        "nengo_decoded": decoded.reshape(-1, 1),
        "spikes_filtered": filtered_spikes,
        "voltage": voltage,
        "spikes_plus_voltage": np.column_stack([filtered_spikes, voltage]),
    }
    if gate is not None:
        feature_sets["reset_gate"] = gate
        feature_sets["voltage_plus_gate"] = np.column_stack([voltage, gate])
        feature_sets["combined_spikes_voltage_gate"] = np.column_stack([filtered_spikes, voltage, gate])

    rows = []
    rate_hz = float(np.mean(spikes))
    for feature_name, features in feature_sets.items():
        train_rmse, test_rmse = fit_linear_decoder(
            features,
            target,
            ridge=ridge,
            min_feature_scale=min_feature_scale,
            clip_z=clip_z,
        )
        rows.append(
            {
                "seed": seed,
                "candidate": candidate_name,
                "feature_set": feature_name,
                "target": "represented_x",
                "n_neurons": n_neurons,
                "duration_s": duration,
                "dt": dt,
                "ridge": ridge,
                "min_feature_scale": min_feature_scale,
                "clip_z": clip_z,
                "n_features": int(features.shape[1] if features.ndim > 1 else 1),
                "train_rmse": train_rmse,
                "test_rmse": test_rmse,
                "rate_hz": rate_hz,
                "status": "ok",
            }
        )
    return rows


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["candidate"], row["feature_set"], row["target"])].append(row)

    summary = []
    for (candidate, feature_set, target), group in sorted(grouped.items()):
        test = np.asarray([float(row["test_rmse"]) for row in group], dtype=float)
        train = np.asarray([float(row["train_rmse"]) for row in group], dtype=float)
        rates = np.asarray([float(row["rate_hz"]) for row in group], dtype=float)
        summary.append(
            {
                "candidate": candidate,
                "feature_set": feature_set,
                "target": target,
                "n": len(group),
                "train_rmse_mean": float(np.mean(train)),
                "train_rmse_std": float(np.std(train, ddof=1)) if len(train) > 1 else 0.0,
                "test_rmse_mean": float(np.mean(test)),
                "test_rmse_std": float(np.std(test, ddof=1)) if len(test) > 1 else 0.0,
                "rate_hz_mean": float(np.mean(rates)),
                "rate_hz_std": float(np.std(rates, ddof=1)) if len(rates) > 1 else 0.0,
                "n_fail": sum(1 for row in group if row["status"] != "ok"),
            }
        )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="0", help="Comma-separated seed list, e.g. 0,1,2.")
    parser.add_argument("--n-neurons", type=int, default=100)
    parser.add_argument("--duration", type=float, default=1.0)
    parser.add_argument("--dt", type=float, default=0.001)
    parser.add_argument("--ridge", type=float, default=1e-2)
    parser.add_argument("--min-feature-scale", type=float, default=0.05)
    parser.add_argument("--clip-z", type=float, default=20.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_results()
    seeds = [int(token.strip()) for token in args.seeds.split(",") if token.strip()]

    rows = []
    for seed in seeds:
        for candidate_name, make_neuron in candidates().items():
            print(f"seed={seed} candidate={candidate_name}")
            rows.extend(
                run_one(
                    candidate_name,
                    make_neuron,
                    seed=seed,
                    n_neurons=args.n_neurons,
                    duration=args.duration,
                    dt=args.dt,
                    ridge=args.ridge,
                    min_feature_scale=args.min_feature_scale,
                    clip_z=args.clip_z,
                )
            )

    summary = summarize(rows)
    write_rows(CSV_DIR / "18_nef_decoder_state_ablation.csv", rows)
    write_rows(CSV_DIR / "18_nef_decoder_state_ablation_summary.csv", summary)

    lines = [
        "Experiment 18 NEF decoder-state ablation",
        (
            f"seeds={seeds} n_neurons={args.n_neurons} duration={args.duration} "
            f"dt={args.dt} ridge={args.ridge} min_feature_scale={args.min_feature_scale} "
            f"clip_z={args.clip_z}"
        ),
        "summary:",
    ]
    for row in summary:
        lines.append(
            "{candidate:38s} {feature_set:28s} test={test_rmse_mean:.4f} "
            "+/- {test_rmse_std:.4f} rate={rate_hz_mean:.1f} n={n}".format(**row)
        )
    write_log("18_nef_decoder_state_ablation.txt", "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
