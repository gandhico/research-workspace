"""Rebuild a P1 benchmark cache directly from its recovered source HDF5.

The original derived caches (`nmnist_wide.pt`, `dvsg32_wide.pt`, `dvsg48_wide.pt`) lived in HPC
scratch and are gone. What survives on the backup drive are the *source* audit HDF5 files plus the
two scripts that produced the caches from them: `extract_h5.py` (balanced per-class subset) and
`export_hdf5.py` (PyTorch cache to HDF5). This script performs both steps in one pass, writing the
HDF5 the Julia loader reads and skipping the PyTorch intermediate entirely.

The selection logic is copied from `extract_h5.py`'s native-split branch verbatim: one
`numpy.random.default_rng(seed)` shuffle per class, take the first `per_class`, then restore
ascending source-row order. NumPy guarantees PCG64 stream stability, so the same source file, seed,
and per-class counts reproduce the same subset.

This is a *reconstruction*, not a byte-identical recovery: no original `.pt` survives to diff
against. The parameters are corroborated by file size. With `--train-per-class 100
--test-per-class 40 --seed 0` the implied cache sizes match the recorded HPC manifest
(`nmnist_wide.pt` 371M, `dvsg32_wide.pt` 319M, `dvsg48_wide.pt` 718M) for all three datasets, so
those defaults are almost certainly the ones originally used. Every run writes a provenance JSON;
treat the output as a NEW dataset identity with a new hash, per REPRODUCIBILITY.md.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path

import h5py
import numpy as np


def sha256(path, chunk=8 << 20):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def balanced(handle, data_key, label_key, per_class, seed):
    """extract_h5.py's `balanced`: per-class shuffle, take per_class, ascending row order."""
    labels = np.asarray(handle[label_key][:]).astype(np.int64).ravel()
    rng = np.random.default_rng(seed)
    indices, chosen = [], []
    for klass in np.unique(labels):
        rows = np.where(labels == klass)[0]
        rng.shuffle(rows)
        take = rows[:per_class].tolist()
        indices += take
        chosen += [int(klass)] * len(take)
    order = np.argsort(indices)
    data = np.asarray(handle[data_key][np.array(indices)[order]], dtype=np.float32)
    if data.ndim >= 3:
        data = data.reshape(data.shape[0], data.shape[1], -1)
    return data, np.array(chosen, dtype=np.int64)[order]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="recovered audit HDF5")
    parser.add_argument("--out", required=True, help="cache HDF5 to write")
    parser.add_argument("--train-per-class", type=int, default=100)
    parser.add_argument("--test-per-class", type=int, default=40)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--skip-source-hash", action="store_true",
                        help="skip hashing the source (it can be tens of GB on a slow drive)")
    parser.add_argument("--expected-manifest-mib", type=float, default=None,
                        help="size recorded for the original .pt cache, for corroboration")
    arguments = parser.parse_args()

    source, out = Path(arguments.source), Path(arguments.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(source, "r") as handle:
        for key in ("X_train", "y_train", "X_test", "y_test"):
            if key not in handle:
                raise SystemExit(f"{source} has no dataset {key}; this tool assumes a native split")
        x_train, y_train = balanced(handle, "X_train", "y_train",
                                    arguments.train_per_class, arguments.seed)
        x_test, y_test = balanced(handle, "X_test", "y_test",
                                  arguments.test_per_class, arguments.seed)

    n_classes = int(max(int(y_train.max()), int(y_test.max()))) + 1
    # export_hdf5.py's checksum, kept so the Julia loader can be cross-checked against this run.
    checksum = float(x_train.sum())

    with h5py.File(out, "w") as handle:
        for key, array in (("X_train", x_train), ("y_train", y_train),
                           ("X_test", x_test), ("y_test", y_test)):
            handle.create_dataset(key, data=array, compression="gzip", compression_opts=4)
        handle.attrs.update(n_in=int(x_train.shape[-1]), T=int(x_train.shape[1]),
                            n_classes=n_classes, dataset=out.stem)

    # The original .pt held raw float32 tensors, so its size is the uncompressed footprint.
    raw_bytes = (x_train.size + x_test.size) * 4
    provenance = {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "reconstruction_from_recovered_source",
        "note": "NOT the original cache binary; no original .pt survives to diff against",
        "source": {
            "path": str(source),
            "sha256": None if arguments.skip_source_hash else sha256(source),
            "bytes": source.stat().st_size,
        },
        "selection": {
            "script_replicated": "extract_h5.py native-split branch",
            "train_per_class": arguments.train_per_class,
            "test_per_class": arguments.test_per_class,
            "seed": arguments.seed,
            "rng": "numpy.random.default_rng (PCG64)",
        },
        "shapes": {
            "train": list(x_train.shape), "test": list(x_test.shape),
            "n_classes": n_classes,
        },
        "checksums": {
            "sum_X_train": checksum,
            "implied_raw_pt_bytes": raw_bytes,
            "implied_raw_pt_mib": round(raw_bytes / 1048576, 1),
            "expected_manifest_mib": arguments.expected_manifest_mib,
            "manifest_size_agrees": (
                None if arguments.expected_manifest_mib is None
                else abs(raw_bytes / 1048576 - arguments.expected_manifest_mib) < 1.0
            ),
        },
        "output": {
            "path": str(out), "bytes": out.stat().st_size, "sha256": sha256(out),
            "format": "X_train/y_train/X_test/y_test, gzip-4, matches export_hdf5.py",
        },
    }
    sidecar = out.with_suffix(".provenance.json")
    sidecar.write_text(json.dumps(provenance, indent=2), encoding="utf-8")

    print(f"{out}  {out.stat().st_size/1e6:.1f} MB compressed")
    print(f"  train {x_train.shape}  test {x_test.shape}  classes {n_classes}")
    print(f"  sum(X_train) = {checksum:.6g}")
    print(f"  implied raw .pt size = {raw_bytes/1048576:.1f} MiB", end="")
    if arguments.expected_manifest_mib is not None:
        agree = provenance["checksums"]["manifest_size_agrees"]
        print(f"  vs manifest {arguments.expected_manifest_mib} MiB -> "
              f"{'AGREES' if agree else 'DISAGREES'}")
    else:
        print()
    print(f"  sha256 {provenance['output']['sha256']}")
    print(f"  provenance -> {sidecar}")


if __name__ == "__main__":
    main()
