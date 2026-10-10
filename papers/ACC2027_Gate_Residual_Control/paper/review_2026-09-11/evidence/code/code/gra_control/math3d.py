from __future__ import annotations

import numpy as np


def quat_normalize(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    n = float(np.linalg.norm(q))
    return q / n if n > 1e-12 else np.array([1.0, 0.0, 0.0, 0.0])


def quat_conj(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    return np.array([q[0], -q[1], -q[2], -q[3]], dtype=float)


def quat_mul(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    p0, p1, p2, p3 = p
    q0, q1, q2, q3 = q
    return np.array([
        p0*q0 - p1*q1 - p2*q2 - p3*q3,
        p0*q1 + p1*q0 + p2*q3 - p3*q2,
        p0*q2 - p1*q3 + p2*q0 + p3*q1,
        p0*q3 + p1*q2 - p2*q1 + p3*q0,
    ], dtype=float)


def euler_to_quat(phi: float, theta: float, psi: float) -> np.ndarray:
    cr, sr = np.cos(phi/2), np.sin(phi/2)
    cp, sp = np.cos(theta/2), np.sin(theta/2)
    cy, sy = np.cos(psi/2), np.sin(psi/2)
    return quat_normalize(np.array([
        cr*cp*cy + sr*sp*sy,
        sr*cp*cy - cr*sp*sy,
        cr*sp*cy + sr*cp*sy,
        cr*cp*sy - sr*sp*cy,
    ]))


def quat_error(q_ref: np.ndarray, q_meas: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return shortest-path q_ref * conj(q_meas) and its vector part."""
    qe = quat_normalize(quat_mul(quat_normalize(q_ref), quat_conj(quat_normalize(q_meas))))
    eq = qe[1:].copy()
    if qe[0] < 0:
        eq *= -1.0
    return qe, eq


def quat_angle(qe: np.ndarray) -> float:
    qe = quat_normalize(qe)
    return float(2.0*np.arctan2(np.linalg.norm(qe[1:]), max(abs(qe[0]), 1e-12)))


def reference_euler(t: float, mission: str, duration: float) -> np.ndarray:
    if mission == "hover":
        return np.zeros(3)
    if mission == "roll":
        return np.array([0.25*np.sin(0.7*t), 0.0, 0.0])
    if mission == "full3":
        return 0.5*np.sin(t + np.array([0.0, np.pi/2, np.pi]))
    if mission == "hard45":
        return np.array([
            0.55*np.sin(0.75*t) + 0.20*np.sin(2.10*t + 0.40),
            0.45*np.sin(0.95*t + np.pi/3) + 0.18*np.sin(1.75*t),
            0.65*np.sin(0.55*t + np.pi) + 0.25*np.sin(1.35*t + 0.20),
        ])
    if mission == "hardstep":
        if t < 1.0:
            return np.zeros(3)
        phase = int((t-1.0)//2.0) % 4
        return np.array([
            [0.75, -0.45, 0.55], [-0.65, 0.55, -0.70],
            [0.50, 0.50, 0.90], [-0.80, -0.35, 0.20],
        ][phase])
    if mission == "yaw360":
        s = np.clip(t/max(duration, 1e-9), 0.0, 1.0)
        return np.array([0.0, 0.0, 2*np.pi*(3*s*s-2*s*s*s)])
    raise ValueError(f"Unknown mission: {mission}")


def reference_quat(t: float, mission: str, duration: float) -> np.ndarray:
    return euler_to_quat(*reference_euler(t, mission, duration))

