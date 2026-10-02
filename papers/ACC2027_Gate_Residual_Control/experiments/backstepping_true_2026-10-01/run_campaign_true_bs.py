"""Campaign: recursive backstepping (plain, adaptive) x {X2, CF2} x 5 missions x {classical, gated CMG-PES}.

Identical settings to run_campaign_a5.py (45 s, dt 5e-4, rho 3, rate feedforward left-neg, beta .5 X2 / .2 CF2,
eta 8e-4, k_e 8, gate on in the CMG arm, seed 1, full-rate nominal law). 40 runs, resumable, <= 4 workers.
"""
from __future__ import annotations

import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_true_backstepping.py"
ROOT = HERE / "results" / "campaign"
FAMILIES = ("bs-true", "bs-adaptive")
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ACTUATOR_SCALE = {"x2": 1.0, "cf2-rotor": 1.5}
BETA = {"x2": 0.5, "cf2-rotor": 0.2}


def run_one(family, platform, mission, controller):
    out = ROOT / family / platform / mission / controller
    if (out / "summary.json").exists():
        return family, platform, mission, controller, "skipped_valid"
    out.mkdir(parents=True, exist_ok=True)
    beta = 0.0 if controller == "classical" else BETA[platform]
    cmd = [sys.executable, str(RUNNER), "--platform", platform, "--controller", controller, "--mission", mission,
           "--duration", "45.0", "--dt", "0.0005", "--beta", str(beta), "--learning-rate", "0.0008",
           "--k-error", "8", "--k-rate", "0", "--actuator-scale", str(ACTUATOR_SCALE[platform]), "--seed", "1",
           "--baseline", family, "--bw-scale", "3.0", "--rate-ff", "left-neg", "--no-model-ff",
           "--log-every", "10", "--no-neural-archive", "--output", str(out)]
    if controller == "nengo-nef-pes":
        cmd += ["--output-gate", "torque-saturation-opposition", "--gate-load-threshold", "1.0",
                "--gate-epsilon-fraction", "0", "--gate-epsilon-nm", "1e-12"]
    t0 = time.time()
    done = subprocess.run(cmd, capture_output=True, text=True)
    (out / "run.log").write_text("$ " + subprocess.list2cmdline(cmd) + "\n\nSTDOUT\n" + done.stdout + "\nSTDERR\n"
                                 + done.stderr, encoding="utf-8")
    if done.returncode:
        return family, platform, mission, controller, f"FAILED ({time.time() - t0:.0f}s): {done.stderr[-300:]}"
    return family, platform, mission, controller, f"completed ({time.time() - t0:.0f}s)"


if __name__ == "__main__":
    jobs = [(f, p, m, c) for f in FAMILIES for p in PLATFORMS for m in MISSIONS for c in ("classical", "nengo-nef-pes")]
    print(f"{len(jobs)} cases -> {ROOT}", flush=True)
    t0, ok, fail = time.time(), 0, 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(run_one, *j) for j in jobs]
        for n, fut in enumerate(as_completed(futs), 1):
            f, p, m, c, status = fut.result()
            ok += status.startswith(("completed", "skipped")); fail += status.startswith("FAILED")
            print(f"[{n:2d}/{len(jobs)}] {status:28s} {f}/{p}/{m}/{c} ({time.time() - t0:.0f}s)", flush=True)
    print(f"done in {time.time() - t0:.0f}s; {ok} ok, {fail} failed", flush=True)
