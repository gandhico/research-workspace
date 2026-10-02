"""Task metrics (accuracy, balanced accuracy, macro-F1) — dependency-free."""

from __future__ import annotations

import numpy as np


def _np(x):
    try:
        import torch

        if isinstance(x, torch.Tensor):
            return x.detach().cpu().numpy()
    except ImportError:
        pass
    return np.asarray(x)


def task_metrics(logits_or_preds, labels, n_classes: int) -> dict[str, float]:
    p = _np(logits_or_preds)
    y = _np(labels).astype(int).ravel()
    preds = p.argmax(axis=-1).astype(int).ravel() if p.ndim > 1 else p.astype(int).ravel()

    acc = float((preds == y).mean()) if y.size else 0.0

    # per-class recall (balanced accuracy) and macro-F1
    recalls, f1s = [], []
    for c in range(n_classes):
        tp = int(((preds == c) & (y == c)).sum())
        fp = int(((preds == c) & (y != c)).sum())
        fn = int(((preds != c) & (y == c)).sum())
        support = int((y == c).sum())
        if support > 0:
            recalls.append(tp / support)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if (prec + rec) else 0.0)

    return {
        "accuracy": acc,
        "balanced_accuracy": float(np.mean(recalls)) if recalls else 0.0,
        "macro_f1": float(np.mean(f1s)) if f1s else 0.0,
    }
