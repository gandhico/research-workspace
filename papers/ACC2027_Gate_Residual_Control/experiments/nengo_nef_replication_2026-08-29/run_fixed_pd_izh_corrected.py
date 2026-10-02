"""Fixed-PD Izhikevich-PES, corrected PES normalization (2026-09-24). Reproduces run_neuron_family_campaign.py's exact
settings for the izhikevich cells (beta=0.5, eta=8e-4, k_e=8, k_rate=0, dt=5e-4, duration=45s, actuator-scale per
platform) via the corrected runner (run_mujoco_nef_corrected.py, --exact-pes-normalization), both platforms, 5 missions.
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_mujoco_nef_corrected.py"
OUT = HERE / "results" / "izh_fixed_pd_corrected_2026-09-24"
SCALE = {"x2": 1.0, "cf2-rotor": 1.5}
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")


def run(platform, mission):
    out = OUT / platform / mission
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(RUNNER), "--platform", platform, "--controller", "nengo-izhikevich-pes",
           "--mission", mission, "--duration", "45.0", "--dt", "0.0005", "--beta", "0.5",
           "--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0",
           "--actuator-scale", str(SCALE[platform]), "--seed", "1", "--exact-pes-normalization",
           "--log-every", "10", "--no-neural-archive", "--output", str(out)]
    done = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    if done.returncode:
        raise RuntimeError(f"{platform}/{mission}: {done.stderr[-1500:]}")
    return platform, mission


if __name__ == "__main__":
    jobs = [(p, m) for p in SCALE for m in MISSIONS]
    with ThreadPoolExecutor(max_workers=4) as ex:
        for p, m in ex.map(lambda j: run(*j), jobs):
            print("done", p, m, flush=True)
    print(f"{len(jobs)} runs complete -> {OUT}")
