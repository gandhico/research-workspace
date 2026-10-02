"""Run the P1 local baseline preflight.

This is a compact, reproducible batch for claim discipline, not the final paper run:

    ff x {lif, plif, alif, hyperlif, adaptive} x 6 readouts x 5 seeds
    on nmnist_tiny_T20, default 5 epochs, hidden 64.

The paper-grade run must use the main/full caches and architecture cells.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
DATA = ROOT / "data" / "tonic" / "_cache" / "nmnist_tiny_T20.pt"
DEFAULT_RESULTS = ROOT / "results" / "p1_plif_alif_ff_nmnist_tiny_20260719"

NEURONS = ["lif", "plif", "alif", "hyperlif", "adaptive"]
READOUTS = ["spike_count", "membrane", "gate", "hybrid_gr", "hybrid_vr", "hybrid_vr_conductance"]
SEEDS = [0, 1, 2, 3, 4]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--hidden", type=int, default=64)
    p.add_argument("--batch", type=int, default=32)
    p.add_argument("--results-root", default=str(DEFAULT_RESULTS))
    p.add_argument("--data-file", default=str(DATA))
    p.add_argument("--device", default="cpu")
    p.add_argument("--no-skip-existing", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    jobs = [(n, r, s) for n in NEURONS for r in READOUTS for s in SEEDS]
    for i, (neuron, readout, seed) in enumerate(jobs, start=1):
        cmd = [
            str(PY if PY.exists() else sys.executable),
            "hpc\\train_hpc.py",
            "--data-file", args.data_file,
            "--arch", "ff",
            "--neuron", neuron,
            "--readout", readout,
            "--seed", str(seed),
            "--epochs", str(args.epochs),
            "--batch", str(args.batch),
            "--hidden", str(args.hidden),
            "--results-root", args.results_root,
            "--device", args.device,
        ]
        if not args.no_skip_existing:
            cmd.append("--skip-existing")
        print(f"[{i:03d}/{len(jobs)}] {neuron}.{readout}.seed{seed}", flush=True)
        subprocess.run(cmd, cwd=str(ROOT), check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
