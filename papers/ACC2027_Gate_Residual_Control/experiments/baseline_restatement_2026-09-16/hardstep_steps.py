"""Per-step characterisation of Hardstep: what fraction of the mean error is unavoidable slew,
and does the residual improve the parts a controller can actually influence?"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

RES = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29"
           r"\results\matched_45s")
CELLS = [("x2", "classical", "X2 PD"), ("x2", "nengo_nef_pes", "X2 CMG"),
         ("cf2-rotor", "classical", "CF2 PD"), ("cf2-rotor", "nengo_nef_pes", "CF2 CMG")]


def load(p, ctrl):
    f = RES / f"{p.replace('-', '_')}_hardstep_{ctrl}" / "trace.csv"
    rows = list(csv.DictReader(f.open(encoding="utf-8")))
    return (np.array([float(r["t"]) for r in rows]),
            np.array([float(r["qerr"]) for r in rows]))


def steps(t, q, thresh_deg):
    """Per-step settling time to thresh, plus residual error in the last 0.5 s of each dwell."""
    out = []
    for k in range(22):                       # steps at t = 1, 3, 5, ... within 45 s
        t0 = 1.0 + 2.0 * k
        if t0 + 2.0 > t[-1]:
            break
        m = (t >= t0) & (t < t0 + 2.0)
        tt, qq = t[m], np.degrees(q[m])
        if qq.size == 0 or qq[0] < thresh_deg:
            continue
        below = np.where(qq < thresh_deg)[0]
        ts = (tt[below[0]] - t0) if below.size else np.nan
        tail = qq[tt - t0 > 1.5]
        out.append((qq.max(), ts, tail.mean() if tail.size else np.nan))
    a = np.array(out, dtype=float)
    return a


print("Hardstep: 63-111 deg commanded rotations, 2 s dwell, 22 steps in 45 s\n")
print(f"{'cell':9s} {'mean[deg]':>9s} {'slew<1.5s':>10s} {'settled':>8s} {'t_settle5':>10s} "
      f"{'t_settle2':>10s} {'peak':>7s}")
for p, ctrl, name in CELLS:
    t, q = load(p, ctrl)
    a5, a2 = steps(t, q, 5.0), steps(t, q, 2.0)
    phase = (t - 1.0) % 2.0
    early = (t > 1.0) & (phase <= 1.5)
    late = (t > 1.0) & (phase > 1.5)
    print(f"{name:9s} {np.degrees(q.mean()):9.2f} {np.degrees(q[early].mean()):10.2f} "
          f"{np.degrees(q[late].mean()):8.2f} {np.nanmean(a5[:, 1]):10.3f} "
          f"{np.nanmean(a2[:, 1]):10.3f} {np.nanmean(a5[:, 0]):7.1f}")

print("\nPD -> CMG change on each quantity (negative = CMG better):")
for p, label in (("x2", "X2"), ("cf2-rotor", "CF2")):
    t0, q0 = load(p, "classical")
    t1, q1 = load(p, "nengo_nef_pes")
    a0, a1 = steps(t0, q0, 5.0), steps(t1, q1, 5.0)
    b0, b1 = steps(t0, q0, 2.0), steps(t1, q1, 2.0)
    phase = (t0 - 1.0) % 2.0
    early, late = (t0 > 1.0) & (phase <= 1.5), (t0 > 1.0) & (phase > 1.5)
    def pct(x, y):
        return 100 * (y - x) / x
    print(f"  {label}: mean {pct(q0.mean(), q1.mean()):+6.1f}% | slew {pct(q0[early].mean(), q1[early].mean()):+6.1f}% | "
          f"settled {pct(q0[late].mean(), q1[late].mean()):+6.1f}% | "
          f"t_settle(5deg) {pct(np.nanmean(a0[:,1]), np.nanmean(a1[:,1])):+6.1f}% | "
          f"t_settle(2deg) {pct(np.nanmean(b0[:,1]), np.nanmean(b1[:,1])):+6.1f}% | "
          f"peak {pct(np.nanmean(a0[:,0]), np.nanmean(a1[:,0])):+6.1f}%")

print("\nFloor of the metric: a torque-limited rigid body cannot track a step, so the mean is dominated")
print("by the slew. Fraction of the 45-s mean error contributed by the first 1.5 s after each step:")
for p, ctrl, name in CELLS:
    t, q = load(p, ctrl)
    phase = (t - 1.0) % 2.0
    early = (t > 1.0) & (phase <= 1.5)
    print(f"  {name:9s} {100 * q[early].sum() / q.sum():5.1f}%")
