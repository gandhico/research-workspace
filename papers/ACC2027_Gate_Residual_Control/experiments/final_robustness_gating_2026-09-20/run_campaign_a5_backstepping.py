"""Backfill the backstepping/pd family through the SAME new pipeline (run_controllers_gated.py) the other five families
went through, instead of reusing the old sealed run_final_robustness.py data -- for a single, uniform source across all
six rows of the A5 table. Cross-checked against the sealed data (must agree to ~1e-15, matching the earlier one-cell
spot check) as part of the certification pass, not assumed.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_controllers_gated.py"
OUT = HERE / "results" / "a5_controllers" / "backstepping"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ACTUATOR_SCALE = {"x2": 1.0, "cf2-rotor": 1.5}
BETA = {"x2": 0.5, "cf2-rotor": 0.2}


def run(platform, mission, controller):
    out = OUT / platform / mission / controller
    if (out / "summary.json").exists():
        return platform, mission, controller, "skipped_valid"
    out.mkdir(parents=True, exist_ok=True)
    beta = 0.0 if controller == "classical" else BETA[platform]
    cmd = [sys.executable, str(RUNNER), "--platform", platform, "--controller", controller, "--mission", mission,
           "--duration", "45.0", "--dt", "0.0005", "--beta", str(beta), "--learning-rate", "0.0008",
           "--k-error", "8", "--k-rate", "0", "--actuator-scale", str(ACTUATOR_SCALE[platform]), "--seed", "1",
           "--log-every", "10", "--no-neural-archive", "--output", str(out)]
    # deliberately NO --baseline/--bw-scale/--rate-ff/--no-model-ff flags: defaults reproduce the frozen backstepping
    # baseline exactly (this is the property being certified).
    if controller == "nengo-nef-pes":
        cmd += ["--output-gate", "torque-saturation-opposition", "--gate-load-threshold", "1.0",
                "--gate-epsilon-fraction", "0", "--gate-epsilon-nm", "1e-12"]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode:
        raise RuntimeError(f"{platform}/{mission}/{controller}: {done.stderr[-800:]}")
    return platform, mission, controller, "completed"


if __name__ == "__main__":
    jobs = [(p, m, c) for p in PLATFORMS for m in MISSIONS for c in ("classical", "nengo-nef-pes")]
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda j: run(*j), jobs))
    for r in results:
        print(r)

    # certification: every cell must match the sealed run_final_robustness.py data already in final_nominal.csv
    import csv
    NOM = {(r["platform"], r["mission"], r["label"]): float(r["qerr_true_mean_rad"])
           for r in csv.DictReader((HERE / "results" / "final_nominal.csv").open(encoding="utf-8"))}
    print("\n=== certification: new-pipeline backstepping vs sealed data ===")
    worst = 0.0
    for p in PLATFORMS:
        for m in MISSIONS:
            for c, label in (("classical", "pdff_rho3"), ("nengo-nef-pes", "cmg_pes_gated")):
                s = json.loads((OUT / p / m / c / "summary.json").read_text(encoding="utf-8"))
                mine = s["metrics"]["qerr_true_mean_rad"]
                sealed = NOM[(p, m, label)]
                rel = abs(mine - sealed) / sealed
                worst = max(worst, rel)
                flag = "OK" if rel < 1e-9 else "CHECK"
                print(f"{p:10s}{m:10s}{c:15s} mine={mine*1e3:.6f} sealed={sealed*1e3:.6f} rel={rel:.2e} {flag}")
    print(f"\nworst relative deviation: {worst:.2e}")
