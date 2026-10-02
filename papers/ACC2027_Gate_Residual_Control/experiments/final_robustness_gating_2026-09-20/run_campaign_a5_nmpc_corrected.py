"""Corrected NMPC re-run for Amendment A5, following the 2026-09-24 audit (audit_nmpc_anomaly_2026-09-24.py,
AUDIT_NMPC_HOLD_RATE_2026-09-24.md): the original A5 NMPC row used --baseline-rate-hz 100 (a leftover from an
older, unrelated exploratory NMPC-only setting) while every other family, MPC included, ran at full rate
(rate=0, default). A two-way ablation on X2 Roll/Yaw360 confirmed the hold, not NMPC's predictive machinery, is
the cause of the A5 NMPC anomaly: removing it from NMPC restores the 40-78% band every other family shows;
imposing the same hold on MPC reproduces the identical near-zero/negative failure. This re-runs NMPC's full row
(2 platforms x 5 missions x 2 arms = 20 cells) at full rate, matching the other five families' methodology, into
a NEW output directory -- the original 100Hz-hold data in results/a5_controllers/nmpc/ is kept, not overwritten,
for the audit trail.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_controllers_gated.py"
ROOT = HERE / "results" / "a5_controllers_nmpc_corrected"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ACTUATOR_SCALE = {"x2": 1.0, "cf2-rotor": 1.5}
BETA = {"x2": 0.5, "cf2-rotor": 0.2}
NMPC_ARGS = ["--nmpc-dt", "0.06", "--nmpc-horizon", "5", "--nmpc-grid", "3", "--nmpc-predict", "policy",
             "--nmpc-offset-frac", "0.1", "--nmpc-rate-weight", "2.0"]   # no --baseline-rate-hz: default 0 = full rate


def run_one(platform, mission, controller):
    out = ROOT / platform / mission / controller
    if (out / "summary.json").exists():
        return platform, mission, controller, "skipped_valid"
    out.mkdir(parents=True, exist_ok=True)
    beta = 0.0 if controller == "classical" else BETA[platform]
    cmd = [sys.executable, str(RUNNER), "--platform", platform, "--controller", controller, "--mission", mission,
           "--duration", "45.0", "--dt", "0.0005", "--beta", str(beta), "--learning-rate", "0.0008",
           "--k-error", "8", "--k-rate", "0", "--actuator-scale", str(ACTUATOR_SCALE[platform]), "--seed", "1",
           "--baseline", "nmpc", "--bw-scale", "3.0", "--rate-ff", "left-neg", "--no-model-ff",
           "--log-every", "10", "--no-neural-archive", "--output", str(out)] + NMPC_ARGS
    if controller == "nengo-nef-pes":
        cmd += ["--output-gate", "torque-saturation-opposition", "--gate-load-threshold", "1.0",
                "--gate-epsilon-fraction", "0", "--gate-epsilon-nm", "1e-12"]
    t0 = time.time()
    done = subprocess.run(cmd, capture_output=True, text=True)
    (out / "run.log").write_text("$ " + subprocess.list2cmdline(cmd) + "\n\nSTDOUT\n" + done.stdout + "\nSTDERR\n" + done.stderr, encoding="utf-8")
    if done.returncode:
        return platform, mission, controller, f"FAILED ({time.time() - t0:.0f}s): {done.stderr[-400:]}"
    return platform, mission, controller, f"completed ({time.time() - t0:.0f}s)"


if __name__ == "__main__":
    jobs = [(p, m, c) for p in PLATFORMS for m in MISSIONS for c in ("classical", "nengo-nef-pes")]
    print(f"{len(jobs)} corrected-NMPC cases; results -> {ROOT}", flush=True)
    t0 = time.time()
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_one, *j): j for j in jobs}
        for n, fut in enumerate(as_completed(futs), 1):
            p, m, c, status = fut.result()
            ok += status.startswith(("completed", "skipped"))
            fail += status.startswith("FAILED")
            print(f"[{n:2d}/{len(jobs)}] {status:40s} {p}/{m}/{c}  ({time.time() - t0:.0f}s elapsed)", flush=True)
    print(f"done in {time.time() - t0:.0f}s; {ok} ok, {fail} failed", flush=True)

    if fail == 0:
        print("\n=== corrected NMPC vs original 100Hz-hold NMPC vs MPC (for context) ===")
        OLD = HERE / "results" / "a5_controllers"

        def qerr(p):
            return json.loads(p.read_text(encoding="utf-8"))["metrics"]["qerr_true_mean_rad"]

        for plat in PLATFORMS:
            for m in MISSIONS:
                b_new = qerr(ROOT / plat / m / "classical" / "summary.json") * 1e3
                c_new = qerr(ROOT / plat / m / "nengo-nef-pes" / "summary.json") * 1e3
                d_new = 100 * (1 - c_new / b_new)
                b_old = qerr(OLD / "nmpc" / plat / m / "classical" / "summary.json") * 1e3
                c_old = qerr(OLD / "nmpc" / plat / m / "nengo-nef-pes" / "summary.json") * 1e3
                d_old = 100 * (1 - c_old / b_old)
                print(f"{plat:10s}{m:10s} old(100Hz): {b_old:9.3f}->{c_old:9.3f} {d_old:+7.1f}%   "
                      f"new(full-rate): {b_new:9.3f}->{c_new:9.3f} {d_new:+7.1f}%")
