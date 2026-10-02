"""Amendment A3 analysis: Izhikevich-PES vs CMG-PES vs PD+ff (rho = 3), same cells, paired seeds.

Reads   results/results_izh_a3_all.csv   (this campaign)   +  results/final_{nominal,noise,disturbance}.csv  (PD+ff and CMG arms)
        results/supplementary_izhikevich/x2/*/nengo_izhikevich_pes/summary.json  (X2 ungated, archived runner; bit-exact to the new runner)
Writes  results/izh_a3_numbers.json, results/IZH_A3_RESULTS.md
Reduction = 100 * (1 - error / error_PD+ff); positive = better than PD+ff.  Noise: geometric mean of the paired per-seed ratios.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
R = HERE / "results"
MISSIONS = ["roll", "full3", "hard45", "hardstep", "yaw360"]
NAMES = {"roll": "Roll", "full3": "Full3", "hard45": "Hard45", "hardstep": "Hardstep", "yaw360": "Yaw360", "hover": "Hover"}
PLAT = {"x2": "X2", "cf2-rotor": "CF2"}


def read(p):
    return list(csv.DictReader(p.open(encoding="utf-8")))


def f(r, k):
    v = r[k]
    return float(v) if v not in ("", None) else float("nan")


def index(rows):
    out = {}
    for r in rows:
        k = (r["platform"], r["mission"], r["label"], r["noise_level"], r["disturbance_level"], int(r["seed"]))
        if k in out:   # duplicates (A2 nominal + A2 confirm): must agree exactly
            assert abs(f(out[k], "qerr_true_mean_rad") - f(r, "qerr_true_mean_rad")) < 1e-12, k
        out[k] = r
    return out


NOM, NOI, DIS = (index(read(R / n)) for n in ("final_nominal.csv", "final_noise.csv", "final_disturbance.csv"))
IZ = index(read(R / "results_izh_a3_all.csv"))
BETA = {"x2": "b0p5", "cf2-rotor": "b0p2"}


def red(e, e0):
    return 100.0 * (1.0 - e / e0)


def izh(plat, m, gated, beta=None, **kw):
    lab = f"izh_pes_{'gated' if gated else 'ungated'}_{beta or BETA[plat]}"
    return IZ.get((plat, m, lab, kw.get("noise", "none"), kw.get("dist", "none"), kw.get("seed", 1)))


def arch_x2(m):
    p = R / "supplementary_izhikevich" / "x2" / m / "nengo_izhikevich_pes" / "summary.json"
    return json.loads(p.read_text(encoding="utf-8"))["qerr_mean_rad"]


num = {"nominal": {}, "noise": {}, "disturbance": {}, "hardstep_cells": {}}
md = []

# ----------------------------------------------------------------------------------------------- nominal
md.append("## Nominal (45 s, no noise): 45-s mean true-attitude error [mrad] and reduction vs PD+ff rho=3 [%]\n")
md.append("| platform | mission | PD+ff | CMG gated | Izh. gated | Izh. ungated | CMG red. | Izh. gated red. | Izh. ungated red. | Izh. gate blocked | Izh. effort (norm. rms) | CMG effort |")
md.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for plat in ("x2", "cf2-rotor"):
    for m in MISSIONS:
        pd_ = f(NOM[(plat, m, "pdff_rho3", "none", "none", 1)], "qerr_true_mean_rad")
        cm = NOM[(plat, m, "cmg_pes_gated", "none", "none", 1)]
        ig = izh(plat, m, True)
        e_ig = f(ig, "qerr_true_mean_rad")
        if plat == "x2":
            e_iu, src = arch_x2(m), "archived runner"
        else:
            iu = izh(plat, m, False, "b0p2") if m == "hardstep" else None
            e_iu, src = (f(iu, "qerr_true_mean_rad") if iu else float("nan")), "new runner"
        row = {"pdff_mrad": pd_ * 1e3, "cmg_gated_mrad": f(cm, "qerr_true_mean_rad") * 1e3, "izh_gated_mrad": e_ig * 1e3,
               "izh_ungated_mrad": e_iu * 1e3, "cmg_red": red(f(cm, "qerr_true_mean_rad"), pd_), "izh_gated_red": red(e_ig, pd_),
               "izh_ungated_red": red(e_iu, pd_), "izh_blocked": f(ig, "gate_blocked_fraction"),
               "izh_effort": f(ig, "residual_normalized_rms"), "cmg_effort": f(cm, "residual_normalized_rms"),
               "izh_qmax": f(ig, "qerr_true_max_rad"), "izh_rotor_sat": f(ig, "rotor_sat_fraction"), "izh_box_sat": f(ig, "torque_box_sat_fraction"),
               "ungated_source": src}
        num["nominal"][f"{plat}/{m}"] = row
        md.append(f"| {PLAT[plat]} | {NAMES[m]} | {row['pdff_mrad']:.3f} | {row['cmg_gated_mrad']:.3f} | {row['izh_gated_mrad']:.3f} | "
                  f"{'-' if np.isnan(e_iu) else format(row['izh_ungated_mrad'], '.3f')} | {row['cmg_red']:+.1f} | {row['izh_gated_red']:+.1f} | "
                  f"{'-' if np.isnan(e_iu) else format(row['izh_ungated_red'], '+.1f')} | {row['izh_blocked']:.3f} | {row['izh_effort']:.3f} | {row['cmg_effort']:.3f} |")

# Hardstep cells, all arms
md.append("\n## Hardstep: every arm, both airframes (mrad; reduction vs PD+ff)\n")
md.append("| platform | arm | beta | error | reduction | blocked share | rotor sat. | box sat. |")
md.append("|---|---|---:|---:|---:|---:|---:|---:|")
for plat in ("x2", "cf2-rotor"):
    pd_ = f(NOM[(plat, "hardstep", "pdff_rho3", "none", "none", 1)], "qerr_true_mean_rad")
    arms = [("PD+ff", None, None)]
    arms += [("CMG ungated (table beta)", "cmg_pes_table", NOM), ("CMG gated", "cmg_pes_gated", NOM)]
    for name, lab, src in arms:
        if lab is None:
            continue
        r = src[(plat, "hardstep", lab, "none", "none", 1)]
        e = f(r, "qerr_true_mean_rad")
        md.append(f"| {PLAT[plat]} | {name} | {r['beta']} | {e * 1e3:.3f} | {red(e, pd_):+.1f} | {f(r, 'gate_blocked_fraction'):.3f} | "
                  f"{f(r, 'rotor_sat_fraction'):.3f} | {f(r, 'torque_box_sat_fraction'):.3f} |")
    for (lab, beta, gated) in ([("izh_pes_ungated_b0p5", "0.5", False), ("izh_pes_gated_b0p5", "0.5", True)] if plat == "x2" else
                               [("izh_pes_ungated_b0p05", "0.05", False), ("izh_pes_ungated_b0p2", "0.2", False), ("izh_pes_gated_b0p2", "0.2", True)]):
        r = IZ[(plat, "hardstep", lab, "none", "none", 1)]
        e = f(r, "qerr_true_mean_rad")
        num["hardstep_cells"][f"{plat}/{lab}"] = {"err_mrad": e * 1e3, "red": red(e, pd_), "blocked": f(r, "gate_blocked_fraction"),
                                                   "rotor_sat": f(r, "rotor_sat_fraction"), "box_sat": f(r, "torque_box_sat_fraction")}
        md.append(f"| {PLAT[plat]} | Izhikevich {'gated' if gated else 'ungated'} | {beta} | {e * 1e3:.3f} | {red(e, pd_):+.1f} | "
                  f"{f(r, 'gate_blocked_fraction'):.3f} | {f(r, 'rotor_sat_fraction'):.3f} | {f(r, 'torque_box_sat_fraction'):.3f} |")

# ----------------------------------------------------------------------------------------------- noise
md.append("\n## Realistic noise (0.020 rad / 0.050 rad/s), seeds 1-3, paired with PD+ff: geometric-mean reduction [%] and per-seed values\n")
md.append("| platform | mission | PD+ff [mrad] (seeds 1-3) | Izh. gated [mrad] | Izh. per-seed red. | Izh. GM red. | CMG GM red. (same 3 seeds) | CMG GM red. (10 seeds) | Izh. vs CMG ratio (GM) |")
md.append("|---|---|---|---|---|---:|---:|---:|---:|")
for plat in ("x2", "cf2-rotor"):
    for m in ("roll", "hard45", "hardstep"):
        pd_ = np.array([f(NOI[(plat, m, "pdff_rho3", "realistic", "none", s)], "qerr_true_mean_rad") for s in (1, 2, 3)])
        cm3 = np.array([f(NOI[(plat, m, "cmg_pes_gated", "realistic", "none", s)], "qerr_true_mean_rad") for s in (1, 2, 3)])
        pd10 = np.array([f(NOI[(plat, m, "pdff_rho3", "realistic", "none", s)], "qerr_true_mean_rad") for s in range(1, 11)])
        cm10 = np.array([f(NOI[(plat, m, "cmg_pes_gated", "realistic", "none", s)], "qerr_true_mean_rad") for s in range(1, 11)])
        iz = np.array([f(izh(plat, m, True, noise="realistic", seed=s), "qerr_true_mean_rad") for s in (1, 2, 3)])
        gm = lambda x: float(np.exp(np.mean(np.log(x))))
        r_iz, r_cm3, r_cm10 = iz / pd_, cm3 / pd_, cm10 / pd10
        row = {"pdff_mrad": (pd_ * 1e3).tolist(), "izh_mrad": (iz * 1e3).tolist(), "izh_red_seed": (100 * (1 - r_iz)).tolist(),
               "izh_gm_red": 100 * (1 - gm(r_iz)), "cmg_gm_red_3": 100 * (1 - gm(r_cm3)), "cmg_gm_red_10": 100 * (1 - gm(r_cm10)),
               "izh_over_cmg": gm(iz / cm3),
               "izh_effort": [f(izh(plat, m, True, noise="realistic", seed=s), "residual_normalized_rms") for s in (1, 2, 3)],
               "izh_qmax": [f(izh(plat, m, True, noise="realistic", seed=s), "qerr_true_max_rad") for s in (1, 2, 3)]}
        num["noise"][f"{plat}/{m}"] = row
        md.append(f"| {PLAT[plat]} | {NAMES[m]} | {', '.join(f'{x:.2f}' for x in pd_ * 1e3)} | {', '.join(f'{x:.2f}' for x in iz * 1e3)} | "
                  f"{', '.join(f'{x:+.1f}' for x in row['izh_red_seed'])} | {row['izh_gm_red']:+.1f} | {row['cmg_gm_red_3']:+.1f} | {row['cmg_gm_red_10']:+.1f} | {row['izh_over_cmg']:.2f} |")

# ----------------------------------------------------------------------------------------------- disturbance
md.append("\n## Hover, intermittent torque bursts (1x amplitude), gated: burst-phase and quiet-phase mean error [mrad] and reduction vs PD+ff\n")
md.append("| platform | PD+ff burst | PD+ff quiet | CMG burst red. | CMG quiet red. | Izh. burst | Izh. quiet | Izh. burst red. | Izh. quiet red. |")
md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for plat in ("x2", "cf2-rotor"):
    p = DIS[(plat, "hover", "pdff_rho3", "none", "x1", 1)]
    c = DIS[(plat, "hover", "cmg_pes_gated", "none", "x1", 1)]
    i = izh(plat, "hover", True, dist="x1")
    pa, pq = f(p, "disturbance_active_mean_rad"), f(p, "disturbance_quiet_mean_rad")
    row = {"pdff_burst": pa * 1e3, "pdff_quiet": pq * 1e3, "cmg_burst_red": red(f(c, "disturbance_active_mean_rad"), pa),
           "cmg_quiet_red": red(f(c, "disturbance_quiet_mean_rad"), pq), "izh_burst": f(i, "disturbance_active_mean_rad") * 1e3,
           "izh_quiet": f(i, "disturbance_quiet_mean_rad") * 1e3, "izh_burst_red": red(f(i, "disturbance_active_mean_rad"), pa),
           "izh_quiet_red": red(f(i, "disturbance_quiet_mean_rad"), pq), "izh_effort": f(i, "residual_normalized_rms"),
           "cmg_effort": f(c, "residual_normalized_rms")}
    num["disturbance"][plat] = row
    md.append(f"| {PLAT[plat]} | {row['pdff_burst']:.3f} | {row['pdff_quiet']:.3f} | {row['cmg_burst_red']:+.1f} | {row['cmg_quiet_red']:+.1f} | "
              f"{row['izh_burst']:.3f} | {row['izh_quiet']:.3f} | {row['izh_burst_red']:+.1f} | {row['izh_quiet_red']:+.1f} |")


# ----------------------------------------------------------------------------------------------- summaries + priors
def gmean(x):
    return float(np.exp(np.mean(np.log(x))))


md.append("\n## Five-mission summaries (noise-free, rho = 3)\n")
md.append("| platform | geo PD+ff [mrad] | geo CMG gated | geo Izh. gated | CMG geo red. [%] | Izh. geo red. [%] | mean effort CMG | mean effort Izh. | Izh. effort / CMG effort |")
md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
num["summary"] = {}
for plat in ("x2", "cf2-rotor"):
    e_pd = [f(NOM[(plat, m, "pdff_rho3", "none", "none", 1)], "qerr_true_mean_rad") for m in MISSIONS]
    e_cm = [f(NOM[(plat, m, "cmg_pes_gated", "none", "none", 1)], "qerr_true_mean_rad") for m in MISSIONS]
    e_iz = [f(izh(plat, m, True), "qerr_true_mean_rad") for m in MISSIONS]
    x_cm = [f(NOM[(plat, m, "cmg_pes_gated", "none", "none", 1)], "residual_normalized_rms") for m in MISSIONS]
    x_iz = [f(izh(plat, m, True), "residual_normalized_rms") for m in MISSIONS]
    row = {"geo_pd_mrad": gmean(e_pd) * 1e3, "geo_cmg_mrad": gmean(e_cm) * 1e3, "geo_izh_mrad": gmean(e_iz) * 1e3,
           "geo_red_cmg": red(gmean(e_cm), gmean(e_pd)), "geo_red_izh": red(gmean(e_iz), gmean(e_pd)),
           "effort_cmg": float(np.mean(x_cm)), "effort_izh": float(np.mean(x_iz)), "effort_ratio": float(np.mean(x_iz) / np.mean(x_cm)),
           "effort_cmg_by_mission": x_cm, "effort_izh_by_mission": x_iz}
    num["summary"][plat] = row
    md.append(f"| {PLAT[plat]} | {row['geo_pd_mrad']:.2f} | {row['geo_cmg_mrad']:.2f} | {row['geo_izh_mrad']:.2f} | {row['geo_red_cmg']:+.1f} | {row['geo_red_izh']:+.1f} | "
              f"{row['effort_cmg']:.3f} | {row['effort_izh']:.3f} | {row['effort_ratio']:.1f} |")

md.append("\n## Gate blocked fraction of the Izhikevich gated nominal runs (more digits)\n")
md.append("| platform | " + " | ".join(NAMES[m] for m in MISSIONS) + " |")
md.append("|---|" + "---:|" * len(MISSIONS))
for plat in ("x2", "cf2-rotor"):
    md.append(f"| {PLAT[plat]} | " + " | ".join(f"{f(izh(plat, m, True), 'gate_blocked_fraction'):.5f}" for m in MISSIONS) + " |")

md.append("\n## First reading of the priors (raw ranking, before amendment A3.2; superseded by izh_a3_priors.md, which applies the floor)\n")
p1 = [(k, v["izh_gated_red"], v["cmg_red"]) for k, v in num["nominal"].items() if not v["izh_gated_red"] < v["cmg_red"]]
md.append(f"- **P1** (Izhikevich reduction below CMG's in every nominal cell): {'holds in 10/10 cells' if not p1 else 'fails in ' + str(len(p1)) + '/10: ' + '; '.join(f'{k}: Izh {a:+.1f} vs CMG {b:+.1f}' for k, a, b in p1)}")
p2r = [k for k in ("x2/roll", "cf2-rotor/roll") if not (num["noise"][k]["izh_gm_red"] < num["noise"][k]["cmg_gm_red_3"] and num["noise"][k]["izh_gm_red"] < 0)]
p2h = [(k, num["noise"][k]["izh_gm_red"], num["noise"][k]["cmg_gm_red_3"]) for k in ("x2/hard45", "cf2-rotor/hard45") if num["noise"][k]["izh_gm_red"] > num["noise"][k]["cmg_gm_red_3"]]
md.append(f"- **P2** (noise: degrades Roll; does not beat CMG on Hard45): Roll degraded on both airframes: {not p2r}; Hard45 not beaten: {'yes, both' if not p2h else 'no - ' + '; '.join(f'{k}: Izh {a:+.1f} vs CMG {b:+.1f}' for k, a, b in p2h)}")
h = num["hardstep_cells"]["x2/izh_pes_gated_b0p5"]["red"]
md.append(f"- **P3** (gate reduces the X2 Hardstep loss, does not make it a gain): ungated -16.9 -> gated {h:+.1f}: {'holds' if -16.9 < h < 0 else 'fails'}")
safe = []
for m in ("roll", "hard45", "hardstep"):
    for s_ in (1, 2, 3):
        r = izh("cf2-rotor", m, True, noise="realistic", seed=s_)
        safe.append((f(r, "qerr_true_mean_rad") < 1.0) and (f(r, "rotor_sat_fraction") < 0.5))
md.append(f"- **P4** (CF2 beta .2 stays safe under noise; safe = every mean error < 1 rad and rotor saturation < 0.5, the sweep criterion): {sum(safe)}/9 cells safe")

(R / "izh_a3_numbers.json").write_text(json.dumps(num, indent=2), encoding="utf-8")
(R / "IZH_A3_RESULTS.md").write_text("# Izhikevich-PES vs CMG-PES under the CMG protocol (amendment A3, reduced grid)\n\n" + "\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
