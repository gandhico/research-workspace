"""Experiment grid for the HPC SLURM array — DATA-FILE mode (HyperLIF_Learning).

Auto-discovers the portable caches in the scratch cache dir and sweeps them x neurons x readouts x
seeds. Drop a {Xtr,ytr,Xte,yte}.pt in the cache dir (uploaded, or produced by make_caches.py /
extract_h5.py) and it is automatically in the array — no editing needed.

    cache dir (auto-discovered, override with HLL_CACHE):
        /fs1/scratch/gandhico/HyperLIF_Learning/cache/

    python hpc/grid.py --list             # show discovered caches + total jobs
    python hpc/grid.py --count            # total jobs (use as --array=0-(N-1))
    python hpc/grid.py --index 7          # train_hpc.py args for job 7
"""

from __future__ import annotations

import argparse
import itertools
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("HLL_CACHE", "/fs1/scratch/gandhico/HyperLIF_Learning/cache"))

NEURONS = ["lif", "hyperlif", "adaptive"]
# Full readout sweep: voltage, event-count, gate-state, gate/conductance, voltage/gate,
# voltage/gate/conductance. (For LIF the gate/conductance channels are zero = honest baseline.)
READOUTS = ["membrane", "spike_count", "gate", "hybrid_gr", "hybrid_vr", "hybrid_vr_conductance"]
SEEDS = [0, 1, 2, 3, 4]
COMMON = "--epochs 30 --hidden 256 --batch 64 --lr 1e-3"   # --data-file ignores --mode/--T


def data_files():
    return sorted(p.name for p in DATA_DIR.glob("*.pt"))


def grid():
    return list(itertools.product(data_files(), NEURONS, READOUTS, SEEDS))


def config_for_index(i):
    f, neuron, readout, seed = grid()[i]
    return (f"--data-file {DATA_DIR / f} --neuron {neuron} --readout {readout} "
            f"--seed {seed} {COMMON}")


def bundles():
    """One SLURM job per (cache, neuron); each runs all readouts x seeds internally.
    Keeps the job count tiny (caches x neurons) to fit a small per-user submit cap."""
    return list(itertools.product(data_files(), NEURONS))


def bundle_configs(i):
    f, neuron = bundles()[i]
    return [f"--data-file {DATA_DIR / f} --neuron {neuron} --readout {r} --seed {s} {COMMON}"
            for r in READOUTS for s in SEEDS]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=int)
    p.add_argument("--count", action="store_true")
    p.add_argument("--bundle-index", type=int)
    p.add_argument("--bundle-count", action="store_true")
    p.add_argument("--list", action="store_true")
    a = p.parse_args()
    g = grid()
    if a.list:
        print(f"cache dir: {DATA_DIR}")
        for f in data_files():
            print(f"  {f}")
        print(f"\n{len(data_files())} caches x {len(NEURONS)} neurons x {len(READOUTS)} readouts "
              f"x {len(SEEDS)} seeds = {len(g)} configs")
        print(f"bundled: {len(bundles())} jobs (cache x neuron), {len(READOUTS) * len(SEEDS)} configs each")
    elif a.bundle_count:
        print(len(bundles()))
    elif a.bundle_index is not None:
        print("\n".join(bundle_configs(a.bundle_index)))
    elif a.count:
        print(len(g))
    elif a.index is not None:
        print(config_for_index(a.index))
    else:
        print(f"{len(g)} jobs. caches={data_files()}. "
              f"Example (0): {config_for_index(0) if g else 'NO .pt CACHES FOUND in ' + str(DATA_DIR)}")


if __name__ == "__main__":
    main()
