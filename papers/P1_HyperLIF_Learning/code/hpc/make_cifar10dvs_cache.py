"""Build cifar10dvs_wide_T20.pt from the ORIGINAL figshare CIFAR10-DVS (AEDAT 2.0 / DVS128).

Tonic's CIFAR10DVS reader only accepts .aedat4; the figshare article (4724671) ships jAER .aedat
(AEDAT 2.0, 8-byte events). This reads those directly, then bins identically to the other caches
(ToFrame, spatial pool 4 -> 32x32x2 = 2048 features, T time-bins) so it drops into the same grid.

    # 1. validate the decoder on ONE file (want x,y in [0,127], p in {0,1}, many events):
    python hpc/make_cifar10dvs_cache.py --inspect path/to/cifar10_airplane_0.aedat

    # 2. full build straight from the downloaded zip (auto-extracts ~8 GB into --work):
    python hpc/make_cifar10dvs_cache.py --src .../4724671.zip --out cifar10dvs_wide_T20.pt
    #    -> writes to $HLL_CACHE (override with an absolute --out). Then upload that ~230 MB .pt.
"""

from __future__ import annotations

import argparse
import glob
import os
import zipfile
from pathlib import Path

import numpy as np

CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]


def read_aedat2(path):
    """jAER DVS128 AEDAT 2.0: ASCII '#' header, then big-endian (addr:u4, timestamp:u4) pairs.
    DVS128 address bits: x = bits 1-7, y = bits 8-14, polarity = bit 0 (SpikingJelly convention).
    Orientation/polarity convention is irrelevant to classification as long as it is consistent."""
    with open(path, "rb") as f:
        data = f.read()
    p = 0
    while p < len(data) and data[p:p + 1] == b"#":      # skip ASCII header lines
        nl = data.find(b"\n", p)
        if nl < 0:
            break
        p = nl + 1
    raw = np.frombuffer(data[p:], dtype=">u4")
    raw = raw[:(raw.size // 2) * 2]
    addr = raw[0::2]
    ts = raw[1::2].astype(np.int64)
    x = ((addr & 0xFE) >> 1).astype(np.int64)
    y = ((addr & 0x7F00) >> 8).astype(np.int64)
    pol = (addr & 0x1).astype(np.int64)
    ev = np.empty(addr.size, dtype=[("t", "<i8"), ("x", "<i8"), ("y", "<i8"), ("p", "<i8")])
    ev["t"] = (ts - ts.min()) if ts.size else ts
    ev["x"] = x; ev["y"] = y; ev["p"] = pol
    return ev


def to_features(frames, pool):
    f = np.asarray(frames, dtype=np.float32)            # [T, P, H, W]
    if f.ndim == 4 and pool > 1:
        T, P, H, W = f.shape
        Hc, Wc = (H // pool) * pool, (W // pool) * pool
        f = f[:, :, :Hc, :Wc].reshape(T, P, Hc // pool, pool, Wc // pool, pool).mean(axis=(3, 5))
    return f.reshape(f.shape[0], -1)


def class_of(path):
    name = os.path.basename(path).lower()
    for c in CLASSES:
        if c in name:
            return CLASSES.index(c)
    par = os.path.basename(os.path.dirname(path)).lower()
    return CLASSES.index(par) if par in CLASSES else -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect")
    ap.add_argument("--src", help="4724671.zip (or a dir already containing .aedat)")
    ap.add_argument("--work", default=None, help="extraction dir (default: <src parent>/cifar10dvs_extracted)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--train-per-class", type=int, default=100)
    ap.add_argument("--test-per-class", type=int, default=40)
    ap.add_argument("--T", type=int, default=20)
    ap.add_argument("--pool", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    if a.inspect:
        ev = read_aedat2(a.inspect)
        xs, ys, ps = ev["x"], ev["y"], ev["p"]
        print(f"events:  {ev.size}")
        print(f"x range: [{xs.min()}, {xs.max()}]   y range: [{ys.min()}, {ys.max()}]")
        print(f"polarity values: {sorted(set(ps.tolist()))}")
        print(f"t span:  {int(ev['t'].max())} us  ({ev['t'].max()/1e6:.2f} s)")
        ok = ev.size > 1000 and 0 <= xs.min() and xs.max() < 128 and 0 <= ys.min() and ys.max() < 128
        print("decoder:", "OK" if ok else "WRONG (x/y out of 0..127 or too few events) -> tell me")
        return

    import torch
    import tonic.transforms as TT

    src = Path(a.src)
    work = Path(a.work) if a.work else (src.parent / "cifar10dvs_extracted")
    work.mkdir(parents=True, exist_ok=True)
    aedats = glob.glob(str(work / "**" / "*.aedat"), recursive=True)
    if not aedats:
        print(f"extracting {src} -> {work} (one-time, ~8 GB) ...", flush=True)
        with zipfile.ZipFile(src) as z:
            z.extractall(work)
        for cz in glob.glob(str(work / "*.zip")):        # the 10 inner class zips
            with zipfile.ZipFile(cz) as z:
                z.extractall(work)
        aedats = glob.glob(str(work / "**" / "*.aedat"), recursive=True)
    print(f"found {len(aedats)} .aedat files")

    rng = np.random.default_rng(a.seed)
    byc = {c: [] for c in range(10)}
    for fp in aedats:
        c = class_of(fp)
        if c >= 0:
            byc[c].append(fp)
    for c in byc:
        rng.shuffle(byc[c])

    tf = TT.ToFrame(sensor_size=(128, 128, 2), n_time_bins=a.T)

    def feats(fp):
        return to_features(tf(read_aedat2(fp)), a.pool)

    Xtr, ytr, Xte, yte = [], [], [], []
    k1, k2 = a.train_per_class, a.train_per_class + a.test_per_class
    for c in range(10):
        files = byc[c]
        for fp in files[:k1]:
            Xtr.append(feats(fp)); ytr.append(c)
        for fp in files[k1:k2]:
            Xte.append(feats(fp)); yte.append(c)
        print(f"  {CLASSES[c]:11s}: {min(len(files), k1)} train, {max(0, min(len(files), k2) - k1)} test", flush=True)

    Xtr = torch.from_numpy(np.stack(Xtr).astype(np.float32)); ytr = torch.tensor(ytr, dtype=torch.long)
    Xte = torch.from_numpy(np.stack(Xte).astype(np.float32)); yte = torch.tensor(yte, dtype=torch.long)
    out = Path(a.out) if (a.out and os.path.isabs(a.out)) else \
        Path(os.environ.get("HLL_CACHE", ".")) / (a.out or "cifar10dvs_wide_T20.pt")
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"Xtr": Xtr, "ytr": ytr, "Xte": Xte, "yte": yte}, out)
    mb = out.stat().st_size / 1e6
    print(f"{out}: {mb:.0f} MB | train {tuple(Xtr.shape)} test {tuple(Xte.shape)} | 10 classes")


if __name__ == "__main__":
    main()
