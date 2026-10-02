"""Izhikevich-PES vs CMG-PES (ungated / gated) on the primary baseline (PD+ff, rho = 3), X2, five missions.

Error = mean quaternion angle over 45 s.  Effort = RMS residual / per-axis torque bound, recomputed identically for all
arms from the 5 ms trace (archived-runner traces carry `residual_*` in N m; the new runner carries `realized_residual_*`).
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
R = HERE / "results"
M = ("roll", "full3", "hard45", "hardstep", "yaw360")
gm = lambda xs: math.exp(sum(math.log(x) for x in xs) / len(xs))


def summ(p):
    return json.load(open(p / "summary.json"))


s0 = summ(R / "supplementary_izhikevich" / "x2" / "hard45" / "nengo_izhikevich_pes")
print("archived summary keys:", list(s0.keys())[:14])
print("metrics keys:", list(s0.get("metrics", {}).keys())[:14])

nom = {(r["platform"], r["mission"], r["label"]): r for r in csv.DictReader((R / "final_nominal.csv").open())}
lim = np.array(json.load(open(R / "confirmatory/nominal/x2/hard45/pdff_rho3/nominal/seed_001/summary.json"))["actuation"]["torque_limits_Nm"])
rows = []
print(f"\n{'mission':9s}{'PD+ff':>9s}{'CMG ungated':>13s}{'CMG gated':>11s}{'Izhikevich':>12s}   reductions vs PD+ff [%]  (CMG ungated / gated / Izh)   effort (CMG / Izh)")
for m in M:
    base = float(nom[("x2", m, "pdff_rho3")]["qerr_true_mean_rad"])
    ung = float(nom[("x2", m, "cmg_pes_table")]["qerr_true_mean_rad"])
    gat = float(nom[("x2", m, "cmg_pes_gated")]["qerr_true_mean_rad"])
    d = R / "supplementary_izhikevich" / "x2" / m / "nengo_izhikevich_pes"
    s = summ(d)
    izh = s["qerr_mean_rad"]          # archived-runner summary schema (top level)
    tr = pd.read_csv(d / "trace.csv")
    eff_izh = float(np.sqrt(np.mean((tr[["residual_x", "residual_y", "residual_z"]].to_numpy() / lim) ** 2)))
    eff_cmg = float(nom[("x2", m, "cmg_pes_gated")]["residual_normalized_rms"])
    rows.append((m, base, ung, gat, izh, eff_cmg, eff_izh))
    print(f"{m:9s}{base*1e3:9.3f}{ung*1e3:13.3f}{gat*1e3:11.3f}{izh*1e3:12.3f}   "
          f"{100*(1-ung/base):+7.1f} / {100*(1-gat/base):+7.1f} / {100*(1-izh/base):+7.1f}      {eff_cmg:.3f} / {eff_izh:.3f}")
b = gm([r[1] for r in rows])
print(f"{'geo':9s}{b*1e3:9.3f}{gm([r[2] for r in rows])*1e3:13.3f}{gm([r[3] for r in rows])*1e3:11.3f}{gm([r[4] for r in rows])*1e3:12.3f}   "
      f"{100*(1-gm([r[2] for r in rows])/b):+7.1f} / {100*(1-gm([r[3] for r in rows])/b):+7.1f} / {100*(1-gm([r[4] for r in rows])/b):+7.1f}")
sys.exit(0)
