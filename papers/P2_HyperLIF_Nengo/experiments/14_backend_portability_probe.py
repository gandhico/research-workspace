"""Backend portability probe: build the SAME minimal ensemble with LIF vs calibrated HyperLIF and try
to run it on each Nengo backend (Core, Loihi emulator, OpenCL). Turns "custom neurons don't port" from
a claim into a result: LIF runs everywhere it can; HyperLIF is accepted only where a custom Python
NeuronType is executed (Core), and rejected by the hardware/kernel backends.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import nengo  # noqa: E402
from src.neurons.nengo_hyperlif import HyperLIFNengo  # noqa: E402


def build(nt):
    with nengo.Network(seed=0) as net:
        a = nengo.Ensemble(50, 1, neuron_type=nt)
        nengo.Connection(nengo.Node(0.5), a)
        nengo.Probe(a, synapse=0.01)
    return net


def make():
    return {"LIF": nengo.LIF(),
            "HyperLIF": HyperLIFNengo(event_threshold=0.95, v_reset=-0.6, min_voltage=-2.0,
                                      rate_to_current=140.0)}


def trial(simulator_ctx, nt):
    try:
        with simulator_ctx(build(nt)) as sim:
            sim.run(0.05)
        return "RUNS"
    except Exception as e:
        msg = str(e).replace("\n", " ")
        return f"REJECTED — {type(e).__name__}: {msg[:110]}"


def main():
    print(f"{'backend':16s} {'neuron':10s}  outcome")
    # --- NengoCore ---
    for nn, nt in make().items():
        print(f"{'NengoCore':16s} {nn:10s}  {trial(nengo.Simulator, nt)}")

    # --- NengoLoihi (pure-Python Loihi emulator; no hardware needed) ---
    try:
        import nengo_loihi
        for nn, nt in make().items():
            print(f"{'NengoLoihi':16s} {nn:10s}  {trial(nengo_loihi.Simulator, nt)}")
    except Exception as e:
        print(f"{'NengoLoihi':16s} {'-':10s}  import failed: {type(e).__name__}: {e}")

    # --- NengoOCL (GPU/OpenCL) ---
    try:
        import pyopencl as cl
        plats = cl.get_platforms()
        devs = [d for p in plats for d in p.get_devices()]
        print(f"{'OpenCL env':16s} {'-':10s}  platforms={len(plats)} devices={len(devs)}"
              + ("" if devs else "  (no OpenCL device on this machine)"))
        if devs:
            import nengo_ocl
            for nn, nt in make().items():
                print(f"{'NengoOCL':16s} {nn:10s}  {trial(nengo_ocl.Simulator, nt)}")
        else:
            print(f"{'NengoOCL':16s} {'-':10s}  cannot run — no OpenCL device (would still need a per-neuron kernel)")
    except Exception as e:
        print(f"{'NengoOCL':16s} {'-':10s}  probe failed: {type(e).__name__}: {str(e)[:100]}")

    # --- NengoDL (TensorFlow) ---
    try:
        import nengo_dl  # noqa: F401
        print(f"{'NengoDL':16s} {'-':10s}  installed (custom neuron needs a TF NeuronBuilder to train)")
    except Exception:
        print(f"{'NengoDL':16s} {'-':10s}  not installed (TensorFlow); custom neuron would need a TF builder")


if __name__ == "__main__":
    main()
