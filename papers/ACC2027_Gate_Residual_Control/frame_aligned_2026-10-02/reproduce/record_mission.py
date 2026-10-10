"""Record a paper mission for video: the sealed runner (run_final_robustness.py) runs unchanged; its mj_step is wrapped
to store the free-joint pose at 60 Hz of simulated time. The run also writes the runner's own full-rate neural archive
(CMG voltage, gate, activity, decoder, residual, torques). At the end the 45-s mean error is checked against the paper
table (MATCH / DIFFERS), exactly as run_mission_viewer.py does.

    .venv\\Scripts\\python.exe reproduce\\record_mission.py --platform x2 --mission hard45 --arm cmg
Writes reproduce/recordings/<platform>_<mission>_<arm>/{pose.npz, trace.csv, summary.json, manifest.json, neural_*.npz}.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reproduce"))
import run_mission_viewer as V  # noqa: E402  (same configuration table, same published-value lookup)

import mujoco  # noqa: E402

rfr = V.rfr


class Recorder:
    def __init__(self, real, every=33):
        self.real, self.every, self.n = real, every, 0
        self.t, self.qpos = [], []

    def __getattr__(self, name):
        return getattr(self.real, name)

    def mj_step(self, model, data):
        if self.n % self.every == 0:
            self.t.append(float(data.time)); self.qpos.append(np.asarray(data.qpos, dtype=float).copy())
        self.real.mj_step(model, data)
        self.n += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", choices=V.PLATFORM, required=True)
    ap.add_argument("--mission", choices=("roll", "full3", "hard45", "hardstep", "yaw360"), required=True)
    ap.add_argument("--arm", choices=("pdff", "cmg"), default="cmg")
    a = ap.parse_args()
    p = V.PLATFORM[a.platform]
    out = ROOT / "reproduce" / "recordings" / f"{a.platform}_{a.mission}_{a.arm}"
    argv = ["--platform", p["name"], "--controller", "nengo-nef-pes" if a.arm == "cmg" else "classical",
            "--mission", a.mission, "--duration", "45.0", "--beta", str(p["beta"]),
            "--actuator-scale", str(p["scale"]), "--seed", "1", "--output", str(out)]
    if a.arm == "cmg":
        argv += ["--output-gate", "torque-saturation-opposition"]
    args = rfr.make_parser().parse_args(argv)
    rfr._validate(args)
    rec = Recorder(mujoco)
    rfr.mujoco = rec
    try:
        summary = rfr.run(args)
    finally:
        rfr.mujoco = mujoco
    np.savez_compressed(out / "pose.npz", t=np.asarray(rec.t), qpos=np.asarray(rec.qpos))
    mean = summary["metrics"]["qerr_true_mean_rad"]
    ref = V.published(p["name"], a.mission, a.arm, "none", 1, "none")
    rel = abs(mean - ref) / ref if ref else None
    res = {"mean_rad": mean, "published_rad": ref, "relative_difference": rel,
           "status": "MATCH" if rel is not None and rel < 1e-6 else "DIFFERS"}
    (out / "match.json").write_text(json.dumps(res, indent=1))
    print(a.platform, a.mission, a.arm, json.dumps(res))


if __name__ == "__main__":
    main()
