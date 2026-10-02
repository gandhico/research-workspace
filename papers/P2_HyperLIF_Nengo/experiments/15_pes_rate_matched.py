"""Rate-matched PES: is HyperLIF's slow online learning a dynamics flaw or just a firing-rate effect?
Sweep HyperLIF firing rate via rate_to_current (learning_rate FIXED) and measure PES late error +
firing rate. If late error falls toward LIF as rate rises, the weakness is a tunable operating point,
not the neuron.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import nengo  # noqa: E402
from src.neurons.nengo_hyperlif import HyperLIFNengo  # noqa: E402

LR = 3e-4
T_RUN = 6.0


def pes_task(nt):
    with nengo.Network(seed=7) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: np.sin(2 * np.pi * t))
        pre = nengo.Ensemble(200, 1); post = nengo.Ensemble(200, 1); err = nengo.Ensemble(200, 1)
        nengo.Connection(stim, pre)
        conn = nengo.Connection(pre, post, function=lambda x: 0.0,
                                learning_rule_type=nengo.PES(learning_rate=LR))
        nengo.Connection(post, err); nengo.Connection(stim, err, transform=-1)
        nengo.Connection(err, conn.learning_rule)
        p_err = nengo.Probe(err, synapse=0.03); p_s = nengo.Probe(pre.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(T_RUN)
    tr = sim.trange()
    late = float(np.sqrt(np.mean(sim.data[p_err][tr > T_RUN - 1.0] ** 2)))
    rate = float(np.mean(sim.data[p_s]))
    return rate, late


def main():
    rows = []
    print(f"{'neuron':22s} {'rate_to_current':>16s} {'firing_hz':>10s} {'pes_late_rmse':>14s}")
    r, late = pes_task(nengo.LIF())
    rows.append(("LIF", "native", r, late))
    print(f"{'LIF (reference)':22s} {'native':>16s} {r:10.1f} {late:14.3f}")
    for r2c in [80, 140, 250, 400, 600, 900]:
        nt = HyperLIFNengo(event_threshold=0.95, v_reset=-0.6, min_voltage=-2.0, rate_to_current=float(r2c))
        r, late = pes_task(nt)
        rows.append((f"HyperLIF", r2c, r, late))
        print(f"{'HyperLIF theta0.95':22s} {r2c:16d} {r:10.1f} {late:14.3f}")

    out = ROOT / "results" / "csv" / "15_pes_rate_matched.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["neuron", "rate_to_current", "firing_hz", "pes_late_rmse"]); w.writerows(rows)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
