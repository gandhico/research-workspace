"""Reduced-CMG runs on the fixed-PD and PD+ff rho=1 baselines (ladder levels 0 and 1), both platforms, five missions.

Arguments are those of the archived CMG ladder runs (nengo_nef_replication run_campaign.py -> matched_45s, and
run_ff_cmg.py -> rate_ff_left_neg); after running, each new manifest's arguments are compared with the archived one.
Level 2 (PD+ff rho=3, gated) is results/confirm/<platform>/<mission>/lpf-logistic.
"""
from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCH = HERE.parents[0] / "nengo_nef_replication_2026-08-29" / "results"
OUT = HERE / "results" / "ladder"
SCALE = {"x2": "1.0", "cf2-rotor": "1.5"}
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
COMMON = ["--controller", "nengo-nef-pes", "--duration", "45", "--dt", "0.0005", "--beta", "0.5",
          "--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0", "--log-every", "10"]


def lab(p: str, m: str) -> str:
    return f"{p}_{m}".replace("-", "_")


def archived(level: str, p: str, m: str) -> Path:
    return (ARCH / "matched_45s" if level == "pd" else ARCH / "pid_baseline_2026-09-10" / "rate_ff_left_neg") / f"{lab(p, m)}_nengo_nef_pes"


def run(job):
    level, p, m = job
    out = OUT / level / f"{lab(p, m)}_reduced_cmg"
    if not (out / "summary.json").exists():
        extra = ["--rate-ff", "left-neg", "--no-neural-archive"] if level == "ff1" else []
        cmd = [sys.executable, str(HERE / "run_reduced_ladder.py"), level, "--", "--platform", p, "--mission", m,
               *COMMON, "--actuator-scale", SCALE[p], *extra, "--output", str(out)]
        out.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        (out / "console.log").write_text(r.stdout + "\n--- STDERR ---\n" + r.stderr, encoding="utf-8")
        if r.returncode != 0:
            return job, "failed"
    a = json.loads((out / "manifest.json").read_text())["arguments"]
    b = json.loads((archived(level, p, m) / "manifest.json").read_text())["arguments"]
    a.pop("output"), b.pop("output")
    return job, "ok" if a == b else f"ARGS DIFFER {set(a.items()) ^ set(b.items())}"


if __name__ == "__main__":
    jobs = [(lv, p, m) for lv in ("pd", "ff1") for p in SCALE for m in MISSIONS]
    with ThreadPoolExecutor(4) as ex:
        for job, status in ex.map(run, jobs):
            print(f"{status:8s} {job}", flush=True)
