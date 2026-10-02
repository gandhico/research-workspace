"""Run the recursive backstepping family through the *unchanged* A5 runner (run_controllers_gated.py).

The sealed runner builds its nominal law with `AdvancedBaseline(args, inertia, limits, BASE_WN_RAD_S)` whenever
--baseline is not "pd". This wrapper adds two family names and substitutes TrueBackstepping for them; everything
else (plant, sensing, residual, gate, allocation, metrics, manifests) is the runner's own code. An extra
true_backstepping_provenance.json records the hashes of this wrapper and of true_backstepping.py.

  python run_true_backstepping.py --baseline bs-true     [all run_controllers_gated.py flags]
  python run_true_backstepping.py --baseline bs-adaptive [...]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FR = REPO / "experiments" / "final_robustness_gating_2026-09-20"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments" / "nengo_nef_replication_2026-08-29"))
sys.path.insert(0, str(FR))
sys.path.insert(0, str(HERE))

import run_controllers_gated as R  # noqa: E402
from true_backstepping import TrueBackstepping  # noqa: E402

NEW = ("bs-true", "bs-adaptive")
_Original = R.AdvancedBaseline


def _factory(args, inertia, limits, wn):
    if args.baseline in NEW:
        return TrueBackstepping(inertia, limits, wn, R.reference_rate, args.mission, args.duration,
                                rho=float(args.bw_scale), zeta=R.BASELINE_ZETA,
                                adaptive=args.baseline == "bs-adaptive", dt=args.dt, rate_ff=args.rate_ff)
    return _Original(args, inertia, limits, wn)


R.AdvancedBaseline = _factory
R.BASELINE_FAMILIES = R.BASELINE_FAMILIES + NEW


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


if __name__ == "__main__":
    args = R.make_parser().parse_args()
    R._validate(args)
    summary = R.run(args)
    prov = {"family": args.baseline, "wrapper": str(Path(__file__).resolve()),
            "source_sha256": {"run_true_backstepping.py": sha(Path(__file__).resolve()),
                              "true_backstepping.py": sha(HERE / "true_backstepping.py"),
                              "run_controllers_gated.py": sha(FR / "run_controllers_gated.py")},
            "note": "summary.json 'baseline.name' is the runner's fixed label; the nominal law is in baseline.stats."}
    (args.output / "true_backstepping_provenance.json").write_text(json.dumps(prov, indent=1))
    m = summary["metrics"]
    print(json.dumps({"family": args.baseline, "qerr_true_mean_rad": m["qerr_true_mean_rad"],
                      "stats": summary["baseline"]["stats"]}, indent=1))
