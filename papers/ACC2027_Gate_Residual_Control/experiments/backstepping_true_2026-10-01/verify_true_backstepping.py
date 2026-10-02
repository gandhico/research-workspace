"""Numerical checks of the recursive backstepping derivation (writes results/verification.json).

1. Kinematics: along a rigid-body trajectory (MuJoCo convention Q_dot = 1/2 Q (x) [0,w], measured q = Q*), the
   closed-form z1_dot = 1/2 (|q_e0| I + [z1]x) w_e and wbar_d_dot = R_e^T w_d_dot - w_e x wbar_d match central
   finite differences of z1 and wbar_d = R(q_e)^T w_d.
2. Lyapunov: closed loop on the same rigid-body model with the plain law and no torque limit, the finite-difference
   V_dot equals -c z1^T K1 z1 - z2^T K2 z2 (and V decreases); adaptive law with a constant unknown torque: d_hat -> d.
3. Linearization: the small-error poles equal those of the paper's PD+ff at rho = 3, zeta = 0.95.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments" / "nengo_nef_replication_2026-08-29"))
sys.path.insert(0, str(HERE))
from gra_control.math3d import quat_conj, quat_mul, reference_quat  # noqa: E402
from run_mujoco_nef_baselines import reference_rate  # noqa: E402
from true_backstepping import TrueBackstepping, design_gains  # noqa: E402

J_X2 = np.array([0.060711294842784244, 0.0364684032704233, 0.025411698113207547])   # A5 manifest
L_X2 = np.array([0.7285355381134109, 0.43762083924507955, 0.2541169811320755])
WN0 = np.array([4.0, 4.0, 3.5])


def deriv(Q, w, tau, J, d=np.zeros(3)):
    return 0.5 * quat_mul(Q, np.r_[0.0, w]), (tau + d - np.cross(w, J * w)) / J


def rk4(Q, w, tau, h, J, d=np.zeros(3)):
    k1 = deriv(Q, w, tau, J, d); k2 = deriv(Q + .5 * h * k1[0], w + .5 * h * k1[1], tau, J, d)
    k3 = deriv(Q + .5 * h * k2[0], w + .5 * h * k2[1], tau, J, d); k4 = deriv(Q + h * k3[0], w + h * k3[1], tau, J, d)
    Q = Q + h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]); w = w + h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
    return Q / np.linalg.norm(Q), w


def main():
    out = {}
    # ---------------------------------------------------------------- 1. kinematics, open loop with smooth rates
    for mission in ("full3", "hard45", "yaw360"):
        bs = TrueBackstepping(J_X2, L_X2, WN0, reference_rate, mission, 45.0)
        Q = np.array([0.95, 0.2, -0.15, 0.18]); Q /= np.linalg.norm(Q)
        h, worst1, worst2, scale1, scale2 = 1e-4, 0.0, 0.0, 0.0, 0.0
        t = 2.0
        for k in range(4000):
            w = np.array([0.8 * np.sin(1.3 * t), -0.6 * np.cos(0.7 * t), 0.5 * np.sin(2.1 * t + 0.3)])
            if k % 200 == 0:
                q = quat_conj(Q)
                z1, _, we, z1d, wbar, wbard, _ = bs.signals(t, q, w)
                Qp, _ = rk4(Q, w, np.zeros(3), h, J_X2 * 1e9)            # huge J: w constant over +-h
                Qm, _ = rk4(Q, w, np.zeros(3), -h, J_X2 * 1e9)
                zp, _, _, _, wbp, _, _ = bs.signals(t + h, quat_conj(Qp), w)
                zm, _, _, _, wbm, _, _ = bs.signals(t - h, quat_conj(Qm), w)
                fd1, fd2 = (zp - zm) / (2 * h), (wbp - wbm) / (2 * h)
                worst1 = max(worst1, float(np.max(np.abs(fd1 - z1d)))); scale1 = max(scale1, float(np.max(np.abs(z1d))))
                worst2 = max(worst2, float(np.max(np.abs(fd2 - wbard)))); scale2 = max(scale2, float(np.max(np.abs(wbard))))
            Q, _ = rk4(Q, w, np.zeros(3), h, J_X2 * 1e9)
            t += h
        out[f"kinematics_{mission}"] = {"z1_dot_max_abs_err": worst1, "z1_dot_scale": scale1,
                                        "wbar_dot_max_abs_err": worst2, "wbar_dot_scale": scale2}

    # ---------------------------------------------------------------- 2. Lyapunov decrease, closed loop
    for mission in ("full3", "hard45"):
        bs = TrueBackstepping(J_X2, np.full(3, 1e9), WN0, reference_rate, mission, 45.0)
        Q = quat_conj(reference_quat(1.0, mission, 45.0)); Q = quat_mul(np.array([0.97, 0.15, -0.12, 0.13]) /
                                                                         np.linalg.norm([0.97, 0.15, -0.12, 0.13]), Q)
        w, t, h = np.zeros(3), 1.0, 2e-4
        V = lambda z1, z2, a0: bs.c * 2 * (1 - a0) + 0.5 * np.sum(bs.J * z2 ** 2)
        worst, Vs = 0.0, []
        for k in range(15000):
            q = quat_conj(Q)
            z1, z2, *_, a0 = bs.signals(t, q, w)
            tau = bs.torque(t, None, w, q)
            Vk = V(z1, z2, a0); Vs.append(Vk)
            pred = -bs.c * np.sum(bs.k1 * z1 ** 2) - np.sum(bs.k2 * z2 ** 2)
            Q2, w2 = rk4(Q, w, tau, h, J_X2)
            z1n, z2n, *_, a0n = bs.signals(t + h, quat_conj(Q2), w2)
            Vdot_fd = (V(z1n, z2n, a0n) - Vk) / h
            if k > 10 and Vk > 1e-9:
                worst = max(worst, abs(Vdot_fd - pred) / max(abs(pred), 1e-12))
            Q, w, t = Q2, w2, t + h
        out[f"lyapunov_{mission}"] = {"V_start": Vs[0], "V_end": Vs[-1], "V_monotone": bool(np.all(np.diff(Vs) <= 1e-12)),
                                      "Vdot_fd_vs_formula_max_rel_err": worst}

    # adaptive: constant unknown body torque d (20% of the box), d_hat must converge to d
    d_true = 0.2 * L_X2 * np.array([1.0, -1.0, 0.5])
    bs = TrueBackstepping(J_X2, np.full(3, 1e9), WN0, reference_rate, "hover", 45.0, adaptive=True, dt=2e-4)
    bs.D = np.full(3, 1e9)
    Q, w, t, h = np.array([1.0, 0, 0, 0]), np.zeros(3), 0.0, 2e-4
    for k in range(100000):
        tau = bs.torque(t, None, w, quat_conj(Q))
        Q, w = rk4(Q, w, tau, h, J_X2, d_true)
        t += h
    out["adaptive_constant_disturbance"] = {"d_true": d_true.tolist(), "d_hat_after_20s": bs.d_hat.tolist(),
                                            "max_rel_err": float(np.max(np.abs(bs.d_hat - d_true) / np.abs(d_true)))}

    # ---------------------------------------------------------------- 3. linearized poles
    k1, k2, c, lam1, lam2 = design_gains(J_X2, 3.0 * WN0, 0.95)
    poles = [np.roots([1.0, k1[i] / 2 + k2[i] / J_X2[i], (c + k1[i] * k2[i]) / (2 * J_X2[i])]) for i in range(3)]
    target = [np.roots([1.0, 2 * 0.95 * w_, w_ ** 2]) for w_ in 3.0 * WN0]
    out["linearization"] = {"c_Nm": c, "k1": k1.tolist(), "k2": k2.tolist(), "lam1": lam1.tolist(), "lam2": lam2.tolist(),
                            "max_pole_diff_vs_pdff": float(max(np.max(np.abs(np.sort_complex(p) - np.sort_complex(q)))
                                                               for p, q in zip(poles, target))),
                            "poles_roll": [str(np.round(p, 4)) for p in poles[0]]}
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "verification.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
