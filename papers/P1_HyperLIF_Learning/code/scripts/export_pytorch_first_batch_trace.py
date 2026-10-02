"""Export PyTorch first-batch trace summaries for APEX-v2 comparison.

This script uses the validated PyTorch architecture logic from ``src/arch`` and
the same SHD-wide HDF5 cache used by Julia/APEX. It records feature dimensions
and state summaries, not weight-identical logits. Weight-identical trace parity
requires a later weight-transfer gate.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import h5py
import torch
import torch.nn as nn


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TRIAGE_SRC = ROOT.parent / "07_AdHyperLIF_Triage" / "src"
for path in (SRC, TRIAGE_SRC):
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arch.common import READOUT_MULT, assemble, conductance, init_state, new_neuron, step  # noqa: E402


DEFAULT_CACHE = Path(r"C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--cache", default=str(DEFAULT_CACHE))
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--hidden-dim", type=int, default=64)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--dt", type=float, default=1e-3)
    p.add_argument("--input-scale", type=float, default=16.0)
    p.add_argument("--architectures", default="dense,recurrent,delay")
    p.add_argument("--neurons", default="lif,hyperlif,adaptive")
    p.add_argument("--readouts", default="spike_count,membrane,gate,hybrid_gr,hybrid_vr,hybrid_vr_conductance")
    p.add_argument("--delay-kernel-size", type=int, default=7)
    p.add_argument("--output", default=None)
    p.add_argument("--device", default="cpu")
    return p.parse_args()


def normalize_architecture(name: str) -> str:
    name = name.strip().lower()
    if name in {"ff", "feedforward"}:
        return "dense"
    if name == "rsnn":
        return "recurrent"
    return name


def split_list(text: str):
    return [x.strip().lower() for x in text.split(",") if x.strip()]


def load_first_batch_h5(path: Path, batch_size: int, device: torch.device):
    with h5py.File(path, "r") as f:
        x = f["X_train"][:batch_size]  # [N,T,F], written by export_hdf5.py
        y = f["y_train"][:batch_size]
        n_classes = int(max(f["y_train"][:].max(), f["y_test"][:].max())) + 1
    xt = torch.as_tensor(x, dtype=torch.float32, device=device)
    yt = torch.as_tensor(y, dtype=torch.long, device=device)
    return xt, yt, n_classes


def init_modules(n_in: int, n_hidden: int, n_classes: int, architecture: str, readout: str,
                 input_scale: float, delay_kernel_size: int):
    fc_in = nn.Linear(n_in, n_hidden)
    nn.init.normal_(fc_in.weight, std=input_scale / max(n_in, 1) ** 0.5)
    nn.init.zeros_(fc_in.bias)

    fc_rec = None
    if architecture == "recurrent":
        fc_rec = nn.Linear(n_hidden, n_hidden, bias=False)
        nn.init.orthogonal_(fc_rec.weight, gain=0.2)

    delay = None
    if architecture == "delay":
        delay = nn.Conv1d(n_hidden, n_hidden, delay_kernel_size,
                          padding=delay_kernel_size // 2, groups=n_hidden, bias=False)
        nn.init.zeros_(delay.weight)
        with torch.no_grad():
            delay.weight[:, :, delay_kernel_size // 2] = 1.0

    feature_dim = n_hidden * READOUT_MULT[readout]
    head = nn.Linear(feature_dim, n_classes)
    norm = nn.BatchNorm1d(feature_dim, affine=True)
    return fc_in, fc_rec, delay, norm, head


@torch.no_grad()
def trace_forward(x, n_classes: int, architecture: str, neuron_kind: str, readout: str,
                  n_hidden: int, dt: float, input_scale: float, delay_kernel_size: int):
    b, time_steps, n_in = x.shape
    fc_in, fc_rec, delay, norm, head = init_modules(
        n_in, n_hidden, n_classes, architecture, readout, input_scale, delay_kernel_size
    )
    fc_in, norm, head = fc_in.to(x.device), norm.to(x.device), head.to(x.device)
    if fc_rec is not None:
        fc_rec = fc_rec.to(x.device)
    if delay is not None:
        delay = delay.to(x.device)

    neuron, gated = new_neuron(neuron_kind, dt=dt)
    neuron = neuron.to(x.device)

    z = torch.zeros(b, n_hidden, device=x.device, dtype=x.dtype)
    vbar, rbar, gbar, spk_sum = z.clone(), z.clone(), z.clone(), z.clone()
    prev_spk = z.clone()
    state = init_state(neuron, gated, (b, n_hidden), x.device, x.dtype)

    if architecture == "delay":
        cur_seq = fc_in(x).transpose(1, 2)
        cur_seq = delay(cur_seq).transpose(1, 2)
    else:
        cur_seq = None

    for t in range(time_steps):
        if architecture == "delay":
            cur = cur_seq[:, t]
        else:
            cur = fc_in(x[:, t])
            if architecture == "recurrent":
                cur = cur + fc_rec(prev_spk)

        spk, state, (v, r), _ = step(neuron, gated, cur, state)
        prev_spk = spk
        vbar = vbar + v
        spk_sum = spk_sum + spk
        if gated:
            rbar = rbar + r
            gbar = gbar + torch.tanh(conductance(neuron, r, cur) / 20.0)

    vbar = vbar / time_steps
    rbar = rbar / time_steps
    gbar = gbar / time_steps
    features = assemble(readout, vbar, rbar, gbar, spk_sum)
    logits = head(norm(features))
    finite = bool(torch.isfinite(features).all().item() and torch.isfinite(logits).all().item())

    return {
        "framework": "pytorch",
        "dataset": "shd_wide_T20",
        "architecture": architecture,
        "neuron": neuron_kind,
        "readout": readout,
        "feature_dim": int(features.shape[1]),
        "logit_rows": int(logits.shape[1]),
        "logit_cols": int(logits.shape[0]),
        "events_per_sample": float(spk_sum.detach().sum(-1).mean().item()),
        "gate_mean": float(rbar.detach().mean().item()),
        "voltage_mean": float(vbar.detach().mean().item()),
        "conductance_mean": float(gbar.detach().mean().item()),
        "finite": finite,
    }


def main():
    args = parse_args()
    cache = Path(args.cache)
    if not cache.exists():
        raise FileNotFoundError(cache)

    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but torch.cuda.is_available() is false")

    torch.manual_seed(args.seed)
    x, _y, n_classes = load_first_batch_h5(cache, args.batch_size, device)
    architectures = [normalize_architecture(a) for a in split_list(args.architectures)]
    neurons = split_list(args.neurons)
    readouts = split_list(args.readouts)

    out_dir = ROOT / "results" / "apex_v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = Path(args.output) if args.output else out_dir / "pytorch_first_batch_trace.csv"

    rows = []
    for architecture in architectures:
        if architecture not in {"dense", "recurrent", "delay"}:
            raise ValueError(f"unsupported architecture: {architecture}")
        for neuron_kind in neurons:
            if neuron_kind not in {"lif", "hyperlif", "adaptive"}:
                raise ValueError(f"unsupported neuron: {neuron_kind}")
            for readout in readouts:
                if readout not in READOUT_MULT:
                    raise ValueError(f"unsupported readout: {readout}")
                torch.manual_seed(args.seed)
                row = trace_forward(
                    x, n_classes, architecture, neuron_kind, readout,
                    args.hidden_dim, args.dt, args.input_scale, args.delay_kernel_size,
                )
                row.update({
                    "seed": args.seed,
                    "batch_size": int(x.shape[0]),
                    "n_input": int(x.shape[2]),
                    "hidden_dim": args.hidden_dim,
                    "time_steps": int(x.shape[1]),
                    "provenance": str(cache),
                })
                rows.append(row)
                print(
                    f"arch={architecture} neuron={neuron_kind} readout={readout} "
                    f"feature_dim={row['feature_dim']} finite={row['finite']} "
                    f"events={row['events_per_sample']:.3f} gate={row['gate_mean']:.5f}",
                    flush=True,
                )

    fieldnames = [
        "framework", "dataset", "architecture", "neuron", "readout", "seed",
        "batch_size", "n_input", "hidden_dim", "time_steps", "feature_dim",
        "logit_rows", "logit_cols", "events_per_sample", "gate_mean",
        "voltage_mean", "conductance_mean", "finite", "provenance",
    ]
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    failures = sum(1 for r in rows if not r["finite"])
    print(f"CSV={output}")
    print(f"PYTORCH_FIRST_BATCH_TRACE total={len(rows)} failures={failures}")
    if failures:
        raise SystemExit(1)
    print("PYTORCH_FIRST_BATCH_TRACE_OK")


if __name__ == "__main__":
    main()

