"""Frame-aligned rate error check for Eq. (15) (Dr. Sandoval's review, 2026-10-02).

The published baseline (AdvancedBaseline, backstepping form, no model feedforward) damps omega - omega_d, where omega_d is
the desired-frame rate of P-(7)-(8) (verified by reproduce/check_rate_frame.py). The frame-aligned rate error of P-(8) is
omega_e = omega - R(q_e)^T omega_d. This script re-runs a primary cell with the baseline's rate error replaced by omega_e,
everything else identical (sealed runner imported unchanged; only the baseline class is substituted).

    python run_frame_aligned.py --platform x2 --mission hard45 --arm cmg
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "reproduce"))
import run_mission_viewer as V  # noqa: E402  (same configuration table and published-value lookup)
from gra_control.math3d import quat_error, reference_quat  # noqa: E402

rfr = V.rfr


def rot(q):
    """R(q) with R(q) v = vec(q (x) [0, v] (x) q*)."""
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


class FrameAligned(rfr.AdvancedBaseline):
    """Identical to the published baseline except omega_e = omega - R(q_e)^T omega_d."""

    def torque(self, t, eq, omega, q_meas):
        assert self.a.baseline == "backstepping" and not self.model_ff and self.every == 1
        wd = self._wd(t)
        qe, _ = quat_error(reference_quat(t, self.a.mission, self.a.duration), q_meas)
        we = omega - rot(qe).T @ wd
        acc = -self.k1 * (2.0 * eq) - self.k2 * we          # wd_dot = 0 and no gyro term, as in the published runs
        self.hold = np.clip(self.J * acc, -self.lim, self.lim)
        return self.hold


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", choices=V.PLATFORM, required=True)
    ap.add_argument("--mission", choices=("roll", "full3", "hard45", "hardstep", "yaw360"), required=True)
    ap.add_argument("--arm", choices=("pdff", "cmg"), required=True)
    a = ap.parse_args()
    p = V.PLATFORM[a.platform]
    out = HERE / "results" / f"{a.platform}_{a.mission}_{a.arm}"
    argv = ["--platform", p["name"], "--controller", "nengo-nef-pes" if a.arm == "cmg" else "classical",
            "--mission", a.mission, "--duration", "45.0", "--beta", str(p["beta"]), "--actuator-scale", str(p["scale"]),
            "--seed", "1", "--no-neural-archive", "--output", str(out)]
    if a.arm == "cmg":
        argv += ["--output-gate", "torque-saturation-opposition"]
    args = rfr.make_parser().parse_args(argv)
    rfr._validate(args)
    rfr.AdvancedBaseline = FrameAligned
    s = rfr.run(args)
    pub = V.published(p["name"], a.mission, a.arm, "none", 1, "none")
    res = {"platform": a.platform, "mission": a.mission, "arm": a.arm,
           "frame_aligned_mean_rad": s["metrics"]["qerr_true_mean_rad"], "published_mean_rad": pub}
    (out / "frame_check.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res))


if __name__ == "__main__":
    main()
