"""Run the Phase-1 roster on the synthetic temporal task (pipeline de-risk + first table).

    python scripts/run_smoke.py --mode smoke --seeds 0,1,2 --epochs 5
Outputs: results/<mode>_synthetic/{_registry.csv, ranking.csv, summary.md} and per-run folders.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adhyperlif_triage.train import run_smoke  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="synthetic",
                    help="synthetic | nmnist | shd | ssc | cifar10dvs")
    ap.add_argument("--mode", default="smoke", choices=["smoke", "tiny"])
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--dt", type=float, default=1e-3)
    ap.add_argument("--T", type=int, default=20, help="time bins for Tonic datasets")
    ap.add_argument("--input-scale", type=float, default=16.0)
    ap.add_argument("--lr", type=float, default=1e-3)
    args = ap.parse_args()
    run_smoke(dataset=args.dataset, mode=args.mode,
              seeds=tuple(int(s) for s in args.seeds.split(",")),
              epochs=args.epochs, hidden=args.hidden, dt=args.dt, T=args.T,
              input_scale=args.input_scale, lr=args.lr)


if __name__ == "__main__":
    main()
