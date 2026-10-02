"""Experiment grid — DATA-FILE + ARCHITECTURE mode (HyperLIF_Learning).

Auto-discovers caches in $HLL_CACHE and sweeps  caches × archs × neurons × readouts × seeds.
`conv` is vision-only (skipped for audio caches — SHD/SSC). `ff` was covered by the base 450-run
sweep, so for the Phase-B §6.4 transfer study scope `ARCHS` to {conv, rsnn, delay} (edit below).

    python hpc/grid.py --list            # caches, per-cache archs, and job/bundle counts
    python hpc/grid.py --bundle-count    # N bundles = (cache × arch × neuron); size --array=0-(N-1)
    python hpc/grid.py --bundle-index i  # the 30 config lines for bundle i (readouts × seeds)
    python hpc/grid.py --index 0         # single-config args (used by preflight.sh)
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

_CLUSTER_CACHE = Path("/fs1/scratch/gandhico/HyperLIF_Learning/cache")
_LOCAL_CACHE = Path(__file__).resolve().parents[1] / "data" / "tonic" / "_cache"
DATA_DIR = Path(os.environ.get("HLL_CACHE", _CLUSTER_CACHE))
if "HLL_CACHE" not in os.environ and not DATA_DIR.exists() and _LOCAL_CACHE.exists():
    DATA_DIR = _LOCAL_CACHE

ARCHS = ["ff", "conv", "rsnn", "delay", "convres"]   # scope via sed for a targeted sweep, e.g. ["convres"]
NEURONS = ["lif", "plif", "alif", "hyperlif", "adaptive"]  # modern baselines + HyperLIF family
READOUTS = ["membrane", "spike_count", "gate", "hybrid_gr", "hybrid_vr", "hybrid_vr_conductance"]
SEEDS = [0, 1, 2, 3, 4]
COMMON = "--epochs 30 --hidden 256 --batch 64 --lr 1e-3"
AUDIO_HINTS = ("shd", "ssc")                 # conv (vision-only) is skipped for these caches


def data_files():
    return sorted(p.name for p in DATA_DIR.glob("*.pt"))


def _conv_ok(name):
    return not any(h in name.lower() for h in AUDIO_HINTS)


def archs_for(name):
    return [a for a in ARCHS if a not in ("conv", "convres") or _conv_ok(name)]


def grid():                                  # every (cache, arch, neuron, readout, seed)
    out = []
    for f in data_files():
        for a in archs_for(f):
            out += [(f, a, n, r, s) for n in NEURONS for r in READOUTS for s in SEEDS]
    return out


def config_for_index(i):
    f, a, n, r, s = grid()[i]
    return f"--data-file {DATA_DIR / f} --arch {a} --neuron {n} --readout {r} --seed {s} {COMMON}"


def bundles():                               # one SLURM job per (cache, arch, neuron)
    out = []
    for f in data_files():
        for a in archs_for(f):
            out += [(f, a, n) for n in NEURONS]
    return out


def bundle_configs(i):
    f, a, n = bundles()[i]
    # convres is the 14M ResNet-18-class net: at batch 64 x T=20 BPTT it OOMs a 16 GB GPU (worst on
    # 48x48 DVS). Use batch 16 for convres only; the light archs keep batch 64 (no OOM, 4x faster).
    cmn = COMMON.replace("--batch 64", "--batch 16") if a == "convres" else COMMON
    return [f"--data-file {DATA_DIR / f} --arch {a} --neuron {n} --readout {r} --seed {s} {cmn}"
            for r in READOUTS for s in SEEDS]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=int)
    p.add_argument("--count", action="store_true")
    p.add_argument("--bundle-index", type=int)
    p.add_argument("--bundle-count", action="store_true")
    p.add_argument("--list", action="store_true")
    a = p.parse_args()
    g, b = grid(), bundles()
    if a.list:
        print(f"cache dir: {DATA_DIR}")
        for f in data_files():
            print(f"  {f:24s} archs={archs_for(f)}")
        print(f"\narchs={ARCHS} x {len(NEURONS)} neurons x {len(READOUTS)} readouts x {len(SEEDS)} seeds")
        print(f"{len(b)} bundles (cache x arch x neuron), {len(READOUTS) * len(SEEDS)} configs each = {len(g)} configs")
    elif a.bundle_count:
        print(len(b))
    elif a.bundle_index is not None:
        print("\n".join(bundle_configs(a.bundle_index)))
    elif a.count:
        print(len(g))
    elif a.index is not None:
        print(config_for_index(a.index))
    else:
        print(f"{len(b)} bundles / {len(g)} configs. "
              f"Example bundle 0[0]: {bundle_configs(0)[0] if b else 'NO .pt CACHES in ' + str(DATA_DIR)}")


if __name__ == "__main__":
    main()
