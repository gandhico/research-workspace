"""Phase-A smoke gate: every (architecture x neuron x readout) must forward + backward finitely on
tiny fabricated data before anything goes near HPC. conv -> tiny vision (F=2*8*8); ff/rsnn -> tiny
audio (F=20). Mirrors the discipline that kept the 450-run array clean."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch
import torch.nn as nn

from arch import ARCHITECTURES, NEURONS, READOUTS, build_model


def run(arch, meta, neuron, readout, X, y):
    m = build_model(arch, meta, neuron=neuron, readout=readout, hidden=32)
    opt = torch.optim.Adam(m.parameters(), 1e-3)
    logits, aux = m(X)
    assert logits.shape == (X.shape[0], meta["n_classes"]), logits.shape
    loss = nn.CrossEntropyLoss()(logits, y)
    opt.zero_grad(); loss.backward(); opt.step()
    ok = bool(torch.isfinite(loss)) and bool(torch.isfinite(logits).all())
    return ok, float(loss.detach()), aux.get("events_per_sample", 0.0)


def main():
    torch.manual_seed(0)
    B, T = 4, 5
    Xv, yv = torch.rand(B, T, 128) * 6, torch.randint(0, 3, (B,))      # vision F=2*8*8 (count-like)
    metav = {"n_in": 128, "n_classes": 3, "T": T, "sensor": (2, 8, 8)}
    Xa, ya = torch.rand(B, T, 20) * 6, torch.randint(0, 3, (B,))       # audio F=20 (count-like)
    metaa = {"n_in": 20, "n_classes": 3, "T": T}

    npass = ntot = 0
    for arch in ARCHITECTURES:
        meta, X, y = (metav, Xv, yv) if arch in ("conv", "convres") else (metaa, Xa, ya)
        for neuron in NEURONS:
            for readout in READOUTS:
                ntot += 1
                try:
                    ok, loss, ev = run(arch, meta, neuron, readout, X, y)
                    npass += ok
                    print(f"{'ok' if ok else 'NONFINITE':10s} {arch:5s} {neuron:9s} {readout:22s} "
                          f"loss={loss:.3f} ev/samp={ev:.1f}")
                except Exception as e:
                    print(f"{'FAIL':10s} {arch:5s} {neuron:9s} {readout:22s} {type(e).__name__}: {e}")
    print(f"\n{npass}/{ntot} passed")


if __name__ == "__main__":
    main()
