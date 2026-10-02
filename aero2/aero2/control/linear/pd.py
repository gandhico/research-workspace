"""Simulink-style 2DOF PD baseline (Ref 3, Eqs. 39-41) — the benchmark to beat.

Filtered-rate damping via the shared second-order derivative filter on measured
angles, with ACTUAL measured dt. No integral term (so no anti-windup). Commands
clipped to ±V_MAX. Faithful to `M7_aero2_simulink_2dof_pd_replicate.py`:
the filtered rate is read BEFORE the filter is updated with the new angle.

Returns the virtual command u = [u_p, u_y]; motor mixing (direct/mixed) is an IO
concern handled by the backend, not here.
"""
from __future__ import annotations

import numpy as np

from aero2.config import gains, params
from aero2.control.base import BaseController, Reference
from aero2.control.filters import SecondOrderDerivative


class PD2DOF(BaseController):
    name = "pd"

    def __init__(
        self,
        kp_pitch: float = gains.PD_KP_PITCH,
        kd_pitch: float = gains.PD_KD_PITCH,
        kp_yaw: float = gains.PD_KP_YAW,
        kd_yaw: float = gains.PD_KD_YAW,
        wn: float = gains.DERIV_FILTER_WN,
        zeta: float = gains.DERIV_FILTER_ZETA,
        voltage_limit: float = params.V_MAX,
    ) -> None:
        super().__init__()
        self.kp_pitch = float(kp_pitch)
        self.kd_pitch = float(kd_pitch)
        self.kp_yaw = float(kp_yaw)
        self.kd_yaw = float(kd_yaw)
        self.voltage_limit = abs(float(voltage_limit))
        self.pitch_filter = SecondOrderDerivative(wn, zeta)
        self.yaw_filter = SecondOrderDerivative(wn, zeta)

    def reset(self) -> None:
        super().reset()
        self.pitch_filter.reset()
        self.yaw_filter.reset()

    def compute(self, x_est: np.ndarray, ref: Reference, dt: float) -> np.ndarray:
        x_est = np.asarray(x_est, dtype=float).reshape(-1)
        theta, psi = float(x_est[0]), float(x_est[2])

        # read filtered rate from prior state, THEN update (original ordering)
        theta_rate_f = self.pitch_filter.filtered_rate
        psi_rate_f = self.yaw_filter.filtered_rate

        e_theta = ref.theta - theta
        e_psi = ref.psi - psi
        u_p_raw = self.kp_pitch * e_theta - self.kd_pitch * theta_rate_f
        u_y_raw = self.kp_yaw * e_psi - self.kd_yaw * psi_rate_f
        u = np.clip([u_p_raw, u_y_raw], -self.voltage_limit, self.voltage_limit)

        self.pitch_filter.update(theta, dt)
        self.yaw_filter.update(psi, dt)

        self.info = {
            "e_theta": e_theta, "e_psi": e_psi,
            "theta_rate_f": theta_rate_f, "psi_rate_f": psi_rate_f,
            "u_p_raw": u_p_raw, "u_y_raw": u_y_raw,
        }
        return u


__all__ = ["PD2DOF"]
