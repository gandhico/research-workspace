"""v5 campaign driver (docs/PLAN.md v5 declaration). Resumable, <=4 parallel (project rule).

Full grid for lqr/backstepping/mpc (fast under apa): 2 platforms x 5 missions x 4 arms = 120 cells.
NMPC pilot only (X2, hard45+roll, 4 arms = 8 cells): the smoke test showed ~884s for a 3s NMPC run under apa
(vs. ~44-53 s/sim-s for NMPC under clip allocation in the ACC2027 A5 campaign) -- a full 45s cell extrapolates
to ~3.7 hours; 40 cells is not practical in this pass. Disclosed scope reduction, not a methodology change.
"""
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_dual_v5.py"
PY = r"C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe"
ROOT = HERE.parent.parent / "results" / "v5_2026-09-25"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ARMS = ("base", "res", "st", "dual")
FULL_FAMILIES = ("lqr", "backstepping", "mpc")
NMPC_PILOT = ("hard45", "roll")


def jobs():
    out = []
    for fam in FULL_FAMILIES:
        for p in PLATFORMS:
            for m in MISSIONS:
                for arm in ARMS:
                    out.append((fam, p, m, arm))
    for p in ("x2",):
        for m in NMPC_PILOT:
            for arm in ARMS:
                out.append(("nmpc", p, m, arm))
    return out


def run_one(fam, plat, mission, arm):
    out = ROOT / fam / plat / mission / arm
    if (out / "summary.json").exists():
        return fam, plat, mission, arm, "skipped_valid"
    out.mkdir(parents=True, exist_ok=True)
    cmd = [PY, str(RUNNER), "--platform", plat, "--mission", mission, "--family", fam, "--arm", arm,
           "--duration", "45.0", "--output", str(out)]
    t0 = time.time()
    done = subprocess.run(cmd, capture_output=True, text=True)
    (out / "run.log").write_text("$ " + subprocess.list2cmdline(cmd) + "\n\nSTDOUT\n" + done.stdout +
                                  "\nSTDERR\n" + done.stderr, encoding="utf-8")
    if done.returncode:
        return fam, plat, mission, arm, f"FAILED ({time.time() - t0:.0f}s): {done.stderr[-400:]}"
    return fam, plat, mission, arm, f"completed ({time.time() - t0:.0f}s)"


if __name__ == "__main__":
    all_jobs = jobs()
    print(f"{len(all_jobs)} v5 cases; results -> {ROOT}", flush=True)
    t0 = time.time()
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_one, *j): j for j in all_jobs}
        for n, fut in enumerate(as_completed(futs), 1):
            fam, p, m, arm, status = fut.result()
            ok += status.startswith(("completed", "skipped"))
            fail += status.startswith("FAILED")
            print(f"[{n:3d}/{len(all_jobs)}] {status:40s} {fam}/{p}/{m}/{arm}  ({time.time() - t0:.0f}s elapsed)",
                  flush=True)
    print(f"done in {time.time() - t0:.0f}s; {ok} ok, {fail} failed", flush=True)
