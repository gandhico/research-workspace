"""NengoDL probe: can a custom HyperLIF NeuronType be (a) built, (b) simulated, and (c) TRAINED in the
NengoDL (TensorFlow) backend? This is the one backend where a custom neuron is possible without hardware
(needs a TF NeuronBuilder / rate approximation). If HyperLIF trains here, it's the direct Nengo<->Paper-2
bridge; if not, the DL/training backend joins the portability wall.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import nengo  # noqa: E402
from src.neurons.nengo_hyperlif import HyperLIFNengo  # noqa: E402


def net_for(nt):
    with nengo.Network(seed=0) as net:
        inp = nengo.Node([0.0])
        ens = nengo.Ensemble(60, 1, neuron_type=nt)
        out = nengo.Node(size_in=1)
        nengo.Connection(inp, ens)
        c = nengo.Connection(ens, out, function=lambda x: x)
        p = nengo.Probe(out)
    return net, inp, p, c


def main():
    try:
        import nengo_dl
        import tensorflow as tf
        print(f"nengo_dl {nengo_dl.__version__} | tensorflow {tf.__version__} | nengo {nengo.__version__}")
    except Exception as e:
        print(f"NengoDL/TensorFlow import FAILED: {type(e).__name__}: {e}")
        return

    nt = HyperLIFNengo(event_threshold=0.95, v_reset=-0.6, min_voltage=-2.0, rate_to_current=140.0)

    # (a) build + (b) simulate under the TF backend
    try:
        net, inp, p, c = net_for(nt)
        with nengo_dl.Simulator(net, progress_bar=False) as sim:
            sim.run(0.05)
        print("(a) build + (b) simulate under NengoDL:  OK")
    except Exception as e:
        print(f"(a/b) build/simulate:  REJECTED — {type(e).__name__}: {str(e)[:160]}")
        return

    # (c) TRAIN: fit the ens->out decoders to a target with NengoDL's deep-learning trainer
    try:
        net, inp, p, c = net_for(nt)
        n_steps = 20
        x = np.abs(np.random.RandomState(0).randn(32, n_steps, 1)) * 0.5
        y = x * 2.0  # target: double the input (a learnable readout)
        with nengo_dl.Simulator(net, minibatch_size=8, progress_bar=False) as sim:
            sim.compile(optimizer=tf.optimizers.Adam(1e-2), loss={p: tf.losses.mse})
            h0 = sim.evaluate({inp: x}, {p: y}, verbose=0)["loss"]
            sim.fit({inp: x}, {p: y}, epochs=5, verbose=0)
            h1 = sim.evaluate({inp: x}, {p: y}, verbose=0)["loss"]
        drop = "LEARNS" if h1 < 0.9 * h0 else "no-learn"
        print(f"(c) TRAIN under NengoDL:  OK — loss {h0:.4f} -> {h1:.4f}  [{drop}]")
    except Exception as e:
        print(f"(c) train:  REJECTED — {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    main()
