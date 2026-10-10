"""Final experiment set for the ACC 2027 paper.

Three studies, one driver. Resumable: a cell whose summary.json already
exists is skipped, so an interrupted run can be restarted.

  A. NOISE SENSITIVITY -- the answer to "n = 1 per cell".
     Both platforms, five missions, both controllers, three measurement-noise
     levels. The clean level reproduces the reported table; the two noisy
     levels are run at two seeds each, which is enough to show that seed
     variation is negligible next to noise magnitude (measured: 0.02% vs
     12.8 percentage points on Yaw360).

  B. LONG-HORIZON INTERMITTENT HOVER -- does decoder retention converge?
     45 s showed the silence-floor drift rising monotonically
     (0.14, 0.18, 0.22, 0.26) without plateauing. 180 s and sixteen bursts
     distinguish saturation against the projection bound from unbounded
     accumulation.

  C. INTERMITTENT HOVER ON CF2 -- the same disturbance study on the second
     platform, so the result is not X2-specific.

Run:  python sweep_final_2026_09_05.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
ROOT = HERE / "results" / "final_sweep_2026-09-05"

CANONICAL = HERE / "run_mujoco_nef.py"
PERTURBED = HERE / "run_mujoco_nef_perturbed.py"

PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
CONTROLLERS = ("classical", "nengo-nef-pes")

# (label, attitude-noise-std [rad], rate-noise-std [rad/s], seeds)
NOISE = (
    ("n0_clean", 0.0, 0.0, (1,)),
    ("n1_moderate", 0.010, 0.025, (7, 8)),
    ("n2_realistic", 0.020, 0.050, (7, 8)),
)

done = skipped = failed = 0
t_start = time.time()


def scale(platform: str) -> str:
    return "1.5" if platform == "cf2-rotor" else "1.0"


def launch(cmd: list[str], out: Path, tag: str) -> dict | None:
    global done, skipped, failed
    if (out / "summary.json").is_file():
        skipped += 1
        return json.loads((out / "summary.json").read_text())
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        failed += 1
        print(f"  FAILED  {tag}\n{r.stderr[-900:]}", flush=True)
        return None
    d = json.loads((out / "summary.json").read_text())
    done += 1
    el = time.time() - t_start
    print(f"  {tag:52s} qerr={d['qerr_mean_rad']:.6f} "
          f"[{time.time() - t0:.0f}s, {el / 60:.1f}m elapsed]", flush=True)
    return d


# ===========================================================================
def study_a() -> dict:
    print("\n=== A. noise sensitivity " + "=" * 46, flush=True)
    res: dict[str, float] = {}
    for plat in PLATFORMS:
        for mis in MISSIONS:
            for ctl in CONTROLLERS:
                for label, an, rn, seeds in NOISE:
                    for sd in seeds:
                        tag = f"{plat}/{mis}/{ctl}/{label}/s{sd}"
                        out = ROOT / "A_noise" / plat / mis / ctl / f"{label}_s{sd}"
                        cmd = [PY, str(CANONICAL),
                               "--platform", plat, "--controller", ctl,
                               "--mission", mis, "--duration", "45",
                               "--attitude-noise-std", str(an),
                               "--rate-noise-std", str(rn),
                               "--seed", str(sd),
                               "--actuator-scale", scale(plat),
                               "--no-neural-archive", "--output", str(out)]
                        d = launch(cmd, out, tag)
                        if d:
                            res[tag] = d["qerr_mean_rad"]
    return res


def study_b() -> dict:
    print("\n=== B. long-horizon intermittent hover (180 s) " + "=" * 24, flush=True)
    res = {}
    for ctl in CONTROLLERS:
        tag = f"x2/hover/{ctl}/180s_intermittent"
        out = ROOT / "B_long_hover" / ctl
        cmd = [PY, str(PERTURBED),
               "--platform", "x2", "--controller", ctl,
               "--mission", "hover", "--duration", "180",
               "--disturbance-torque", "0.15",
               "--disturbance-schedule", "intermittent",
               "--disturbance-warmup", "5", "--disturbance-on", "5",
               "--disturbance-off", "5", "--disturbance-ramp", "0.25",
               "--no-neural-archive", "--output", str(out)]
        d = launch(cmd, out, tag)
        if d:
            res[tag] = d["qerr_mean_rad"]
    return res


def study_c() -> dict:
    print("\n=== C. intermittent hover, CF2 " + "=" * 39, flush=True)
    res = {}
    for ctl in CONTROLLERS:
        tag = f"cf2-rotor/hover/{ctl}/45s_intermittent"
        out = ROOT / "C_cf2_hover" / ctl
        cmd = [PY, str(PERTURBED),
               "--platform", "cf2-rotor", "--controller", ctl,
               "--mission", "hover", "--duration", "45",
               "--disturbance-torque", "0.004",   # scaled to CF2 inertia
               "--disturbance-schedule", "intermittent",
               "--disturbance-warmup", "5", "--disturbance-on", "5",
               "--disturbance-off", "5", "--disturbance-ramp", "0.25",
               "--actuator-scale", "1.5",
               "--no-neural-archive", "--output", str(out)]
        d = launch(cmd, out, tag)
        if d:
            res[tag] = d["qerr_mean_rad"]
    return res


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    total = (len(PLATFORMS) * len(MISSIONS) * len(CONTROLLERS)
             * sum(len(s) for _, _, _, s in NOISE)) + 4
    print(f"final sweep: {total} runs, roughly 40 minutes")
    all_res = {}
    all_res.update(study_a())
    all_res.update(study_b())
    all_res.update(study_c())
    (ROOT / "raw_results.json").write_text(json.dumps(all_res, indent=2))
    print(f"\n{'=' * 70}")
    print(f"ran {done}, skipped {skipped}, failed {failed}, "
          f"{(time.time() - t_start) / 60:.1f} min")
    print(f"written to {ROOT}")
