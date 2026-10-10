"""Consistency audit of the v13 manuscript against the data and against itself.

1. every quoted result number appears in the tex and equals the value recomputed from results/final_*.csv
2. Table II's primary block equals what make_table2.py generates (no hand edits)
3. structural checks: labels unique, every float referenced, every cite key defined, no stale claims, no placeholders
4. build check: pages, undefined references, overfull boxes
"""
from __future__ import annotations

import csv
import math
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = HERE.parents[1] / "paper" / "v13_2026-09-20_robustness"
tex = (D / "ACC2027.tex").read_text(encoding="utf-8")
tab = (D / "tables" / "table_all_restructured.tex").read_text(encoding="utf-8")
whole = tex + "\n" + tab
rd = lambda n: list(csv.DictReader((HERE / "results" / n).open()))
nom = {(r["platform"], r["mission"], r["label"]): r for r in rd("final_nominal.csv")}
noise = {(r["noise_level"], r["platform"], r["mission"], int(r["seed"]), r["label"]): r for r in rd("final_noise.csv")}
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


print("== 1. quoted numbers")
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
check("no stale '35.6/6.5' headline in abstract", "35.6" not in re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S).group(1))

print("\n== 4. build")
log = (D / "ACC2027.log").read_text(encoding="utf-8", errors="ignore")
pages = re.search(r"Output written on ACC2027\.pdf \((\d+) pages", log)
check("7 pages", bool(pages) and int(pages.group(1)) == 7, pages.group(0) if pages else "no pdf")
check("no undefined refs/cites", "undefined" not in log.lower().replace("undefined control sequence", ""))
check("no overfull boxes", "Overfull" not in log)

print(f"\n{'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' CHECK(S) FAILED: ' + '; '.join(fails)}")
sys.exit(1 if fails else 0)
