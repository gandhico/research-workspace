"""Quanser's reaction-torque lab controller: successive loop closure.

    tau2 = R_i - k_v phi_dot                   (inner loop damps the nutation mode)
    R_i  = k_p (psi_ref - psi) - k_d psi_dot   (outer PD on the gray-frame yaw)

The vendor gains (k_v = 0.2, k_p = -1.09, k_d = -0.000238) are in torque units,
as in the .mlx transfer-function design; the derivative acts on the measurement,
so a reference step does not produce a derivative kick. Negative k_p is
correct: a positive yaw error needs a negative roll torque, since psi_dot = -(h/Jz) phi.
"""
from __future__ import annotations

from dataclasses import dataclass

from .params import PARAMS


@dataclass
class ReactionTorqueController:
    kv: float = PARAMS.kv_lab
    kp: float = PARAMS.kp_lab
    kd: float = PARAMS.kd_lab

    def __call__(self, psi_ref: float, phi_dot: float, psi: float, psi_dot: float) -> float:
        r_i = self.kp * (psi_ref - psi) - self.kd * psi_dot
        return r_i - self.kv * phi_dot
