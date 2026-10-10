"""A2 confirmation (PREREGISTRATION §9 + addenda): held-out evaluation of CF2 gated beta = 0.2.

(i)   no held-out run diverges: CF2 Hardstep, moderate seeds 3-5 and realistic seeds 1-10, mean error < 2 x PD+ff (same seed)
(ii') no nominal CF2 cell is worse than the previously reported configuration (beta = 0.05, ungated)
(iii) X2 keeps beta = 0.5 and is unchanged by construction (nothing to run)
"""
import csv
import glob
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "results"
nom = {(r["platform"], r["mission"], r["label"]): float(r["qerr_true_mean_rad"]) for r in csv.DictReader((R / "final_nominal.csv").open())}
noise = {(r["noise_level"], r["platform"], r["mission"], int(r["seed"]), r["label"]): float(r["qerr_true_mean_rad"])
         for r in csv.DictReader((R / "final_noise.csv").open())}

print("(i) held-out CF2 Hardstep, gated beta = 0.2 vs PD+ff (same seed, same noise stream)")
ok_i = True
for lvl, seeds in (("moderate", (3, 4, 5)), ("realistic", tuple(range(1, 11)))):
    ratios = []
    for s in seeds:
        b = noise[(lvl, "cf2-rotor", "hardstep", s, "pdff_rho3")]
        c = noise[(lvl, "cf2-rotor", "hardstep", s, "cmg_pes_gated")]
        ratios.append(c / b)
    ok_i &= max(ratios) < 2.0
    print(f"   {lvl:9s} seeds {seeds[0]}-{seeds[-1]}: ratio min {min(ratios):.3f}  max {max(ratios):.3f}  -> {'OK' if max(ratios) < 2 else 'DIVERGES'}")

print("\n(ii') nominal CF2 cells: gated beta = 0.2 vs published beta = 0.05 ungated  (error [mrad], lower is better)")
ok_ii = True
for m in ("roll", "full3", "hard45", "hardstep", "yaw360"):
    new, old = nom[("cf2-rotor", m, "cmg_pes_gated")], nom[("cf2-rotor", m, "cmg_pes_table")]
    ok_ii &= new <= old * 1.000001
    print(f"   {m:9s} beta=.2 gated {new * 1e3:9.3f}   beta=.05 ungated {old * 1e3:9.3f}   -> {'not worse' if new <= old else 'WORSE'}")
print("\n(iii) X2 keeps beta = 0.5: unchanged by construction")
verdict = ok_i and ok_ii
print("\nA2 verdict: ", "ADOPT gated beta = 0.2 for CF2" if verdict else "DO NOT ADOPT")
sys.exit(0 if verdict else 1)
