"""Reproduce the reference 80-second run and compare it field by field.

The reference is `reference/dilisic_80s_smoothed`, the best run recorded in
docs/dilisic_replication_report.md (2026-04-25). This script re-runs the
experiment from the installed package and checks that every summary metric
still matches, so a broken environment or an accidental code change is
caught immediately rather than at the next paper deadline.

    python verify.py              # full 80 s reproduction, about 40 s
    python verify.py --quick      # 5 s smoke check, no reference comparison
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference" / "dilisic_80s_contract_fixed_20260908" / "plots" / "summary.json"

# Relative tolerance per field. Floating-point summation order can differ
# across NumPy builds, so exact equality is not required -- but anything
# beyond 1e-6 relative means the dynamics changed, not the arithmetic.
RTOL = 1.0e-6


def compare(got: dict, want: dict) -> int:
    width = max(len(k) for k in want)
    bad = 0
    print(f"\n{'metric':<{width}}  {'reference':>22}  {'reproduced':>22}  rel.diff")
    print("-" * (width + 60))
    for key, ref in want.items():
        new = got.get(key)
        if new is None:
            print(f"{key:<{width}}  {ref:>22}  {'MISSING':>22}")
            bad += 1
            continue
        if ref == 0.0:
            rel = abs(new)
        else:
            rel = abs(new - ref) / abs(ref)
        flag = "" if rel <= RTOL else "   <-- DIFFERS"
        if rel > RTOL:
            bad += 1
        print(f"{key:<{width}}  {ref:>22.12g}  {new:>22.12g}  {rel:8.2e}{flag}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="5 s smoke run instead of the 80 s reproduction")
    ap.add_argument("--output", type=Path, default=HERE / "runs" / "verify")
    args = ap.parse_args()

    from dilisic.experiments.flexible_arm_mas import run
    from dilisic.experiments.plot_flexible_arm_mas import summarize

    duration = 5.0 if args.quick else 80.0
    print(f"running {duration:g} s at dt = 0.001 -> {args.output}")
    result = run(duration=duration, dt=1.0e-3, output=args.output, plot=False)
    print(f"  final_com_error : {result['final_com_error']:.12g}")
    print(f"  max_weight_norm : {result['max_weight_norm']:.12g}")

    summary = summarize(Path(result["csv"]))

    if args.quick:
        print("\nquick mode: no reference comparison.")
        ok = all(math.isfinite(v) for v in summary.values())
        print("all summary values finite:", ok)
        return 0 if ok else 1

    if not REFERENCE.is_file():
        print(f"\nreference missing at {REFERENCE}", file=sys.stderr)
        return 2

    want = json.loads(REFERENCE.read_text(encoding="utf-8"))
    bad = compare(summary, want)

    print()
    if bad == 0:
        print(f"MATCH: all {len(want)} metrics within {RTOL:g} relative tolerance.")
    else:
        print(f"{bad} of {len(want)} metrics differ beyond {RTOL:g}.")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
