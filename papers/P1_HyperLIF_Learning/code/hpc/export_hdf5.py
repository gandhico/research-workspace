"""Export a portable {Xtr,ytr,Xte,yte}.pt cache to HDF5 — the cross-framework contract for the
Julia/APEX arm of Paper 2. Same data, framework-agnostic.

    python hpc/export_hdf5.py --data-file $HLL_CACHE/shd_wide_T20.pt   # -> shd_wide_T20.h5
    python hpc/export_hdf5.py --all                                    # every .pt in $HLL_CACHE

HDF5 datasets are written [N, T, F] (h5py C-order). NOTE for the Julia side: HDF5.jl reads with
reversed dimension order (F, T, N) — permutedims if you need [N,T,F]. The printed sum(Xtr) is a
byte-exact checksum to cross-check against the Julia loader.
"""
from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path

import h5py
import numpy as np
import torch


def export(pt_path, out=None):
    d = torch.load(pt_path, weights_only=True)
    Xtr, ytr, Xte, yte = (d[k].numpy() for k in ("Xtr", "ytr", "Xte", "yte"))
    n_classes = int(max(int(ytr.max()), int(yte.max()))) + 1
    out = out or str(Path(pt_path).with_suffix(".h5"))
    # keys X_train/y_train/X_test/y_test — matches APEX's data.jl (load_dvs_h5) and the audit HDF5.
    with h5py.File(out, "w") as f:
        for k, arr in (("X_train", Xtr), ("y_train", ytr), ("X_test", Xte), ("y_test", yte)):
            f.create_dataset(k, data=arr, compression="gzip", compression_opts=4)
        f.attrs.update(n_in=int(Xtr.shape[-1]), T=int(Xtr.shape[1]),
                       n_classes=n_classes, dataset=Path(pt_path).stem)
    mb = os.path.getsize(out) / 1e6
    print(f"{out}: {mb:.0f} MB | train {tuple(Xtr.shape)} test {tuple(Xte.shape)} | "
          f"{n_classes} classes | sum(Xtr)={float(Xtr.sum()):.6g}")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-file")
    p.add_argument("--all", action="store_true")
    p.add_argument("--out", default=None)
    a = p.parse_args()
    cache = os.environ.get("HLL_CACHE", ".")
    if a.all:
        files = sorted(glob.glob(os.path.join(cache, "*.pt")))
        if not files:
            raise SystemExit(f"no .pt caches in {cache}")
        for fp in files:
            export(fp)
    elif a.data_file:
        export(a.data_file, a.out)
    else:
        raise SystemExit("give --data-file <cache.pt> or --all")


if __name__ == "__main__":
    main()
