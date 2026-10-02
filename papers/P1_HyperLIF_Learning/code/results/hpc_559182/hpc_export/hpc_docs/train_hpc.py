"""HPC training entry point: train ONE (dataset, neuron, readout, seed) config and log metrics.
Called by the SLURM array (one task per config) or directly. GPU if available.

    python hpc/train_hpc.py --dataset nmnist --neuron hyperlif --readout hybrid_vr_conductance \
        --seed 0 --mode full --epochs 30 --batch 64 --T 20
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent      # .../hpc
ROOT = HERE.parent                           # project root (e.g. HyperLIF_Learning on the cluster)
# Find the adhyperlif_triage package: env override (HLL_PKG), local ../src, or vendored in hpc/.
for _cand in (os.environ.get("HLL_PKG"), str(ROOT / "src"), str(HERE)):
    if _cand and (Path(_cand) / "adhyperlif_triage").is_dir():
        sys.path.insert(0, _cand)
        break
else:
    sys.path.insert(0, str(ROOT / "src"))

import torch  # noqa: E402
import torch.nn as nn  # noqa: E402

from adhyperlif_triage.data import load_dataset  # noqa: E402
from adhyperlif_triage.metrics import task_metrics  # noqa: E402
from adhyperlif_triage.models.snntorch_net import SNNTorchNet  # noqa: E402
from adhyperlif_triage.utils import RunDir, append_registry, set_seed, write_summary_json  # noqa: E402


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default=None, help="Tonic dataset name (auto-download/process)")
    p.add_argument("--data-file", default=None,
                   help="OR load a uniform {Xtr,ytr,Xte,yte}.pt directly (skip Tonic/figshare/19GB)")
    p.add_argument("--neuron", default="hyperlif", choices=["lif", "hyperlif", "adaptive"])
    p.add_argument("--readout", default="hybrid_vr_conductance")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--mode", default="full", choices=["smoke", "tiny", "wide", "full"])
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--hidden", type=int, default=256)
    p.add_argument("--T", type=int, default=20)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--input-scale", type=float, default=16.0)
    p.add_argument("--clip", type=float, default=1.0)
    p.add_argument("--results-root", default=os.environ.get("HLL_RESULTS", "/fs1/scratch/gandhico/HyperLIF_Learning/results"))
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--skip-existing", action="store_true",
                   help="skip if a matching registry row already exists (makes bundles resumable)")
    return p.parse_args()


def main():
    a = parse()
    set_seed(a.seed)
    dev = torch.device(a.device)
    if a.skip_existing:  # resumable bundles: bail before the (expensive) cache load if already done
        ds_stem = Path(a.data_file).stem if a.data_file else f"{a.dataset}_{a.mode}"
        reg = Path(a.results_root) / "_registry.csv"
        key = f"{ds_stem},{a.neuron},{a.readout},{a.seed},"
        if reg.exists() and any(ln.startswith(key) for ln in reg.read_text(encoding="utf-8").splitlines()):
            print(f"SKIP {ds_stem}/{a.neuron}/{a.readout}/s{a.seed} (already in registry)", flush=True)
            return
    if a.data_file:  # uniform portable cache (the recommended HPC path)
        d = torch.load(a.data_file, weights_only=True)
        Xtr, ytr, Xte, yte = d["Xtr"], d["ytr"], d["Xte"], d["yte"]
        nC = int(max(int(ytr.max()), int(yte.max()))) + 1
        meta = {"n_in": Xtr.shape[-1], "T": Xtr.shape[1], "n_classes": nC,
                "dataset": Path(a.data_file).stem}
    else:
        Xtr, ytr, Xte, yte, meta = load_dataset(a.dataset, mode=a.mode, seed=a.seed, T=a.T)
        nC = meta["n_classes"]
    Xtr, ytr, Xte, yte = (t.to(dev) for t in (Xtr, ytr, Xte, yte))

    model = SNNTorchNet(meta["n_in"], a.hidden, nC, neuron=a.neuron, readout=a.readout,
                        dt=1e-3, input_scale=a.input_scale).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    lossfn = nn.CrossEntropyLoss()

    t0, nan_batches = time.time(), 0
    history = []
    for epoch in range(a.epochs):
        model.train()
        perm = torch.randperm(Xtr.shape[0], device=dev)
        for i in range(0, Xtr.shape[0], a.batch):
            idx = perm[i:i + a.batch]
            logits, _ = model(Xtr[idx])
            loss = lossfn(logits, ytr[idx])
            if not torch.isfinite(loss):
                nan_batches += 1
                continue
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), a.clip)
            opt.step()
        model.eval()
        with torch.no_grad():
            logits = torch.cat([model(Xte[j:j + a.batch])[0] for j in range(0, Xte.shape[0], a.batch)])
        tm = task_metrics(logits, yte, nC)
        history.append({"epoch": epoch, **tm})
        print(f"[{meta['dataset']}/{a.neuron}/{a.readout}/s{a.seed}] epoch {epoch} acc={tm['accuracy']:.4f}", flush=True)

    model.eval()
    with torch.no_grad():
        _, aux = model(Xte[: min(a.batch, Xte.shape[0])])
    final = history[-1]
    summary = {"config": vars(a), "meta": meta, **{f"final_{k}": v for k, v in final.items()},
               **aux, "nan_batches": nan_batches, "stable": nan_batches == 0,
               "wall_time_s": round(time.time() - t0, 1), "device": str(dev)}

    name = f"{a.neuron}_{a.readout}"
    prov = Path(a.data_file).name if a.data_file else f"tonic:{a.dataset}:{a.mode}"
    run = RunDir(a.results_root, meta["dataset"], name, a.seed, mode=a.mode)
    write_summary_json(run.file("summary.json"), summary)
    append_registry(a.results_root, {
        "dataset": meta["dataset"], "neuron": a.neuron, "readout": a.readout, "seed": a.seed,
        "accuracy": final["accuracy"], "macro_f1": final["macro_f1"],
        "events_per_sample": aux["events_per_sample"], "gate_mean": aux["gate_mean"],
        "stable": summary["stable"], "nan_batches": nan_batches,
        "n_classes": nC, "T": int(meta["T"]), "provenance": prov,
        "wall_s": summary["wall_time_s"],
    })
    print(f"DONE acc={final['accuracy']:.4f} macroF1={final['macro_f1']:.4f} stable={summary['stable']}", flush=True)


if __name__ == "__main__":
    main()
