"""The paper's baseline-ladder figure (Fig. 3, variant C) with the reduced CMG in place of CMG, for every mission.

Reuses final_robustness_gating_2026-09-20/make_ladder_figure.py unchanged in layout, colours, zoom windows and legend.
Only the three red runs change:
  level 0  fixed PD + reduced CMG-PES          results/ladder/pd/<p>_<m>_reduced_cmg
  level 1  PD+ff rho=1 + reduced CMG-PES       results/ladder/ff1/<p>_<m>_reduced_cmg
  level 2  PD+ff rho=3 + reduced CMG-PES, gated results/confirm/<platform>/<mission>/lpf-logistic
The blue PD runs and their table check are the original ones.
Outputs: analysis/ladder/<platform>_<mission>_ladder_reduced_C.{png,pdf,json}
"""
from __future__ import annotations

import argparse
import csv
import inspect
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FINAL = HERE.parents[0] / "final_robustness_gating_2026-09-20"
sys.path.insert(0, str(FINAL))
import make_ladder_figure as L  # noqa: E402

LAD = HERE / "results" / "ladder"
CONF = HERE / "results" / "confirm"
_orig_specs = L.run_specs
_orig_label = L.label


def run_specs(platform: str, mission: str, cf2_beta: float) -> list[dict]:
    a = "x2" if platform == "x2" else "cf2_rotor"
    specs = [s for s in _orig_specs(platform, mission, cf2_beta) if s["fam"] == "pd"]
    beta2 = 0.5 if platform == "x2" else 0.2
    return specs + [
        dict(fam="cmg", lvl=0, load=L._load_archived, path=LAD / "pd" / f"{a}_{mission}_reduced_cmg", beta=0.5),
        dict(fam="cmg", lvl=1, load=L._load_archived, path=LAD / "ff1" / f"{a}_{mission}_reduced_cmg", beta=0.5),
        dict(fam="cmg", lvl=2, load=L._load_sealed, path=CONF / platform / mission / "lpf-logistic", beta=beta2),
    ]


def check_means(platform: str, mission: str, runs: list[dict]) -> None:
    """PD runs must match the paper's tables (as in the original); reduced-CMG runs are new and carry no table value."""
    mt = next(r for r in csv.DictReader(L.MASTER.open(encoding="utf-8")) if r["platform"] == platform and r["mission"] == mission)
    fn = {(r["platform"], r["mission"], r["label"]): float(r["qerr_true_mean_rad"]) for r in csv.DictReader((L.R / "final_nominal.csv").open(encoding="utf-8"))}
    want = {0: float(mt["PD"]), 1: float(mt["PDff_1x"]), 2: fn[(platform, mission, "pdff_rho3")]}
    for r in runs:
        r["table_rel_dev"] = abs(r["mean"] - want[r["lvl"]]) / want[r["lvl"]] if r["fam"] == "pd" else None
        if r["fam"] == "pd":
            assert r["table_rel_dev"] <= 1e-4, (platform, mission, r["lvl"], r["mean"])


def label(r: dict, base: float | None) -> str:
    return _orig_label(r, base).replace("CMG-PES", "reduced CMG-PES")


# Same figure function, with the output folder, file stem and the one hard-coded "best CMG run" caption adapted.
src = inspect.getsource(L.ladder_figure)
src = src.replace("best CMG run", "best reduced-CMG run").replace('_ladder_{variant}{suffix}"', '_ladder_reduced_{variant}{suffix}"')
L.run_specs, L.check_means, L.label = run_specs, check_means, label
L.OUT = HERE / "analysis" / "ladder"
exec(compile(src, L.__file__, "exec"), L.__dict__)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platforms", nargs="+", default=["x2", "cf2-rotor"])
    ap.add_argument("--missions", nargs="+", default=["roll", "full3", "hard45", "hardstep", "yaw360"])
    ap.add_argument("--variants", nargs="+", default=["C"])
    a = ap.parse_args()
    for p in a.platforms:
        for m in a.missions:
            for v in a.variants:
                print("wrote", L.ladder_figure(p, m, v))
