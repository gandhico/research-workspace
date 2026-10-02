"""A2 selection stage: noise-free CF2 five-mission geometric-mean reduction of each SAFE variant (PREREGISTRATION §9)."""
import csv
import glob
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "results"
M = ("roll", "full3", "hard45", "hardstep", "yaw360")
nom = {(r["platform"], r["mission"], r["label"]): float(r["qerr_true_mean_rad"])
       for r in csv.DictReader((R / "results_nominal.csv").open())}
gm = lambda xs: math.exp(sum(math.log(x) for x in xs) / len(xs))


def val(variant, mission):
    fs = glob.glob(str(R / "confirmatory_a2" / "a2_nominal" / "cf2-rotor" / mission / f"cmg_pes_{variant}" / "*" / "seed_001" / "summary.json"))
    return json.load(open(fs[0]))["metrics"]["qerr_true_mean_rad"] if fs else None


best, best_geo = None, -1e9
print("CF2, noise-free, PD+ff rho=3 baseline; reduction [%] per mission and geometric mean")
print(f"{'variant':12s}" + "".join(f"{m:>9s}" for m in M) + f"{'geo':>9s}")
for v in ("gated_b02", "gated_b01"):
    vs = [val(v, m) for m in M]
    if any(x is None for x in vs):
        print(f"{v:12s} incomplete")
        continue
    red = [100 * (1 - x / nom[("cf2-rotor", m, "pdff_rho3")]) for x, m in zip(vs, M)]
    geo = 100 * (1 - gm(vs) / gm([nom[("cf2-rotor", m, "pdff_rho3")] for m in M]))
    print(f"{v:12s}" + "".join(f"{r:9.1f}" for r in red) + f"{geo:9.1f}")
    if geo > best_geo:
        best, best_geo = v, geo
print("\nreference (noise-free): beta=.05 ungated 6.5 % | beta=.5 gated 36.5 % (diverges under noise)")
print("SELECTED by the pre-registered rule:", best, f"({best_geo:.1f} %)" if best else "")
sys.exit(0)
