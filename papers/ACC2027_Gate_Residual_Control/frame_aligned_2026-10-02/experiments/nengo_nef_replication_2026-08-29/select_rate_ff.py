"""Pick the reference-rate feedforward mode empirically, then verify it.

Step 1 (select). PD + feedforward, ki = 0, on the four moving-reference
missions of X2, for each of the four frame/sign modes. The mode consistent
with the codebase's quaternion convention is the one that REDUCES error on
every mission; a wrong frame or sign cannot do that on all four, because
Full3 and Hard45 exercise all three axes at once. Selection is on X2 only.

Step 2 (verify). The selected mode on CF2, which played no part in choosing
it. If it also reduces error on all four CF2 missions, the choice is not an
artifact of the selection set.

Run:  python select_rate_ff.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
RUNNER = HERE / "run_mujoco_nef_pid.py"
CANON = HERE / "results" / "matched_45s"
ROOT = HERE / "results" / "pid_baseline_2026-09-10" / "rate_ff_select"
MODES = ("left", "right", "left-neg", "right-neg")
MOVING = ("roll", "full3", "hard45", "yaw360")
SCALE = {"x2": "1.0", "cf2-rotor": "1.5"}


def run(plat: str, mis: str, mode: str) -> float:
    out = ROOT / mode / f"{plat}_{mis}".replace("-", "_")
    if not (out / "summary.json").is_file():
        cmd = [PY, str(RUNNER), "--platform", plat, "--controller", "classical",
               "--mission", mis, "--duration", "45", "--dt", "0.0005",
               "--beta", "0.5", "--learning-rate", "0.0008",
               "--k-error", "8", "--k-rate", "0",
               "--actuator-scale", SCALE[plat], "--log-every", "10",
               "--rate-ff", mode, "--no-neural-archive", "--output", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"{plat}/{mis}/{mode}:\n{r.stderr[-1000:]}")
    return json.loads((out / "summary.json").read_text())["qerr_mean_rad"]


def pd(plat: str, mis: str) -> float:
    lab = f"{plat}_{mis}_classical".replace("-", "_")
    return json.loads((CANON / lab / "summary.json").read_text())["qerr_mean_rad"]


def table(plat: str, modes, got) -> None:
    print(f"\n{plat}: PD+feedforward mean error [rad], ki=0")
    print(f"{'mode':>10s}" + "".join(f"{m:>11s}" for m in MOVING) + "   reduces all?")
    print(f"{'PD':>10s}" + "".join(f"{pd(plat, m):11.5f}" for m in MOVING))
    for mode in modes:
        v = [got[(plat, m, mode)] for m in MOVING]
        good = all(x < pd(plat, m) for x, m in zip(v, MOVING))
        print(f"{mode:>10s}" + "".join(f"{x:11.5f}" for x in v)
              + f"   {'YES' if good else 'no'}")


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    jobs = [("x2", m, mode) for mode in MODES for m in MOVING]
    with ThreadPoolExecutor(8) as ex:
        got = dict(zip(jobs, ex.map(lambda j: run(*j), jobs)))
    table("x2", MODES, got)

    winners = [mode for mode in MODES
               if all(got[("x2", m, mode)] < pd("x2", m) for m in MOVING)]
    if len(winners) != 1:
        sys.exit(f"\nselection ambiguous or empty: {winners} -- inspect before use")
    mode = winners[0]
    print(f"\nselected on X2: {mode}")

    vjobs = [("cf2-rotor", m, mode) for m in MOVING]
    with ThreadPoolExecutor(4) as ex:
        got.update(dict(zip(vjobs, ex.map(lambda j: run(*j), vjobs))))
    table("cf2-rotor", (mode,), got)
    ok = all(got[("cf2-rotor", m, mode)] < pd("cf2-rotor", m) for m in MOVING)
    print(f"\nheld-out CF2 check: {'PASSED' if ok else 'FAILED'}")
    (ROOT / "selected_mode.json").write_text(json.dumps(
        {"mode": mode, "cf2_heldout_passed": ok}, indent=2))
