"""Validation gate: the new runner must reproduce the archived rho=3 block of Table II.

The runner in this folder is a re-implementation (Codex, 2026-09-20).  Before any new
result is trusted it must return, for every one of the 10 mission x platform cells and
both arms (PD+ff rho=3, and CMG-PES at the beta the table used), the archived mean
quaternion error in ``baseline_restatement_2026-09-16/master_table.csv``.

A previous re-implementation (hardstep_limits_test.py, 2026-09-16) was caught by exactly
this kind of gate: it omitted the CF2 1.5x rotor authority.  The gate is therefore not
optional and is run BEFORE the campaigns.

Pass criterion (declared before running): relative error <= 1e-4 on every cell.
"""
from __future__ import annotations

import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_campaign as rc  # noqa: E402

MASTER = HERE.parent / "baseline_restatement_2026-09-16" / "master_table.csv"
ROOT = HERE / "results_validation"
TOL = 1e-4
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")


def cases() -> list[rc.Case]:
    out = []
    for platform in rc.PLATFORMS:
        for mission in MISSIONS:
            for controller, label in (("classical", "pdff_rho3"), ("nengo-nef-pes", "cmg_pes")):
                out.append(
                    rc.Case(
                        protocol="validation",
                        campaign="table2_rho3",
                        platform=platform,
                        mission=mission,
                        label=label,
                        controller=controller,
                    )
                )
    return out


def main() -> None:
    master = {(r["platform"], r["mission"]): r for r in csv.DictReader(MASTER.open())}
    todo = cases()
    ROOT.mkdir(parents=True, exist_ok=True)
    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(rc.run_case, c, ROOT, 45.0, 5e-4, False): c for c in todo}
        for i, f in enumerate(as_completed(futs), 1):
            c = futs[f]
            r = f.result()
            results[(c.platform, c.mission, c.label)] = r["summary"]["metrics"]["qerr_true_mean_rad"]
            print(f"[{i:2d}/{len(todo)}] {r['status']:14s} {c.platform:9s} {c.mission:9s} {c.label}", flush=True)

    rows, worst = [], 0.0
    for platform in rc.PLATFORMS:
        for mission in MISSIONS:
            m = master[(platform, mission)]
            for label, col in (("pdff_rho3", "PDff_3x"), ("cmg_pes", "CMG_on_PDff_3x")):
                new, old = results[(platform, mission, label)], float(m[col])
                rel = abs(new - old) / old
                worst = max(worst, rel)
                rows.append(dict(platform=platform, mission=mission, arm=label, archived_rad=old,
                                 new_rad=new, rel_err=rel, beta=rc.BETA[platform] if label == "cmg_pes" else 0,
                                 passed=rel <= TOL))
    with (ROOT / "validation_report.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{'platform':10s}{'mission':10s}{'arm':10s}{'archived':>12s}{'new':>12s}{'rel.err':>11s}")
    for r in rows:
        flag = "" if r["passed"] else "   <-- FAIL"
        print(f"{r['platform']:10s}{r['mission']:10s}{r['arm']:10s}{r['archived_rad']:12.6f}"
              f"{r['new_rad']:12.6f}{r['rel_err']:11.2e}{flag}")
    verdict = "PASS" if worst <= TOL else "FAIL"
    print(f"\nworst relative error {worst:.3e}  (tolerance {TOL:g})  -> {verdict}")
    (ROOT / "validation_verdict.json").write_text(json.dumps(
        {"verdict": verdict, "worst_rel_err": worst, "tolerance": TOL, "n_cells": len(rows)}, indent=2))
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
