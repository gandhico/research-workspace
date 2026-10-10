"""Validation gate for amendment A3: the Izhikevich adapter inside the new runner must reproduce the ARCHIVED runner.

Declared tolerance: relative error <= 1e-9 on the 45-s mean quaternion error, with the gate not acting.
  V1  X2 Hard45   beta 0.5   vs supplementary_izhikevich (archived runner, run 2026-09-21)
  V2  X2 Hardstep beta 0.5   vs supplementary_izhikevich
  V3  CF2 Hard45  beta 0.2   vs a fresh archived-runner run (actuator scale 1.5), executed here
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_campaign as rc  # noqa: E402

rc.RUNNER = HERE / "run_izh_robustness.py"
ARCH_RUNNER = HERE.parent / "nengo_nef_replication_2026-08-29" / "run_mujoco_nef_baselines.py"
ROOT = HERE / "results_validation_izh"
TOL = 1e-9


def mine(platform, mission, beta):
    c = rc.Case(protocol="validation_izh", campaign="izh_vs_archived", platform=platform, mission=mission, label="izh_pes_ungated",
                controller="nengo-izhikevich-pes", beta=beta)
    r = rc.run_case(c, ROOT, 45.0, 5e-4, False)
    s = r["summary"]
    return s["metrics"]["qerr_true_mean_rad"], s["output_gate"]["blocked_fraction_any_axis"]


def archived_cf2():
    out = ROOT / "archived_cf2_hard45_beta0.2"
    out.mkdir(parents=True, exist_ok=True)
    if not (out / "summary.json").exists():
        cmd = [sys.executable, str(ARCH_RUNNER), "--platform", "cf2-rotor", "--controller", "nengo-izhikevich-pes", "--mission", "hard45",
               "--duration", "45.0", "--dt", "0.0005", "--beta", "0.2", "--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0",
               "--actuator-scale", "1.5", "--seed", "1", "--baseline", "backstepping", "--bw-scale", "3.0", "--rate-ff", "left-neg",
               "--no-model-ff", "--log-every", "10", "--no-neural-archive", "--output", str(out)]
        done = subprocess.run(cmd, capture_output=True, text=True, cwd=ARCH_RUNNER.parent)
        if done.returncode:
            raise RuntimeError(done.stderr[-1500:])
    return json.loads((out / "summary.json").read_text(encoding="utf-8"))["qerr_mean_rad"]


def arch_x2(mission):
    p = HERE / "results" / "supplementary_izhikevich" / "x2" / mission / "nengo_izhikevich_pes" / "summary.json"
    return json.loads(p.read_text(encoding="utf-8"))["qerr_mean_rad"]


if __name__ == "__main__":
    ROOT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as ex:
        f1 = ex.submit(mine, "x2", "hard45", 0.5)
        f2 = ex.submit(mine, "x2", "hardstep", 0.5)
        f3 = ex.submit(mine, "cf2-rotor", "hard45", 0.2)
        f4 = ex.submit(archived_cf2)
        (v1, g1), (v2, g2), (v3, g3), a4 = f1.result(), f2.result(), f3.result(), f4.result()
    rows = [("V1 X2 Hard45 b.5", v1, arch_x2("hard45"), g1), ("V2 X2 Hardstep b.5", v2, arch_x2("hardstep"), g2),
            ("V3 CF2 Hard45 b.2", v3, a4, g3)]
    ok = True
    print(f"{'cell':22s}{'new runner':>14s}{'archived':>14s}{'rel.err':>11s}{'gate share':>12s}")
    for name, new, old, gate in rows:
        rel = abs(new - old) / old
        good = rel <= TOL and gate == 0.0
        ok &= good
        print(f"{name:22s}{new * 1e3:14.6f}{old * 1e3:14.6f}{rel:11.2e}{gate:12.3f}   {'OK' if good else 'FAIL'}")
    (ROOT / "validation_verdict.json").write_text(json.dumps({"verdict": "PASS" if ok else "FAIL", "tolerance": TOL,
                                                             "cells": [(n, a, b) for n, a, b, _ in rows]}, indent=2))
    print("\nIZHIKEVICH RUNNER VALIDATED" if ok else "\nVALIDATION FAILED")
    sys.exit(0 if ok else 1)
