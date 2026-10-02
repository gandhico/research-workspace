"""B2: snnTorch training de-risk. Trains a small classifier with the snnTorch HyperLIF port vs the
standard ``snntorch.Leaky`` (LIF) baseline on the synthetic temporal task — confirms the snnTorch
neuron trains stably (no NaN), the full data->train->log pipeline works, and HyperLIF >= LIF (the
finding from the native harness). This is the 'make sure it works before HPC' step.

    python scripts/run_snntorch_smoke.py --seeds 0,1 --epochs 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import snntorch  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from snntorch import surrogate  # noqa: E402

from adhyperlif_triage.data import load_synthetic  # noqa: E402
from adhyperlif_triage.metrics import task_metrics  # noqa: E402
from adhyperlif_triage.neurons.snntorch_hyperlif import HyperLIFsnn  # noqa: E402
from adhyperlif_triage.utils import set_seed  # noqa: E402

DT = 1e-3


class Net(nn.Module):
    def __init__(self, n_in, n_hidden, n_classes, kind="hyperlif", input_scale=16.0):
        super().__init__()
        self.kind, self.n_hidden = kind, n_hidden
        self.fc1 = nn.Linear(n_in, n_hidden)
        nn.init.normal_(self.fc1.weight, std=input_scale / max(n_in, 1) ** 0.5)
        nn.init.zeros_(self.fc1.bias)
        if kind == "lif":
            self.neuron = snntorch.Leaky(beta=0.95, spike_grad=surrogate.fast_sigmoid(slope=25.0))
        else:
            self.neuron = HyperLIFsnn(model=("adaptive_hyperlif" if kind == "adaptive" else "hyperlif"), dt=DT)
        self.norm = nn.BatchNorm1d(n_hidden)
        self.fc2 = nn.Linear(n_hidden, n_classes)

    def forward(self, X):  # [B, T, F]
        cur = self.fc1(X)  # [B, T, H]
        acc = torch.zeros(X.shape[0], self.n_hidden, dtype=X.dtype, device=X.device)
        if self.kind == "lif":
            mem = self.neuron.init_leaky()
            for t in range(X.shape[1]):
                _, mem = self.neuron(cur[:, t], mem)
                acc = acc + mem
        else:
            v, r = self.neuron.init_hyperlif((X.shape[0], self.n_hidden), device=X.device, dtype=X.dtype)
            for t in range(X.shape[1]):
                _, v, r = self.neuron(cur[:, t], v, r)
                acc = acc + v
        return self.fc2(self.norm(acc / X.shape[1]))


def train_eval(kind, data, n_classes, epochs, seed):
    set_seed(seed)
    Xtr, ytr, Xte, yte, meta = data
    net = Net(meta["n_in"], 64, n_classes, kind=kind)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    lossfn = nn.CrossEntropyLoss()
    nan = False
    for _ in range(epochs):
        net.train()
        perm = torch.randperm(Xtr.shape[0])
        for i in range(0, Xtr.shape[0], 16):
            idx = perm[i:i + 16]
            logits = net(Xtr[idx])
            loss = lossfn(logits, ytr[idx])
            if not torch.isfinite(loss):
                nan = True
                continue
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step()
    net.eval()
    with torch.no_grad():
        acc = task_metrics(net(Xte), yte, n_classes)["accuracy"]
    return acc, nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0,1")
    ap.add_argument("--epochs", type=int, default=10)
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]

    print(f"snnTorch training de-risk (synthetic, {len(seeds)} seeds, {args.epochs} epochs)\n")
    print(f"{'neuron':22s} {'accuracy':>16s} {'stable':>8s}")
    for kind, label in [("lif", "snntorch.Leaky (LIF)"), ("hyperlif", "HyperLIFsnn"), ("adaptive", "HyperLIFsnn adaptive")]:
        accs, nans = [], []
        for s in seeds:
            data = load_synthetic("smoke", seed=s)
            a, nan = train_eval(kind, data, data[4]["n_classes"], args.epochs, s)
            accs.append(a); nans.append(nan)
        print(f"{label:22s} {np.mean(accs):.3f} ± {np.std(accs):.3f}   {'no' if not any(nans) else 'NaN!':>6s}")


if __name__ == "__main__":
    main()
