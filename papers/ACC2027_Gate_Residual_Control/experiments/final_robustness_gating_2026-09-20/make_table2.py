"""Regenerate the primary block of Table II from the campaign CSVs (no numbers typed by hand).

The ladder (rho = 1), fixed-PD and neuron-family blocks are kept verbatim from the current table file.
The old fixed-PD noise rows (feedback-corrupted error, two seeds) are removed: they are superseded by the
rho = 3 noise rows, which score the TRUE attitude error over paired seeds.

usage: python make_table2.py <path/to/tables/table_all_restructured.tex> [--write]
"""
from __future__ import annotations

import csv
import math
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
PLATFORMS = ("x2", "cf2-rotor")


def gm(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def fmt(v_rad: float) -> str:
    v = v_rad * 1e3
    return f"{v:.3f}" if v < 0.1 else f"{v:.2f}"


def pct(b, c):
    return f"{100 * (1 - c / b):.1f}"


def nominal():
    return {(r["platform"], r["mission"], r["label"]): float(r["qerr_true_mean_rad"])
            for r in csv.DictReader((RES / "final_nominal.csv").open())}


def noise_rows(level: str, n_expected: int):
    path = RES / "final_noise.csv"
    if not path.exists():
        return None
    rows = [r for r in csv.DictReader(path.open()) if r["noise_level"] == level and r["label"] in ("pdff_rho3", "cmg_pes_gated")]
    per = {}
    for r in rows:
        per.setdefault((r["platform"], r["mission"], r["label"]), []).append(float(r["qerr_true_mean_rad"]))
    for p in PLATFORMS:
        for m in MISSIONS:
            for a in ("pdff_rho3", "cmg_pes_gated"):
                if len(per.get((p, m, a), [])) < n_expected:
                    return None
    return {k: st.mean(v) for k, v in per.items()}


DIVERGED = 2.0     # candidate mean error above 2x the baseline's is reported as divergence


def delta_row(label, base, cand):
    cells = []
    for p in PLATFORMS:
        vals_b = [base[(p, m)] for m in MISSIONS]
        vals_c = [cand[(p, m)] for m in MISSIONS]
        div = [c > DIVERGED * b for b, c in zip(vals_b, vals_c)]
        cells += ["div." if d else pct(b, c) for d, b, c in zip(div, vals_b, vals_c)]
        cells += ["--" if any(div) else f"\\emph{{{pct(gm(vals_b), gm(vals_c))}}}"]
    return label + " & " + " & ".join(cells) + r"\\"


def value_row(label, d):
    cells = []
    for p in PLATFORMS:
        vals = [d[(p, m)] for m in MISSIONS]
        cells += [fmt(v) for v in vals] + [f"\\emph{{{fmt(gm(vals))}}}"]
    return label + " & " + " & ".join(cells) + r"\\"


def primary_block() -> tuple[list[str], list[str]]:
    n = nominal()
    base = {(p, m): n[(p, m, "pdff_rho3")] for p in PLATFORMS for m in MISSIONS}
    gated = {(p, m): n[(p, m, "cmg_pes_gated")] for p in PLATFORMS for m in MISSIONS}
    # ungated arm as the paper reported it before: X2 beta=.5, CF2 beta=.05
    ung = {(p, m): n[(p, m, "cmg_pes_table")] for p in PLATFORMS for m in MISSIONS}
    lines = [r"\multicolumn{13}{@{}l}{\textit{Primary baseline: PD + rate feedforward, $\rho=3$ (bandwidth-tuned)}}\\[1pt]",
             value_row("PD+ff", base),
             value_row(r"\;+CMG--PES, gated", gated),
             delta_row(r"\;\;$\Delta$ [\%]", base, gated),
             value_row(r"\;+CMG--PES, ungated$^\ddagger$", ung),
             delta_row(r"\;\;$\Delta$ [\%]", base, ung)]
    missing = []
    for level, n_exp, name in (("realistic", 10, "realistic"), ("moderate", 5, "moderate")):
        d = noise_rows(level, n_exp)
        if d is None:
            missing.append(level)
            continue
        b = {(p, m): d[(p, m, "pdff_rho3")] for p in PLATFORMS for m in MISSIONS}
        c = {(p, m): d[(p, m, "cmg_pes_gated")] for p in PLATFORMS for m in MISSIONS}
        lines.append(delta_row(rf"\;\;$\Delta$, {name} noise [\%]", b, c))
    return lines, missing


def main() -> None:
    path = Path(sys.argv[1])
    write = "--write" in sys.argv
    tex = path.read_text(encoding="utf-8")
    a = tex.index(r"\multicolumn{13}{@{}l}{\textit{Primary baseline")
    b = tex.index(r"\midrule", a)
    lines, missing = primary_block()
    new = tex[:a] + "\n".join(lines) + "\n" + tex[b:]
    # drop the superseded fixed-PD noise rows
    out = []
    dropped = 0
    for ln in new.split("\n"):
        if ln.startswith(r"\;\;$\Delta$, moderate noise [\%] & 32.3") or ln.startswith(r"\;\;$\Delta$, realistic noise [\%] & 32.2"):
            dropped += 1
            continue
        out.append(ln)
    new = "\n".join(out)
    print("noise rows missing (data incomplete):", missing or "none")
    print("old fixed-PD noise rows dropped:", dropped)
    print("\n".join(lines))
    if write:
        path.write_text(new, encoding="utf-8")
        print("written", path)


if __name__ == "__main__":
    main()
