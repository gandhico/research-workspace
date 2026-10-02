"""v6 campaign (docs/PLAN.md v5 deep-dive addendum; docs/ARCHITECTURE_MATH.md sec.8). Two changes vs v5,
together: (1) e_ref set per family+platform from that cell's own v5 `*_base` Hard45 mean error (read from disk,
not hand-transcribed); (2) sat_gate_axes=True -- gain increases blocked on axes already at their torque box
last step (gate_multiplier in run_dual_v5.py).

G11 (run first, blocking): reproduce results/v5_regression_check exactly with the gate off -- already confirmed
bit-exact in this session; this script assumes that check stands and does not repeat it.
"""
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = r"C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe"
V5_ROOT = HERE.parent.parent / "results" / "v5_2026-09-25"
ROOT = HERE.parent.parent / "results" / "v6_2026-09-25"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ARMS = ("base", "res", "st", "dual")
FULL_FAMILIES = ("lqr", "backstepping", "mpc")
NMPC_PILOT = ("hard45", "roll")


def e_ref_for(fam: str, plat: str) -> float:
    p = V5_ROOT / fam / plat / "hard45" / "base" / "summary.json"
    return json.loads(p.read_text(encoding="utf-8"))["qerr_mean_rad"]


def jobs():
    out = []
    for fam in FULL_FAMILIES:
        for p in PLATFORMS:
            e = e_ref_for(fam, p)
            for m in MISSIONS:
                for arm in ARMS:
                    out.append((fam, p, m, arm, e))
    e_nmpc = e_ref_for("lqr", "x2")  # nmpc has no full v5 base grid (pilot only); reuse lqr/x2's Hard45 value
    for p in ("x2",):                # (same k1,k2 nominal form and near-identical Hard45 base error, ~10.5-10.6 mrad)
        for m in NMPC_PILOT:
            for arm in ARMS:
                out.append(("nmpc", p, m, arm, e_nmpc))
    return out


def run_one(fam, plat, mission, arm, e_ref):
    out = ROOT / fam / plat / mission / arm
    if (out / "summary.json").exists():
        return fam, plat, mission, arm, "skipped_valid"
    out.mkdir(parents=True, exist_ok=True)
    py = ("from pathlib import Path\n"
          "from run_dual_v5 import run\n"
          "from dual_controller import TunerConfig\n"
          f"tcfg = TunerConfig(v2_gating=True, e_ref={e_ref!r}) if {arm!r} in ('st', 'dual') else None\n"
          f"run({plat!r}, {mission!r}, {fam!r}, {arm!r}, Path({str(out)!r}), duration=45.0, "
          f"tuner=tcfg, sat_gate_axes=True)\n")
    t0 = time.time()
    done = subprocess.run([PY, "-c", py], capture_output=True, text=True, cwd=str(HERE))
    (out / "run.log").write_text(py + "\n\nSTDOUT\n" + done.stdout + "\nSTDERR\n" + done.stderr, encoding="utf-8")
    if done.returncode:
        return fam, plat, mission, arm, f"FAILED ({time.time() - t0:.0f}s): {done.stderr[-400:]}"
    return fam, plat, mission, arm, f"completed ({time.time() - t0:.0f}s)"


if __name__ == "__main__":
    all_jobs = jobs()
    print(f"{len(all_jobs)} v6 cases; results -> {ROOT}", flush=True)
    for fam in FULL_FAMILIES:
        for p in PLATFORMS:
            print(f"  e_ref[{fam}/{p}] = {e_ref_for(fam, p):.6f} rad", flush=True)
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
