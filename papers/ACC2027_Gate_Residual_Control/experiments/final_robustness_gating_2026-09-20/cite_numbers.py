"""Every number quoted in the Hardstep / gating text, computed from the campaign CSVs and traces."""
import csv
import math
import sys
from pathlib import Path

import numpy as np

import figlib as F

HERE = Path(__file__).resolve().parent
nom = {(r["platform"], r["mission"], r["label"]): r for r in csv.DictReader((HERE / "results" / "final_nominal.csv").open())}
M = ("roll", "full3", "hard45", "yaw360")

# This script documents the beta = 0.5 gate (X2 and CF2).  In the final tables CF2's beta = 0.5 gated arm is labelled
# `cmg_pes_gated_b05` (the label `cmg_pes_gated` there is the selected beta = 0.2), so map it back for this analysis.
CF2_B02 = {m: nom[("cf2-rotor", m, "cmg_pes_gated")] for m in ("roll", "full3", "hard45", "hardstep", "yaw360") if ("cf2-rotor", m, "cmg_pes_gated") in nom}
for _m in ("roll", "full3", "hard45", "hardstep", "yaw360"):
    nom[("cf2-rotor", _m, "cmg_pes_gated")] = nom[("cf2-rotor", _m, "cmg_pes_gated_b05")]

# 1. gated vs the ungated beta = 0.5 arm on the eight non-Hardstep cells
worst = 0.0
for p in ("x2", "cf2-rotor"):
    ref_arm = "cmg_pes_table" if p == "x2" else "cmg_pes_b05_ungated"   # X2 table beta is already 0.5
    for m in M:
        a, b = float(nom[(p, m, ref_arm)]["qerr_true_mean_rad"]), float(nom[(p, m, "cmg_pes_gated")]["qerr_true_mean_rad"])
        rel = 100 * abs(b - a) / a
        worst = max(worst, rel)
        print(f"  {p:9s}{m:8s} ungated(b=.5) {a*1e3:8.4f}  gated {b*1e3:8.4f}  |diff| {rel:.4f} %  gate acts {float(nom[(p, m, 'cmg_pes_gated')]['gate_blocked_fraction'])*100:.3f} % of samples")
print(f"worst gated-vs-ungated difference over the 8 non-Hardstep cells: {worst:.4f} %")
print("gate share on Hardstep:", {p: round(100 * float(nom[(p, 'hardstep', 'cmg_pes_gated')]['gate_blocked_fraction']), 1) for p in ('x2', 'cf2-rotor')})
print("max gate share elsewhere: %.3f %%" % max(100 * float(nom[(p, m, 'cmg_pes_gated')]['gate_blocked_fraction']) for p in ('x2', 'cf2-rotor') for m in M))

# 2. Hard45 initial transient for the Fig. 4 caption
df, _ = F.load(HERE / "results/confirmatory/nominal/x2/hard45/pdff_rho3/nominal/seed_001")
e = df.qerr_true_rad.to_numpy() * 1e3
t = df.t.to_numpy()
print(f"\nX2 Hard45 PD+ff: initial error {e[0]:.0f} mrad; first time below 25 mrad: {t[np.argmax(e < 25)]:.3f} s; max after 1 s: {e[t > 1].max():.1f} mrad")

# 3. geometric means and Hardstep quantities quoted
def gm(xs): return math.exp(sum(math.log(x) for x in xs) / len(xs))
for p in ("x2", "cf2-rotor"):
    ms = ("roll", "full3", "hard45", "hardstep", "yaw360")
    b = gm([float(nom[(p, m, "pdff_rho3")]["qerr_true_mean_rad"]) for m in ms])
    for arm in ("cmg_pes_table", "cmg_pes_gated"):
        c = gm([float(nom[(p, m, arm)]["qerr_true_mean_rad"]) for m in ms])
        print(f"{p:9s}{arm:15s} geo {b*1e3:.3f} -> {c*1e3:.3f} mrad  ({100*(1-c/b):.2f} %)")
r = nom[("cf2-rotor", "hardstep", "cmg_pes_b05_ungated")]
print(f"CF2 Hardstep beta=.5 ungated: mean {math.degrees(float(r['qerr_true_mean_rad'])):.1f} deg, rotor sat {float(r['rotor_sat_fraction'])*100:.0f} %")
sys.exit(0)
