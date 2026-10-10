"""Hardstep across the whole ladder, scored by settling time instead of slew-dominated mean error."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

R = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\results")
CELLS = {
    "PD":            (R / "matched_45s/{p}_hardstep_classical",
                      R / "matched_45s/{p}_hardstep_nengo_nef_pes"),
    "PD+ff (rho=1)": (R / "pid_baseline_2026-09-10/rate_ff_left_neg/{p}_hardstep_classical",
                      R / "pid_baseline_2026-09-10/rate_ff_left_neg/{p}_hardstep_nengo_nef_pes"),
    # rho=3 CMG uses each platform's SELECTED beta: X2 0.5 (stretch/), CF2 0.05 (cmg_beta/b0.05/)
    "PD+ff (rho=3)": (R / "baselines_2026-09-10/tune/pdff/bw3/{p}_hardstep_classical", None),
}
CMG_RHO3 = {"x2": R / "baselines_2026-09-10/stretch/pdff/bw3/x2_hardstep_nengo_nef_pes",
            "cf2_rotor": R / "baselines_2026-09-10/cmg_beta/pdff/bw3/b0.05/cf2_rotor_hardstep_nengo_nef_pes"}


def load(d: Path):
    rows = list(csv.DictReader((d / "trace.csv").open(encoding="utf-8")))
    return (np.array([float(r["t"]) for r in rows]), np.array([float(r["qerr"]) for r in rows]))


def metrics(t, q, thresh_deg=5.0):
    ts, tails, miss = [], [], 0
    for k in range(22):
        t0 = 1.0 + 2.0 * k
        if t0 + 2.0 > t[-1]:
            break
        m = (t >= t0) & (t < t0 + 2.0)
        tt, qq = t[m] - t0, np.degrees(q[m])
        if qq.size == 0 or qq[0] < thresh_deg:
            continue
        below = np.where(qq < thresh_deg)[0]
        if below.size:
            ts.append(tt[below[0]])
        else:
            miss += 1
            ts.append(2.0)                      # censored at the dwell
        tails.append(qq[tt > 1.5].mean())
    phase = (t - 1.0) % 2.0
    early, late = (t > 1.0) & (phase <= 1.5), (t > 1.0) & (phase > 1.5)
    return dict(mean=np.degrees(q.mean()), slew=np.degrees(q[early].mean()),
                settled=np.degrees(q[late].mean()), t_settle=float(np.mean(ts)),
                censored=miss, n=len(ts))


print("Hardstep, 22 steps of 63-111 deg with a 2 s dwell. t_settle = mean time to enter a 5 deg band")
print("(censored at 2 s when a step never settles).\n")
hdr = f"{'platform':6s} {'rung':14s} {'ctrl':4s} {'mean[deg]':>9s} {'slew':>7s} {'settled':>8s} {'t_set[s]':>9s} {'miss':>5s}"
print(hdr)
print("-" * len(hdr))
res = {}
for p, plat in (("x2", "X2"), ("cf2_rotor", "CF2")):
    for rung, (base, cmg) in CELLS.items():
        for tag, d in (("PD", base), ("CMG", cmg if cmg is not None else CMG_RHO3[p])):
            path = Path(str(d).format(p=p))
            if not (path / "trace.csv").exists():
                print(f"{plat:6s} {rung:14s} {tag:4s}   MISSING {path}")
                continue
            m = metrics(*load(path))
            res[(plat, rung, tag)] = m
            print(f"{plat:6s} {rung:14s} {tag:4s} {m['mean']:9.2f} {m['slew']:7.2f} {m['settled']:8.2f} "
                  f"{m['t_settle']:9.3f} {m['censored']:5d}")

print("\nCMG effect on Hardstep at each rung (negative = better):")
print(f"{'platform':6s} {'rung':14s} {'mean':>8s} {'settling time':>14s}")
for p in ("X2", "CF2"):
    for rung in CELLS:
        if (p, rung, "PD") in res and (p, rung, "CMG") in res:
            a, b = res[(p, rung, "PD")], res[(p, rung, "CMG")]
            print(f"{p:6s} {rung:14s} {100 * (b['mean'] / a['mean'] - 1):+7.1f}% "
                  f"{100 * (b['t_settle'] / a['t_settle'] - 1):+13.1f}%")
Path(__file__).with_name("hardstep_ladder.json").write_text(
    json.dumps({f"{k[0]}|{k[1]}|{k[2]}": v for k, v in res.items()}, indent=1), encoding="utf-8")
