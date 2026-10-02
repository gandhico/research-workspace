"""Supervised trainer: surrogate-gradient BPTT with clipping + task/dynamics metrics.

Gradient clipping is on by default (the stiff continuous-reset dynamics can produce large
gradients near a solution — the Gate-Eligibility finding). NaN/Inf losses are caught and flagged
rather than crashing, since "does this neuron train stably?" is itself triage signal.
"""

from __future__ import annotations

import math
import time

import torch
import torch.nn as nn

from ..metrics import dynamics_metrics, task_metrics


def _batches(n, bs, generator=None):
    perm = torch.randperm(n, generator=generator)
    for i in range(0, n, bs):
        yield perm[i:i + bs]


@torch.no_grad()
def _predict(model, X, bs=64):
    model.eval()
    logits = []
    for i in range(0, X.shape[0], bs):
        out, _ = model(X[i:i + bs])
        logits.append(out)
    return torch.cat(logits, 0)


def train_and_eval(
    model, data, *, n_classes, epochs=5, batch_size=16, lr=1e-3, clip_norm=1.0,
    seed=0, device="cpu",
):
    Xtr, ytr, Xte, yte = [d.to(device) for d in data]
    model.to(device)
    gen = torch.Generator().manual_seed(seed)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.Adam(params, lr=lr)
    lossfn = nn.CrossEntropyLoss()

    history, nan_batches, last_gnorm = [], 0, 0.0
    t0 = time.time()
    for epoch in range(epochs):
        model.train()
        ep_loss, n_seen = 0.0, 0
        for idx in _batches(Xtr.shape[0], batch_size, gen):
            logits, _ = model(Xtr[idx])
            loss = lossfn(logits, ytr[idx])
            if not torch.isfinite(loss):
                nan_batches += 1
                continue
            opt.zero_grad()
            loss.backward()
            gnorm = torch.nn.utils.clip_grad_norm_(params, clip_norm)
            last_gnorm = float(gnorm)
            opt.step()
            ep_loss += loss.item() * idx.numel()
            n_seen += idx.numel()
        tm = task_metrics(_predict(model, Xte), yte, n_classes)
        history.append({
            "epoch": epoch,
            "train_loss": ep_loss / max(n_seen, 1),
            "grad_norm": last_gnorm,
            **tm,
        })

    # dynamics on a held-out batch
    model.eval()
    with torch.no_grad():
        _, out = model(Xte[: min(batch_size, Xte.shape[0])])
    dm = dynamics_metrics(out, model.dt)
    final = dict(history[-1]) if history else {}
    summary = {
        **{f"final_{k}": v for k, v in final.items()},
        **dm,
        "nan_batches": nan_batches,
        "stable": nan_batches == 0 and dm.get("nan_count", 0) == 0,
        "wall_time_s": round(time.time() - t0, 2),
        "n_params": int(sum(p.numel() for p in params)),
    }
    return history, summary
