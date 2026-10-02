"""HyperLIF x Nengo capability matrix — easiest-but-complete example of each Nengo capability,
run with LIF vs calibrated HyperLIF (T023) vs Adaptive (T033), to evaluate where HyperLIF works,
where it is weak, and where Nengo itself limits a custom NeuronType.

Capabilities: NEF representation (comm channel, nonlinear function, 2D transform), NEF dynamics
(integrator, oscillator), working memory (gated), online learning (PES), cognition (binding via
circular convolution, action selection via basal ganglia + thalamus). Plus a backend-portability
probe (NengoDL / NengoOCL / NengoLoihi) — the real limitation story for a custom continuous neuron.

Run:  <05 venv python> experiments/13_hyperlif_nengo_capability_matrix.py
"""
from __future__ import annotations

import csv
import importlib
import sys
import traceback
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import nengo  # noqa: E402
from src.neurons.nengo_hyperlif import AdaptiveHyperLIFNengo, HyperLIFNengo  # noqa: E402


def neurons():
    return {
        "LIF": lambda: nengo.LIF(),
        "HyperLIF_T023": lambda: HyperLIFNengo(event_threshold=0.95, v_reset=-0.6, min_voltage=-2.0,
                                               rate_to_current=140.0, reset_gain=100.0),
        "Adaptive_T033": lambda: AdaptiveHyperLIFNengo(event_threshold=0.95, v_reset=-0.6,
                                                       min_voltage=-2.0, rate_to_current=140.0),
    }


def _rate(sim, probe, n):
    return float(np.mean(sim.data[probe])) if probe is not None else float("nan")


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


# ---------- capability apps: each returns (metric_name, error, rate_hz) ----------
def app_comm_channel(nt):
    with nengo.Network(seed=1) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: np.sin(2 * np.pi * t))
        a = nengo.Ensemble(200, 1); b = nengo.Ensemble(200, 1)
        nengo.Connection(stim, a); nengo.Connection(a, b, synapse=0.01)
        p_in = nengo.Probe(stim); p_b = nengo.Probe(b, synapse=0.03)
        p_s = nengo.Probe(a.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.0)
    m = sim.trange() > 0.3
    return "decode_rmse", rmse(sim.data[p_b][m], sim.data[p_in][m]), _rate(sim, p_s, 200)


def app_function_square(nt):
    with nengo.Network(seed=2) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: np.sin(2 * np.pi * t))
        a = nengo.Ensemble(200, 1); out = nengo.Node(size_in=1)
        nengo.Connection(stim, a); nengo.Connection(a, out, function=lambda x: x ** 2, synapse=0.01)
        p_in = nengo.Probe(stim); p_o = nengo.Probe(out, synapse=0.03); p_s = nengo.Probe(a.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.0)
    m = sim.trange() > 0.3
    return "function_rmse", rmse(sim.data[p_o][m], sim.data[p_in][m] ** 2), _rate(sim, p_s, 200)


def app_transform_2d(nt):
    T = np.array([[0.0, -1.0], [1.0, 0.0]])  # 90-deg rotation
    with nengo.Network(seed=3) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: [np.sin(2 * np.pi * t), np.cos(2 * np.pi * t)])
        a = nengo.Ensemble(300, 2); b = nengo.Ensemble(300, 2)
        nengo.Connection(stim, a); nengo.Connection(a, b, transform=T, synapse=0.01)
        p_in = nengo.Probe(stim); p_b = nengo.Probe(b, synapse=0.03); p_s = nengo.Probe(a.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.0)
    m = sim.trange() > 0.3
    ideal = (T @ sim.data[p_in][m].T).T
    return "transform_rmse", rmse(sim.data[p_b][m], ideal), _rate(sim, p_s, 300)


def app_integrator(nt):
    with nengo.Network(seed=4) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: 1.0 if t < 0.3 else 0.0)  # integrate to ~0.3
        a = nengo.Ensemble(300, 1)
        nengo.Connection(a, a, synapse=0.1)
        nengo.Connection(stim, a, transform=0.1, synapse=0.1)
        p = nengo.Probe(a, synapse=0.03); p_s = nengo.Probe(a.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.0)
    held = float(np.mean(sim.data[p][(sim.trange() > 0.7)]))
    return "hold_err_to_0.3", abs(held - 0.3), _rate(sim, p_s, 300)


def app_oscillator(nt):
    w = 2 * np.pi * 2.0
    with nengo.Network(seed=5) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        a = nengo.Ensemble(300, 2)
        nengo.Connection(a, a, transform=[[1.0, -w * 0.1], [w * 0.1, 1.0]], synapse=0.1)
        kick = nengo.Node(lambda t: [1.0, 0.0] if t < 0.1 else [0.0, 0.0])
        nengo.Connection(kick, a)
        p = nengo.Probe(a, synapse=0.02); p_s = nengo.Probe(a.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.5)
    amp = float(np.std(sim.data[p][(sim.trange() > 0.5)]))
    return "osc_amp_err", abs(amp - 0.5), _rate(sim, p_s, 300)


def app_working_memory(nt):
    with nengo.Network(seed=6) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        mem = nengo.networks.InputGatedMemory(300, 1)
        val = nengo.Node(lambda t: 0.6 if t < 0.3 else 0.0)
        gate = nengo.Node(lambda t: 0.0 if t < 0.3 else 1.0)  # store then hold
        nengo.Connection(val, mem.input); nengo.Connection(gate, mem.gate)
        p = nengo.Probe(mem.output, synapse=0.03)
        p_s = nengo.Probe(mem.mem.ea_ensembles[0].neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(1.0)
    held = float(np.mean(sim.data[p][(sim.trange() > 0.7)]))
    return "hold_err_to_0.6", abs(held - 0.6), _rate(sim, p_s, 300)


def app_pes_learning(nt):
    with nengo.Network(seed=7) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        stim = nengo.Node(lambda t: np.sin(2 * np.pi * t))
        pre = nengo.Ensemble(200, 1); post = nengo.Ensemble(200, 1); err = nengo.Ensemble(200, 1)
        nengo.Connection(stim, pre)
        conn = nengo.Connection(pre, post, function=lambda x: 0.0,
                                learning_rule_type=nengo.PES(learning_rate=2e-4))
        nengo.Connection(post, err); nengo.Connection(stim, err, transform=-1)
        nengo.Connection(err, conn.learning_rule)
        p_err = nengo.Probe(err, synapse=0.03); p_s = nengo.Probe(pre.neurons)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(4.0)
    late = float(np.sqrt(np.mean(sim.data[p_err][(sim.trange() > 3.0)] ** 2)))
    return "pes_late_rmse", late, _rate(sim, p_s, 200)


def _cconv_ideal(a, b):
    return np.fft.irfft(np.fft.rfft(a) * np.fft.rfft(b), n=len(a))


def app_binding(nt):
    D = 16
    rng = np.random.RandomState(11)
    va = rng.randn(D); va /= np.linalg.norm(va)
    vb = rng.randn(D); vb /= np.linalg.norm(vb)
    ideal = _cconv_ideal(va, vb)
    with nengo.Network(seed=8) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        cc = nengo.networks.CircularConvolution(80, D)
        na = nengo.Node(va); nb = nengo.Node(vb)
        nengo.Connection(na, cc.input_a); nengo.Connection(nb, cc.input_b)
        p = nengo.Probe(cc.output, synapse=0.03)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(0.6)
    out = np.mean(sim.data[p][(sim.trange() > 0.3)], axis=0)
    cos = float(np.dot(out, ideal) / (np.linalg.norm(out) * np.linalg.norm(ideal) + 1e-9))
    return "binding_1-cos", 1.0 - cos, float("nan")


def app_action_selection(nt):
    utils = np.array([0.8, 0.5, 0.3])  # action 0 should win
    with nengo.Network(seed=9) as net:
        net.config[nengo.Ensemble].neuron_type = nt
        bg = nengo.networks.BasalGanglia(3); thal = nengo.networks.Thalamus(3)
        stim = nengo.Node(utils)
        nengo.Connection(stim, bg.input); nengo.Connection(bg.output, thal.input)
        p = nengo.Probe(thal.output, synapse=0.03)
    with nengo.Simulator(net, progress_bar=False) as sim:
        sim.run(0.6)
    final = np.mean(sim.data[p][(sim.trange() > 0.4)], axis=0)
    selected = int(np.argmax(final))
    # error = 0 if picks action 0 with a clear margin, else 1
    err = 0.0 if (selected == 0 and final[0] - max(final[1], final[2]) > 0.3) else 1.0
    return "select_err(argmax)", err, float("nan")


APPS = {
    "comm_channel": app_comm_channel, "function_square": app_function_square,
    "transform_2d": app_transform_2d, "integrator": app_integrator, "oscillator": app_oscillator,
    "working_memory": app_working_memory, "pes_learning": app_pes_learning,
    "binding_cconv": app_binding, "action_selection": app_action_selection,
}
CAP = {"comm_channel": "NEF repr", "function_square": "NEF repr", "transform_2d": "NEF repr",
       "integrator": "NEF dyn", "oscillator": "NEF dyn", "working_memory": "memory",
       "pes_learning": "online learn", "binding_cconv": "cognition", "action_selection": "cognition"}


def main():
    rows = []
    print(f"{'capability':13s} {'app':17s} {'neuron':14s} {'metric':18s} {'error':>9s} {'rate_hz':>8s}  status")
    for app_name, fn in APPS.items():
        for nname, mk in neurons().items():
            try:
                metric, err, rate = fn(mk())
                status = "ok"
            except Exception as e:  # capability/neuron incompatibility is itself a finding
                metric, err, rate, status = "-", float("nan"), float("nan"), f"FAIL:{type(e).__name__}"
                traceback.print_exc(limit=1)
            rows.append({"capability": CAP[app_name], "app": app_name, "neuron": nname,
                         "metric": metric, "error": err, "rate_hz": rate, "status": status})
            print(f"{CAP[app_name]:13s} {app_name:17s} {nname:14s} {metric:18s} {err:9.3f} {rate:8.1f}  {status}")

    out = ROOT / "results" / "csv" / "13_hyperlif_nengo_capability_matrix.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"\nwrote {out}")

    # ---------- backend portability probe (the custom-NeuronType limitation) ----------
    print("\n=== backend portability probe (HyperLIF as a custom NeuronType) ===")
    for pkg in ["nengo_dl", "nengo_ocl", "nengo_loihi", "nengo_spa"]:
        try:
            importlib.import_module(pkg)
            print(f"  {pkg:12s} INSTALLED")
        except Exception as e:
            print(f"  {pkg:12s} not installed ({type(e).__name__})")
    print("  NengoCore (this run): HyperLIF runs as a full NeuronType (see matrix above).")


if __name__ == "__main__":
    main()
