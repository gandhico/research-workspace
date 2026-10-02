"""Reconstruct attitude, tilt and airframe clearance during Hardstep from the canonical traces.

q_e = q_ref (x) conj(q_meas)  =>  q_meas = conj(q_e) (x) q_ref.  R33 = 1 - 2(x^2+y^2) (same for q and conj q).
Lowest airframe point = z + min_i (R p_i)_z over the four rotor sites.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

RES = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29"
           r"\results\matched_45s")
SITES = {"x2": np.array([[-.14, -.18, .05], [-.14, .18, .05], [.14, .18, .08], [.14, -.18, .08]]),
         "cf2-rotor": np.array([[-.0325, -.0325, 0.0], [-.0325, .0325, 0.0],
                                [.0325, .0325, 0.0], [.0325, -.0325, 0.0]])}


def qmul(a, b):
    w1, x1, y1, z1 = a.T
    w2, x2, y2, z2 = b.T
    return np.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                     w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], axis=-1)


def euler_to_quat(r, p, y):
    cr, sr = np.cos(r / 2), np.sin(r / 2)
    cp, sp = np.cos(p / 2), np.sin(p / 2)
    cy, sy = np.cos(y / 2), np.sin(y / 2)
    return np.stack([cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy,
                     cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy], axis=-1)


def rotmat(q):
    w, x, y, z = q.T
    return np.stack([
        np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)], -1),
        np.stack([2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)], -1),
        np.stack([2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], -1)], -2)


for p in ("x2", "cf2-rotor"):
    for ctrl in ("classical", "nengo_nef_pes"):
        f = RES / f"{p.replace('-', '_')}_hardstep_{ctrl}" / "trace.csv"
        rows = list(csv.DictReader(f.open(encoding="utf-8")))
        t = np.array([float(r["t"]) for r in rows])
        z = np.array([float(r["z"]) for r in rows])
        qe = np.array([[float(r["qe_w"]), float(r["qe_x"]), float(r["qe_y"]), float(r["qe_z"])] for r in rows])
        ref = np.array([[float(r["ref_roll"]), float(r["ref_pitch"]), float(r["ref_yaw"])] for r in rows])
        q_ref = euler_to_quat(ref[:, 0], ref[:, 1], ref[:, 2])
        q_conj = qe * np.array([1, -1, -1, -1])
        q_meas = qmul(q_conj, q_ref)
        tilt = np.degrees(np.arccos(np.clip(1 - 2 * (q_meas[:, 1] ** 2 + q_meas[:, 2] ** 2), -1, 1)))
        tilt_ref = np.degrees(np.arccos(np.clip(1 - 2 * (q_ref[:, 1] ** 2 + q_ref[:, 2] ** 2), -1, 1)))
        R = rotmat(q_meas)                                   # body->world (R33 identical for conj)
        arms = np.einsum('nij,kj->nki', R, SITES[p])         # rotated site offsets
        clearance = z[:, None] + arms[:, :, 2]
        low = clearance.min(axis=1)
        print(f"{p:10s} {ctrl:14s}")
        print(f"   commanded tilt: mean {tilt_ref.mean():5.1f} deg, max {tilt_ref.max():5.1f} deg | "
              f"actual tilt: mean {tilt.mean():5.1f}, max {tilt.max():5.1f} deg")
        print(f"   body z: min {z.min():.3f} m | lowest rotor/airframe point: min {low.min():+.3f} m "
              f"at t={t[low.argmin()]:.2f} s")
        print(f"   samples with airframe below the floor: {(low < 0).sum()} "
              f"({100 * (low < 0).mean():.2f}% of run); below 5 cm: {100 * (low < 0.05).mean():.2f}%")
        print(f"   time with actual tilt > 60 deg: {100 * (tilt > 60).mean():.1f}%  > 90 deg: "
              f"{100 * (tilt > 90).mean():.1f}%")
