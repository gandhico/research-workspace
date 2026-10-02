"""Phase 2: reservoir / LSM architecture. Same neuron shortlist, but a fixed recurrent 'liquid'
with a trained readout. Tests whether HyperLIF's richer state makes a better reservoir than LIF.

    python scripts/run_phase2.py --dataset shd --mode wide --seeds 0,1,2,3 --epochs 20
Outputs: results/phase2res_<dataset>/{summary.md, ranking.csv, _registry.csv}.
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
    ap.add_argument("--dataset", default="synthetic")
    ap.add_argument("--mode", default="wide", choices=["smoke", "tiny", "wide"])
    ap.add_argument("--seeds", default="0,1,2,3")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--hidden", type=int, default=128, help="reservoir size")
    ap.add_argument("--dt", type=float, default=1e-3)
    ap.add_argument("--T", type=int, default=20)
    ap.add_argument("--input-scale", type=float, default=16.0)
    args = ap.parse_args()
    run_smoke(dataset=args.dataset, mode=args.mode, tag="phase2res", architecture="reservoir",
              seeds=tuple(int(s) for s in args.seeds.split(",")),
              epochs=args.epochs, hidden=args.hidden, dt=args.dt, T=args.T,
              input_scale=args.input_scale, roster=phase1b_roster())


if __name__ == "__main__":
    main()
