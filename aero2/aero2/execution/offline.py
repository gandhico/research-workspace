"""OfflineBackend — integrates a `Model` as the plant (brief §5).

Ground truth by construction, with optional injectable encoder quantization
and sensor noise (from config.sensors). Command/torque disturbances are injected
by the Application layer. This is the first backend to come up and the reference
against which the virtual-twin and hardware backends are validated.

State layout follows the canonical 2-DOF convention x = [theta, theta_dot, psi,
psi_dot]. Reduced-DOF variants that embed in this layout (inert other axis)
compose unchanged; genuinely reduced models get a thin adapter in Phase 3.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from aero2.config import params, sensors
from aero2.execution.backend import Measurement
from aero2.models.base import Model


class OfflineBackend:
    """Deterministic plant simulation behind the `Backend` contract."""

    name = "offline"

    def __init__(
        self,
        model: Model,
        dt: float = 0.01,
        quantize: bool = False,
        measurement_noise: bool = False,
        emit_gyro: bool = False,
        seed: Optional[int] = None,
    ) -> None:
        self.model = model
        self.dt = float(dt)
        self.quantize = bool(quantize)
        self.measurement_noise = bool(measurement_noise)
        self.emit_gyro = bool(emit_gyro)
        self._rng = np.random.default_rng(seed)
        self._x = np.zeros(model.state_dim)
        self._u = np.zeros(model.input_dim)
        self._t = 0.0

    # --- Backend contract --------------------------------------------------
    def reset(self, x0: np.ndarray) -> Measurement:
        self._x = np.asarray(x0, dtype=float).reshape(self.model.state_dim).copy()
        self._u = np.zeros(self.model.input_dim)
        self._t = 0.0
        return self._measure()

    def apply(self, u: np.ndarray) -> None:
        self._u = np.asarray(u, dtype=float).reshape(self.model.input_dim).copy()

    def read(self) -> Measurement:
        self._x = self.model.step(self._x, self._u, self.dt, self._t)
        self._t += self.dt
        return self._measure()

    def dt_actual(self) -> float:
        return self.dt

    def close(self) -> None:
        pass

    # --- helpers -----------------------------------------------------------
    def _measure(self) -> Measurement:
        x = self._x
        theta = float(x[0])
        theta_dot_true = float(x[1])
        psi = float(x[2]) if self.model.state_dim >= 3 else 0.0
        psi_dot_true = float(x[3]) if self.model.state_dim >= 4 else 0.0

        ny = self._rng.normal(0.0, sensors.GYRO_NOISE_STD[1]) if self.measurement_noise else 0.0
        nz = self._rng.normal(0.0, sensors.GYRO_NOISE_STD[2]) if self.measurement_noise else 0.0

        # synthesize a raw gyro (true rate + bias + noise) so the gyro estimator path works
        gyro = None
        if self.emit_gyro:
            nx = self._rng.normal(0.0, sensors.GYRO_NOISE_STD[0]) if self.measurement_noise else 0.0
            gyro = np.array([
                sensors.GYRO_BIAS[0] + nx,
                theta_dot_true + sensors.GYRO_BIAS[1] + ny,
                psi_dot_true + sensors.GYRO_BIAS[2] + nz,
            ])

        if self.quantize:
            theta = self._quantize(theta, params.PITCH_COUNTS_PER_REV)
            psi = self._quantize(psi, params.YAW_COUNTS_PER_REV)

        return Measurement(t=self._t, theta=theta, psi=psi,
                           theta_dot=theta_dot_true + ny, psi_dot=psi_dot_true + nz,
                           gyro=gyro, raw={"x_true": x.copy()})

    @staticmethod
    def _quantize(angle: float, counts_per_rev: int) -> float:
        res = 2.0 * np.pi / counts_per_rev
        return round(angle / res) * res


__all__ = ["OfflineBackend"]
