"""Run the two cells most likely to behave badly under sensor noise.

Hardstep is the only mission with nonzero actuator-bound occupancy, and
Yaw360 carries the paper's largest reported reduction. If noise is going to
cost anything, it costs it here. Both platforms, both controllers, one seed:
eight 45-s runs, about four minutes.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
OUT = HERE / "results" / "noise_check_2026-09-05"

ATT_NOISE = 0.02   # rad, about 1.1 deg
RATE_NOISE = 0.05  # rad/s
SEED = 7

CELLS = [(p, m, c)
         for p in ("x2", "cf2-rotor")
         for m in ("hardstep", "yaw360")
         for c in ("classical", "nengo-nef-pes")]


def run(platform: str, mission: str, controller: str) -> float:
    out = OUT / f"{platform}_{mission}_{controller}"
    cmd = [PY, str(HERE / "run_mujoco_nef.py"),
           "--platform", platform, "--controller", controller,
           "--mission", mission, "--duration", "45",
           "--attitude-noise-std", str(ATT_NOISE),
           "--rate-noise-std", str(RATE_NOISE),
           "--seed", str(SEED),
           "--actuator-scale", "1.5" if platform == "cf2-rotor" else "1.0",
           "--no-neural-archive", "--output", str(out)]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  FAILED {platform}/{mission}/{controller}")
        print(r.stderr[-1500:])
        return float("nan")
    summary = json.loads((out / "summary.json").read_text())
    print(f"  {platform:10s} {mission:9s} {controller:14s} "
          f"qerr_mean={summary['qerr_mean_rad']:.6f}  "
          f"sat={summary.get('saturation_fraction', 0):.5f}  "
          f"[{time.time() - t0:.0f}s]", flush=True)
    return summary["qerr_mean_rad"]


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"noise: attitude {ATT_NOISE} rad, rate {RATE_NOISE} rad/s, seed {SEED}")
    print(f"paper noise-free reference: X2 Hardstep 20.94%, Yaw360 60.58%; "
          f"CF2 Hardstep 18.37%, Yaw360 60.60%\n")
    got: dict[tuple[str, str, str], float] = {}
    for cell in CELLS:
        got[cell] = run(*cell)

    print("\n" + "=" * 66)
    print(f"{'platform':11s}{'mission':10s}{'PD':>11s}{'CMG-PES':>11s}"
          f"{'reduction':>12s}")
    print("=" * 66)
    for p in ("x2", "cf2-rotor"):
        for m in ("hardstep", "yaw360"):
            pd = got[(p, m, "classical")]
            nn = got[(p, m, "nengo-nef-pes")]
            red = 100.0 * (1.0 - nn / pd) if pd else float("nan")
            print(f"{p:11s}{m:10s}{pd:11.6f}{nn:11.6f}{red:11.2f}%")
    json.dump({f"{p}/{m}/{c}": v for (p, m, c), v in got.items()},
              (OUT / "noise_check_summary.json").open("w"), indent=2)
    print(f"\nwritten to {OUT}")
