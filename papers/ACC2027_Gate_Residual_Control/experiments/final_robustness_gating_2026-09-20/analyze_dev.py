"""Exploratory X2-Hardstep gate-variant screen (PREREGISTRATION section 5).  NOT confirmatory.

Evaluates the promotion rule literally:
  (1) mean true error below PD+ff by >= 2 % AND below the exact-saturation output gate;
  (2)/(3) are only evaluated for a variant that passes (1), in a separate declared run.
"""
import csv
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
nom = {(r["platform"], r["mission"], r["label"]): r for r in csv.DictReader((HERE / "results" / "results_nominal.csv").open())}
dev = list(csv.DictReader((HERE / "results" / "results_hardstep-development.csv").open()))

base = nom[("x2", "hardstep", "pdff_rho3")]
gate1 = nom[("x2", "hardstep", "cmg_pes_gated")]
b = float(base["qerr_true_mean_rad"])
g1 = float(gate1["qerr_true_mean_rad"])
deg = math.degrees


def line(name, r):
    m = float(r["qerr_true_mean_rad"])
    return (f"  {name:34s}{deg(m):8.3f}{100*(1-m/b):+9.2f}%{deg(float(r['hardstep_settled_mean_rad'])):9.3f}"
            f"{float(r['hardstep_settling_time_5deg_s']):9.3f}{float(r['rotor_sat_fraction']):9.3f}"
            f"{float(r['gate_blocked_fraction']):8.3f}"), m


print("X2 Hardstep, rho=3, beta=0.5  (exploratory variants; confirmatory rows for reference)")
print(f"  {'variant':34s}{'mean[deg]':>8s}{'vs PD+ff':>10s}{'settled':>9s}{'t_settle':>9s}{'rotorSat':>9s}{'gated':>8s}")
print(line("PD+ff (baseline)", base)[0])
print(line("gate 1.0, output-only  [CONFIRMATORY]", gate1)[0])
passers = []
for r in sorted(dev, key=lambda r: (r["label"], -float(r["gate_load_threshold"]))):
    kind = "output-only" if r["label"].endswith("_gate") else "output + freeze PES"
    txt, m = line(f"gate {float(r['gate_load_threshold']):g}, {kind}", r)
    ok = (100 * (1 - m / b) >= 2.0) and (m < g1)
    print(txt + ("   <-- passes rule (1)" if ok else ""))
    if ok:
        passers.append(r["case_id"])
print()
print("promotion rule (1) passers:", passers if passers else "NONE")
print("=> exact-saturation output gate stays canonical." if not passers else "=> a confirmatory run is required (rule 2/3).")
sys.exit(0)
