"""Deep diagnosis of the Hardstep cell: is the 0.45 rad baseline error control quality or an infeasible reference?

Read-only over the canonical matched_45s traces.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

RES = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29"
           r"\results\matched_45s")
ROWS = [[.75, -.45, .55], [-.65, .55, -.70], [.50, .50, .90], [-.80, -.35, .20]]
J = {"x2": np.array([0.0366517, 0.0254117, 0.0605280]),          # body-frame diag, from the model
     "cf2-rotor": np.array([2.3951e-5, 2.3951e-5, 3.2347e-5])}
JT = {"x2": np.array([6.0711e-2, 3.6468e-2, 2.5412e-2]),          # j_tune used for gains AND torque limits
      "cf2-rotor": np.array([2.3951e-5, 2.3951e-5, 3.2347e-5])}
NU = np.array([12.0, 12.0, 10.0])


def euler_to_quat(r, p, y):
    cr, sr = np.cos(r / 2), np.sin(r / 2)
    cp, sp = np.cos(p / 2), np.sin(p / 2)
    cy, sy = np.cos(y / 2), np.sin(y / 2)
    return np.array([cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy,
                     cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy])


def ang(q1, q2):
    d = abs(float(np.dot(q1, q2)))
    return 2 * np.arccos(min(1.0, d))


print("=== 1. How big are the Hardstep commands? ===")
qs = [euler_to_quat(*r) for r in ROWS]
q0 = euler_to_quat(0, 0, 0)
seq = [q0] + [qs[i % 4] for i in range(4)] + [qs[0]]
steps = [np.degrees(ang(seq[i], seq[i + 1])) for i in range(len(seq) - 1)]
print("   consecutive commanded rotations [deg]:", " ".join(f"{s:.1f}" for s in steps))
print("   dwell between steps: 2.0 s")

print("\n=== 2. Is that reference feasible with the available torque? ===")
for p in ("x2", "cf2-rotor"):
    lim = np.maximum(JT[p] * NU, 1e-6)
    acc = lim / J[p]                       # rad/s^2 actually available per body axis
    print(f"   {p}: torque limit {lim} N m -> real max accel {np.round(acc, 2)} rad/s^2 "
          f"(intended {NU})")
    worst = np.radians(max(steps))
    t_bb = 2 * np.sqrt(worst / acc.min())  # bang-bang rest-to-rest on the slowest axis
    print(f"        rest-to-rest bang-bang for the largest step ({np.degrees(worst):.0f} deg) on the "
          f"slowest axis: {t_bb:.2f} s of the 2.0 s dwell")

print("\n=== 3. What do the traces actually show? ===")
for p in ("x2", "cf2-rotor"):
    for ctrl in ("classical", "nengo_nef_pes"):
        f = RES / f"{p.replace('-', '_')}_hardstep_{ctrl}" / "trace.csv"
        rows = list(csv.DictReader(f.open(encoding="utf-8")))
        t = np.array([float(r["t"]) for r in rows])
        q = np.array([float(r["qerr"]) for r in rows])
        z = np.array([float(r["z"]) for r in rows])
        sat = np.array([float(r["saturated"]) for r in rows])
        tau = np.abs(np.array([[float(r["tau_x"]), float(r["tau_y"]), float(r["tau_z"])] for r in rows]))
        lim = np.maximum(JT[p] * NU, 1e-6)
        at_lim = (tau >= 0.999 * lim).mean(axis=0)
        # settled error: last 0.5 s of each 2 s dwell (steps start at t=1 s)
        phase = np.clip((t - 1.0) % 2.0, 0, 2)
        late = (t > 1.0) & (phase > 1.5)
        early = (t > 1.0) & (phase <= 1.5)
        print(f"\n   {p:10s} {ctrl:14s} mean {q.mean():.4f} rad ({np.degrees(q.mean()):.1f} deg)")
        print(f"      slew phase (first 1.5 s after each step): {q[early].mean():.4f} rad | "
              f"settled phase (last 0.5 s): {q[late].mean():.4f} rad ({np.degrees(q[late].mean()):.1f} deg)")
        print(f"      z: start {z[0]:.2f} m, min {z.min():.3f} m, final {z[-1]:.2f} m | "
              f"rotor-sat fraction {sat.mean():.3f}")
        print(f"      per-axis torque at its limit: roll {at_lim[0]:.2f} pitch {at_lim[1]:.2f} "
              f"yaw {at_lim[2]:.2f}")
