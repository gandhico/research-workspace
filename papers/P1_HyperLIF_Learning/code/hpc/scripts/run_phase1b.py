"""Phase 1b: firmer all-class runs (mode=wide) on the 8-config shortlist, to separate the
noisy middle band from the tiny runs.

    python scripts/run_phase1b.py --dataset shd --seeds 0,1,2,3 --epochs 20
Outputs: results/phase1b_<dataset>/{summary.md, ranking.csv, _registry.csv}.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adhyperlif_triage.train import phase1b_roster, run_smoke  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="nmnist | shd | ssc | ...")
    ap.add_argument("--seeds", default="0,1,2,3")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--dt", type=float, default=1e-3)
    ap.add_argument("--T", type=int, default=20)
    ap.add_argument("--input-scale", type=float, default=16.0)
    args = ap.parse_args()
    run_smoke(dataset=args.dataset, mode="wide", tag="phase1b",
              seeds=tuple(int(s) for s in args.seeds.split(",")),
              epochs=args.epochs, hidden=args.hidden, dt=args.dt, T=args.T,
              input_scale=args.input_scale, roster=phase1b_roster())


if __name__ == "__main__":
    main()
