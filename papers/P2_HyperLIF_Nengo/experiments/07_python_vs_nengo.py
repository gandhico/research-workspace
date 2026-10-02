"""Experiment 07: standalone stable stepping vs Nengo custom-neuron stepping.

The Nengo ``NeuronType`` ports and the standalone ``method="stable"`` simulators
call the same numerical kernel (exact gate relaxation + exact linearized
membrane update). This experiment drives a single neuron with an identical
current in both implementations and confirms bit-for-bit agreement in voltage,
gate, and event timing across two protocols and both models. Generates the
trace CSV, the parity-metrics CSV, and the log used by Figure ``fig_parity`` and
Table ``tab_parity``.
"""

from __future__ import annotations

import numpy as np

from _common import CSV_DIR, ensure_results, write_log
from neurons import AdaptiveHyperLIFParams, HyperLIFParams
from neurons.adaptive_hyperlif import simulate_adaptive_hyperlif
from neurons.hyperlif import simulate_hyperlif
from neurons.nengo_hyperlif import AdaptiveHyperLIFNengo, HyperLIFNengo
from simulation.current_protocols import step_protocol, stress_protocol, time_axis
from simulation.metrics import rmse, write_csv, write_rows


def _current_lookup(current: np.ndarray, dt: float):
    def f(t):
        idx = int(np.floor((t - 0.5 * dt) / dt))
        idx = min(max(idx, 0), current.size - 1)
        return float(current[idx])

    return f


def _run_nengo(neuron_type, current: np.ndarray, dt: float, probe_dynamic_gain: bool = False):
    import nengo

    with nengo.Network(label="python_vs_nengo") as model:
        stim = nengo.Node(_current_lookup(current, dt), size_out=1)
        ens = nengo.Ensemble(
            n_neurons=1,
            dimensions=1,
            neuron_type=neuron_type,
            gain=np.ones(1),
            bias=np.zeros(1),
            encoders=np.ones((1, 1)),
        )
        nengo.Connection(stim, ens.neurons, transform=np.ones((1, 1)), synapse=None)
        p_out = nengo.Probe(ens.neurons)
        p_v = nengo.Probe(ens.neurons, "voltage")
        p_r = nengo.Probe(ens.neurons, "reset_gate")
        p_g = nengo.Probe(ens.neurons, "dynamic_gain") if probe_dynamic_gain else None

    with nengo.Simulator(model, dt=dt, progress_bar=False) as sim:
        sim.run(current.size * dt)

    result = {
        "events": sim.data[p_out][:, 0],
        "voltage": sim.data[p_v][:, 0],
        "reset_gate": sim.data[p_r][:, 0],
    }
    if p_g is not None:
        result["dynamic_gain"] = sim.data[p_g][:, 0]
    return result


def _hyper_nengo(p: HyperLIFParams) -> HyperLIFNengo:
    return HyperLIFNengo(
        tau=p.tau, v_rest=p.v_rest, v_thresh=p.v_thresh, v_reset=p.v_reset,
        alpha=p.alpha, reset_gain=p.reset_gain, tau_r=p.tau_r, gamma=p.gamma,
        amplitude=p.amplitude, min_voltage=p.min_voltage, event_threshold=p.v_thresh,
    )


def _adaptive_nengo(p: AdaptiveHyperLIFParams) -> AdaptiveHyperLIFNengo:
    return AdaptiveHyperLIFNengo(
        tau=p.tau, v_rest=p.v_rest, v_thresh=p.v_thresh, v_reset=p.v_reset,
        alpha=p.alpha, base_gain=p.base_gain, gain_scaling=p.gain_scaling, tau_r=p.tau_r,
        gamma=p.gamma, amplitude=p.amplitude, min_voltage=p.min_voltage, event_threshold=p.v_thresh,
    )


def _clip_common(*traces):
    n = min(tr["voltage"].size for tr in traces)
    for tr in traces:
        for k, v in list(tr.items()):
            tr[k] = v[:n]
    return n


def _parity_row(model: str, protocol: str, py: dict, ng: dict) -> dict:
    return {
        "model": model,
        "protocol": protocol,
        "voltage_rmse": rmse(py["voltage"], ng["voltage"]),
        "voltage_max_abs_diff": float(np.max(np.abs(py["voltage"] - ng["voltage"]))),
        "gate_rmse": rmse(py["reset_gate"], ng["reset_gate"]),
        "gate_max_abs_diff": float(np.max(np.abs(py["reset_gate"] - ng["reset_gate"]))),
        "event_mismatch_count": int(np.count_nonzero((py["events"] > 0) != (ng["events"] > 0))),
        "python_events": int(np.count_nonzero(py["events"] > 0)),
        "nengo_events": int(np.count_nonzero(ng["events"] > 0)),
    }


def main() -> None:
    ensure_results()

    dt = 1e-4
    hyper_p = HyperLIFParams()
    adapt_p = AdaptiveHyperLIFParams()

    protocols = {
        "stress": (time_axis(0.34, dt), stress_protocol),
        "step": (time_axis(0.25, dt), lambda tt: step_protocol(tt, high=1.4)),
    }

    parity_rows: list[dict] = []
    primary = {}

    for name, (t, build) in protocols.items():
        current = build(t)

        py_h = simulate_hyperlif(current, dt, hyper_p, method="stable")
        py_a = simulate_adaptive_hyperlif(current, dt, adapt_p, method="stable")
        ng_h = _run_nengo(_hyper_nengo(hyper_p), current, dt)
        ng_a = _run_nengo(_adaptive_nengo(adapt_p), current, dt, probe_dynamic_gain=True)

        n = _clip_common(py_h, py_a, ng_h, ng_a)
        t = t[:n]
        current = current[:n]

        parity_rows.append(_parity_row("HyperLIF", name, py_h, ng_h))
        parity_rows.append(_parity_row("Adaptive HyperLIF", name, py_a, ng_a))

        if name == "stress":
            primary = dict(
                t=t, current=current, py_h=py_h, py_a=py_a, ng_h=ng_h, ng_a=ng_a
            )

    write_csv(
        CSV_DIR / "07_python_vs_nengo.csv",
        {
            "t": primary["t"],
            "input_current": primary["current"],
            "python_hyper_voltage": primary["py_h"]["voltage"],
            "nengo_hyper_voltage": primary["ng_h"]["voltage"],
            "python_hyper_gate": primary["py_h"]["reset_gate"],
            "nengo_hyper_gate": primary["ng_h"]["reset_gate"],
            "python_hyper_events": primary["py_h"]["events"],
            "nengo_hyper_events": primary["ng_h"]["events"],
            "python_adaptive_voltage": primary["py_a"]["voltage"],
            "nengo_adaptive_voltage": primary["ng_a"]["voltage"],
            "python_adaptive_gate": primary["py_a"]["reset_gate"],
            "nengo_adaptive_gate": primary["ng_a"]["reset_gate"],
            "python_adaptive_dynamic_gain": primary["py_a"]["dynamic_gain"],
            "nengo_adaptive_dynamic_gain": primary["ng_a"]["dynamic_gain"],
            "python_adaptive_events": primary["py_a"]["events"],
            "nengo_adaptive_events": primary["ng_a"]["events"],
        },
    )

    write_rows(CSV_DIR / "07_parity_metrics.csv", parity_rows)
    write_log("07_python_vs_nengo.txt", "\n".join(str(row) for row in parity_rows) + "\n")


if __name__ == "__main__":
    main()
