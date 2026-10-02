"""Force-download a Tonic dataset to the local cache (run in background while we work).

    python scripts/download_dataset.py --dataset shd
Prints progress markers and a DONE line with sample counts when fully downloaded + extracted.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adhyperlif_triage.data.tonic_adapter import SPECS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="shd", choices=list(SPECS))
    ap.add_argument("--root", default=str(ROOT / "data" / "tonic"))
    args = ap.parse_args()

    import tonic.datasets as D

    spec = SPECS[args.dataset]
    cls = getattr(D, spec["cls"])
    root = str(Path(args.root) / args.dataset)
    t0 = time.time()
    print(f"[download] {args.dataset} -> {root}  (class {spec['cls']})", flush=True)

    counts = {}
    if spec["has_split"]:
        for split in (True, False):
            print(f"[download] building split train={split} ...", flush=True)
            ds = cls(save_to=root, train=split)
            _ = ds[0]  # force extraction / first read
            counts[f"train={split}"] = len(ds)
            print(f"[download]   split train={split}: {len(ds)} samples  ({time.time()-t0:.0f}s)", flush=True)
    else:
        ds = cls(save_to=root)
        _ = ds[0]
        counts["all"] = len(ds)
        print(f"[download]   all: {len(ds)} samples  ({time.time()-t0:.0f}s)", flush=True)

    print(f"[download] DONE {args.dataset} in {time.time()-t0:.0f}s  counts={counts}", flush=True)


if __name__ == "__main__":
    main()
