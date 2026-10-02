import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments" / "nengo_nef_replication_2026-08-29"))
from gra_control.math3d import quat_conj, quat_mul, quat_normalize, reference_quat  # noqa: E402
from run_mujoco_nef_baselines import reference_rate  # noqa: E402


def rotm(q):
    w, x, y, z = quat_normalize(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ])


# 1. Is the left-neg rate the omega_d of the paper's passive kinematics, qd_dot = -1/2 [0, wd] (x) qd ?
print("1. left-neg vs passive kinematics (one-step propagation residual; O(d^2) means consistent)")
for mission in ("hard45", "full3", "yaw360"):
    worst = {}
    for mode in ("left", "left-neg", "right", "right-neg"):
        r = []
        for t in np.linspace(2.0, 40.0, 200):
            wd = reference_rate(t, mission, 45.0, mode)
            d = 1e-4
            q0 = reference_quat(t, mission, 45.0)
            pred = quat_normalize(q0 + d * (-0.5) * quat_mul(np.r_[0.0, wd], q0))
            q1 = reference_quat(t + d, mission, 45.0)
            r.append(min(np.linalg.norm(pred - q1), np.linalg.norm(pred + q1)))
        worst[mode] = max(r)
    print(f"   {mission:7s} " + "  ".join(f"{k} {v:.1e}" for k, v in worst.items()))

# 2. Size of the omitted transport on the real rho=3 runs: |(I - R(q_e)^T) wd| vs |wd|
print("\n2. omitted transport on the published rho=3 runs")
R = ROOT / "experiments" / "final_robustness_gating_2026-09-20" / "results" / "confirmatory" / "nominal"
for plat in ("x2", "cf2-rotor"):
    for mission in ("roll", "full3", "hard45", "yaw360", "hardstep"):
        for arm, tag in (("pdff_rho3", "nominal"), ("cmg_pes_gated", "load_1")):
            tr = pd.read_csv(R / plat / mission / arm / tag / "seed_001" / "trace.csv")
            tr = tr[tr.t >= 2.0]
            num, den, peak = [], [], 0.0
            for _, row in tr.iloc[::5].iterrows():
                qd = row[[f"qref_{c}" for c in "wxyz"]].to_numpy(float)
                q = row[[f"qtrue_{c}" for c in "wxyz"]].to_numpy(float)
                qe = quat_mul(qd, quat_conj(q))
                wd = reference_rate(row.t, mission, 45.0, "left-neg")
                dv = np.linalg.norm((np.eye(3) - rotm(qe).T) @ wd)
                num.append(dv)
                den.append(np.linalg.norm(wd))
                peak = max(peak, dv)
            rel = np.mean(num) / max(np.mean(den), 1e-12)
            print(f"   {plat:9s} {mission:8s} {arm:14s} mean|wd| {np.mean(den):.3f} rad/s  mean omitted {np.mean(num):.2e} rad/s  ({100 * rel:.2f} % of |wd|)  peak {peak:.2e}")

# 3. Hardstep: the reference is piecewise constant; what does the finite difference give at a step?
print("\n3. Hardstep reference rate around the t = 3 s step (dt = 5e-4 grid)")
for k in range(5998, 6003):
    t = k * 5e-4
    print(f"   t = {t:.4f}  |wd| = {np.linalg.norm(reference_rate(t, 'hardstep', 45.0, 'left-neg')):.3e} rad/s")
