"""Consistency audit of the paper against the generated result files.

Checks: (1) headline numbers quoted in the text match the result CSVs; (2) no stale claims left over
from earlier versions; (3) every citation resolves and every label is unique; (4) Steven's v9 content
is present; (5) the figures referenced exist on disk.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

PAPER = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\paper\v12_2026-09-16_final")
V9 = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\paper\v9_2026-09-12_steven\ACC2027.tex")
EXP = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\baseline_restatement_2026-09-16")
tex = (PAPER / "ACC2027.tex").read_text(encoding="utf-8")
live = "\n".join(l for l in re.sub(r"\\begin\{comment\}.*?\\end\{comment\}", "", tex, flags=re.S).split("\n")
                 if not l.strip().startswith("%"))
ok, warn = [], []


def check(cond, msg):
    (ok if cond else warn).append(msg)


# ---- 1. headline numbers against the master table
master = {(r["platform"], r["mission"]): r for r in
          csv.DictReader((EXP / "master_table.csv").open(encoding="utf-8"))}
import math
geo = lambda v: math.exp(sum(math.log(x) for x in v) / len(v))  # noqa: E731
MIS = ("roll", "full3", "hard45", "hardstep", "yaw360")
for plat, tag in (("x2", "X2"), ("cf2-rotor", "CF2")):
    g1 = 100 * (1 - geo([float(master[(plat, m)]["CMG_on_PDff_1x"]) for m in MIS])
                / geo([float(master[(plat, m)]["PDff_1x"]) for m in MIS]))
    g3 = 100 * (1 - geo([float(master[(plat, m)]["CMG_on_PDff_3x"]) for m in MIS])
                / geo([float(master[(plat, m)]["PDff_3x"]) for m in MIS]))
    check(f"{g1:.1f}" in live, f"rho=1 geo-mean {g1:.1f}% ({tag}) appears in the text")
    check(f"{g3:.1f}" in live, f"rho=3 geo-mean {g3:.1f}% ({tag}) appears in the text")

# ---- 2. stale claims that must be gone
stale = {
    "Desired-rate feedforward and gyroscopic cancellation are omitted":
        "old claim that feedforward is omitted",
    "Future work includes baselines with desired-rate feedforward":
        "feedforward still listed as future work",
    "Table~\\ref{tab:mujoco}": "reference to the removed primary-matrix table",
    "Table~\\ref{tab:noise}": "reference to the removed noise table",
    "Table~\\ref{tab:ladder}": "reference to the removed ladder table",
    "Table~\\ref{tab:family}": "reference to the removed family table",
}
for pat, why in stale.items():
    check(pat not in live, f"no stale text: {why}")

# ---- 3. labels unique, citations resolve
labels = re.findall(r"\\label\{([^}]*)\}", live)
dupes = {x for x in labels if labels.count(x) > 1}
check(not dupes, f"labels unique (duplicates: {sorted(dupes) or 'none'})")
bib_keys = set(re.findall(r"^@\w+\{([^,]+),", (PAPER / "references.bib").read_text(encoding="utf-8"),
                          flags=re.M))
cited = {k.strip() for c in re.findall(r"\\cite\{([^}]*)\}", live) for k in c.split(",")}
check(cited <= bib_keys, f"all citations in the bib (missing: {sorted(cited - bib_keys) or 'none'})")

# ---- 4. Steven's v9 content present
v9 = V9.read_text(encoding="utf-8")
v9_cited = {k.strip() for c in re.findall(r"\\cite\{([^}]*)\}", v9) for k in c.split(",")}
lost = sorted(v9_cited - cited)
check(not lost, f"no v9 citation dropped (lost: {lost or 'none'})")
for macro in ("certXLA", "certCLA", "certXLr", "certXbetamax", "certCbetamax", "pesCorner",
              "stiffRatioRP", "stiffRatioY", "pesLeakLatched", "certXrstar"):
    check("\\" + macro in live, f"certificate macro \\{macro} used")
for phrase in ("LaSalle", "nonexpansive", "sigma$-modification", "instantaneous",
               "exponential", "Hurwitz"):
    check(phrase in live, f"Steven theory item present: {phrase}")

# ---- 5. graphics exist
for g in re.findall(r"\\includegraphics\[[^]]*\]\{([^}]*)\}", live):
    check((PAPER / g).exists(), f"graphic on disk: {g}")

print("PASS")
for m in ok:
    print("  +", m)
print("\nCHECK" if warn else "\nNo problems found.")
for m in warn:
    print("  -", m)
