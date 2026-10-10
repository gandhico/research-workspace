"""How much of the time does the residual sit on its authority rails (|residual| >= 0.98 * beta * limit)?  CMG vs Izhikevich, A3 gated runs.

Also: correlation of the per-mission mean normalized effort with the PD+ff error of that mission (does the residual shrink with the error?).
Writes results/izh_a3_rails.txt
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
R = HERE / "results"
MISSIONS = ["roll", "full3", "hard45", "hardstep", "yaw360"]
BETA = {"x2": 0.5, "cf2-rotor": 0.2}
IZH = {"x2": "b0p5", "cf2-rotor": "b0p2"}


def rail_fraction(run_dir: Path, beta: float):
    tr = pd.read_csv(run_dir / "trace.csv")
    lim = np.array(json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))["actuation"]["torque_limits_Nm"])
    r = np.abs(tr[[f"realized_residual_{a}" for a in "xyz"]].to_numpy()) / (beta * lim[None, :])
    t = tr["t"].to_numpy()
    m = t >= 2.0                     # skip the initial transient
    return float((r[m] >= 0.98).mean()), float(np.median(r[m])), float((r[m] <= 0.02).mean())


stats = {"izh_rails": [], "cmg_rails": [], "cmg_range": [], "izh_range": []}
lines = ["Fraction of samples (t >= 2 s, all three axes) with |realized residual| >= 0.98 beta l  |  median |residual|/(beta l)  |  fraction <= 0.02 (idle)\n",
         f"{'platform':10s}{'mission':10s}{'CMG rails':>11s}{'CMG med':>9s}{'CMG idle':>10s}{'Izh rails':>11s}{'Izh med':>9s}{'Izh idle':>10s}"]
for plat in ("x2", "cf2-rotor"):
    for m in MISSIONS:
        cm_dir = (R / "confirmatory" / "nominal" / plat / m / "cmg_pes_gated" / "load_1" / "seed_001") if plat == "x2" else \
            (R / "confirmatory_a2" / "a2_nominal" / plat / m / "cmg_pes_gated_b02" / "load_1" / "seed_001")
        iz_dir = R / "izh_a3" / "nominal" / plat / m / f"izh_pes_gated_{IZH[plat]}" / "load_1" / "seed_001"
        c, i = rail_fraction(cm_dir, BETA[plat]), rail_fraction(iz_dir, BETA[plat])
        stats["cmg_rails"].append(c[0])
        stats["izh_rails"].append(i[0])
        lines.append(f"{plat:10s}{m:10s}{c[0]:11.3f}{c[1]:9.3f}{c[2]:10.3f}{i[0]:11.3f}{i[1]:9.3f}{i[2]:10.3f}")
# effort vs baseline error across missions (Spearman via ranks)
nom = {(r["platform"], r["mission"], r["label"]): r for r in csv.DictReader((R / "final_nominal.csv").open(encoding="utf-8"))}
iz = {(r["platform"], r["mission"]): r for r in csv.DictReader((R / "results_izh_a3_all.csv").open(encoding="utf-8"))
      if r["campaign"] == "nominal" and r["label"].startswith("izh_pes_gated")}
lines.append("\nEffort (normalized rms) against the PD+ff error of the mission, ten cells (2 airframes x 5 missions):")
for name, get in (("CMG", lambda p, m: float(nom[(p, m, "cmg_pes_gated")]["residual_normalized_rms"])),
                  ("Izhikevich", lambda p, m: float(iz[(p, m)]["residual_normalized_rms"]))):
    for plat in ("x2", "cf2-rotor"):
        e = np.array([float(nom[(plat, m, "pdff_rho3")]["qerr_true_mean_rad"]) for m in MISSIONS])
        x = np.array([get(plat, m) for m in MISSIONS])
        rk = lambda v: np.argsort(np.argsort(v)).astype(float)
        rho = float(np.corrcoef(rk(e), rk(x))[0, 1])
        stats["cmg_range" if name == "CMG" else "izh_range"].append(float(x.max() / max(x.min(), 1e-12)))
        lines.append(f"  {name:11s}{plat:10s} effort by mission {np.round(x, 3).tolist()}   max/min {x.max() / max(x.min(), 1e-12):9.1f}   Spearman rho vs PD+ff error {rho:+.2f}")
text = "\n".join(lines)
(R / "izh_a3_rails.txt").write_text(text + "\n", encoding="utf-8")
(R / "izh_a3_rails.json").write_text(json.dumps({
    "izh_rails_min": min(stats["izh_rails"]), "izh_rails_max": max(stats["izh_rails"]), "cmg_rails_max": max(stats["cmg_rails"]),
    "cmg_effort_range_min": min(stats["cmg_range"]), "cmg_effort_range_max": max(stats["cmg_range"]),
    "izh_effort_range_max": max(stats["izh_range"])}, indent=2), encoding="utf-8")
print(text)
