"""Is Hardstep near a physical floor? Compare measured settling with the time-optimal rest-to-rest bound.

Rotor-feasible yaw torque matters: yaw comes only from rotor drag, tau_z = kappa * sum(+/- f_i), so at a
hover collective T the differential thrust available for yaw is bounded by the rotor range, not by l.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import mujoco
import numpy as np

ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
sys.path.insert(0, str(ACC / "src"))
from gra_control.platforms.drone import SPECS, _free_joint, _mixer  # noqa: E402

RES = ACC / "experiments/nengo_nef_replication_2026-08-29/results/matched_45s"
ROWS = [[.75, -.45, .55], [-.65, .55, -.70], [.50, .50, .90], [-.80, -.35, .20]]
NU = np.array([12.0, 12.0, 10.0])


def platform_facts(name, scale):
    model = mujoco.MjModel.from_xml_path(str(SPECS[name].model))
    _, body_id, _, _ = _free_joint(model)
    j_tune = model.body_inertia[body_id].copy()
    R = np.zeros(9)
    mujoco.mju_quat2Mat(R, model.body_iquat[body_id])
    J = np.diag(R.reshape(3, 3) @ np.diag(j_tune) @ R.reshape(3, 3).T).copy()
    mass = float(np.sum(model.body_mass))
    g = abs(float(model.opt.gravity[2]))
    act_ids, _, B_inv, ctrl_range = _mixer(model)
    fmax = ctrl_range[:, 1].copy() * scale
    B = np.linalg.inv(B_inv)
    limits = np.maximum(j_tune * NU, 1e-6)
    # rotor-feasible torque about each axis at hover collective, keeping sum(f) = m g
    hover = mass * g / 4.0
    head = np.minimum(fmax - hover, hover)            # symmetric differential thrust per rotor
    feas = np.abs(B[1:, :]) @ head                    # |tau_i| reachable with that differential
    return dict(j_tune=j_tune, J=J, limits=limits, feasible=feas, mass=mass, g=g,
                fmax=fmax[0], hover=hover)


def euler_seq():
    seq = [np.zeros(3)] + [np.array(ROWS[i % 4]) for i in range(5)]
    return [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]


def measured(p, ctrl):
    rows = list(csv.DictReader((RES / f"{p.replace('-', '_')}_hardstep_{ctrl}" / "trace.csv")
                               .open(encoding="utf-8")))
    t = np.array([float(r["t"]) for r in rows])
    q = np.degrees(np.array([float(r["qerr"]) for r in rows]))
    out = []
    for k in range(5):
        t0 = 1.0 + 2.0 * k
        m = (t >= t0) & (t < t0 + 2.0)
        tt, qq = t[m] - t0, q[m]
        below = np.where(qq < 5.0)[0]
        out.append(tt[below[0]] if below.size else np.nan)
    return out


for name, scale, label in (("x2", 1.0, "X2"), ("cf2-rotor", 1.5, "CF2")):
    f = platform_facts(name, scale)
    print(f"=== {label} ===")
    print(f"  j_tune {np.round(f['j_tune'], 5)}  diag(J) {np.round(f['J'], 5)}")
    print(f"  controller torque box l = j_tune*nu : {np.round(f['limits'], 4)} N m")
    print(f"  rotor-feasible torque at hover      : {np.round(f['feasible'], 4)} N m "
          f"(hover {f['hover']:.2f} N/rotor of {f['fmax']:.2f} N)")
    ratio = f['limits'] / f['feasible']
    print(f"  box / feasible                      : {np.round(ratio, 2)}  "
          f"({'yaw box EXCEEDS rotors' if ratio[2] > 1 else 'yaw box within rotors'})")
    acc = np.minimum(f['limits'], f['feasible']) / f['J']
    print(f"  realizable angular acceleration     : {np.round(acc, 2)} rad/s^2 (intended {NU})")
    pd_t, cmg_t = measured(name, "classical"), measured(name, "nengo_nef_pes")
    print(f"  {'step':4s} {'d(roll,pitch,yaw) [deg]':>26s} {'t_opt[s]':>9s} {'PD[s]':>7s} {'CMG[s]':>7s} "
          f"{'PD/t_opt':>9s}")
    for k, (a, b) in enumerate(euler_seq()):
        d = np.abs(b - a)
        t_ax = 2 * np.sqrt(d / acc)
        t_opt = float(t_ax.max())
        print(f"  {k:<4d} {np.array2string(np.round(np.degrees(d), 0), separator=','):>26s} "
              f"{t_opt:9.2f} {pd_t[k]:7.2f} {cmg_t[k]:7.2f} {pd_t[k] / t_opt:9.2f}")
    print()
