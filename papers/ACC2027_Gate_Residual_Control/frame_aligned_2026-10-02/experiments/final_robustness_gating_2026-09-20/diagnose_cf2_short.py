"""Where does the new runner first differ from the archived runner on CF2?  1-s runs, every step logged, exact equality.

Three controllers, same settings (Hard45, beta 0.2, actuator scale 1.5): classical baseline only, CMG-PES, Izhikevich-PES.
If the baseline-only pair already differs in the last bits, the difference is in the shared runner path (not in the adapter).
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ARCH = HERE.parent / "nengo_nef_replication_2026-08-29" / "run_mujoco_nef_baselines.py"
NEW = {"classical": HERE / "run_final_robustness.py", "nengo-nef-pes": HERE / "run_final_robustness.py",
       "nengo-izhikevich-pes": HERE / "run_izh_robustness.py"}
ROOT = HERE / "results_validation_izh" / "short_cf2"
COMMON = ["--platform", "cf2-rotor", "--mission", "hard45", "--duration", "1.0", "--dt", "0.0005", "--beta", "0.2",
          "--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0", "--actuator-scale", "1.5", "--seed", "1",
          "--log-every", "1", "--no-neural-archive"]
ARCH_EXTRA = ["--baseline", "backstepping", "--bw-scale", "3.0", "--rate-ff", "left-neg", "--no-model-ff"]


def go(which, ctrl):
    out = ROOT / f"{which}_{ctrl}"
    out.mkdir(parents=True, exist_ok=True)
    runner = ARCH if which == "archived" else NEW[ctrl]
    extra = ARCH_EXTRA if which == "archived" else []
    cmd = [sys.executable, str(runner), "--controller", ctrl, *COMMON, *extra, "--output", str(out)]
    done = subprocess.run(cmd, capture_output=True, text=True, cwd=runner.parent)
    if done.returncode:
        raise RuntimeError(f"{which} {ctrl}: {done.stderr[-800:]}")
    return pd.read_csv(out / "trace.csv")


PAIRS = [("qerr", "qerr_true_rad"), ("tau0_x", "tau0_x"), ("tau0_y", "tau0_y"), ("tau0_z", "tau0_z"), ("omega_x", "omega_true_x"),
         ("omega_y", "omega_true_y"), ("omega_z", "omega_true_z"), ("residual_x", "realized_residual_x"),
         ("residual_y", "realized_residual_y"), ("z", "z"), ("activity_0", "activity_0"), ("decoder_w_0", "decoder_w_0")]

if __name__ == "__main__":
    jobs = [(w, c) for c in NEW for w in ("archived", "new")]
    with ThreadPoolExecutor(max_workers=4) as ex:
        res = dict(zip(jobs, ex.map(lambda j: go(*j), jobs)))
    for ctrl in NEW:
        A, N = res[("archived", ctrl)], res[("new", ctrl)]
        print(f"\n=== {ctrl}   rows archived/new: {len(A)}/{len(N)}")
        print(f"{'column':14s}{'first exact diff (row)':>24s}{'t [s]':>9s}{'#rows differing':>17s}{'max |diff|':>13s}")
        for a, n in PAIRS:
            if a not in A or n not in N:
                continue
            m = min(len(A), len(N))
            x, y = A[a].to_numpy()[:m], N[n].to_numpy()[:m]
            idx = np.flatnonzero(x != y)
            print(f"{a:14s}{(int(idx[0]) if idx.size else -1):24d}{(float(A.t[idx[0]]) if idx.size else float('nan')):9.4f}"
                  f"{idx.size:17d}{(np.abs(x - y).max()):13.3e}")
