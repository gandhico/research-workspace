"""Amendment A5 (PREREGISTRATION.md section 14): controller-family portability, Stage A.

5 new families (lqr, smc, mpc, nmpc, pid) x 2 platforms x 5 missions x 2 arms (classical, nengo-nef-pes) = 100 runs.
(backstepping/pd is the existing sealed pdff_rho3/cmg_pes_gated data, proven identical, not re-run -- see amendment.)

  python run_campaign_a5.py            # all 100, resumable, <=4 workers
  python run_campaign_a5.py --families lqr smc     # subset
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_controllers_gated.py"
ROOT = HERE / "results" / "a5_controllers"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ACTUATOR_SCALE = {"x2": 1.0, "cf2-rotor": 1.5}
BETA = {"x2": 0.5, "cf2-rotor": 0.2}
ARMS = (("classical", 0.0), ("nengo-nef-pes", None))          # beta filled from BETA[platform] for the CMG arm

FAMILY_ARGS = {
    "lqr": [],
    "smc": ["--smc-eta-frac", "0.5"],
    "mpc": ["--mpc-dt", "0.02", "--mpc-horizon", "120", "--mpc-q-rate", "0.0"],
    "nmpc": ["--nmpc-dt", "0.06", "--nmpc-horizon", "5", "--nmpc-grid", "3", "--nmpc-predict", "policy",
             "--nmpc-offset-frac", "0.1", "--nmpc-rate-weight", "2.0", "--baseline-rate-hz", "100"],
    "pid": ["--baseline", "pd", "--ki-factor", "0.3", "--antiwindup", "rotor"],
}


def family_flag(family: str) -> list[str]:
    if family == "pid":
        return FAMILY_ARGS["pid"]
    return ["--baseline", family] + FAMILY_ARGS[family]


def run_one(family, platform, mission, controller):
    out = ROOT / family / platform / mission / controller
    if (out / "summary.json").exists():
        return family, platform, mission, controller, "skipped_valid"
    out.mkdir(parents=True, exist_ok=True)
    beta = 0.0 if controller == "classical" else BETA[platform]
    cmd = [sys.executable, str(RUNNER), "--platform", platform, "--controller", controller, "--mission", mission,
           "--duration", "45.0", "--dt", "0.0005", "--beta", str(beta), "--learning-rate", "0.0008",
           "--k-error", "8", "--k-rate", "0", "--actuator-scale", str(ACTUATOR_SCALE[platform]), "--seed", "1",
           "--bw-scale", "3.0", "--rate-ff", "left-neg", "--no-model-ff",
           "--log-every", "10", "--no-neural-archive", "--output", str(out)] + family_flag(family)
    if controller == "nengo-nef-pes":
        cmd += ["--output-gate", "torque-saturation-opposition", "--gate-load-threshold", "1.0",
                "--gate-epsilon-fraction", "0", "--gate-epsilon-nm", "1e-12"]
    t0 = time.time()
    done = subprocess.run(cmd, capture_output=True, text=True)
    (out / "run.log").write_text("$ " + subprocess.list2cmdline(cmd) + "\n\nSTDOUT\n" + done.stdout + "\nSTDERR\n" + done.stderr, encoding="utf-8")
    if done.returncode:
        return family, platform, mission, controller, f"FAILED ({time.time() - t0:.0f}s): {done.stderr[-400:]}"
    return family, platform, mission, controller, f"completed ({time.time() - t0:.0f}s)"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", nargs="+", default=list(FAMILY_ARGS), choices=list(FAMILY_ARGS))
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    jobs = [(f, p, m, c) for f in a.families for p in PLATFORMS for m in MISSIONS for c, _ in ARMS]
    print(f"{len(jobs)} A5 cases ({a.families}); results {ROOT}", flush=True)
    t0 = time.time()
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_one, *j): j for j in jobs}
        for n, fut in enumerate(as_completed(futs), 1):
            f, p, m, c, status = fut.result()
            ok += status.startswith(("completed", "skipped"))
            fail += status.startswith("FAILED")
            print(f"[{n:3d}/{len(jobs)}] {status:40s} {f}/{p}/{m}/{c}  ({time.time() - t0:.0f}s elapsed)", flush=True)
    print(f"done in {time.time() - t0:.0f}s; {ok} ok, {fail} failed", flush=True)
