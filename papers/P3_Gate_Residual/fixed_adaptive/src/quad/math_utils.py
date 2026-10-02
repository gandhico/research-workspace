"""
Canonical quaternion math utilities.
Convention: q = [q0, q1, q2, q3] = [w, x, y, z].
All functions are pure NumPy, no side effects.
"""
from __future__ import annotations
import numpy as np


def quat_normalize(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    n = np.linalg.norm(q)
    return q / n if n > 1e-12 else np.array([1.0, 0.0, 0.0, 0.0])


def quat_conj(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    return np.array([q[0], -q[1], -q[2], -q[3]])


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
    """ZYX Euler (roll, pitch, yaw) → quaternion [w,x,y,z]."""
    cphi, sphi = np.cos(phi / 2), np.sin(phi / 2)
    cth,  sth  = np.cos(theta / 2), np.sin(theta / 2)
    cpsi, spsi = np.cos(psi / 2), np.sin(psi / 2)
    return quat_normalize(np.array([
        cphi*cth*cpsi + sphi*sth*spsi,
        sphi*cth*cpsi - cphi*sth*spsi,
        cphi*sth*cpsi + sphi*cth*spsi,
        cphi*cth*spsi - sphi*sth*cpsi,
    ], dtype=float))


def quat_to_euler(q: np.ndarray) -> np.ndarray:
    """Quaternion [w,x,y,z] → ZYX Euler [roll, pitch, yaw] radians."""
    q = quat_normalize(q)
    q0, q1, q2, q3 = q
    phi   = np.arctan2(2*(q0*q1 + q2*q3), q0**2 - q1**2 - q2**2 + q3**2)
    theta = np.arcsin(np.clip(2*(q0*q2 - q3*q1), -1.0, 1.0))
    psi   = np.arctan2(2*(q0*q3 + q1*q2), q0**2 + q1**2 - q2**2 - q3**2)
    return np.array([phi, theta, psi], dtype=float)


def quat_angle_error(q_err: np.ndarray) -> float:
    """Rotation angle magnitude of an error quaternion [rad]."""
    q_err = quat_normalize(q_err)
    return float(2.0 * np.arctan2(np.linalg.norm(q_err[1:]), max(1e-12, abs(q_err[0]))))


def axis_angle_to_quat(axis: np.ndarray, angle: float) -> np.ndarray:
    axis = np.asarray(axis, dtype=float)
    n = np.linalg.norm(axis)
    if n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0])
    axis = axis / n
    half = 0.5 * angle
    return quat_normalize(np.array([
        np.cos(half),
        axis[0]*np.sin(half), axis[1]*np.sin(half), axis[2]*np.sin(half),
    ], dtype=float))


def wrap_to_pi(x: np.ndarray) -> np.ndarray:
    return (np.asarray(x) + np.pi) % (2.0 * np.pi) - np.pi


def mujoco_quat_to_body(q_mj: np.ndarray) -> np.ndarray:
    """Convert MuJoCo body quaternion to paper convention by conjugating."""
    return quat_conj(quat_normalize(q_mj))
