"""
3-axis STN-PID / STN-PID-PES attitude controller core.

This module is independent from MuJoCo. It receives a 3D attitude-error vector
and angular velocity vector, then returns a 3D torque command.

It is designed to be connected later to:

    experiments/controller_benchmarks/mujoco_classical_vs_neural.py

Controller modes:
    pid       : fixed 3-axis PID
    stn       : self-tuning PID using finite-difference sensitivity
    stn_pes   : self-tuning PID using PES-inspired learned sensitivity

Implemented control law per axis:

    tau_i = Kp_i * e_i + Ki_i * integral(e_i) + Kd_i * de_i/dt

For attitude control, we use:

    de_i/dt ≈ -omega_i

because if the desired reference is slowly varying, the attitude-error derivative
is approximately the negative body angular velocity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple
import numpy as np


def clip_array(x: np.ndarray, lo: float | np.ndarray, hi: float | np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(x, lo), hi)


@dataclass
class STNPIDAttitudeState:
    integral: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))
    prev_error: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))
    prev_tau: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))
    prev_measure: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))
    filtered_derivative: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))
    initialized: bool = False


@dataclass
class STNPIDAttitudeController:
    """
    3-axis attitude STN-PID / PES controller.

    Parameters are intentionally conservative. The output torque is clipped.
    """

    mode: str = "stn_pes"

    # Initial PID gains per axis.
    Kp: np.ndarray = field(default_factory=lambda: np.array([0.03, 0.03, 0.03], dtype=float))
    Ki: np.ndarray = field(default_factory=lambda: np.array([0.0005, 0.0005, 0.0005], dtype=float))
    Kd: np.ndarray = field(default_factory=lambda: np.array([0.002, 0.002, 0.002], dtype=float))

    # Gain limits.
    Kp_min: float = 0.0
    Kp_max: float = 0.25
    Ki_min: float = 0.0
    Ki_max: float = 0.02
    Kd_min: float = 0.0
    Kd_max: float = 0.05

    # Learning rates.
    eta_p: float = 2.0e-4
    eta_i: float = 2.0e-6
    eta_d: float = 2.0e-5

    # Sensitivity estimate per axis.
    sensitivity: np.ndarray = field(default_factory=lambda: np.ones(3, dtype=float))
    sensitivity_min: float = -20.0
    sensitivity_max: float = 20.0
    sensitivity_smoothing: float = 0.02
    pes_learning_rate: float = 0.02

    # Safety.
    tau_limit: float = 0.02
    integral_limit: float = 2.0
    derivative_filter: float = 0.15

    state: STNPIDAttitudeState = field(default_factory=STNPIDAttitudeState)

    def reset(self) -> None:
        self.state = STNPIDAttitudeState()

    def estimate_sensitivity_fd(
        self,
        measure: np.ndarray,
        tau: np.ndarray,
        eps: float = 1e-8,
    ) -> np.ndarray:
        """
        Finite-difference sensitivity per axis:

            S_i = d(measure_i) / d(tau_i)

        If the torque change is too small, keep the previous sensitivity.
        """
        d_measure = measure - self.state.prev_measure
        d_tau = tau - self.state.prev_tau

        s_fd = self.sensitivity.copy()

        for i in range(3):
            if abs(d_tau[i]) >= eps:
                s_fd[i] = d_measure[i] / d_tau[i]

        s_fd = clip_array(s_fd, self.sensitivity_min, self.sensitivity_max)

        s = (
            (1.0 - self.sensitivity_smoothing) * self.sensitivity
            + self.sensitivity_smoothing * s_fd
        )
        return clip_array(s, self.sensitivity_min, self.sensitivity_max)

    def update_sensitivity_pes(
        self,
        error: np.ndarray,
        tau: np.ndarray,
    ) -> np.ndarray:
        """
        PES-inspired sensitivity update.

        This avoids direct division by d_tau.

        activity_i = tanh(tau_i / tau_limit)

        S_i <- S_i + lr * error_i * activity_i
        """
        denom = max(self.tau_limit, 1e-12)
        activity = np.tanh(tau / denom)

        delta_s = self.pes_learning_rate * error * activity

        s_candidate = self.sensitivity + delta_s
        s = (
            (1.0 - self.sensitivity_smoothing) * self.sensitivity
            + self.sensitivity_smoothing * s_candidate
        )

        return clip_array(s, self.sensitivity_min, self.sensitivity_max)

    def update_gains(
        self,
        error: np.ndarray,
        integral: np.ndarray,
        derivative: np.ndarray,
        sensitivity: np.ndarray,
    ) -> None:
        """
        Conservative self-tuning update per axis.

        We use sign(sensitivity) to preserve the estimated control direction.
        """
        direction = np.where(sensitivity >= 0.0, 1.0, -1.0)

        self.Kp = self.Kp + self.eta_p * direction * error * error
        self.Ki = self.Ki + self.eta_i * direction * error * integral
        self.Kd = self.Kd + self.eta_d * direction * error * derivative

        self.Kp = clip_array(self.Kp, self.Kp_min, self.Kp_max)
        self.Ki = clip_array(self.Ki, self.Ki_min, self.Ki_max)
        self.Kd = clip_array(self.Kd, self.Kd_min, self.Kd_max)

    def step(
        self,
        error: np.ndarray,
        omega: np.ndarray,
        dt: float,
        measure: np.ndarray | None = None,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Compute torque command.

        Args:
            error:
                3D attitude-error vector.
            omega:
                3D angular velocity vector.
            dt:
                timestep.
            measure:
                optional measured variable for sensitivity estimation.
                If None, error is used.
        """
        error = np.asarray(error, dtype=float).reshape(3)
        omega = np.asarray(omega, dtype=float).reshape(3)

        if measure is None:
            measure = error
        else:
            measure = np.asarray(measure, dtype=float).reshape(3)

        if not self.state.initialized:
            self.state.prev_error = error.copy()
            self.state.prev_measure = measure.copy()
            self.state.prev_tau = np.zeros(3, dtype=float)
            self.state.initialized = True

        self.state.integral = self.state.integral + error * dt
        self.state.integral = clip_array(
            self.state.integral,
            -self.integral_limit,
            self.integral_limit,
        )

        # In attitude control, use filtered error derivative.
        raw_derivative = (error - self.state.prev_error) / max(dt, 1e-12)

        # Blend with -omega to make derivative physically meaningful.
        derivative_measure = 0.5 * raw_derivative + 0.5 * (-omega)

        self.state.filtered_derivative = (
            (1.0 - self.derivative_filter) * self.state.filtered_derivative
            + self.derivative_filter * derivative_measure
        )

        derivative = self.state.filtered_derivative

        tau_raw = (
            self.Kp * error
            + self.Ki * self.state.integral
            + self.Kd * derivative
        )

        tau = clip_array(tau_raw, -self.tau_limit, self.tau_limit)

        if self.mode == "pid":
            pass

        elif self.mode == "stn":
            self.sensitivity = self.estimate_sensitivity_fd(measure=measure, tau=tau)
            self.update_gains(
                error=error,
                integral=self.state.integral,
                derivative=derivative,
                sensitivity=self.sensitivity,
            )

        elif self.mode == "stn_pes":
            self.sensitivity = self.update_sensitivity_pes(error=error, tau=tau)
            self.update_gains(
                error=error,
                integral=self.state.integral,
                derivative=derivative,
                sensitivity=self.sensitivity,
            )

        else:
            raise ValueError(f"Unknown STN-PID attitude mode: {self.mode}")

        self.state.prev_error = error.copy()
        self.state.prev_measure = measure.copy()
        self.state.prev_tau = tau.copy()

        info = {
            "tau_stn_x": float(tau[0]),
            "tau_stn_y": float(tau[1]),
            "tau_stn_z": float(tau[2]),
            "Kp_x": float(self.Kp[0]),
            "Kp_y": float(self.Kp[1]),
            "Kp_z": float(self.Kp[2]),
            "Ki_x": float(self.Ki[0]),
            "Ki_y": float(self.Ki[1]),
            "Ki_z": float(self.Ki[2]),
            "Kd_x": float(self.Kd[0]),
            "Kd_y": float(self.Kd[1]),
            "Kd_z": float(self.Kd[2]),
            "sens_x": float(self.sensitivity[0]),
            "sens_y": float(self.sensitivity[1]),
            "sens_z": float(self.sensitivity[2]),
            "int_x": float(self.state.integral[0]),
            "int_y": float(self.state.integral[1]),
            "int_z": float(self.state.integral[2]),
        }

        return tau, info
