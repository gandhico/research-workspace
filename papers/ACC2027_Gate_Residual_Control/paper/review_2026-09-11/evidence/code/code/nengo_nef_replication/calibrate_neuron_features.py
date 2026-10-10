"""Calibrate conventional neuron feature scales at the declared J_max=2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import nengo
import numpy as np

from nengo_neuron_family import FAMILIES, neuron_type


def calibrate(family: str, dt: float, duration: float, tau: float) -> dict:
    if family == "cmg":
        return {"family": family, "feature_scale": 1.0, "observable": "gate-derived continuous activity"}
    native_current_scale = 10.0 if family == "izhikevich" else 1.0
    native_j = 2.0 * native_current_scale
    with nengo.Network(seed=1) as model:
        drive = nengo.Node(np.full(6, native_j))
        pop = nengo.Ensemble(
            6, 1, neuron_type=neuron_type(family), gain=np.ones(6),
            bias=np.zeros(6), encoders=np.ones((6, 1)),
        )
        nengo.Connection(drive, pop.neurons, synapse=None)
        probe = nengo.Probe(pop.neurons, synapse=nengo.Lowpass(tau))
    with nengo.Simulator(model, dt=dt, progress_bar=False) as sim:
        sim.run(duration)
    values = np.asarray(sim.data[probe])
    tail = values[int(0.5 * len(values)):]
    scale = max(float(np.mean(tail)), 1e-9)
    return {
        "family": family,
        "feature_scale": scale,
        "native_current_scale": native_current_scale,
        "observable": "5-ms low-pass spike trace" if family != "lifrate" else "5-ms low-pass rate output",
        "canonical_J_calibration": 2.0,
        "native_J_calibration": native_j,
        "tail_mean": float(np.mean(tail)),
        "tail_max": float(np.max(tail)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dt", type=float, default=5e-4)
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--feature-tau", type=float, default=0.005)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("feature_calibration.json"))
    args = parser.parse_args()
    payload = {
        "schema": 1,
        "method": "mean over second half of constant maximum canonical J=2 calibration",
        "dt_s": args.dt,
        "duration_s": args.duration,
        "feature_tau_s": args.feature_tau,
        "families": {family: calibrate(family, args.dt, args.duration, args.feature_tau) for family in FAMILIES},
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
