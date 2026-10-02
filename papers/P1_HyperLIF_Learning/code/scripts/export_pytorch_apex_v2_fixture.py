"""Export a shared-weight PyTorch fixture for APEX-v2 value-level parity.

The structural trace comparison checks that PyTorch and Julia/APEX-v2 expose the
same architecture/readout surface. This fixture is the next gate: it records the
exact first batch, initialized weights, expected readout features, and logits
from the validated PyTorch architecture path so Julia can inject the same
weights and compare values directly.
"""

from __future__ import annotations

import argparse
import csv
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


DEFAULT_CACHE = Path(
    r"C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5"
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--cache", default=str(DEFAULT_CACHE))
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--hidden-dim", type=int, default=64)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--dt", type=float, default=1e-3)
    p.add_argument("--input-scale", type=float, default=16.0)
    p.add_argument("--architecture", default="recurrent")
    p.add_argument("--neuron", default="hyperlif")
    p.add_argument("--readout", default="hybrid_vr")
    p.add_argument("--delay-kernel-size", type=int, default=7)
    p.add_argument("--output", default=None)
    return p.parse_args()


def normalize_architecture(name: str) -> str:
    name = name.strip().lower()
    if name in {"ff", "feedforward"}:
        return "dense"
    if name == "rsnn":
        return "recurrent"
    return name


def load_first_batch_h5(path: Path, batch_size: int):
    with h5py.File(path, "r") as f:
        x = f["X_train"][:batch_size]  # [B,T,F] from Python
        y = f["y_train"][:batch_size]
        n_classes = int(max(f["y_train"][:].max(), f["y_test"][:].max())) + 1
    return (
        torch.as_tensor(x, dtype=torch.float32),
        torch.as_tensor(y, dtype=torch.long),
        n_classes,
    )


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
    norm = nn.BatchNorm1d(feature_dim, affine=True)
    head = nn.Linear(feature_dim, n_classes)
    return fc_in, fc_rec, delay, norm, head


@torch.no_grad()
def forward_with_features(x, n_classes: int, architecture: str, neuron_kind: str, readout: str,
                          n_hidden: int, dt: float, input_scale: float, delay_kernel_size: int):
    b, time_steps, n_in = x.shape
    fc_in, fc_rec, delay, norm, head = init_modules(
        n_in, n_hidden, n_classes, architecture, readout, input_scale, delay_kernel_size
    )
    neuron, gated = new_neuron(neuron_kind, dt=dt)

    z = torch.zeros(b, n_hidden, dtype=x.dtype)
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
        "fc_in": fc_in,
        "fc_rec": fc_rec,
        "delay": delay,
        "head": head,
        "features": features,
        "logits": logits,
        "events_per_sample": float(spk_sum.detach().sum(-1).mean().item()),
        "gate_mean": float(rbar.detach().mean().item()),
        "voltage_mean": float(vbar.detach().mean().item()),
        "conductance_mean": float(gbar.detach().mean().item()),
        "finite": finite,
    }


def write_matrix_for_julia(group, name: str, tensor: torch.Tensor):
    # HDF5.jl reads Python/HDF5 dimensions reversed; writing transpose restores
    # the original 2-D orientation when Julia reads the dataset.
    group.create_dataset(name, data=tensor.detach().cpu().numpy().astype("float32").T)


def main():
    args = parse_args()
    cache = Path(args.cache)
    if not cache.exists():
        raise FileNotFoundError(cache)

    architecture = normalize_architecture(args.architecture)
    if architecture not in {"dense", "recurrent", "delay"}:
        raise ValueError(f"unsupported architecture: {architecture}")
    if args.readout not in READOUT_MULT:
        raise ValueError(f"unsupported readout: {args.readout}")
    if args.neuron not in {"lif", "hyperlif", "adaptive"}:
        raise ValueError(f"unsupported neuron for APEX-v2 fixture: {args.neuron}")

    torch.manual_seed(args.seed)
    x, y, n_classes = load_first_batch_h5(cache, args.batch_size)
    result = forward_with_features(
        x, n_classes, architecture, args.neuron, args.readout,
        args.hidden_dim, args.dt, args.input_scale, args.delay_kernel_size,
    )
    if not result["finite"]:
        raise RuntimeError("PyTorch fixture produced non-finite features/logits")

    out_dir = ROOT / "results" / "apex_v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"pytorch_apex_v2_fixture_{architecture}_{args.neuron}_{args.readout}_seed{args.seed}"
    h5_path = Path(args.output) if args.output else out_dir / f"{stem}.h5"
    csv_path = h5_path.with_suffix(".csv")

    with h5py.File(h5_path, "w") as f:
        f.create_dataset("labels", data=y.detach().cpu().numpy().astype("int64"))
        f.create_dataset("expected_features_bt", data=result["features"].detach().cpu().numpy().astype("float32"))
        f.create_dataset("expected_logits_bc", data=result["logits"].detach().cpu().numpy().astype("float32"))
        write_matrix_for_julia(f, "fc_in_weight", result["fc_in"].weight)
        f.create_dataset("fc_in_bias", data=result["fc_in"].bias.detach().cpu().numpy().astype("float32"))
        if architecture == "recurrent":
            write_matrix_for_julia(f, "fc_rec_weight", result["fc_rec"].weight)
        if architecture == "delay":
            kernel = result["delay"].weight[:, 0, :]
            write_matrix_for_julia(f, "delay_kernel", kernel)
        write_matrix_for_julia(f, "head_weight", result["head"].weight)
        f.create_dataset("head_bias", data=result["head"].bias.detach().cpu().numpy().astype("float32"))

    row = {
        "fixture": str(h5_path),
        "cache": str(cache),
        "architecture": architecture,
        "neuron": args.neuron,
        "readout": args.readout,
        "seed": args.seed,
        "batch_size": int(x.shape[0]),
        "n_input": int(x.shape[2]),
        "hidden_dim": args.hidden_dim,
        "time_steps": int(x.shape[1]),
        "n_classes": n_classes,
        "feature_dim": int(result["features"].shape[1]),
        "events_per_sample": result["events_per_sample"],
        "gate_mean": result["gate_mean"],
        "voltage_mean": result["voltage_mean"],
        "conductance_mean": result["conductance_mean"],
        "finite": result["finite"],
    }
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)

    print(f"H5={h5_path}")
    print(f"CSV={csv_path}")
    print(
        f"PYTORCH_APEX_V2_FIXTURE architecture={architecture} neuron={args.neuron} "
        f"readout={args.readout} feature_dim={row['feature_dim']} "
        f"events={row['events_per_sample']:.6f} gate={row['gate_mean']:.6f}"
    )
    print("PYTORCH_APEX_V2_FIXTURE_OK")


if __name__ == "__main__":
    main()
