"""Idea-1 origin experiment: sweep static + gate-coupled AHP across Adaptive HyperLIF / static-0.95
/ LIF on the synthetic temporal task. Identifies the best origin candidates to fold into the
main roster.

    python scripts/run_origin.py --seeds 0,1,2 --epochs 5
Outputs: results/origin_synthetic/{summary.md, ranking.csv, _registry.csv} + per-run folders.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adhyperlif_triage.train import origin_roster, run_smoke  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="synthetic")
    ap.add_argument("--mode", default="smoke", choices=["smoke", "tiny"])
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--dt", type=float, default=1e-3)
    ap.add_argument("--T", type=int, default=20)
    ap.add_argument("--input-scale", type=float, default=16.0)
    args = ap.parse_args()
    run_smoke(dataset=args.dataset, mode=args.mode, tag="origin",
              seeds=tuple(int(s) for s in args.seeds.split(",")),
              epochs=args.epochs, hidden=args.hidden, dt=args.dt, T=args.T,
              input_scale=args.input_scale, roster=origin_roster())


if __name__ == "__main__":
    main()
