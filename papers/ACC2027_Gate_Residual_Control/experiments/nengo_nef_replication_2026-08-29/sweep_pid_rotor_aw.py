"""Re-run the PID factor sweep with rotor-level anti-windup.

The first sweep froze integration only when the baseline torque box clipped.
In this runner the binding limit is the per-rotor ctrl_range after
allocation, so high-gain PID could wind up while every torque axis looked
unsaturated. Hardstep and Hard45 diverged at high factors (sat fraction up to
0.97). This sweep freezes integration whenever any rotor sat at its bound on
the previous step. If the divergence disappears, it was an anti-windup
artifact and must not be reported as a property of PID.

Run:  python sweep_pid_rotor_aw.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
RES = HERE / "results"
ROOT = RES / "pid_baseline_2026-09-10"
OUT = ROOT / "tune_rotor_aw"
PLATFORMS = {"x2": "1.0", "cf2-rotor": "1.5"}
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
FACTORS = (0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0)


def lab(p, m, c):
    return f"{p}_{m}_{c}".replace("-", "_")


def run(p, m, f):
    out = OUT / f"ki{f:g}" / lab(p, m, "classical")
    if not (out / "summary.json").is_file():
        cmd = [PY, str(HERE / "run_mujoco_nef_pid.py"), "--platform", p,
               "--controller", "classical", "--mission", m, "--duration", "45",
               "--dt", "0.0005", "--beta", "0.5", "--learning-rate", "0.0008",
               "--k-error", "8", "--k-rate", "0", "--actuator-scale", PLATFORMS[p],
               "--log-every", "10", "--ki-factor", repr(f), "--antiwindup", "rotor",
               "--no-neural-archive", "--output", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"{out}:\n{r.stderr[-1000:]}")
    return json.loads((out / "summary.json").read_text())


def js(path):
    return json.loads(Path(path).read_text())


if __name__ == "__main__":
    jobs = [(p, m, f) for f in FACTORS for p in PLATFORMS for m in MISSIONS]
    with ThreadPoolExecutor(8) as ex:
        got = dict(zip(jobs, ex.map(lambda j: run(*j), jobs)))

    for p in PLATFORMS:
        print(f"\n{p}: PID with ROTOR anti-windup, mean error [rad]  "
              f"(torque-AW value in brackets where it diverged)")
        print(f"{'factor':>7s}" + "".join(f"{m:>18s}" for m in MISSIONS))
        for f in FACTORS:
            cells = []
            for m in MISSIONS:
                v = got[(p, m, f)]["qerr_mean_rad"]
                old = ROOT / "tune" / f"ki{f:g}" / lab(p, m, "classical") / "summary.json"
                ov = js(old)["qerr_mean_rad"] if old.is_file() else None
                note = f"[{ov:.3f}]" if ov is not None and ov > 1.0 else ""
                cells.append(f"{v:9.5f}{note:>9s}")
            print(f"{f:7g}" + "".join(cells))

    print("\nper-mission oracle (best of PD, torque-AW PID, rotor-AW PID) vs CMG:")
    print(f"{'cell':20s}{'CMG|PD':>9s}{'best PID':>10s}{'factor':>8s}{'AW':>8s}   winner")
    for p in PLATFORMS:
        for m in MISSIONS:
            cands = [(js(RES / "matched_45s" / lab(p, m, "classical") / "summary.json")
                      ["qerr_mean_rad"], 0.0, "-")]
            for f in (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0):
                t = ROOT / "tune" / f"ki{f:g}" / lab(p, m, "classical") / "summary.json"
                if t.is_file():
                    cands.append((js(t)["qerr_mean_rad"], f, "torque"))
            for f in FACTORS:
                cands.append((got[(p, m, f)]["qerr_mean_rad"], f, "rotor"))
            q, f, aw = min(cands)
            cmg = js(ROOT / "regress" / lab(p, m, "nengo_nef_pes") / "summary.json")[
                "qerr_mean_rad"]
            print(f"{p + ' ' + m:20s}{cmg:9.5f}{q:10.5f}{f:8g}{aw:>8s}   "
                  f"{'PID' if q < cmg else 'CMG'}  ({100 * (1 - cmg / q):+.0f}% CMG vs best PID)")
