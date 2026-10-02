"""Single-run reproducibility floor of the Izhikevich cells (amendment A3.1, decision c).

For the four multi-axis nominal cells (Full3, Hard45; X2 beta .5, CF2 beta .2; gated arm, i.e. exactly the A3 cells) the initial attitude is
perturbed by k * 1e-12 deg, k = 1..6 (about 2e-14 rad per step of k: numerical dust, far below anything physical).  The spread of the
45-s mean error over {A3 run, 6 perturbed runs} is the floor below which a single-run difference between Izhikevich cells, or between
Izhikevich and CMG, must not be interpreted.  24 runs, 4 workers.
"""
import csv
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_izh_robustness.py"
R = HERE / "results"
ROOT = HERE / "results_validation_izh" / "floor"
CELLS = [("x2", "full3", 0.5, 1.0), ("x2", "hard45", 0.5, 1.0), ("cf2-rotor", "full3", 0.2, 1.5), ("cf2-rotor", "hard45", 0.2, 1.5)]
EPS = [1e-12 * k for k in range(1, 7)]
GATE = ["--output-gate", "torque-saturation-opposition", "--gate-load-threshold", "1.0", "--gate-epsilon-fraction", "0",
        "--gate-epsilon-nm", "1e-12"]


def run(job):
    plat, mission, beta, scale, eps = job
    out = ROOT / f"{plat}_{mission}_eps{eps:.0e}"
    if not (out / "summary.json").exists():
        out.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(RUNNER), "--platform", plat, "--controller", "nengo-izhikevich-pes", "--mission", mission,
               "--duration", "45.0", "--dt", "0.0005", "--beta", str(beta), "--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0",
               "--actuator-scale", str(scale), "--seed", "1", "--initial-angle-deg", repr(eps), *GATE, "--log-every", "10",
               "--no-neural-archive", "--output", str(out)]
        done = subprocess.run(cmd, capture_output=True, text=True)
        if done.returncode:
            raise RuntimeError(done.stderr[-800:])
    return json.loads((out / "summary.json").read_text(encoding="utf-8"))["metrics"]["qerr_true_mean_rad"]


if __name__ == "__main__":
    jobs = [(p, m, b, s, e) for (p, m, b, s) in CELLS for e in EPS]
    with ThreadPoolExecutor(max_workers=4) as ex:
        vals = list(ex.map(run, jobs))
    nom = {(r["platform"], r["mission"]): float(r["qerr_true_mean_rad"]) for r in csv.DictReader((R / "final_nominal.csv").open(encoding="utf-8"))
           if r["label"] == "pdff_rho3"}
    a3 = {}
    for r in csv.DictReader((R / "results_izh_a3_all.csv").open(encoding="utf-8")):
        if r["campaign"] == "nominal" and r["label"].startswith("izh_pes_gated"):
            a3[(r["platform"], r["mission"])] = float(r["qerr_true_mean_rad"])
    lines = ["Single-run floor of the Izhikevich cells: 45-s mean error over the A3 run + 6 perturbed initial attitudes (k * 1e-12 deg)\n",
             f"{'cell':22s}{'A3 run':>9s}{'mean':>9s}{'sd':>8s}{'sd/mean':>9s}{'min':>8s}{'max':>8s}{'sd in pp of PD+ff':>19s}   [mrad]"]
    summary = {}
    for i, (p, m, b, s) in enumerate(CELLS):
        v = np.array(vals[i * len(EPS):(i + 1) * len(EPS)])
        allv = np.r_[a3[(p, m)], v]
        pdff = nom[(p, m)]
        sd = allv.std(ddof=1)
        summary[f"{p}/{m}"] = {"a3": a3[(p, m)] * 1e3, "values_mrad": (allv * 1e3).tolist(), "mean_mrad": allv.mean() * 1e3, "sd_mrad": sd * 1e3,
                               "sd_rel": sd / allv.mean(), "sd_pp_of_pdff": 100 * sd / pdff, "range_pp_of_pdff": 100 * (allv.max() - allv.min()) / pdff}
        lines.append(f"{p + ' ' + m:22s}{a3[(p, m)] * 1e3:9.3f}{allv.mean() * 1e3:9.3f}{sd * 1e3:8.3f}{100 * sd / allv.mean():8.2f}%"
                     f"{allv.min() * 1e3:8.3f}{allv.max() * 1e3:8.3f}{100 * sd / pdff:18.2f}")
    text = "\n".join(lines)
    (ROOT / "floor_result.txt").write_text(text + "\n", encoding="utf-8")
    (ROOT / "floor_result.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(text)
