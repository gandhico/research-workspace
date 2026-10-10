"""Segment the intermittent-hover runs into bursts and silences.

The aggregate mean hides the question we actually care about: what the
learned residual does once the disturbance stops.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RES = HERE / "results" / "hover_intermittent_2026-09-05"
WARMUP, ON, OFF = 5.0, 5.0, 5.0


def load(run: str) -> dict[str, np.ndarray]:
    p = RES / run / "trace.csv"
    with io.open(p, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    cols = rows[0].keys()
    return {c: np.array([float(r[c]) for r in rows]) for c in cols
            if all(r[c] not in ("", None) for r in rows)}


def phase_of(t: float) -> str:
    if t < WARMUP:
        return "initial quiet"
    ph = (t - WARMUP) % (ON + OFF)
    return "burst" if ph < ON else "silence"


def main() -> None:
    pd_, cmg = load("pd_disturbed"), load("cmg_disturbed")
    tkey = "t" if "t" in pd_ else next(k for k in pd_ if k.startswith("t"))
    qkey = next(k for k in pd_ if "qerr" in k or "theta" in k)
    print(f"time column '{tkey}', error column '{qkey}'")
    print(f"available columns: {sorted(pd_)}\n")

    t = pd_[tkey]
    ph = np.array([phase_of(x) for x in t])

    print(f"{'phase':16s}{'PD':>12s}{'CMG-PES':>12s}{'reduction':>12s}")
    print("-" * 52)
    for label in ("initial quiet", "burst", "silence"):
        m = ph == label
        if not m.any():
            continue
        a, b = pd_[qkey][m].mean(), cmg[qkey][m].mean()
        red = 100 * (1 - b / a) if a > 1e-12 else float("nan")
        print(f"{label:16s}{a:12.6f}{b:12.6f}{red:11.2f}%")

    # per-silence detail: is there an after-effect that decays?
    print("\nper-interval detail (mean |qerr|):")
    print(f"{'window [s]':>14s}{'phase':>10s}{'PD':>12s}{'CMG-PES':>12s}")
    edges = [WARMUP + k * (ON + OFF) for k in range(5)]
    for k, e in enumerate(edges[:-1]):
        for label, s0, s1 in (("burst", e, e + ON),
                              ("silence", e + ON, e + ON + OFF)):
            m = (t >= s0) & (t < s1)
            if m.sum() < 10:
                continue
            print(f"{f'{s0:.0f}-{s1:.0f}':>14s}{label:>10s}"
                  f"{pd_[qkey][m].mean():12.6f}{cmg[qkey][m].mean():12.6f}")

    # does the residual persist into silence?
    rk = [k for k in cmg if "residual" in k.lower()]
    if rk:
        k = rk[0]
        print(f"\nresidual column '{k}' during each phase (mean |.|):")
        for label in ("initial quiet", "burst", "silence"):
            m = ph == label
            if m.any():
                print(f"  {label:16s}{np.abs(cmg[k][m]).mean():.6e}")


if __name__ == "__main__":
    main()
