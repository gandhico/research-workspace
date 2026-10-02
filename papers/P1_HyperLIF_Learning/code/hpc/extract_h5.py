"""Extract a small, uniform {Xtr,ytr,Xte,yte}.pt from an EXISTING HDF5 dataset on the cluster
(your nmnist_34x34.h5 / dvs_gesture_*.h5). Loads ONLY the selected rows — never the full 19 GB.

Bare --h5 names resolve against $HLL_DATA (read-only sources); --out defaults to $HLL_CACHE.

    # 1. see what's inside (run this first, paste the output if extraction needs tuning):
    python hpc/extract_h5.py --h5 nmnist_34x34.h5 --inspect

    # 2. extract a balanced subset -> uniform cache the benchmark reads via --data-file:
    python hpc/extract_h5.py --h5 nmnist_34x34.h5 --out nmnist_wide.pt \
        --train-per-class 100 --test-per-class 40
    #    -> /fs1/scratch/gandhico/HyperLIF_Learning/cache/nmnist_wide.pt
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np


def walk(f):
    import h5py
    items = []
    f.visititems(lambda name, obj: items.append((name, tuple(obj.shape), str(obj.dtype)))
                 if isinstance(obj, h5py.Dataset) else None)
    return items


def guess_keys(items):
    data = sorted([it for it in items if len(it[1]) >= 2], key=lambda it: int(np.prod(it[1])), reverse=True)
    data_key = data[0][0] if data else None
    n = data[0][1][0] if data else None
    labels = [it for it in items if len(it[1]) == 1 and it[1][0] == n and ("int" in it[2] or "uint" in it[2])]
    return data_key, (labels[0][0] if labels else None)


def main():
    import h5py
    import torch

    p = argparse.ArgumentParser()
    p.add_argument("--h5", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--inspect", action="store_true")
    p.add_argument("--data-key", default=None)
    p.add_argument("--label-key", default=None)
    p.add_argument("--train-per-class", type=int, default=100)
    p.add_argument("--test-per-class", type=int, default=40)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()

    data_dir = os.environ.get("HLL_DATA", "/fs1/scratch/gandhico/HyperLIF_replication/data")
    cache_dir = os.environ.get("HLL_CACHE", "/fs1/scratch/gandhico/HyperLIF_Learning/cache")
    h5path = a.h5 if (os.path.isabs(a.h5) or os.path.exists(a.h5)) else os.path.join(data_dir, a.h5)

    with h5py.File(h5path, "r") as f:
        items = walk(f)
        if a.inspect:
            print(f"datasets in {h5path}:")
            for name, shape, dt in items:
                print(f"  {name:30s} shape={shape} dtype={dt}")
            dk, lk = guess_keys(items)
            names = {n.lower(): n for n, _, _ in items}
            te = names.get(dk.lower().replace("train", "test")) if (dk and "train" in dk.lower()) else None
            print(f"\nguessed  data='{dk}'  label='{lk}'  (override with --data-key/--label-key)")
            if te:
                print(f"native test split detected -> will use '{te}' for the held-out test set")
            return

        dk = a.data_key or guess_keys(items)[0]
        lk = a.label_key or guess_keys(items)[1]
        names = {n.lower(): n for n, _, _ in items}

        # Prefer the dataset's NATIVE held-out test split (X_train/X_test + y_train/y_test) over
        # carving test out of the train pool — that is the canonical, publishable split.
        te_dk = te_lk = None
        if "train" in dk.lower() and "train" in lk.lower():
            te_dk = names.get(dk.lower().replace("train", "test"))
            te_lk = names.get(lk.lower().replace("train", "test"))

        def balanced(dkey, lkey, per_class):
            """Up to per_class samples/class. h5py fancy-indexing needs ascending indices."""
            y = np.asarray(f[lkey][:]).astype(np.int64).ravel()
            rng = np.random.default_rng(a.seed)
            idx, ys = [], []
            for c in np.unique(y):
                ci = np.where(y == c)[0]
                rng.shuffle(ci)
                take = ci[:per_class].tolist()
                idx += take; ys += [int(c)] * len(take)
            order = np.argsort(idx)
            X = np.asarray(f[dkey][np.array(idx)[order]], dtype=np.float32)
            X = X.reshape(X.shape[0], X.shape[1], -1) if X.ndim >= 3 else X  # [N, T, F]
            return torch.from_numpy(X), torch.tensor(np.array(ys)[order], dtype=torch.long)

        if te_dk and te_lk:
            Xtr, ytr = balanced(dk, lk, a.train_per_class)
            Xte, yte = balanced(te_dk, te_lk, a.test_per_class)
            split = f"native (train<-{dk}, test<-{te_dk})"
        else:  # no native split: carve disjoint train/test per class out of the single set
            y_all = np.asarray(f[lk][:]).astype(np.int64).ravel()
            rng = np.random.default_rng(a.seed)
            tr_idx, te_idx, tr_y, te_y = [], [], [], []
            for c in np.unique(y_all):
                ci = np.where(y_all == c)[0]; rng.shuffle(ci)
                k1, k2 = a.train_per_class, a.train_per_class + a.test_per_class
                tr_idx += ci[:k1].tolist(); tr_y += [int(c)] * len(ci[:k1])
                te_idx += ci[k1:k2].tolist(); te_y += [int(c)] * len(ci[k1:k2])

            def load(idx, lbl):
                order = np.argsort(idx)
                X = np.asarray(f[dk][np.array(idx)[order]], dtype=np.float32)
                X = X.reshape(X.shape[0], X.shape[1], -1) if X.ndim >= 3 else X
                return torch.from_numpy(X), torch.tensor(np.array(lbl)[order], dtype=torch.long)
            Xtr, ytr = load(tr_idx, tr_y)
            Xte, yte = load(te_idx, te_y)
            split = f"carved from {dk}"

    out = Path(a.out) if (a.out and os.path.isabs(a.out)) else Path(cache_dir) / (a.out or (Path(h5path).stem + "_wide.pt"))
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"Xtr": Xtr, "ytr": ytr, "Xte": Xte, "yte": yte}, out)
    mb = out.stat().st_size / 1e6
    print(f"{out}: {mb:.0f} MB | train {tuple(Xtr.shape)} test {tuple(Xte.shape)} | "
          f"{int(max(ytr.max(), yte.max())) + 1} classes | split={split}")


if __name__ == "__main__":
    main()
