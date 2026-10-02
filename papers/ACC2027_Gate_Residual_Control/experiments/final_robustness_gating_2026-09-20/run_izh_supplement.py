"""Supplementary: Izhikevich-PES on the paper's primary baseline (PD + rate feedforward, rho = 3), X2, five missions.

Uses the ARCHIVED runner (`run_mujoco_nef_baselines.py`, the one that produced the paper's rho = 3 CMG rows) with the same
arguments as the archived `baselines_2026-09-10/stretch/pdff/bw3` runs, changing only the controller to
`nengo-izhikevich-pes`.  The paper's Izhikevich rows are on the fixed-PD baseline; this puts the rival basis on the same
baseline as the gated and ungated CMG arms so the three can be plotted together.  Exploratory / reference only: it is not a
pre-registered endpoint and is not used for any claim in the manuscript.
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE.parent / "nengo_nef_replication_2026-08-29" / "run_mujoco_nef_baselines.py"
ROOT = HERE / "results" / "supplementary_izhikevich"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ARCHIVE = ("hard45", "hardstep")          # full-rate neural archives only for the plotted missions


def run(mission: str) -> tuple[str, int, float]:
    out = ROOT / "x2" / mission / "nengo_izhikevich_pes"
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(RUNNER), "--platform", "x2", "--controller", "nengo-izhikevich-pes", "--mission", mission,
           "--duration", "45.0", "--dt", "0.0005", "--beta", "0.5", "--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0",
           "--actuator-scale", "1.0", "--seed", "1", "--baseline", "backstepping", "--bw-scale", "3.0", "--rate-ff", "left-neg",
           "--no-model-ff", "--log-every", "10", "--output", str(out)]
    if mission not in ARCHIVE:
        cmd.append("--no-neural-archive")
    done = subprocess.run(cmd, capture_output=True, text=True, cwd=RUNNER.parent)
    (out / "run.log").write_text("$ " + subprocess.list2cmdline(cmd) + "\n\n" + done.stdout + "\n" + done.stderr, encoding="utf-8")
    return mission, done.returncode, 0.0


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as ex:
        for mission, rc, _ in ex.map(run, MISSIONS):
            print(f"{mission:9s} rc={rc}", flush=True)
