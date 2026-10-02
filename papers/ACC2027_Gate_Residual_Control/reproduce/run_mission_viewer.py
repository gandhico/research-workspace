"""Replay any paper mission with a live MuJoCo viewer, using the paper's own (sealed) runner unchanged.

The sealed runner experiments/final_robustness_gating_2026-09-20/run_final_robustness.py is imported, not copied or edited.
Its single physics call, mujoco.mj_step, is wrapped: after each step the viewer is refreshed (read-only), so the simulated
trajectory and every saved number are identical to a headless run. Mouse drags in the viewer WOULD perturb the plant;
do not drag the body if you want the published numbers.

Viewer: the vehicle with its body axes, plus ghost axes of the commanded reference attitude (thin, semi-transparent);
when tracking is good the two triads coincide. Top-left text: time, mission, arm, current and running-mean error.

    .venv\\Scripts\\python.exe reproduce\\run_mission_viewer.py --platform x2 --mission hard45 --arm cmg
    .venv\\Scripts\\python.exe reproduce\\run_mission_viewer.py --platform cf2 --mission hover --arm cmg --disturbance x1
    .venv\\Scripts\\python.exe reproduce\\run_mission_viewer.py --platform x2 --mission full3 --arm pdff --noise realistic --seed 3

At the end the 45-s mean error is compared with the published value from the paper's result tables.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FR = ROOT / "experiments" / "final_robustness_gating_2026-09-20"
sys.path.insert(0, str(FR))
import mujoco  # noqa: E402
import mujoco.viewer  # noqa: E402
import run_final_robustness as rfr  # noqa: E402  (the sealed paper runner)
from gra_control.math3d import quat_angle, quat_conj, quat_error, reference_quat  # noqa: E402

PLATFORM = {"x2": dict(name="x2", beta=0.5, scale=1.0, dist=0.15, view=0.40),     # view: vehicle span [m] for camera/axes
            "cf2": dict(name="cf2-rotor", beta=0.2, scale=1.5, dist=0.00015, view=0.10)}
NOISE = {"none": (0.0, 0.0), "moderate": (0.010, 0.025), "realistic": (0.020, 0.050)}
LEVEL = {"none": 0.0, "x0.5": 0.5, "x1": 1.0, "x2": 2.0}


class LiveView:
    """Wraps mujoco.mj_step: step, then refresh a passive viewer at ~60 Hz of simulated time."""

    def __init__(self, real, mission: str, duration: float, arm: str, platform: str, realtime: float, show: bool,
                 span: float = 0.4):
        self.real, self.mission, self.duration = real, mission, duration
        self.extent = span
        self.label = f"{platform}  {mission}  {'PD+ff + CMG-PES (gated)' if arm == 'cmg' else 'PD+ff (rho=3)'}"
        self.realtime, self.show = realtime, show
        self.handle = None
        self.wall0 = None
        self.steps = 0
        self.err_sum = 0.0
        self.body = None
        self.qa = None

    def __getattr__(self, name):          # every other mujoco attribute passes through untouched
        return getattr(self.real, name)

    def _start(self, model, data):
        jid = next(j for j in range(model.njnt) if model.jnt_type[j] == self.real.mjtJoint.mjJNT_FREE)
        self.body, self.qa = int(model.jnt_bodyid[jid]), int(model.jnt_qposadr[jid])
        if self.show:
            self.handle = self.real.viewer.launch_passive(model, data, show_left_ui=False, show_right_ui=False)
            with self.handle.lock():
                self.handle.opt.frame = self.real.mjtFrame.mjFRAME_BODY
                self.handle.cam.trackbodyid = self.body
                self.handle.cam.type = self.real.mjtCamera.mjCAMERA_TRACKING
                self.handle.cam.distance = 4.0 * self.extent
        self.wall0 = time.perf_counter()

    def _draw(self, data):
        t = float(data.time)
        q_true = quat_conj(np.asarray(data.qpos[self.qa + 3:self.qa + 7], dtype=float))
        q_ref = reference_quat(t, self.mission, self.duration)
        err = quat_angle(quat_error(q_ref, q_true)[0])
        Rd = np.zeros(9)
        self.real.mju_quat2Mat(Rd, quat_conj(q_ref))          # reference body-to-world attitude
        Rd = Rd.reshape(3, 3)
        pos = np.asarray(data.xpos[self.body], dtype=float)
        L = 1.2 * self.extent
        with self.handle.lock():
            scn = self.handle.user_scn
            scn.ngeom = 0
            for k, rgba in enumerate(([1, .25, .25, .55], [.25, 1, .25, .55], [.3, .45, 1, .55])):
                if scn.ngeom >= scn.maxgeom:
                    break
                g = scn.geoms[scn.ngeom]
                self.real.mjv_initGeom(g, self.real.mjtGeom.mjGEOM_CAPSULE, np.zeros(3), np.zeros(3), np.zeros(9),
                                       np.asarray(rgba, dtype=np.float32))
                self.real.mjv_connector(g, self.real.mjtGeom.mjGEOM_CAPSULE, 0.012 * self.extent, pos, pos + L * Rd[:, k])
                scn.ngeom += 1
            mean = self.err_sum / max(self.steps, 1)
            self.handle.set_texts((None, self.real.mjtGridPos.mjGRID_TOPLEFT,
                                   "time\nmission\nerror now\nmean so far\nghost axes",
                                   f"{t:6.2f} / {self.duration:.0f} s\n{self.label}\n{math.degrees(err):7.3f} deg\n"
                                   f"{math.degrees(mean):7.3f} deg\nreference attitude"))
        self.handle.sync()

    def mj_step(self, model, data):
        if self.wall0 is None:
            self._start(model, data)
        self.real.mj_step(model, data)
        self.steps += 1
        if self.handle is None and self.steps % 20000 == 0:
            print(f"  t = {float(data.time):5.1f} s", flush=True)
        if self.steps % 33 == 0:                         # ~60 Hz of simulated time at dt = 0.5 ms
            q_true = quat_conj(np.asarray(data.qpos[self.qa + 3:self.qa + 7], dtype=float))
            e = quat_angle(quat_error(reference_quat(float(data.time), self.mission, self.duration), q_true)[0])
            self.err_sum += e * 33
            if self.handle is not None:
                if not self.handle.is_running():
                    raise SystemExit("viewer closed by the user; run aborted (no results written)")
                self._draw(data)
                if self.realtime > 0:
                    lag = float(data.time) / self.realtime - (time.perf_counter() - self.wall0)
                    if lag > 0:
                        time.sleep(lag)


def published(platform: str, mission: str, arm: str, noise: str, seed: int, level: str) -> float | None:
    label = "cmg_pes_gated" if arm == "cmg" else "pdff_rho3"
    if level != "none":
        rows = csv.DictReader((FR / "results" / "final_disturbance.csv").open(encoding="utf-8"))
        hit = [r for r in rows if r["platform"] == platform and r["disturbance_level"] == level and r["label"] == label]
    elif noise != "none":
        rows = csv.DictReader((FR / "results" / "final_noise.csv").open(encoding="utf-8"))
        hit = [r for r in rows if r["platform"] == platform and r["mission"] == mission and r["label"] == label
               and r["noise_level"] == noise and int(r["seed"]) == seed]
    else:
        rows = csv.DictReader((FR / "results" / "final_nominal.csv").open(encoding="utf-8"))
        hit = [r for r in rows if r["platform"] == platform and r["mission"] == mission and r["label"] == label]
    return float(hit[0]["qerr_true_mean_rad"]) if hit else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platform", choices=PLATFORM, required=True)
    ap.add_argument("--mission", choices=("roll", "full3", "hard45", "hardstep", "yaw360", "hover"), required=True)
    ap.add_argument("--arm", choices=("pdff", "cmg"), default="cmg", help="pdff = tuned PD+ff baseline; cmg = + gated CMG-PES")
    ap.add_argument("--noise", choices=NOISE, default="none")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--disturbance", choices=LEVEL, default="none", help="hover bursts: x0.5, x1 (paper nominal), x2")
    ap.add_argument("--duration", type=float, default=45.0, help="45 s reproduces the paper; shorter runs are previews")
    ap.add_argument("--realtime", type=float, default=1.0, help="1 = wall clock, 2 = twice as fast, 0 = as fast as possible")
    ap.add_argument("--no-viewer", action="store_true", help="headless run (same numbers)")
    ap.add_argument("--no-hold", action="store_true", help="close the viewer when the run ends")
    ap.add_argument("--output", type=Path, default=None)
    a = ap.parse_args()
    if a.mission == "hover" and a.disturbance == "none":
        a.disturbance = "x1"
    p = PLATFORM[a.platform]
    out = a.output or ROOT / "reproduce" / "viewer_runs" / f"{a.platform}_{a.mission}_{a.arm}_{a.noise}_s{a.seed}_{a.disturbance}"
    att, rate = NOISE[a.noise]
    argv = ["--platform", p["name"], "--controller", "nengo-nef-pes" if a.arm == "cmg" else "classical",
            "--mission", a.mission, "--duration", str(a.duration), "--beta", str(p["beta"]),
            "--actuator-scale", str(p["scale"]), "--attitude-noise-std", str(att), "--rate-noise-std", str(rate),
            "--seed", str(a.seed), "--no-neural-archive", "--output", str(out)]
    if a.arm == "cmg":
        argv += ["--output-gate", "torque-saturation-opposition"]
    if LEVEL[a.disturbance] > 0:
        argv += ["--disturbance-torque", str(p["dist"] * LEVEL[a.disturbance]), "--disturbance-schedule", "intermittent"]
    args = rfr.make_parser().parse_args(argv)
    rfr._validate(args)

    print("sealed runner:", FR / "run_final_robustness.py")
    print("arguments    :", " ".join(argv))
    live = LiveView(mujoco, a.mission, a.duration, a.arm, a.platform.upper(), a.realtime, not a.no_viewer, p["view"])
    rfr.mujoco = live                                 # only the runner's module reference is wrapped
    try:
        summary = rfr.run(args)
    finally:
        rfr.mujoco = mujoco
    mean = summary["metrics"]["qerr_true_mean_rad"]
    print(f"\n{a.duration:g}-s mean true-attitude error: {mean * 1e3:.4f} mrad ({math.degrees(mean):.4f} deg)")
    print("results written to:", out)
    if a.duration == 45.0:
        ref = published(p["name"], a.mission, a.arm, a.noise, a.seed, a.disturbance)
        if ref is None:
            print("published value: not in the paper's tables for this combination")
        else:
            rel = abs(mean - ref) / ref
            print(f"published value: {ref * 1e3:.4f} mrad   relative difference {rel:.1e}   "
                  f"{'MATCH' if rel < 1e-6 else 'DIFFERS'}")
    if live.handle is not None:
        if a.no_hold:
            live.handle.close()
        else:
            print("Close the viewer window to exit.")
            while live.handle.is_running():
                time.sleep(0.1)


if __name__ == "__main__":
    main()
