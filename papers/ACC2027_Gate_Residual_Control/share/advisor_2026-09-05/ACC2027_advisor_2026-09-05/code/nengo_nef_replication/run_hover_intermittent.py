"""Hover hold under intermittent disturbance: PD versus CMG-PES.

45 s holding the equilibrium attitude, with a multi-sine body torque gated
into four bursts separated by quiet intervals:

    .....#####.....#####.....#####.....#####.....
    0    5   10   15   20   25   30   35   40  45 s

The quiet intervals are the point. Anything can look good while a
disturbance is present; the question for an online-learning residual is what
it does in the silence afterwards, holding a decoder that was adapted under
a disturbance which has just stopped. Three outcomes are distinguishable:

  * the residual decays and the loop returns to baseline behaviour;
  * the residual persists and actively fights the now-undisturbed plant,
    i.e. a learned after-effect;
  * the residual persists harmlessly because the decoder found a correction
    the baseline also wanted.

Run:  python run_hover_intermittent.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
OUT = HERE / "results" / "hover_intermittent_2026-09-05"

TORQUE = 0.15     # N m peak, X2
WARMUP, ON, OFF, RAMP = 5.0, 5.0, 5.0, 0.25


def run(controller: str, torque: float, tag: str) -> Path:
    out = OUT / tag
    cmd = [PY, str(HERE / "run_mujoco_nef_perturbed.py"),
           "--platform", "x2", "--controller", controller,
           "--mission", "hover", "--duration", "45",
           "--disturbance-torque", str(torque),
           "--disturbance-schedule", "intermittent",
           "--disturbance-warmup", str(WARMUP),
           "--disturbance-on", str(ON),
           "--disturbance-off", str(OFF),
           "--disturbance-ramp", str(RAMP),
           "--no-neural-archive", "--output", str(out)]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  FAILED {tag}\n{r.stderr[-1500:]}")
        return out
    d = json.loads((out / "summary.json").read_text())
    print(f"  {tag:26s} qerr_mean={d['qerr_mean_rad']:.6f} "
          f"max={d['qerr_max_rad']:.6f}  [{time.time() - t0:.0f}s]", flush=True)
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"X2 hover, 45 s, disturbance {TORQUE} N m, "
          f"{WARMUP:.0f} s quiet then {ON:.0f} on / {OFF:.0f} off\n")
    run("classical", TORQUE, "pd_disturbed")
    run("nengo-nef-pes", TORQUE, "cmg_disturbed")
    # undisturbed controls, to separate disturbance response from drift
    run("classical", 0.0, "pd_quiet")
    run("nengo-nef-pes", 0.0, "cmg_quiet")
    print(f"\nwritten to {OUT}")
