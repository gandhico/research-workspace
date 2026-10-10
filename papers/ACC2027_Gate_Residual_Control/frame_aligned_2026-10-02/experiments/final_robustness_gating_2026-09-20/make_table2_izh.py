"""v14: rewrite the last block of Table II ("strongest rival basis and realized effort") from the A3 numbers.

New rows (rho = 3, gated, same protocol as the CMG rows) come from results/izh_a3_numbers.json (written by analyze_izh_a3.py from the
campaign CSVs); the two fixed-PD Izhikevich rows are kept verbatim from the current table and relabelled; the fixed-PD effort rows are
replaced by the effort measured on the rho = 3 gated runs (same definition: RMS residual / per-axis bound).

usage: python make_table2_izh.py <path/to/tables/table_all_restructured.tex> [--write]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NUM = json.loads((HERE / "results" / "izh_a3_numbers.json").read_text(encoding="utf-8"))
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
PLATS = ("x2", "cf2-rotor")


def delta(v: float) -> str:
    return f"{v:.0f}" if abs(v) >= 100 else f"{v:.1f}"


def eff(v: float) -> str:
    return r"$<$0.001" if v < 5e-4 else f"{v:.3f}"


def delta_row(label: str) -> str:
    cells = []
    for p in PLATS:
        cells += [delta(NUM["nominal"][f"{p}/{m}"]["izh_gated_red"]) for m in MISSIONS]
        cells.append(rf"\emph{{{delta(NUM['summary'][p]['geo_red_izh'])}}}")
    return label + " & " + " & ".join(cells) + r"\\"


def noise_row(label: str) -> str:
    """Realistic-noise reduction (geometric mean of the paired per-seed ratios, seeds 1-3); Full3 and Yaw360 were not run."""
    cells = []
    for p in PLATS:
        for m in MISSIONS:
            k = f"{p}/{m}"
            cells.append(delta(NUM["noise"][k]["izh_gm_red"]) if k in NUM["noise"] else "--")
        cells.append(r"\emph{--}")
    return label + " & " + " & ".join(cells) + r"\\"


def effort_row(label: str, key: str) -> str:
    cells = []
    for p in PLATS:
        cells += [eff(v) for v in NUM["summary"][p][f"effort_{key}_by_mission"]]
        cells.append(rf"\emph{{{eff(NUM['summary'][p]['effort_' + key])}}}")
    return label + " & " + " & ".join(cells) + r"\\"


def main() -> None:
    path = Path(sys.argv[1])
    tex = path.read_text(encoding="utf-8")
    head = r"\multicolumn{13}{@{}l}{\textit{Same fixed-PD baseline and bounded interface: strongest rival basis and realized effort}}\\[1pt]"
    assert tex.count(head) == 1
    a = tex.index(head)
    b = tex.index(r"\bottomrule", a)
    old = tex[a:b].split("\n")
    keep_pes = [l for l in old if l.startswith(r"\;\;$\Delta$, Izhikevich--PES [\%] &")]
    keep_fix = [l for l in old if l.startswith(r"\;\;$\Delta$, Izhikevich fixed [\%] &")]
    assert len(keep_pes) == 1 and len(keep_fix) == 1
    new_rows = [
        r"\multicolumn{13}{@{}l}{\textit{Strongest rival basis (Izhikevich): reduction and realized effort}}\\[1pt]",
        delta_row(r"\;\;$\Delta$, Izhikevich--PES, $\rho=3$ [\%]"),
        noise_row(r"\;\;$\Delta$, Izhikevich--PES, $\rho=3$, realistic noise [\%]"),
        keep_pes[0].replace(r"Izhikevich--PES [\%]", r"Izhikevich--PES, fixed PD [\%]"),
        keep_fix[0].replace(r"Izhikevich fixed [\%]", r"Izhikevich fixed dec., fixed PD [\%]"),
        effort_row(r"\;\;effort, CMG--PES, $\rho=3$", "cmg"),
        effort_row(r"\;\;effort, Izhikevich--PES, $\rho=3$", "izh"),
    ]
    out = tex[:a] + "\n".join(new_rows) + "\n" + tex[b:]
    print("\n".join(new_rows))
    if "--write" in sys.argv:
        path.write_text(out, encoding="utf-8")
        print("written", path)


if __name__ == "__main__":
    main()
