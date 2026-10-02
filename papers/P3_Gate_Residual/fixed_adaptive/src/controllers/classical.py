"""
Classical quaternion P2/PD attitude controller.

Control law:
    q_err = q_ref ⊗ conj(q_meas)
    e_q   = vec(q_err)  [optionally shortest-path corrected]
    tau   = -kq * e_q - kw * omega
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from quad.math_utils import quat_normalize, quat_mul, quat_conj


@dataclass
class ControllerOutput:
    tau: np.ndarray       # commanded body torque [Nm]
    q_err: np.ndarray     # quaternion error [w,x,y,z]
    e_q: np.ndarray       # vector part of q_err used in control
    info: dict            # controller diagnostics


class ClassicalPD:
    """
    Classical quaternion PD torque controller.
    tau = -kq * e_q - kw * omega  (clipped to tau_limit)
    """
    def __init__(self, kq: np.ndarray, kw: np.ndarray, tau_limit: np.ndarray):
        self.kq = np.asarray(kq, dtype=float)
        self.kw = np.asarray(kw, dtype=float)
        self.tau_limit = np.asarray(tau_limit, dtype=float)

    def reset(self) -> None:
        pass

    def step(self, q_ref: np.ndarray, q_meas: np.ndarray,
             omega: np.ndarray, dt: float) -> ControllerOutput:
        q_ref  = quat_normalize(q_ref)
        q_meas = quat_normalize(q_meas)

        q_err = quat_mul(q_ref, quat_conj(q_meas))
        q_err = quat_normalize(q_err)
        e_q   = q_err[1:].copy()
        if q_err[0] < 0.0:
            e_q = -e_q  # shortest-path correction

        tau = -self.kq * e_q - self.kw * np.asarray(omega, dtype=float)
        tau = np.clip(tau, -self.tau_limit, self.tau_limit)

        return ControllerOutput(tau=tau, q_err=q_err, e_q=e_q,
                                info={"controller": "classical"})
