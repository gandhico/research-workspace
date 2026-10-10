"""Compare the corrected fixed-PD Izhikevich-PES results (2026-09-24) against the currently-published Table II numbers.

Table II's "Original fixed PD baseline" block (PD row: 50.56/303.28/294.08/454.53/75.86 X2, 51.34/288.38/285.45/426.18/75.81
CF2, geo 173.12/168.68) is unaffected -- it's the classical controller, no augmentor. The Izhikevich-PES row is what used
the buggy rate; recomputed here from results/izh_fixed_pd_corrected_2026-09-24/.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "izh_fixed_pd_corrected_2026-09-24"
MISSIONS = ["roll", "full3", "hard45", "hardstep", "yaw360"]
NAMES = {"roll": "Roll", "full3": "Full3", "hard45": "Hard45", "hardstep": "Hardstep", "yaw360": "Yaw360"}
# published Table II "Original fixed PD baseline" PD row (10^-3 rad) -- classical controller, unaffected by the bug
PD = {"x2": [50.56, 303.28, 294.08, 454.53, 75.86], "cf2-rotor": [51.34, 288.38, 285.45, 426.18, 75.81]}
# currently-published (buggy-rate) Izhikevich-PES fixed-PD row, for reference
PUBLISHED_IZH_RED = {"x2": [51.1, 52.3, 49.7, 22.6, 60.7], "cf2-rotor": [51.5, 51.9, 50.3, 21.4, 56.4]}
PUBLISHED_GEO = {"x2": 48.6, "cf2-rotor": 47.5}


def gm(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def red(b, c):
    return 100.0 * (1.0 - c / b)


print(f"{'platform':10s}{'mission':10s}{'PD (pub.)':>11s}{'Izh corr.':>11s}{'red corr. %':>13s}{'red published %':>17s}{'delta pp':>10s}")
new_err = {}
for plat in ("x2", "cf2-rotor"):
    errs = []
    for i, m in enumerate(MISSIONS):
        s = json.loads((OUT / plat / m / "summary.json").read_text(encoding="utf-8"))
        e = s["qerr_mean_rad"] * 1e3
        errs.append(e)
        r = red(PD[plat][i], e)
        print(f"{plat:10s}{NAMES[m]:10s}{PD[plat][i]:11.2f}{e:11.3f}{r:13.1f}{PUBLISHED_IZH_RED[plat][i]:17.1f}{r - PUBLISHED_IZH_RED[plat][i]:10.1f}")
    new_err[plat] = errs
    g = red(gm(PD[plat]), gm(errs))
    print(f"{plat:10s}{'geo':10s}{gm(PD[plat]):11.2f}{gm(errs):11.3f}{g:13.1f}{PUBLISHED_GEO[plat]:17.1f}{g - PUBLISHED_GEO[plat]:10.1f}")
    print()
