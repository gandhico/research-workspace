"""Divergence onset on CF2 step missions: when does error run away, and what were the gains?

Reads decimated traces (every 20 steps = 10 ms) of the v0/v1 campaigns.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

P5 = Path(__file__).resolve().parents[2]
CELLS = [
    ("quat_dual_v0_2026-09-12", "hardstep", "pid"),
    ("quat_dual_v0_2026-09-12", "hardstep", "st_pid"),
    ("quat_v1_2026-09-12", "hardstep", "st_pid_f"),
    ("quat_v1_2026-09-12", "hardstep", "stn_b_ks"),
    ("quat_v1_2026-09-12", "hardstep", "dual_stn_b"),
    ("quat_v1_2026-09-12", "hardstep_b", "st_pid_f"),
    ("quat_v1_2026-09-12", "hardstep_b", "stn_b_ks"),
]
for run, mission, ctrl in CELLS:
    path = P5 / "results" / run / "cf2-rotor" / mission / ctrl / "trace.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    t = np.array([float(r["t"]) for r in rows])
    q = np.array([float(r["qerr"]) for r in rows])
    sat = np.array([int(r["saturated"]) for r in rows])
    z = np.array([float(r["z"]) for r in rows])
    m = {k: np.array([float(r[k]) for r in rows]) for k in rows[0] if k.startswith("m")}
    run_away = np.argmax(q > 1.2) if np.any(q > 1.2) else None
    first_sat = np.argmax(sat > 0) if np.any(sat) else None
    print(f"\n== {mission}/{ctrl}: mean {q.mean():.3f} rad, sat {sat.mean():.3f}, z range [{z.min():.2f}, {z.max():.2f}]")
    if first_sat is not None:
        i = first_sat
        print(f"  first rotor saturation t={t[i]:.2f}s  qerr={q[i]:.2f}  "
              f"m_p={[round(m[f'mp_{a}'][i], 2) for a in 'xyz']} m_i={[round(m[f'mi_{a}'][i], 2) for a in 'xyz']} "
              f"m_d={[round(m[f'md_{a}'][i], 2) for a in 'xyz']}")
    if run_away is not None:
        i = run_away
        j = max(0, i - 50)                                  # 0.5 s before
        print(f"  error > 1.2 rad at t={t[i]:.2f}s; 0.5 s earlier: qerr={q[j]:.2f}, sat frac last 1 s="
              f"{sat[max(0, i - 100):i].mean():.2f}")
        print(f"  gains 0.5 s before run-away: m_p={[round(m[f'mp_{a}'][j], 2) for a in 'xyz']} "
              f"m_i={[round(m[f'mi_{a}'][j], 2) for a in 'xyz']} m_d={[round(m[f'md_{a}'][j], 2) for a in 'xyz']}")
        print(f"  z at run-away: {z[i]:.2f} m (start 1.0)")
    else:
        print("  no run-away (qerr never > 1.2 rad)")
