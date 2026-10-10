"""Amendment A2: evaluate the development stage against the pre-declared selection rule (section 9).

safe  :=  in BOTH development seeds the mean true error of the variant is < 2 x that of PD+ff (same seed, same noise)
choose:=  among safe variants, the largest noise-free CF2 geometric-mean reduction (needs the `nominal` stage)
"""
import csv
import glob
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "results"
VARIANTS = ("rotorflag", "starvation", "gated_b02", "gated_b01")


def load_dev(variant, seed):
    d = R / "development_only" / "a2_dev" / "cf2-rotor" / "hardstep" / f"cmg_pes_{variant}"
    fs = glob.glob(str(d / "*" / f"seed_{seed:03d}" / "summary.json"))
    return json.load(open(fs[0])) if fs else None


def base(seed):
    f = R / "confirmatory" / "noise" / "cf2-rotor" / "hardstep" / "pdff_rho3" / "noise_moderate" / f"seed_{seed:03d}" / "summary.json"
    return json.load(open(f))


print("CF2 Hardstep, moderate noise, development seeds 1 and 2")
print(f"{'variant':12s}{'seed':>5s}{'PD+ff [deg]':>13s}{'variant [deg]':>15s}{'ratio':>8s}{'rotorSat':>10s}{'gate share':>11s}")
safe = []
for v in VARIANTS:
    ok = True
    for s in (1, 2):
        r = load_dev(v, s)
        if r is None:
            print(f"{v:12s}{s:5d}  (missing)")
            ok = False
            continue
        b = base(s)["metrics"]["qerr_true_mean_rad"]
        c = r["metrics"]["qerr_true_mean_rad"]
        ok &= c < 2 * b
        print(f"{v:12s}{s:5d}{math.degrees(b):13.2f}{math.degrees(c):15.2f}{c / b:8.2f}"
              f"{r['actuation']['rotor_saturation_fraction_any_rotor']:10.3f}{r['output_gate']['blocked_fraction_any_axis']:11.3f}")
    if ok:
        safe.append(v)
print("\nsafe variants (rule):", safe or "NONE")
sys.exit(0)
