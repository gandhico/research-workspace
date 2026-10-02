"""Reference-rate feedforward baseline and CMG on top of it.

select_rate_ff.py found that PD with rate-error damping, -kw*(omega-omega_d),
beats CMG-PES on every moving-reference X2 mission. Two modes passed; mode
'left-neg' dominates on the multi-axis missions (Full3, Hard45) and ties on
the single-axis ones, where left and right products coincide. This script:

  1. held-out check: left-neg on the four CF2 moving-reference missions,
     which played no part in the selection;
  2. Hardstep on both platforms, where omega_d is zero between steps and
     feedforward cannot help;
  3. CMG-PES on top of PD + feedforward on all ten cells: does the learned
     residual still add anything once the baseline uses the rate error the
     paper defines in eq. (6)?

Run:  python run_ff_cmg.py
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
RES = HERE / "results"
ROOT = RES / "pid_baseline_2026-09-10"
OUT = ROOT / "rate_ff_left_neg"
MODE = "left-neg"
SCALE = {"x2": "1.0", "cf2-rotor": "1.5"}
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")


def lab(p, m, c):
    return f"{p}_{m}_{c}".replace("-", "_")


def js(path):
    return json.loads(Path(path).read_text())


def run(p, m, ctl):
    out = OUT / lab(p, m, ctl)
    sel = ROOT / "rate_ff_select" / MODE / f"{p}_{m}".replace("-", "_")
    if ctl == "classical" and (sel / "summary.json").is_file():
        return js(sel / "summary.json")          # already run during selection
    if not (out / "summary.json").is_file():
        cmd = [PY, str(HERE / "run_mujoco_nef_pid.py"), "--platform", p,
               "--controller", ctl, "--mission", m, "--duration", "45",
               "--dt", "0.0005", "--beta", "0.5", "--learning-rate", "0.0008",
               "--k-error", "8", "--k-rate", "0", "--actuator-scale", SCALE[p],
               "--log-every", "10", "--rate-ff", MODE,
               "--no-neural-archive", "--output", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"{out}:\n{r.stderr[-1000:]}")
    return js(out / "summary.json")


if __name__ == "__main__":
    jobs = [(p, m, c) for p in SCALE for m in MISSIONS
            for c in ("classical", "nengo-nef-pes")]
    # 4 workers: 10 concurrent Nengo+MuJoCo processes exhausted RAM on
    # 2026-09-10 ("engine error: Could not allocate memory" at model load).
    with ThreadPoolExecutor(4) as ex:
        got = dict(zip(jobs, ex.map(lambda j: run(*j), jobs)))

    rows = []
    for p in SCALE:
        for m in MISSIONS:
            pd = js(RES / "matched_45s" / lab(p, m, "classical") / "summary.json")
            cmg = js(ROOT / "regress" / lab(p, m, "nengo_nef_pes") / "summary.json")
            pid = js(ROOT / "tune" / "ki0.05" / lab(p, m, "classical") / "summary.json")
            ff = got[(p, m, "classical")]
            ffc = got[(p, m, "nengo-nef-pes")]
            rows.append({
                "platform": p, "mission": m,
                "PD": pd["qerr_mean_rad"], "PID_0.05": pid["qerr_mean_rad"],
                "CMG_on_PD": cmg["qerr_mean_rad"],
                "PD_ff": ff["qerr_mean_rad"], "CMG_on_PD_ff": ffc["qerr_mean_rad"],
                "sat_PD": pd["saturation_fraction"], "sat_PD_ff": ff["saturation_fraction"],
                "sat_CMG_on_PD_ff": ffc["saturation_fraction"],
                "tau_PD": pd["tau_mean_Nm"], "tau_PD_ff": ff["tau_mean_Nm"],
                "tau_CMG_on_PD": cmg["tau_mean_Nm"],
                "residual_CMG_on_PD": cmg["residual_mean_Nm"],
                "residual_CMG_on_PD_ff": ffc["residual_mean_Nm"],
            })
    with (ROOT / "rate_ff_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{'cell':20s}{'PD':>9s}{'PID.05':>9s}{'CMG|PD':>9s}{'PD+ff':>9s}"
          f"{'CMG|ff':>9s}{'ff vs PD':>10s}{'CMG|ff vs ff':>14s}{'sat ff':>8s}")
    for r in rows:
        print(f"{r['platform'] + ' ' + r['mission']:20s}{r['PD']:9.5f}"
              f"{r['PID_0.05']:9.5f}{r['CMG_on_PD']:9.5f}{r['PD_ff']:9.5f}"
              f"{r['CMG_on_PD_ff']:9.5f}"
              f"{100 * (1 - r['PD_ff'] / r['PD']):9.1f}%"
              f"{100 * (1 - r['CMG_on_PD_ff'] / r['PD_ff']):13.1f}%"
              f"{r['sat_PD_ff']:8.4f}")
    held = [r for r in rows if r["platform"] == "cf2-rotor" and r["mission"] != "hardstep"]
    ok = all(r["PD_ff"] < r["PD"] for r in held)
    print(f"\nheld-out CF2 check of '{MODE}': {'PASSED' if ok else 'FAILED'} "
          f"(reduces error on all four moving-reference CF2 missions)")
    print(f"written {ROOT / 'rate_ff_summary.csv'}")
