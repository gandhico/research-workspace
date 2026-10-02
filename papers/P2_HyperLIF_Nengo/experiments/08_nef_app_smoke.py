"""Phase-A NEF app smoke for Paper 3.

This is the first rung of the Nengo full-capability program: place the custom
HyperLIF neuron types inside canonical NEF dynamical systems and record whether
they build, run, integrate/hold, and oscillate.
"""

from __future__ import annotations

import numpy as np

from _common import CSV_DIR, ensure_results, write_log
from neurons.nengo_hyperlif import AdaptiveHyperLIFNengo, HyperLIFNengo
from simulation.metrics import write_rows

import nengo


def integrator(neuron_type, tau: float = 0.1, runtime: float = 0.8) -> float:
    """Return the retained value after a short NEF integrator pulse."""

    with nengo.Network(seed=1) as net:
        stim = nengo.Node(lambda t: 1.0 if 0.1 < t < 0.4 else 0.0)
        ens = nengo.Ensemble(200, 1, neuron_type=neuron_type)
        nengo.Connection(stim, ens, transform=tau, synapse=tau)
        nengo.Connection(ens, ens, synapse=tau)
        probe = nengo.Probe(ens, synapse=0.05)

    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(runtime)

    trace = sim.data[probe][:, 0]
    return float(np.mean(trace[-100:]))


def oscillator(neuron_type, freq: float = 3.0, tau: float = 0.1, runtime: float = 1.5) -> float:
    """Return a post-settle oscillation-amplitude proxy."""

    omega = 2.0 * np.pi * freq
    with nengo.Network(seed=1) as net:
        kick = nengo.Node(lambda t: [1.0, 0.0] if t < 0.05 else [0.0, 0.0])
        ens = nengo.Ensemble(400, 2, neuron_type=neuron_type)
        nengo.Connection(kick, ens)
        nengo.Connection(
            ens,
            ens,
            synapse=tau,
            transform=[[1.0, -omega * tau], [omega * tau, 1.0]],
        )
        probe = nengo.Probe(ens[0], synapse=0.02)

    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(runtime)

    trace = sim.data[probe][:, 0]
    return float(np.std(trace[200:]))


def main() -> None:
    ensure_results()

    neurons = {
        "LIF": nengo.LIF(),
        "HyperLIF": HyperLIFNengo(),
        "Adaptive": AdaptiveHyperLIFNengo(),
    }
    rows: list[dict[str, object]] = []
    lines = ["neuron,integrator_held,oscillator_std,status"]

    for name, neuron_type in neurons.items():
        try:
            held = integrator(neuron_type)
            osc = oscillator(neuron_type)
            status = "ok" if abs(held) > 0.1 and osc > 0.05 else "WEAK"
            row = {
                "neuron": name,
                "integrator_held": held,
                "oscillator_std": osc,
                "integrator_pass": abs(held) > 0.1,
                "oscillator_pass": osc > 0.05,
                "status": status,
            }
        except Exception as exc:  # pragma: no cover - failure path is logged.
            row = {
                "neuron": name,
                "integrator_held": np.nan,
                "oscillator_std": np.nan,
                "integrator_pass": False,
                "oscillator_pass": False,
                "status": f"FAIL {type(exc).__name__}: {exc}",
            }

        rows.append(row)
        lines.append(
            f"{row['neuron']},{row['integrator_held']},{row['oscillator_std']},{row['status']}"
        )

    write_rows(CSV_DIR / "08_nef_app_smoke.csv", rows)
    write_log("08_nef_app_smoke.txt", "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
