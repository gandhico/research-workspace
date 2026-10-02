"""Recompute every checkable number in the ACC 2027 paper from the raw run outputs and compare it with the paper text.

Read-only: runs no simulation, edits nothing. Takes a few seconds.
    .venv\\Scripts\\python.exe reproduce\\verify_acc2027_claims.py
Writes reproduce/claims_check.md and reproduce/claims_check.csv, exits 1 if any check mismatches.
"""
from __future__ import annotations

import csv
import json
import math
import re
import statistics as st
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "experiments"
FR = E / "final_robustness_gating_2026-09-20"
NB = E / "neuron_basis_decisive_2026-09-24"
NN = E / "nengo_nef_replication_2026-08-29"
BR = E / "baseline_restatement_2026-09-16"
M = ("roll", "full3", "hard45", "hardstep", "yaw360")
X, C = "x2", "cf2-rotor"
gm = lambda v: math.exp(sum(math.log(x) for x in v) / len(v))
red = lambda b, c: 100.0 * (1.0 - c / b)
f1 = lambda v: f"{v:.1f}"
rows: list[dict] = []


def check(section: str, claim: str, paper: str, value: str, source: str) -> None:
    rows.append(dict(section=section, claim=claim, paper=paper, recomputed=value, status="OK" if paper == value else "MISMATCH", source=source))


def csv_rows(p: Path) -> list[dict]:
    return list(csv.DictReader(p.open(encoding="utf-8")))


def summary(d: Path) -> dict:
    return json.loads((d / "summary.json").read_text(encoding="utf-8"))


def err(d: Path) -> float:
    s = summary(d)
    return s["metrics"]["qerr_true_mean_rad"] if "metrics" in s else s["qerr_mean_rad"]


nom = {(r["platform"], r["mission"], r["label"]): r for r in csv_rows(FR / "results" / "final_nominal.csv")}
q = lambda p, m, a: float(nom[(p, m, a)]["qerr_true_mean_rad"])
SRC_NOM = "final_robustness_gating/results/final_nominal.csv  (run_campaign.py -> build_final_csv.py)"

# ---------------------------------------------------------------- 1. primary result (Sec. VI-B, abstract, Table II)
for p, s_geo in ((X, "37.3"), (C, "22.4")):
    check("VI-B primary", f"{p} gated geo reduction", s_geo, f1(red(gm([q(p, m, "pdff_rho3") for m in M]), gm([q(p, m, "cmg_pes_gated") for m in M]))), SRC_NOM)
for p, b, c in ((X, "4.54", "2.85"), (C, "3.77", "2.92")):
    check("VI-B primary", f"{p} geo error PD+ff -> CMG (1e-3 rad)", f"{b}->{c}",
          f"{gm([q(p, m, 'pdff_rho3') for m in M]) * 1e3:.2f}->{gm([q(p, m, 'cmg_pes_gated') for m in M]) * 1e3:.2f}", SRC_NOM)
check("VI-B primary", "CF2 ungated beta=.05 geo", "6.5", f1(red(gm([q(C, m, "pdff_rho3") for m in M]), gm([q(C, m, "cmg_pes_table") for m in M]))), SRC_NOM)
check("VI-B primary", "X2 ungated geo", "35.6", f1(red(gm([q(X, m, "pdff_rho3") for m in M]), gm([q(X, m, "cmg_pes_table") for m in M]))), SRC_NOM)
check("VI-B primary", "Full3/Hard45 reductions X2", "12.4/13.8", "/".join(f1(red(q(X, m, "pdff_rho3"), q(X, m, "cmg_pes_gated"))) for m in ("full3", "hard45")), SRC_NOM)
check("VI-B primary", "Full3/Hard45 reductions CF2", "5.4/7.3", "/".join(f1(red(q(C, m, "pdff_rho3"), q(C, m, "cmg_pes_gated"))) for m in ("full3", "hard45")), SRC_NOM)

# ---------------------------------------------------------------- 2. baseline ladder (Table II middle/lower blocks)
mt = {(r["platform"], r["mission"]): r for r in csv_rows(BR / "master_table.csv")}
col = lambda p, k: [float(mt[(p, m)][k]) for m in M]
SRC_MT = "baseline_restatement/master_table.csv  (build_restatement.py over nengo_nef_replication results)"
for p, s_ in ((X, "57.8"), (C, "57.6")):
    check("Table II rho=1", f"{p} geo reduction on PD+ff rho=1", s_, f1(red(gm(col(p, "PDff_1x")), gm(col(p, "CMG_on_PDff_1x")))), SRC_MT)
for p, s_ in ((X, "44.5"), (C, "44.2")):
    check("Table II fixed PD", f"{p} geo reduction on fixed PD", s_, f1(red(gm(col(p, "PD")), gm(col(p, "CMG_on_PD")))), SRC_MT)
allpd = [float(mt[(p, m)]["CMGonPD_vs_PD_pct"]) for p in (X, C) for m in M]
check("VI-B primary", "fixed-PD range, all ten cells", "17.3-60.6", f"{min(allpd):.1f}-{max(allpd):.1f}", SRC_MT)

# ---------------------------------------------------------------- 3. portability (Sec. VI-B paragraph)
a5 = json.loads((FR / "results" / "a5_numbers.json").read_text(encoding="utf-8"))["families"]
for fam, s_ in (("lqr", "31.1/22.4"), ("pid", "36.7/22.4"), ("smc", "43.8/26.6"), ("mpc", "33.4/22.7"), ("nmpc", "31.9/21.7"), ("backstepping", "37.3/22.4")):
    check("VI-B portability", fam, s_, f"{f1(a5[fam][X]['geo_red_pct'])}/{f1(a5[fam][C]['geo_red_pct'])}",
          "final_robustness_gating/results/a5_numbers.json  (run_campaign_a5*.py -> analyze_a5.py)")

# ---------------------------------------------------------------- 4. Izhikevich, rho=3 (Table II last block, abstract, Sec. VI-D)
SE = NB / "results" / "strict_exact"
SRC_SE = "neuron_basis_decisive/results/strict_exact/<plat>/<mission>/<basis>  (run_campaign.py)"
base = {p: [err(SE / p / m / "classical") for m in M] for p in (X, C)}
izh = {p: [err(SE / p / m / "izhikevich") for m in M] for p in (X, C)}
izh_row_paper = {X: "-48.0,5.8,4.5,-1.1,-76.3,-18.9", C: "0.7,1.3,0.8,-0.5,-33.3,-5.4"}
for p in (X, C):
    cells = [f1(red(b, i)) for b, i in zip(base[p], izh[p])] + [f1(red(gm(base[p]), gm(izh[p])))]
    check("Table II Izhikevich", f"{p} Delta row (5 missions, geo)", izh_row_paper[p], ",".join(cells), SRC_SE)
check("Abstract / VI-D", "Izhikevich geo increase X2/CF2", "18.9/5.4",
      f"{f1(-red(gm(base[X]), gm(izh[X])))}/{f1(-red(gm(base[C]), gm(izh[C])))}", SRC_SE)
check("VI-D", "Izhikevich geo error ratio X2/CF2", "1.19/1.05", f"{gm(izh[X]) / gm(base[X]):.2f}/{gm(izh[C]) / gm(base[C]):.2f}", SRC_SE)
check("VI-D", "Izhikevich Full3/Hard45 X2", "5.8/4.5", "/".join(f1(red(base[X][i], izh[X][i])) for i in (1, 2)), SRC_SE)

# effort rows (realized residual RMS / axis bound, arithmetic mean)
IZC = FR / "results_izh_corrected" / "table2_full_2026-09-29"
for p, folder, s_ in ((X, "x2", "0.053,0.051,0.053,0.106,0.052,0.063"), (C, "cf2", "0.012,0.021,0.021,0.047,0.012,0.023")):
    v = [summary(IZC / f"{folder}_{m}")["metrics"]["realized_residual_normalized_rms"] for m in M]
    check("Table II Izhikevich", f"{p} effort row", s_, ",".join(f"{x:.3f}" for x in v + [float(np.mean(v))]),
          "final_robustness_gating/results_izh_corrected/table2_full_2026-09-29  (run_izh_corrected.py)")
for p, s_ in ((X, "0.003,0.023,0.023,0.109,0.001,0.032"), (C, "0.005,0.010,0.012,0.049,<0.001,0.015")):
    v = [float(nom[(p, m, "cmg_pes_gated")]["residual_normalized_rms"]) for m in M]
    fmt = lambda x: "<0.001" if x < 5e-4 else f"{x:.3f}"
    check("Table II Izhikevich", f"{p} CMG effort row", s_, ",".join(fmt(x) for x in v + [float(np.mean(v))]), SRC_NOM)

# Two checks need per-step traces. When the traces are present they are recomputed from them and the derived values are
# cached in reproduce/trace_derived.json; a release without the trace archive (see DATA.md) reads that cache instead.
TRACE_CACHE = ROOT / "reproduce" / "trace_derived.json"
_cache = json.loads(TRACE_CACHE.read_text(encoding="utf-8")) if TRACE_CACHE.exists() else {}

# rail fraction (|realized residual| >= 0.98 beta l, t >= 2 s)
rails = []
if (IZC / "x2_roll" / "trace.csv").exists():
    for p, folder, beta in ((X, "x2", 0.5), (C, "cf2", 0.2)):
        for m in M:
            d = IZC / f"{folder}_{m}"
            tr = pd.read_csv(d / "trace.csv")
            lim = np.array(summary(d)["actuation"]["torque_limits_Nm"])
            a = np.abs(tr[[f"realized_residual_{c}" for c in "xyz"]].to_numpy()) / (beta * lim[None, :])
            rails.append(float((a[tr["t"].to_numpy() >= 2.0] >= 0.98).mean()))
    _cache["izhikevich_rail_fractions"] = rails
    rail_src = "results_izh_corrected/table2_full_2026-09-29/*/trace.csv  (method of rail_fraction_izh.py)"
else:
    rails = _cache["izhikevich_rail_fractions"]
    rail_src = "reproduce/trace_derived.json (per-step traces not distributed)"
check("VI-D", "Izhikevich rail fraction range (%)", "0-1.7", f"{100 * min(rails):.0f}-{100 * max(rails):.1f}", rail_src)

# Izhikevich on fixed PD (corrected PES rate)
IFP = NN / "results" / "izh_fixed_pd_corrected_2026-09-24"
for p, s_ in ((X, "39.6,37.5,32.2,6.6,46.6,33.8"), (C, "33.7,38.9,32.2,diverges,41.5,--")):
    pd_ = col(p, "PD")
    e = [err(IFP / p / m) for m in M]
    cells = ["diverges" if ei > 2 * b else f1(red(b, ei)) for b, ei in zip(pd_, e)]
    cells.append("--" if "diverges" in cells else f1(red(gm(pd_), gm(e))))
    check("Table II Izhikevich", f"{p} Delta row, fixed PD", s_, ",".join(cells),
          "nengo_nef_replication/results/izh_fixed_pd_corrected_2026-09-24  (run_fixed_pd_izh_corrected.py)")

# ---------------------------------------------------------------- 5. non-neural and threshold-aware bases (Sec. VI-D paragraph)
for basis, s_ in (("paired-current", "11.9/4.8"), ("constant-one", "10.3/4.3")):
    v = {p: red(gm(base[p]), gm([err(SE / p / m / basis) for m in M])) for p in (X, C)}
    check("VI-D alternatives", basis, s_, f"{f1(v[X])}/{f1(v[C])}", SRC_SE)
SV = NB / "results" / "selected_validate"
ho = {X: ("full3", "hardstep", "yaw360"), C: M}
v = {p: red(gm([err(SE / p / m / "classical") for m in ho[p]]), gm([err(SV / p / m / "lifrate") for m in ho[p]])) for p in (X, C)}
check("VI-D alternatives", "LIFRate threshold-aware, held out", "15.8/11.4", f"{f1(v[X])}/{f1(v[C])}",
      "neuron_basis_decisive/results/selected_validate  (select_development.py -> run_selected_validation.py)")
act = []
if (SE / X / M[0] / "lif" / "neural_trace_full_rate.npz").exists():
    for p in (X, C):
        for fam in ("lif", "alif", "lifrate"):
            per_mission = []
            for m in M:
                with np.load(SE / p / m / fam / "neural_trace_full_rate.npz") as z:
                    per_mission.append(float(np.mean(z["activity"] > 1e-6)))
            act.append(float(np.mean(per_mission)))
    _cache["lif_family_occupancy"] = act
    act_src = "strict_exact/*/{lif,alif,lifrate}/neural_trace_full_rate.npz"
    TRACE_CACHE.write_text(json.dumps(_cache, indent=1), encoding="utf-8")
else:
    act = _cache["lif_family_occupancy"]
    act_src = "reproduce/trace_derived.json (neural traces not distributed)"
check("VI-D", "LIF/ALIF/LIFRate active unit-samples, mission mean, rho=3 (%)", "3.2-4.4", f"{100 * min(act):.1f}-{100 * max(act):.1f}",
      act_src)

# ---------------------------------------------------------------- 6. noise (Sec. VI-E)
nz = {(r["noise_level"], r["platform"], r["mission"], int(r["seed"]), r["label"]): r for r in csv_rows(FR / "results" / "final_noise.csv")}
fq = lambda r: float(r["qerr_true_mean_rad"])
seeds = {lv: sorted({k[3] for k in nz if k[0] == lv}) for lv in ("moderate", "realistic")}
SRC_NZ = "final_robustness_gating/results/final_noise.csv  (run_campaign.py --campaign noise, run_campaign_a2.py)"
check("VI-E noise", "seeds moderate/realistic", "5/10", f"{len(seeds['moderate'])}/{len(seeds['realistic'])}", SRC_NZ)
mr = lambda lv, p, m: st.mean(red(fq(nz[(lv, p, m, s, "pdff_rho3")]), fq(nz[(lv, p, m, s, "cmg_pes_gated")])) for s in seeds[lv])
check("VI-E noise", "realistic Full3/Hard45 X2", "11.3/10.8", f"{f1(mr('realistic', X, 'full3'))}/{f1(mr('realistic', X, 'hard45'))}", SRC_NZ)
check("VI-E noise", "realistic Full3/Hard45 CF2", "3.9/4.0", f"{f1(mr('realistic', C, 'full3'))}/{f1(mr('realistic', C, 'hard45'))}", SRC_NZ)
ry = [mr(lv, p, m) for lv in seeds for p in (X, C) for m in ("roll", "yaw360")]
check("VI-E noise", "Roll/Yaw360 change range", "-5.3..2.2", f"{min(ry):.1f}..{max(ry):.1f}", SRC_NZ)
geo_n = lambda p: red(gm([st.mean(fq(nz[("realistic", p, m, s, "pdff_rho3")]) for s in seeds["realistic"]) for m in M]),
                      gm([st.mean(fq(nz[("realistic", p, m, s, "cmg_pes_gated")]) for s in seeds["realistic"]) for m in M]))
check("VI-E noise", "realistic geo X2/CF2", "2.3/1.0", f"{f1(geo_n(X))}/{f1(geo_n(C))}", SRC_NZ)
div = [fq(nz[(lv, C, "hardstep", s, "cmg_pes_gated_b05")]) > 2 * fq(nz[(lv, C, "hardstep", s, "pdff_rho3")]) for lv in seeds for s in seeds[lv]]
check("VI-E noise", "CF2 beta=.5 Hardstep diverges", "15/15", f"{sum(div)}/{len(div)}", SRC_NZ)
sat = [float(nz[(lv, C, "hardstep", s, "cmg_pes_gated_b05")]["rotor_sat_fraction"]) * 100 for lv in seeds for s in seeds[lv]]
check("VI-E noise", "rotor-bound share (%)", "61-79", f"{min(sat):.0f}-{max(sat):.0f}", SRC_NZ)

# ---------------------------------------------------------------- 7. disturbance (Sec. VI-E)
ds = {(r["platform"], r["disturbance_level"], r["label"]): r for r in csv_rows(FR / "results" / "final_disturbance.csv")}
act_ = lambda p, lv, a: float(ds[(p, lv, a)]["disturbance_active_mean_rad"])
qui = lambda p, lv, a: float(ds[(p, lv, a)]["disturbance_quiet_mean_rad"])
SRC_DS = "final_robustness_gating/results/final_disturbance.csv  (run_campaign.py --campaign disturbance -> analyze_robustness.py)"
for p, s_ in ((X, "14.4"), (C, "5.9")):
    check("VI-E disturbance", f"{p} burst reduction 1x", s_, f1(red(act_(p, "x1", "pdff_rho3"), act_(p, "x1", "cmg_pes_gated"))), SRC_DS)
for p, s_ in ((X, "24.0/13.3"), (C, "6.5/4.7")):
    check("VI-E disturbance", f"{p} burst reduction 0.5x/2x", s_,
          "/".join(f1(red(act_(p, lv, "pdff_rho3"), act_(p, lv, "cmg_pes_gated"))) for lv in ("x0.5", "x2")), SRC_DS)
for p, s_ in ((X, "1.61->1.38"), (C, "2.27->2.14")):
    check("VI-E disturbance", f"{p} burst error (deg)", s_, f"{math.degrees(act_(p, 'x1', 'pdff_rho3')):.2f}->{math.degrees(act_(p, 'x1', 'cmg_pes_gated')):.2f}", SRC_DS)
for p, s_ in ((X, "14.7"), (C, "19.8")):
    check("VI-E disturbance", f"{p} quiet reduction 1x", s_, f1(red(qui(p, "x1", "pdff_rho3"), qui(p, "x1", "cmg_pes_gated"))), SRC_DS)
check("VI-E disturbance", "X2 quiet 0.5x (deg)", "0.021->0.036",
      f"{math.degrees(qui(X, 'x0.5', 'pdff_rho3')):.3f}->{math.degrees(qui(X, 'x0.5', 'cmg_pes_gated')):.3f}", SRC_DS)
check("VI-E disturbance", "CF2 burst 1x at beta=.5 / beta=.05", "13.7/1.5",
      f"{f1(red(act_(C, 'x1', 'pdff_rho3'), act_(C, 'x1', 'cmg_pes_gated_b05')))}/{f1(red(act_(C, 'x1', 'pdff_rho3'), act_(C, 'x1', 'cmg_pes_table')))}", SRC_DS)

# ---------------------------------------------------------------- 8. Hardstep and the gate (Sec. VI-F)
hs = lambda p, a: red(q(p, "hardstep", "pdff_rho3"), q(p, "hardstep", a))
check("VI-F Hardstep", "X2 ungated / gated", "-17.0/-2.0", f"{f1(hs(X, 'cmg_pes_table'))}/{f1(hs(X, 'cmg_pes_gated'))}", SRC_NOM)
check("VI-F Hardstep", "CF2 beta=.5 gated Hardstep / geo", "-1.2/36.5",
      f"{f1(hs(C, 'cmg_pes_gated_b05'))}/{f1(red(gm([q(C, m, 'pdff_rho3') for m in M]), gm([q(C, m, 'cmg_pes_gated_b05') for m in M])))}", SRC_NOM)
r5 = nom[(C, "hardstep", "cmg_pes_b05_ungated")]
check("VI-F Hardstep", "CF2 beta=.5 ungated divergence (deg, rotor %)", "136/92",
      f"{math.degrees(float(r5['qerr_true_mean_rad'])):.0f}/{float(r5['rotor_sat_fraction']) * 100:.0f}", SRC_NOM)
check("VI-F Hardstep", "gate blocked share X2/CF2 (%)", "20.5/15.5",
      f"{float(nom[(X, 'hardstep', 'cmg_pes_gated')]['gate_blocked_fraction']) * 100:.1f}/{float(nom[(C, 'hardstep', 'cmg_pes_gated_b05')]['gate_blocked_fraction']) * 100:.1f}", SRC_NOM)

# ---------------------------------------------------------------- 9. implementation and mechanism constants
eq = csv_rows(NN / "results" / "compiled" / "archived_equivalence.csv")
check("VI-A", "Nengo vs NumPy worst relative error over ten cases", "2.013e-06 (10)",
      f"{max(float(r['relative_difference_ppm']) for r in eq) * 1e-6:.3e} ({len(eq)})",
      "nengo_nef_replication/results/compiled/archived_equivalence.csv  (verify_archived_equivalence.py)")
mac = (E / "theory_certificate_2026-09-12" / "certificate_macros.tex").read_text(encoding="utf-8")
check("VI-C ablation", "PES corner (rad/s)", "9.60", re.search(r"\\pesCorner\}\{([^}]+)\}", mac).group(1),
      "theory_certificate/certificate_macros.tex  (compute_local_certificate.py)")

# ---------------------------------------------------------------- 10. Fig. 4 legend
lad = json.loads((FR / "figures_out" / "ladder" / "x2_hard45_ladder_C.json").read_text(encoding="utf-8"))
deg = {(r["family"], r["level"]): r["mean_deg"] for r in lad["runs"]}
check("Fig. 4", "legend degrees PD/CMG per level", "16.85/7.91,4.07/2.19,0.60/0.52",
      ",".join(f"{deg[('pd', l)]:.2f}/{deg[('cmg', l)]:.2f}" for l in (0, 1, 2)),
      "final_robustness_gating/figures_out/ladder/x2_hard45_ladder_C.json  (make_ladder_figure.py)")

# ---------------------------------------------------------------- 11. reduced CMG and latching (Sec. VI-C, Table II, abstract) [v31]
MC = E / "cmg_mechanism_controls_2026-10-01"
SX = NB / "results" / "strict_exact"
CF = MC / "results" / "confirm"
SRC_MC = "cmg_mechanism_controls_2026-10-01/results/{confirm,development}  (run_campaign.py -> analyze.py)"
base = lambda p, m: err(SX / p / m / "classical")
arm = lambda p, m, a: err((SX if a == "cmg" else CF) / p / m / a)
check("VI-C reduced CMG", "strict_exact classical == final_nominal PD+ff (max rel diff < 1e-12)", "True",
      str(max(abs(base(p, m) - q(p, m, "pdff_rho3")) / q(p, m, "pdff_rho3") for p in (X, C) for m in M) < 1e-12), SRC_MC)
geo_arm = lambda p, a: red(gm([base(p, m) for m in M]), gm([arm(p, m, a) for m in M]))
check("VI-C reduced CMG", "reduced CMG geo X2/CF2 (abstract, Table II)", "46.3/28.6", f"{f1(geo_arm(X, 'lpf-logistic'))}/{f1(geo_arm(C, 'lpf-logistic'))}", SRC_MC)
for p, s_ in ((X, "78.5,35.2,45.5,-0.6,41.8"), (C, "60.1,23.0,24.6,-0.4,20.3")):
    check("VI-C reduced CMG", f"{p} Table II row", s_, ",".join(f1(red(base(p, m), arm(p, m, "lpf-logistic"))) for m in M), SRC_MC)
eff = lambda p, a: st.mean(summary((SX if a == "cmg" else CF) / p / m / a)["metrics"]["realized_residual_normalized_rms"] for m in M)
check("VI-C reduced CMG", "mean effort reduced X2/CF2 vs CMG X2/CF2", "0.033/0.016 vs 0.032/0.015",
      f"{eff(X, 'lpf-logistic'):.3f}/{eff(C, 'lpf-logistic'):.3f} vs {eff(X, 'cmg'):.3f}/{eff(C, 'cmg'):.3f}", SRC_MC)
gap = max(abs(red(base(p, m), arm(p, m, "lpf-logistic")) - red(base(p, m), arm(p, m, "cmg"))) for p in (X, C) for m in ("roll", "yaw360", "hardstep"))
check("VI-C reduced CMG", "max |reduced - CMG| on Roll/Yaw360/Hardstep (pp)", "1.5", f1(gap), SRC_MC)
for a, s_ in (("cmg_G1e3", "9.0/3.6"), ("cmg_G1", "4.4/1.7"), ("latch-replay", "9.6/3.8")):
    check("VI-C reduced CMG", f"{a} geo X2/CF2", s_, f"{f1(geo_arm(X, a))}/{f1(geo_arm(C, a))}", SRC_MC)
dev = MC / "results" / "development"
chi_gap = [abs(geo_arm(p, "cmg_chi0") - geo_arm(p, "cmg")) for p in (X, C)]
chi_gap += [abs(err(dev / f"G{g}_chi0" / m) - err(dev / f"G{g}_chi1" / m)) / err(dev / f"G{g}_chi1" / m) * 100 for g in ("1e00", "1e03", "1e05") for m in ("roll", "hard45")]
check("VI-C ablation", "chi toggle, max effect at every tested G (pp)", "0.0", f1(max(chi_gap)), SRC_MC)
ah, gam, Gr = 50.0, 2.0, 1e5
rpm = [0.5 * (1 + s * math.sqrt(1 - 4 / (ah * gam))) for s in (-1, 1)]
vf = [1.0 - gam * r + math.log(r / (1 - r)) / ah for r in rpm]
check("VI-C ablation", "gate folds v_on/v_off (Table I)", "0.888/-0.888", f"{vf[0]:.3f}/{vf[1]:.3f}", "Table I parameters, closed form")
rel = 0
for p in (X, C):
    for m in M:
        r_ = np.load(SX / p / m / "cmg" / "neural_trace_full_rate.npz")["gate"]
        for j in range(r_.shape[1]):
            on = np.flatnonzero(r_[:, j] > 0.5)
            rel += int(on.size > 0 and bool(np.any(r_[on[0]:, j] < 0.5)))
check("VI-C ablation", "gate releases after latching, ten primary runs", "0", str(rel), "neuron_basis_decisive/results/strict_exact/*/cmg/neural_trace_full_rate.npz")
check("VI-C reduced CMG", "removed-term bounds alpha*gamma/G, c_max (1/s)", "1e-03, <2e-08",
      f"{ah * gam / Gr:.0e}, {'<2e-08' if (120 + 30 * 2.0) / Gr ** 2 < 2e-8 else 'FAIL'}", "Table I parameters, closed form")
a1 = np.load(SX / X / "hard45" / "constant-one" / "neural_trace_full_rate.npz")["activity"]
check("VI-D", "constant basis is a = 1", "1", str(int(np.all(a1 == 1.0))), "neuron_basis_decisive/results/strict_exact/x2/hard45/constant-one")

# ---------------------------------------------------------------- report
out = ROOT / "reproduce"
with (out / "claims_check.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
lines = ["| # | section | claim | paper | recomputed | status | source |", "|---|---|---|---|---|---|---|"]
lines += [f"| {i} | {r['section']} | {r['claim']} | {r['paper']} | {r['recomputed']} | {r['status']} | `{r['source']}` |" for i, r in enumerate(rows, 1)]
(out / "claims_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
w_ = max(len(r["claim"]) for r in rows)
for i, r in enumerate(rows, 1):
    print(f"{i:3d} {r['status']:8s} {r['section']:20s} {r['claim']:{w_}s}  paper {r['paper']:34s} data {r['recomputed']}")
bad = [r for r in rows if r["status"] != "OK"]
print(f"\n{len(rows) - len(bad)}/{len(rows)} match" + (f"; {len(bad)} mismatch" if bad else ""))
sys.exit(1 if bad else 0)
