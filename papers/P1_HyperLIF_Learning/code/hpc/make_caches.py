"""Generate portable, uniform {Xtr,ytr,Xte,yte}.pt caches via Tonic, written to the scratch cache.

For datasets reachable via Tonic — SHD (upload-sized, also generated here), and on the cluster SSC
and CIFAR10-DVS (faster network, figshare reachable). 'wide' = ALL classes, 100/class. The cluster
then runs `train_hpc.py --data-file <file>` directly (no Tonic / figshare / 19 GB in the loop).

    # local (for the SHD upload):       python hpc/make_caches.py --datasets shd --mode wide --T 20
    # on the cluster:                    python hpc/make_caches.py --datasets ssc cifar10dvs --mode wide --T 20
    # output dir defaults to $HLL_CACHE (/fs1/scratch/gandhico/HyperLIF_Learning/cache)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for _cand in (os.environ.get("HLL_PKG"), str(ROOT / "src"), str(HERE)):
    if _cand and (Path(_cand) / "adhyperlif_triage").is_dir():
        sys.path.insert(0, _cand)
        break
else:
    sys.path.insert(0, str(ROOT / "src"))

import torch  # noqa: E402

from adhyperlif_triage.data import load_dataset  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--datasets", nargs="+", default=["shd"])
    p.add_argument("--mode", default="wide", choices=["tiny", "wide", "full"])  # full = all samples (SOTA runs)
    p.add_argument("--T", type=int, default=20)
    a = p.parse_args()
    out_dir = Path(os.environ.get("HLL_CACHE", "/fs1/scratch/gandhico/HyperLIF_Learning/cache"))
    out_dir.mkdir(parents=True, exist_ok=True)

    for ds in a.datasets:
        Xtr, ytr, Xte, yte, meta = load_dataset(ds, mode=a.mode, seed=0, T=a.T)
        out = out_dir / f"{ds}_{a.mode}_T{a.T}.pt"
        torch.save({"Xtr": Xtr, "ytr": ytr, "Xte": Xte, "yte": yte}, out)
        mb = out.stat().st_size / 1e6
        print(f"{out.name}: {mb:.0f} MB  | train {tuple(Xtr.shape)} test {tuple(Xte.shape)} "
              f"| {meta['n_classes']} classes  {'<500MB OK' if mb < 500 else 'OVER 500MB!'}")


if __name__ == "__main__":
    main()
