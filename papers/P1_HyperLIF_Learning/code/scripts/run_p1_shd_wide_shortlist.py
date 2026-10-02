"""Run a bounded P1 baseline shortlist on SHD wide.

This is the next step after the local N-MNIST tiny preflight:

    ff x selected readout per neuron x 5 seeds
    on shd_wide_T20, default 5 epochs, hidden 128.

It is designed to answer whether the new PLIF/ALIF baselines remain serious on a harder audio
cache before launching the full paper grid.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
DATA = ROOT / "data" / "tonic" / "_cache" / "shd_wide_T20.pt"
DEFAULT_RESULTS = ROOT / "results" / "p1_baseline_shortlist_ff_shd_wide_20260719"

SHORTLIST = [
    ("lif", "hybrid_vr"),
    ("plif", "hybrid_vr"),
    ("alif", "hybrid_vr_conductance"),
    ("hyperlif", "hybrid_vr"),
    ("adaptive", "hybrid_vr_conductance"),
]
SEEDS = [0, 1, 2, 3, 4]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--hidden", type=int, default=128)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--results-root", default=str(DEFAULT_RESULTS))
    p.add_argument("--data-file", default=str(DATA))
    p.add_argument("--device", default="cpu")
    p.add_argument("--no-skip-existing", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    jobs = [(n, r, s) for n, r in SHORTLIST for s in SEEDS]
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
        print(f"[{i:02d}/{len(jobs)}] {neuron}.{readout}.seed{seed}", flush=True)
        subprocess.run(cmd, cwd=str(ROOT), check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
