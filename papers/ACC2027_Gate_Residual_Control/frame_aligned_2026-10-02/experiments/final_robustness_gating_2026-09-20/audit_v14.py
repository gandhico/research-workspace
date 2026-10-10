"""Consistency audit of the v14 manuscript against the data and against itself.

1. every quoted result number of the CMG study appears in the tex and equals the value recomputed from results/final_*.csv  (as in v13)
2. Table II's primary block equals what make_table2.py generates (no hand edits)
3. structural checks: labels unique, every float referenced, every cite key defined, no stale claims, no placeholders
4. build check: pages, undefined references, overfull boxes
5. NEW in v14 - the Izhikevich comparison (amendment A3), recomputed independently of analyze_izh_a3.py from the raw campaign
   CSVs, the run traces and the floor ensemble: abstract, Sec. IV-E, table footnote, table rows, and the trimmed noise sentence
"""
from __future__ import annotations

import csv
import glob
import json
import math
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
D = HERE.parents[1] / "paper" / "v14_2026-09-21_izhikevich"
tex = (D / "ACC2027.tex").read_text(encoding="utf-8")
tab = (D / "tables" / "table_all_restructured.tex").read_text(encoding="utf-8")
whole = tex + "\n" + tab
rd = lambda n: list(csv.DictReader((HERE / "results" / n).open(encoding="utf-8")))
nom = {(r["platform"], r["mission"], r["label"]): r for r in rd("final_nominal.csv")}
noise = {(r["noise_level"], r["platform"], r["mission"], int(r["seed"]), r["label"]): r for r in rd("final_noise.csv")}
dist = {(r["platform"], r["disturbance_level"], r["label"]): r for r in rd("final_disturbance.csv")}
X, C = "x2", "cf2-rotor"
M = ("roll", "full3", "hard45", "hardstep", "yaw360")
gm = lambda xs: math.exp(sum(math.log(x) for x in xs) / len(xs))
red = lambda b, c: 100 * (1 - c / b)
f = lambda r: float(r["qerr_true_mean_rad"])
fails: list[str] = []


def check(name: str, cond: bool, detail: str = ""):
    print(f"  {'ok  ' if cond else 'FAIL'} {name} {detail}")
    if not cond:
        fails.append(name)


def has(snippet: str) -> bool:
    return snippet in whole


print("== 1. quoted numbers (CMG study, unchanged from v13)")
geo = lambda p, arm: red(gm([f(nom[(p, m, "pdff_rho3")]) for m in M]), gm([f(nom[(p, m, arm)]) for m in M]))
vals = {
    "X2 geo gated": (geo(X, "cmg_pes_gated"), "37.3"), "CF2 geo gated b.2": (geo(C, "cmg_pes_gated"), "22.4"),
    "CF2 geo gated b.5": (geo(C, "cmg_pes_gated_b05"), "36.5"), "CF2 geo ungated b.05": (geo(C, "cmg_pes_table"), "6.5"),
    "X2 geo ungated": (geo(X, "cmg_pes_table"), "35.6"),
}
for k, (v, s_) in vals.items():
    check(k, f"{v:.1f}" == s_ and has(s_), f"data {v:.2f} vs text {s_}")
hs = lambda p, arm: red(f(nom[(p, "hardstep", "pdff_rho3")]), f(nom[(p, "hardstep", arm)]))
check("X2 Hardstep gated -2.0", abs(hs(X, "cmg_pes_gated") + 2.0) < 0.06, f"{hs(X, 'cmg_pes_gated'):.2f}")
check("X2 Hardstep ungated -17.0", abs(hs(X, "cmg_pes_table") + 17.0) < 0.06, f"{hs(X, 'cmg_pes_table'):.2f}")
check("CF2 Hardstep b.5 -1.2", abs(hs(C, "cmg_pes_gated_b05") + 1.2) < 0.06, f"{hs(C, 'cmg_pes_gated_b05'):.2f}")
check("CF2 Hardstep b.2 -0.2", abs(hs(C, "cmg_pes_gated") + 0.2) < 0.06, f"{hs(C, 'cmg_pes_gated'):.2f}")
r = nom[(C, "hardstep", "cmg_pes_b05_ungated")]
check("CF2 b.5 ungated divergence 136 deg / 92 %", round(math.degrees(f(r))) == 136 and round(float(r["rotor_sat_fraction"]) * 100) == 92,
      f"{math.degrees(f(r)):.1f} deg, {float(r['rotor_sat_fraction']) * 100:.1f} %")
gs = lambda p, arm: float(nom[(p, "hardstep", arm)]["gate_blocked_fraction"]) * 100
check("gate share Hardstep 20.5 / 15.5", f"{gs(X, 'cmg_pes_gated'):.1f}" == "20.5" and f"{gs(C, 'cmg_pes_gated_b05'):.1f}" == "15.5")
worst = max(abs(f(nom[(p, m, "cmg_pes_gated" if p == X else "cmg_pes_gated_b05")]) - f(nom[(p, m, "cmg_pes_table" if p == X else "cmg_pes_b05_ungated")])) /
            f(nom[(p, m, "cmg_pes_table" if p == X else "cmg_pes_b05_ungated")]) * 100 for p in (X, C) for m in ("roll", "full3", "hard45", "yaw360"))
check("other eight cells <= 0.1 %", worst <= 0.1006, f"worst {worst:.4f} %")

seeds = {lv: sorted({k[3] for k in noise if k[0] == lv}) for lv in ("moderate", "realistic")}
check("noise seeds 5 / 10", len(seeds["moderate"]) == 5 and len(seeds["realistic"]) == 10)
mred = lambda lv, p, m, arm="cmg_pes_gated": st.mean(red(f(noise[(lv, p, m, s, "pdff_rho3")]), f(noise[(lv, p, m, s, arm)])) for s in seeds[lv])
for lv, p, m, s_ in (("moderate", X, "roll", "1.4"), ("moderate", X, "yaw360", "3.9"), ("realistic", X, "roll", "4.2"), ("realistic", X, "yaw360", "5.3"),
                      ("realistic", X, "full3", "11.3"), ("realistic", X, "hard45", "10.8"), ("realistic", C, "full3", "3.9"), ("realistic", C, "hard45", "4.0"),
                      ("moderate", C, "roll", "2.2"), ("moderate", C, "yaw360", "2.0"), ("realistic", C, "roll", "0.4"), ("realistic", C, "yaw360", "2.2")):
    check(f"noise {lv} {p} {m} ~ {s_}", f"{abs(mred(lv, p, m)):.1f}" == s_, f"{mred(lv, p, m):+.2f}")
# v14: the Roll/Yaw360 noise sentence now quotes the range of the eight values
ry = [mred(lv, p, m) for lv in ("moderate", "realistic") for p in (X, C) for m in ("roll", "yaw360")]
check("Roll/Yaw360 noise changes span -5.3 to +2.2 (text and data)", f"{min(ry):.1f}" == "-5.3" and f"{max(ry):.1f}" == "2.2" and has(r"$-$5.3 to $+$2.2"),
      f"data {min(ry):+.2f} .. {max(ry):+.2f}")
b5 = [f(noise[(lv, C, "hardstep", s, "cmg_pes_gated_b05")]) > 2 * f(noise[(lv, C, "hardstep", s, "pdff_rho3")]) for lv in seeds for s in seeds[lv]]
check("CF2 beta .5 Hardstep diverges 15/15", sum(b5) == 15 and len(b5) == 15, f"{sum(b5)}/{len(b5)}")
b2 = max(f(noise[(lv, C, "hardstep", s, "cmg_pes_gated")]) / f(noise[(lv, C, "hardstep", s, "pdff_rho3")]) for lv in seeds for s in seeds[lv])
check("CF2 beta .2 Hardstep max ratio < 1.01", b2 < 1.01, f"{b2:.4f}")
sat = [float(noise[(lv, C, "hardstep", s, "cmg_pes_gated_b05")]["rotor_sat_fraction"]) * 100 for lv in seeds for s in seeds[lv]]
check("rotor saturation 61-79 %", round(min(sat)) == 61 and round(max(sat)) == 79, f"{min(sat):.1f}-{max(sat):.1f}")
sd_ = max(st.stdev([red(f(noise[(lv, p, m, s, "pdff_rho3")]), f(noise[(lv, p, m, s, "cmg_pes_gated")])) for s in seeds[lv]])
          for lv in seeds for p in (X, C) for m in ("full3", "hard45"))
check("Full3/Hard45 seed sd below 0.2 pp", sd_ < 0.2, f"max {sd_:.3f}")

print("\n== 2. Table II primary block is what the generator produces")
out = subprocess.run([sys.executable, str(HERE / "make_table2.py"), str(D / "tables" / "table_all_restructured.tex")], capture_output=True, text=True)
gen = [l for l in out.stdout.splitlines() if l.startswith(("PD+ff", r"\;+CMG", r"\;\;$\Delta$"))]
check("generated rows all present in the table file", all(l in tab for l in gen), f"{len(gen)} rows")

print("\n== 3. structure")
body = "\n".join(l for l in whole.split("\n") if not l.lstrip().startswith("%"))
body = re.sub(r"\\iffalse.*?\\fi", "", body, flags=re.S)
labels = re.findall(r"\\label\{([^}]+)\}", body)
refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", body))
check("labels unique", len(labels) == len(set(labels)))
check("every figure/table/proposition referenced", all(l in refs for l in labels if l.startswith(("fig:", "tab:", "prop:"))),
      str([l for l in labels if l.startswith(("fig:", "tab:", "prop:")) and l not in refs]))
check("no undefined references", not (refs - set(labels)), str(sorted(refs - set(labels))))
bib = (D / "references_ACC2027.bib").read_text(encoding="utf-8")
keys = set(re.findall(r"@\w+\{([^,\s]+),", bib))
cited = {k.strip() for m in re.findall(r"\\cite\{([^}]+)\}", body) for k in m.split(",")}
check("every cite key defined", cited <= keys, str(sorted(cited - keys)))
for bad in ("your-repo", "TODO", "??", "quaternium", "in this paper", "In this paper", "obviously", "clearly"):
    check(f"no '{bad}'", bad not in whole)
check("old fixed-PD noise claims removed", "18.08" not in whole and "55.75" not in whole and "two paired seeds" not in whole)
abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S).group(1)
check("no stale '35.6/6.5' headline in abstract", "35.6" not in abstract)
check("no stale v13 Izhikevich claims (few points more / three times / 0.37 versus 0.12)",
      not any(s in whole for s in ("a few points more", "three times the realized", "0.37$ versus $0.12", "lower error is not free")))

print("\n== 4. build")
log = (D / "ACC2027.log").read_text(encoding="utf-8", errors="ignore")
pages = re.search(r"Output written on ACC2027\.pdf \((\d+) pages", log)
check("7 pages", bool(pages) and int(pages.group(1)) == 7, pages.group(0) if pages else "no pdf")
check("no undefined refs/cites", "undefined" not in log.lower().replace("undefined control sequence", ""))
check("no overfull boxes", "Overfull" not in log)

print("\n== 5. Izhikevich comparison (amendment A3): recomputed from the raw campaign outputs")
iz = {(r["platform"], r["mission"], r["label"], r["noise_level"], r["disturbance_level"], int(r["seed"])): r for r in rd("results_izh_a3_all.csv")}
check("33 A3 runs, all valid", len(iz) == 33 and all(r["status"] in ("completed", "skipped_valid") for r in iz.values()), f"{len(iz)}")
check("footnote says 33 runs and seeds 1--3", has("$33$ runs in all") and has("seeds 1--3"))
IZB = {X: "b0p5", C: "b0p2"}
izg = lambda p, m, **kw: iz[(p, m, f"izh_pes_gated_{IZB[p]}", kw.get("noise", "none"), kw.get("dist", "none"), kw.get("seed", 1))]
pdn = lambda p, m: f(nom[(p, m, "pdff_rho3")])
cmgr = lambda p, m: red(pdn(p, m), f(nom[(p, m, "cmg_pes_gated")]))
izr = lambda p, m: red(pdn(p, m), f(izg(p, m)))
fmt_delta = lambda v: f"{v:.0f}" if abs(v) >= 100 else f"{v:.1f}"

# 5a geometric means (abstract and Sec. IV-E)
for p, ratio, pct in ((X, "2.6", "162"), (C, "1.8", "79")):
    g_i, g_p = gm([f(izg(p, m)) for m in M]), gm([pdn(p, m) for m in M])
    check(f"{p}: geometric-mean error ratio {ratio}x and +{pct} % (abstract, IV-E, table)",
          f"{g_i / g_p:.1f}" == ratio and f"{100 * (g_i / g_p - 1):.0f}" == pct and has(f"${ratio}\\times$") and has(f"${pct}\\%$"),
          f"data {g_i / g_p:.3f}")
# 5b efforts ("ten times", 0.36 / 0.14)
ex = {p: (np.mean([float(izg(p, m)["residual_normalized_rms"]) for m in M]), np.mean([float(nom[(p, m, "cmg_pes_gated")]["residual_normalized_rms"]) for m in M])) for p in (X, C)}
check("effort X2 0.36, CF2 0.14 (text)", f"{ex[X][0]:.2f}" == "0.36" and f"{ex[C][0]:.2f}" == "0.14" and has("$0.36$ of the axis bound on X2, $0.14$ on CF2"),
      f"{ex[X][0]:.3f}, {ex[C][0]:.3f}")
check("effort ratio Izh/CMG in [9, 12] ('ten times' in abstract and IV-E)", all(9 <= ex[p][0] / ex[p][1] <= 12 for p in (X, C)) and has("ten times"),
      f"{ex[X][0] / ex[X][1]:.1f}, {ex[C][0] / ex[C][1]:.1f}")
# 5c CMG effort follows the baseline error (rank correlation 1), Izhikevich effort does not
rk = lambda v: np.argsort(np.argsort(v)).astype(float)
for p in (X, C):
    e = [pdn(p, m) for m in M]
    rc_ = np.corrcoef(rk(e), rk([float(nom[(p, m, "cmg_pes_gated")]["residual_normalized_rms"]) for m in M]))[0, 1]
    ri_ = np.corrcoef(rk(e), rk([float(izg(p, m)["residual_normalized_rms"]) for m in M]))[0, 1]
    check(f"{p}: CMG effort rank-follows the baseline error (rho=1), Izhikevich does not (|rho|<1)", abs(rc_ - 1) < 1e-9 and abs(ri_) < 0.5, f"CMG {rc_:+.2f}, Izh {ri_:+.2f}")
# 5d rails: fraction of samples with |residual| >= 0.98 beta l  (t >= 2 s)
rails = []
for p in (X, C):
    for m in M:
        d_ = HERE / "results" / "izh_a3" / "nominal" / p / m / f"izh_pes_gated_{IZB[p]}" / "load_1" / "seed_001"
        tr = pd.read_csv(d_ / "trace.csv")
        lim = np.array(json.loads((d_ / "summary.json").read_text(encoding="utf-8"))["actuation"]["torque_limits_Nm"])
        beta = 0.5 if p == X else 0.2
        a = np.abs(tr[[f"realized_residual_{c}" for c in "xyz"]].to_numpy()) / (beta * lim[None, :])
        rails.append(float((a[tr["t"].to_numpy() >= 2.0] >= 0.98).mean()))
check("residual on a rail in 35-48 % of samples (text)", f"{100 * min(rails):.0f}" == "35" and f"{100 * max(rails):.0f}" == "48" and has("$35$--$48\\%$"),
      f"{100 * min(rails):.1f}-{100 * max(rails):.1f} %")
# 5e Full3 / Hard45: 'level with or below CMG' under the A3.2 threshold; 'leads on the fixed-PD baseline' from the table cells
floor_vals = {}
for cell in (("x2", "full3"), ("x2", "hard45"), ("cf2-rotor", "full3"), ("cf2-rotor", "hard45")):
    runs = sorted(glob.glob(str(HERE / "results_validation_izh" / "floor" / f"{cell[0]}_{cell[1]}_eps*" / "summary.json")))
    v = [json.loads(Path(q).read_text(encoding="utf-8"))["metrics"]["qerr_true_mean_rad"] for q in runs] + [f(izg(*cell))]
    floor_vals[cell] = v
check("floor ensemble: 6 perturbed runs + the A3 run per cell", all(len(v) == 7 for v in floor_vals.values()), str({k: len(v) for k, v in floor_vals.items()}))
sd_rel = max(np.std(v, ddof=1) / np.mean(v) for v in floor_vals.values()) * 100
sd_pp = max(100 * np.std(v, ddof=1) / pdn(*k) for k, v in floor_vals.items())
check("single-run scatter 1.4 % of the error; threshold 4 points (footnote)", f"{sd_rel:.1f}" == "1.4" and f"{3 * sd_pp:.0f}" == "4" and has("scatter is $1.4\\%$ of the error")
      and has("differences below $4$ points"), f"sd {sd_rel:.2f} %, 3 sd = {3 * sd_pp:.2f} points")
check("offsets described as below 2e-13 rad", has("below $2\\times10^{-13}$\\,rad") and 1.32 * math.radians(6e-12) < 2e-13, f"{1.32 * math.radians(6e-12):.2e} rad")
thr = 3 * sd_pp
lvl = [(k, izr(*k) - cmgr(*k)) for k in (("x2", "full3"), ("x2", "hard45"), ("cf2-rotor", "full3"), ("cf2-rotor", "hard45"))]
check("Full3/Hard45: Izhikevich never above CMG by more than the threshold ('level with or below')", all(d_ < thr for _, d_ in lvl),
      ", ".join(f"{k[0]}/{k[1]} {d_:+.1f}" for k, d_ in lvl))
# 5f Hardstep: X2 ungated / gated, CF2 divergence at beta .2 ungated removed by the gate
arch = lambda mm: json.loads((HERE / "results" / "supplementary_izhikevich" / "x2" / mm / "nengo_izhikevich_pes" / "summary.json").read_text(encoding="utf-8"))["qerr_mean_rad"]
ung_x2 = red(pdn(X, "hardstep"), f(iz[(X, "hardstep", "izh_pes_ungated_b0p5", "none", "none", 1)]))
ung_x2_arch = red(pdn(X, "hardstep"), arch("hardstep"))
gat_x2 = red(pdn(X, "hardstep"), f(izg(X, "hardstep")))
check("X2 Hardstep Izhikevich ungated -16.9 -> gated -1.5 (text; new and archived runner agree)",
      f"{-ung_x2:.1f}" == "16.9" and f"{-ung_x2_arch:.1f}" == "16.9" and f"{-gat_x2:.1f}" == "1.5" and has("$16.9\\%$ to $1.5\\%$"),
      f"{ung_x2:.2f}, archived {ung_x2_arch:.2f}, gated {gat_x2:.2f}")
d_u = iz[(C, "hardstep", "izh_pes_ungated_b0p2", "none", "none", 1)]
gat_c = red(pdn(C, "hardstep"), f(izg(C, "hardstep")))
check("CF2 Hardstep Izhikevich: ungated beta .2 diverges (>2x PD+ff, rotors at a bound), gated -0.5 %",
      f(d_u) > 2 * pdn(C, "hardstep") and float(d_u["rotor_sat_fraction"]) > 0.5 and f"{-gat_c:.1f}" == "0.5" and has("$-0.5\\%$"),
      f"ungated {math.degrees(f(d_u)):.0f} deg, rotor sat {float(d_u['rotor_sat_fraction']):.2f}; gated {gat_c:.2f} %")
# 5g noise (table row) and hover bursts (text says 'persists under noise and between hover bursts')
nz = lambda p, m: 100 * (1 - gm([f(izg(p, m, noise="realistic", seed=s)) / f(noise[("realistic", p, m, s, "pdff_rho3")]) for s in (1, 2, 3)]))
check("Izhikevich under realistic noise: Roll degraded on both airframes", nz(X, "roll") < -100 and nz(C, "roll") < -20, f"{nz(X, 'roll'):+.1f}, {nz(C, 'roll'):+.1f}")
qh = lambda p: (float(izg(p, "hover", dist="x1")["disturbance_quiet_mean_rad"]), float(dist[(p, "x1", "pdff_rho3")]["disturbance_quiet_mean_rad"]))
check("hover bursts: Izhikevich quiet-phase error above the baseline's on both airframes ('persists between bursts')", all(qh(p)[0] > 2 * qh(p)[1] for p in (X, C)),
      f"X2 {qh(X)[0] * 1e3:.2f} vs {qh(X)[1] * 1e3:.2f} mrad; CF2 {qh(C)[0] * 1e3:.2f} vs {qh(C)[1] * 1e3:.2f} mrad")
# 5h table rows: every cell of the new block recomputed
def row_cells(prefix: str):
    line = next(l for l in tab.split("\n") if l.startswith(prefix))
    return [c.strip().replace(r"\emph{", "").replace("}", "").replace(r"\\", "").strip() for c in line.split("&")[1:]]


exp_delta = []
for p in (X, C):
    exp_delta += [fmt_delta(izr(p, m)) for m in M] + [fmt_delta(red(gm([pdn(p, m) for m in M]), gm([f(izg(p, m)) for m in M])))]
check("Table II row 'Izhikevich--PES, rho=3' equals the recomputed values", row_cells(r"\;\;$\Delta$, Izhikevich--PES, $\rho=3$ [\%]") == exp_delta,
      str(row_cells(r"\;\;$\Delta$, Izhikevich--PES, $\rho=3$ [\%]")[:6]))
exp_noise = []
for p in (X, C):
    exp_noise += [fmt_delta(nz(p, m)) if m in ("roll", "hard45", "hardstep") else "--" for m in M] + ["--"]
check("Table II row 'Izhikevich, realistic noise' equals the recomputed values", row_cells(r"\;\;$\Delta$, Izhikevich--PES, $\rho=3$, realistic noise [\%]") == exp_noise)
eff = lambda v: r"$<$0.001" if v < 5e-4 else f"{v:.3f}"
for lab, src in ((r"\;\;effort, CMG--PES, $\rho=3$", lambda p, m: float(nom[(p, m, "cmg_pes_gated")]["residual_normalized_rms"])),
                 (r"\;\;effort, Izhikevich--PES, $\rho=3$", lambda p, m: float(izg(p, m)["residual_normalized_rms"]))):
    e_ = []
    for p in (X, C):
        v = [src(p, m) for m in M]
        e_ += [eff(x) for x in v] + [eff(float(np.mean(v)))]
    got = [c.replace("$<$", "$<$") for c in row_cells(lab)]
    check(f"Table II '{lab.strip(chr(92) + ';')}' equals the recomputed values", got == e_)
# 5i the fixed-PD rows (old campaign, unchanged) still show Izhikevich ahead of CMG, as the text says ('leads on the fixed-PD baseline')
gi = row_cells(r"\;\;$\Delta$, Izhikevich--PES, fixed PD [\%]")
gc = row_cells(r"\;+CMG--PES & 41.79")
check("fixed-PD rows: Izhikevich geometric-mean reduction above CMG's on both airframes ('leads')",
      float(gi[5]) > float(row_cells(r"\;\;$\Delta$ [\%] & 17.4")[5]) and float(gi[11]) > float(row_cells(r"\;\;$\Delta$ [\%] & 17.4")[11]),
      f"Izh {gi[5]}/{gi[11]} vs CMG {row_cells(chr(92) + ';' + chr(92) + ';$' + chr(92) + 'Delta$ [' + chr(92) + '%] & 17.4')[5]}/{row_cells(chr(92) + ';' + chr(92) + ';$' + chr(92) + 'Delta$ [' + chr(92) + '%] & 17.4')[11]}")

print(f"\n{'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' CHECK(S) FAILED: ' + '; '.join(fails)}")
sys.exit(1 if fails else 0)
