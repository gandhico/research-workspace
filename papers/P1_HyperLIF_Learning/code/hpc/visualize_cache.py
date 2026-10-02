"""Visualize a portable {Xtr,ytr,Xte,yte}.pt cache — rasters, per-class signatures, activity.

Modality is inferred from the feature dim F (override with --P/--H/--W or --kind):
  audio/temporal (SHD/SSC, F=700): channel x time heatmaps + per-class mean "signatures"
  vision (N-MNIST/DVS/CIFAR, F=P*H*W): ON-OFF event images + a time-lapse strip

    pip install matplotlib                     # one-time (not pulled by setup_env)
    python hpc/visualize_cache.py --data-file $HLL_CACHE/shd_wide_T20.pt
    python hpc/visualize_cache.py --data-file $HLL_CACHE/nmnist_wide.pt   # auto P,H,W from F=2312
    # -> PNGs in $HLL_RESULTS/figs/<name>/  (open in OnDemand Files, or scp them down)

For audit HDF5 vision caches the flatten order may be (H,W,P) not (P,H,W); if images look
scrambled pass --order hwp.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np

KNOWN_PHW = {2312: (2, 34, 34), 2048: (2, 32, 32), 4608: (2, 48, 48), 1024: (1, 32, 32)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-file", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--split", default="tr", choices=["tr", "te"])
    p.add_argument("--n", type=int, default=8, help="example samples to montage")
    p.add_argument("--kind", default=None, choices=["audio", "vision"])
    p.add_argument("--P", type=int); p.add_argument("--H", type=int); p.add_argument("--W", type=int)
    p.add_argument("--order", default="phw", choices=["phw", "hwp"])
    a = p.parse_args()

    import torch
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = torch.load(a.data_file, weights_only=True)
    s = "tr" if a.split == "tr" else "te"
    X = d["X" + s].numpy().astype(np.float32)
    y = d["y" + s].numpy().astype(int)
    N, T, F = X.shape
    name = Path(a.data_file).stem

    P, H, W = a.P, a.H, a.W
    if P is None and F in KNOWN_PHW:
        P, H, W = KNOWN_PHW[F]
    kind = a.kind or ("vision" if (P and H and W) else "audio")
    out = Path(a.out or os.path.join(os.environ.get("HLL_RESULTS", "results"), "figs", name))
    out.mkdir(parents=True, exist_ok=True)
    classes = np.unique(y)

    # --- stats (both modalities) ---
    ev = X.reshape(N, -1).sum(1)
    tprof = X.sum((0, 2)) / N
    fig, ax = plt.subplots(1, 2, figsize=(9, 3))
    ax[0].plot(range(T), tprof, marker="o"); ax[0].set(title="mean events / time-bin", xlabel="t")
    ax[1].hist(ev, bins=30); ax[1].set(title="events / sample", xlabel="events")
    fig.suptitle(f"{name}   N={N}  T={T}  F={F}   kind={kind}")
    fig.tight_layout(); fig.savefig(out / "00_stats.png", dpi=110); plt.close(fig)

    def grid(nctx):
        cols = min(4, nctx); rows = int(np.ceil(nctx / cols))
        fig, ax = plt.subplots(rows, cols, figsize=(cols * 3, rows * 2.5))
        return fig, np.array(ax).reshape(-1)

    if kind == "audio":
        idx = np.linspace(0, N - 1, min(a.n, N)).astype(int)
        fig, ax = grid(len(idx))
        for k, i in enumerate(idx):
            ax[k].imshow(X[i].T, aspect="auto", origin="lower", cmap="magma")
            ax[k].set_title(f"y={int(y[i])}", fontsize=8); ax[k].set(xlabel="t", ylabel="ch")
        for k in range(len(idx), len(ax)): ax[k].axis("off")
        fig.suptitle(f"{name}: example rasters (channel x time)")
        fig.tight_layout(); fig.savefig(out / "01_examples.png", dpi=110); plt.close(fig)

        cl = classes[:min(len(classes), 20)]
        fig, ax = grid(len(cl))
        for k, c in enumerate(cl):
            ax[k].imshow(X[y == c].mean(0).T, aspect="auto", origin="lower", cmap="magma")
            ax[k].set_title(f"class {int(c)}", fontsize=8); ax[k].set(xlabel="t", ylabel="ch")
        for k in range(len(cl), len(ax)): ax[k].axis("off")
        fig.suptitle(f"{name}: per-class mean signature (channel x time)")
        fig.tight_layout(); fig.savefig(out / "02_class_means.png", dpi=110); plt.close(fig)
    else:
        def fr(i):
            f = X[i].reshape(T, H, W, P).transpose(0, 3, 1, 2) if a.order == "hwp" else X[i].reshape(T, P, H, W)
            return f

        def onoff(f):
            on = f[:, 0].sum(0); off = f[:, 1].sum(0) if P > 1 else np.zeros_like(on)
            return on - off

        idx = np.linspace(0, N - 1, min(a.n, N)).astype(int)
        fig, ax = grid(len(idx))
        for k, i in enumerate(idx):
            im = onoff(fr(i)); v = float(np.abs(im).max()) or 1.0
            ax[k].imshow(im, cmap="bwr", vmin=-v, vmax=v); ax[k].set_title(f"y={int(y[i])}", fontsize=8); ax[k].axis("off")
        for k in range(len(idx), len(ax)): ax[k].axis("off")
        fig.suptitle(f"{name}: ON-OFF event image (red=ON, blue=OFF, time-collapsed)")
        fig.tight_layout(); fig.savefig(out / "01_examples.png", dpi=110); plt.close(fig)

        i = idx[0]; f = fr(i)
        fig, ax = plt.subplots(1, T, figsize=(T * 1.1, 1.5))
        for t in range(T):
            im = f[t, 0] - (f[t, 1] if P > 1 else 0); v = float(np.abs(im).max()) or 1.0
            ax[t].imshow(im, cmap="bwr", vmin=-v, vmax=v); ax[t].axis("off"); ax[t].set_title(str(t), fontsize=6)
        fig.suptitle(f"{name}: time-lapse of one sample (y={int(y[i])})")
        fig.tight_layout(); fig.savefig(out / "03_timelapse.png", dpi=110); plt.close(fig)

    print(f"wrote figures to {out}")
    for f in sorted(out.glob("*.png")):
        print("  ", f.name)


if __name__ == "__main__":
    main()
