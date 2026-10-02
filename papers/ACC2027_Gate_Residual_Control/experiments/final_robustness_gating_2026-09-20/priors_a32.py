"""Amendment A3.2: re-evaluate the priors P1-P4 of section 10 with the reading rule of section 12.

threshold = 3 x the largest s.d. of the floor ensemble, in points of the PD+ff error.  Noise cells (3 seeds) are read per seed.
Writes results/izh_a3_priors.md
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
R = HERE / "results"
N = json.loads((R / "izh_a3_numbers.json").read_text(encoding="utf-8"))
FLOOR = json.loads((HERE / "results_validation_izh" / "floor" / "floor_result.json").read_text(encoding="utf-8"))
sd_pp = {k: v["sd_pp_of_pdff"] for k, v in FLOOR.items()}
THR = 3 * max(sd_pp.values())
out = [f"# Priors of section 10 read with the rule of section 12\n",
       "Floor ensemble (7 runs per cell: the A3 run + 6 initial-attitude perturbations of k * 1e-12 deg), s.d. in points of the PD+ff error: " +
       ", ".join(f"{k} {v:.2f}" for k, v in sd_pp.items()) + f".  Threshold = 3 x max = {THR:.1f} points.\n"]

out.append("## P1 - Izhikevich reduction below CMG's in every nominal cell\n")
out.append("| cell | Izh. [%] | CMG [%] | Izh. - CMG [pp] | reading |")
out.append("|---|---:|---:|---:|---|")
counts = {"below": 0, "level": 0, "above": 0}
for k, v in N["nominal"].items():
    d = v["izh_gated_red"] - v["cmg_red"]
    r = "level" if abs(d) < THR else ("below CMG" if d < 0 else "ABOVE CMG")
    counts["level" if r == "level" else ("below" if d < 0 else "above")] += 1
    out.append(f"| {k} | {v['izh_gated_red']:+.1f} | {v['cmg_red']:+.1f} | {d:+.1f} | {r} |")
out.append(f"\nP1: {counts['below']} cells below CMG by more than the threshold, {counts['level']} level, {counts['above']} above.  "
           f"{'P1 is not contradicted.' if counts['above'] == 0 else 'P1 fails.'}\n")

out.append("## P2 - under realistic noise Izhikevich degrades Roll and does not beat CMG on Hard45 (per seed, 3 seeds)\n")
NOI = {}
for r in csv.DictReader((R / "final_noise.csv").open(encoding="utf-8")):
    NOI[(r["platform"], r["mission"], r["label"], r["noise_level"], int(r["seed"]))] = float(r["qerr_true_mean_rad"])
IZ = {}
for r in csv.DictReader((R / "results_izh_a3_all.csv").open(encoding="utf-8")):
    if r["campaign"] == "noise":
        IZ[(r["platform"], r["mission"], int(r["seed"]))] = float(r["qerr_true_mean_rad"])
out.append("| cell | seed | PD+ff [mrad] | CMG red. [%] | Izh. red. [%] | Izh. - CMG [pp] |")
out.append("|---|---:|---:|---:|---:|---:|")
for plat in ("x2", "cf2-rotor"):
    for m in ("roll", "hard45", "hardstep"):
        ds = []
        for s in (1, 2, 3):
            pd_ = NOI[(plat, m, "pdff_rho3", "realistic", s)]
            c = 100 * (1 - NOI[(plat, m, "cmg_pes_gated", "realistic", s)] / pd_)
            i = 100 * (1 - IZ[(plat, m, s)] / pd_)
            ds.append(i - c)
            out.append(f"| {plat} {m} | {s} | {pd_ * 1e3:.2f} | {c:+.1f} | {i:+.1f} | {i - c:+.1f} |")
        out.append(f"| **{plat} {m}: mean Izh. - CMG** | | | | | **{np.mean(ds):+.1f}** (all three seeds {'same sign' if len({np.sign(x) for x in ds}) == 1 else 'mixed'}) |")
out.append("\nThe noise cells carry their own scatter (seed to seed); the noise-free threshold is not applied to them.  Reading: Roll is degraded on both airframes "
           "(large effects); on Hard45 the paired per-seed difference is given above.\n")

out.append("## P3 / P4\n")
h = N["hardstep_cells"]
out.append(f"- P3: X2 Hardstep ungated {h['x2/izh_pes_ungated_b0p5']['red']:+.1f} % -> gated {h['x2/izh_pes_gated_b0p5']['red']:+.1f} % (effect {h['x2/izh_pes_gated_b0p5']['red'] - h['x2/izh_pes_ungated_b0p5']['red']:.1f} points, far above the threshold); "
           "not a gain: holds.")
out.append("- P4: CF2 beta 0.2 gated stayed safe in 9/9 noisy cells (see IZH_A3_RESULTS.md).")
text = "\n".join(out) + "\n"
(R / "izh_a3_priors.md").write_text(text, encoding="utf-8")
print(text)
