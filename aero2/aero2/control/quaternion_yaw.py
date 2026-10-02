"""Quaternion yaw PD — wrap-aware, rate-limited yaw positioning (experimental).

Yaw is represented as a unit quaternion about +z. The tracking error is the
SHORTEST-path angle from the *canonicalized* error quaternion (qw >= 0, else
negate — otherwise ``2*atan2`` can return the long way, up to +/-2*pi). This is
correct across the +/-180 deg boundary and supports continuous 360 deg+
references, unlike the naive ``psi_ref - psi``.

Removing the +/-180 deg "wall" means positioning depends on damping, so an
internal yaw setpoint slews toward the commanded yaw at a bounded rate
(``QPD_YAW_SLEW_RATE``): the loop tracks a feasible moving target and settles
instead of limit-cycling. Pitch reuses the standard PD.

For this single yaw axis the quaternion reduces to SO(2) wrapping; the
formulation generalizes directly to full 3D attitude (QDrone / QArm).
"""
from __future__ import annotations

import numpy as np

from aero2.config import gains, params
from aero2.control.base import BaseController, Reference
from aero2.control.filters import SecondOrderDerivative


# --- quaternion helpers (rotation about +z) --------------------------------
def _quat_from_yaw(psi: float) -> np.ndarray:
    return np.array([np.cos(psi / 2.0), 0.0, 0.0, np.sin(psi / 2.0)])  # [w,x,y,z]


def _quat_conj(q: np.ndarray) -> np.ndarray:
    return np.array([q[0], -q[1], -q[2], -q[3]])


def _quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ])


def yaw_error_quaternion(psi_ref: float, psi_meas: float) -> float:
    """Shortest-path yaw error via the (canonicalized) error quaternion, (-pi, pi]."""
    qe = _quat_mul(_quat_from_yaw(psi_ref), _quat_conj(_quat_from_yaw(psi_meas)))
    if qe[0] < 0.0:
        qe = -qe
    return 2.0 * np.arctan2(qe[3], qe[0])


class QuaternionYawPD(BaseController):
    """PD with a wrap-aware, rate-limited quaternion yaw channel."""

    name = "qpd"

    def __init__(
        self,
        kp_pitch: float = gains.PD_KP_PITCH,
        kd_pitch: float = gains.PD_KD_PITCH,
        kp_yaw: float = gains.QPD_KP_YAW,
        kd_yaw: float = gains.QPD_KD_YAW,
        yaw_slew_rate: float = gains.QPD_YAW_SLEW_RATE,
        wn: float = gains.DERIV_FILTER_WN,
        zeta: float = gains.DERIV_FILTER_ZETA,
        voltage_limit: float = params.V_MAX,
    ) -> None:
        super().__init__()
        self.kp_pitch = float(kp_pitch)
        self.kd_pitch = float(kd_pitch)
        self.kp_yaw = float(kp_yaw)
        self.kd_yaw = float(kd_yaw)
        self.yaw_slew_rate = abs(float(yaw_slew_rate))
        self.voltage_limit = abs(float(voltage_limit))
        self.pitch_filter = SecondOrderDerivative(wn, zeta)
        self.yaw_filter = SecondOrderDerivative(wn, zeta)
        self._psi_cmd: float | None = None

    def reset(self) -> None:
        super().reset()
        self.pitch_filter.reset()
        self.yaw_filter.reset()
        self._psi_cmd = None

    def compute(self, x_est: np.ndarray, ref: Reference, dt: float) -> np.ndarray:
        x = np.asarray(x_est, dtype=float).reshape(-1)
        theta, psi = float(x[0]), float(x[2])

        theta_rate_f = self.pitch_filter.filtered_rate
        psi_rate_f = self.yaw_filter.filtered_rate

        # Internal yaw setpoint slews toward the target along the shortest path.
        if self._psi_cmd is None:
            self._psi_cmd = psi
        to_target = yaw_error_quaternion(ref.psi, self._psi_cmd)
        max_step = self.yaw_slew_rate * max(float(dt), 1e-4)
        self._psi_cmd += float(np.clip(to_target, -max_step, max_step))

        e_theta = ref.theta - theta
        e_psi = yaw_error_quaternion(self._psi_cmd, psi)     # wrap-aware tracking error
        u_p_raw = self.kp_pitch * e_theta - self.kd_pitch * theta_rate_f
        u_y_raw = self.kp_yaw * e_psi - self.kd_yaw * psi_rate_f
        u = np.clip([u_p_raw, u_y_raw], -self.voltage_limit, self.voltage_limit)

        self.pitch_filter.update(theta, dt)
        self.yaw_filter.update(psi, dt)

        self.info = {
            "e_theta": e_theta, "e_psi": e_psi,
            "psi_cmd": self._psi_cmd, "to_target": to_target,
            "u_p_raw": u_p_raw, "u_y_raw": u_y_raw,
        }
        return u


__all__ = ["QuaternionYawPD", "yaw_error_quaternion"]
