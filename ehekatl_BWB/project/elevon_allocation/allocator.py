"""Constrained and covariance-aware control allocation for EHEKATL.

The model is deliberately dimensioned as angular acceleration per normalized
surface command.  Its coefficients are a transparent research prior, not an
identified X-Plane or wind-tunnel model.  Identification can replace the
matrix without changing the allocator API.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


SURFACES = (
    "elevon_L1",
    "elevon_L2",
    "elevon_L3",
    "elevon_L4",
    "elevon_R1",
    "elevon_R2",
    "elevon_R3",
    "elevon_R4",
    "rudder_L",
    "rudder_R",
)


@dataclass(frozen=True)
class EffectivenessModel:
    """Nominal effectiveness and one-sigma multiplicative uncertainty."""

    matrix: np.ndarray
    sigma_fraction: np.ndarray
    surface_names: tuple[str, ...] = SURFACES

    @staticmethod
    def research_prior() -> "EffectivenessModel":
        # Rows: roll, pitch, yaw angular acceleration [deg/s^2].
        # Columns: four left elevons, four right elevons, two rudders.
        # Positive symmetric elevon command produces positive pitch response;
        # antisymmetric command produces roll. Outer elevons have more roll
        # authority and higher assumed uncertainty.
        pitch = np.array([26.0, 24.0, 20.0, 16.0, 26.0, 24.0, 20.0, 16.0, 0.0, 0.0])
        roll = np.array([-7.0, -11.0, -17.0, -23.0, 7.0, 11.0, 17.0, 23.0, -2.0, 2.0])
        yaw = np.array([1.0, 1.4, 2.0, 2.8, -1.0, -1.4, -2.0, -2.8, 21.0, 21.0])
        sigma = np.array([0.08, 0.09, 0.12, 0.16, 0.08, 0.09, 0.12, 0.16, 0.10, 0.10])
        return EffectivenessModel(np.vstack((roll, pitch, yaw)), sigma)

    def sampled(self, rng: np.random.Generator, common_scale_sigma: float = 0.06) -> np.ndarray:
        """Draw one effectiveness matrix with common and surface uncertainty."""
        common = rng.normal(1.0, common_scale_sigma, size=(3, 1))
        surface = rng.normal(1.0, self.sigma_fraction, size=self.matrix.shape[1])
        coupling = rng.normal(0.0, 0.015, size=self.matrix.shape)
        return self.matrix * common * surface[np.newaxis, :] + coupling * np.maximum(
            np.abs(self.matrix), 2.0
        )


@dataclass(frozen=True)
class AllocationResult:
    command: np.ndarray
    achieved_nominal: np.ndarray
    residual: np.ndarray
    iterations: int
    saturated: np.ndarray


class BoxQPAllocator:
    """Warm-started projected-gradient allocator with box and slew constraints.

    It minimizes

        ||W(Bu-v)||^2 + lambda_delta ||u-u_prev||^2
        + lambda_trim ||u-u_trim||^2 + gamma u' Sigma u

    where Sigma is the expected virtual-control error caused by independent
    column-effectiveness uncertainty.  All constraints are imposed directly on
    surface commands.
    """

    def __init__(
        self,
        model: EffectivenessModel,
        dt: float,
        *,
        covariance_weight: float = 0.0,
        delta_weight: float = 0.08,
        trim_weight: float = 0.015,
        virtual_weights: tuple[float, float, float] = (1.0, 1.15, 0.8),
        command_limits: np.ndarray | None = None,
        rate_limits: np.ndarray | None = None,
        max_iterations: int = 55,
        tolerance: float = 1e-8,
    ) -> None:
        self.model = model
        self.dt = float(dt)
        self.covariance_weight = float(covariance_weight)
        self.delta_weight = float(delta_weight)
        self.trim_weight = float(trim_weight)
        self.virtual_weights = np.asarray(virtual_weights, dtype=float)
        n = model.matrix.shape[1]
        self.command_limits = np.asarray(
            command_limits if command_limits is not None else np.ones(n), dtype=float
        )
        # 60 deg/s for 25-deg elevons, 80 deg/s for 20-deg rudders.
        default_rate = np.r_[np.full(8, 60.0 / 25.0), np.full(2, 80.0 / 20.0)]
        self.rate_limits = np.asarray(rate_limits if rate_limits is not None else default_rate)
        self.max_iterations = int(max_iterations)
        self.tolerance = float(tolerance)
        self.trim = np.zeros(n)
        self.previous = np.zeros(n)
        self.enabled = np.ones(n, dtype=bool)
        self.effectiveness_scale = np.ones(n)
        self._refresh_quadratic()

    def _refresh_quadratic(self) -> None:
        b = self.model.matrix * self.effectiveness_scale[np.newaxis, :]
        w2 = np.diag(self.virtual_weights**2)
        uncertainty = np.sum((self.virtual_weights[:, None] * b) ** 2, axis=0)
        uncertainty *= self.model.sigma_fraction**2
        diagonal = self.delta_weight + self.trim_weight + self.covariance_weight * uncertainty
        self._b = b
        self._w2 = w2
        self._h = b.T @ w2 @ b + np.diag(diagonal)
        # Gradient of the objective written without its common factor two.
        self._step = 1.0 / max(float(np.linalg.eigvalsh(self._h)[-1]), 1e-9)

    def reset(self, command: np.ndarray | None = None) -> None:
        self.previous = np.zeros_like(self.previous) if command is None else np.asarray(command, float).copy()

    def configure_failure(self, surface: str, scale: float = 0.0) -> None:
        index = self.model.surface_names.index(surface)
        self.effectiveness_scale[index] = float(scale)
        self.enabled[index] = scale != 0.0
        if not self.enabled[index]:
            self.previous[index] = 0.0
        self._refresh_quadratic()

    def allocate(self, virtual_command: np.ndarray) -> AllocationResult:
        v = np.asarray(virtual_command, dtype=float)
        lower = np.maximum(-self.command_limits, self.previous - self.rate_limits * self.dt)
        upper = np.minimum(self.command_limits, self.previous + self.rate_limits * self.dt)
        lower[~self.enabled] = 0.0
        upper[~self.enabled] = 0.0

        linear = self._b.T @ self._w2 @ v + self.delta_weight * self.previous + self.trim_weight * self.trim
        command = np.clip(self.previous, lower, upper)
        iterations = 0
        for iterations in range(1, self.max_iterations + 1):
            updated = np.clip(command - self._step * (self._h @ command - linear), lower, upper)
            if np.max(np.abs(updated - command)) <= self.tolerance:
                command = updated
                break
            command = updated

        self.previous = command.copy()
        achieved = self._b @ command
        residual = achieved - v
        saturated = np.isclose(command, lower, atol=2e-6) | np.isclose(command, upper, atol=2e-6)
        return AllocationResult(command, achieved, residual, iterations, saturated)


class FixedMixer:
    """Rate-limited weighted pseudoinverse baseline."""

    def __init__(self, model: EffectivenessModel, dt: float) -> None:
        self.model = model
        self.dt = dt
        self.previous = np.zeros(model.matrix.shape[1])
        self.enabled = np.ones(model.matrix.shape[1], dtype=bool)
        self.scale = np.ones(model.matrix.shape[1])
        self.command_limits = np.ones(model.matrix.shape[1])
        self.rate_limits = np.r_[np.full(8, 60.0 / 25.0), np.full(2, 80.0 / 20.0)]

    def reset(self, command: np.ndarray | None = None) -> None:
        self.previous = np.zeros_like(self.previous) if command is None else np.asarray(command, float).copy()

    def configure_failure(self, surface: str, scale: float = 0.0) -> None:
        index = self.model.surface_names.index(surface)
        self.scale[index] = float(scale)
        self.enabled[index] = scale != 0.0
        if not self.enabled[index]:
            self.previous[index] = 0.0

    def allocate(self, virtual_command: np.ndarray) -> AllocationResult:
        b = self.model.matrix * self.scale[np.newaxis, :]
        active = np.flatnonzero(self.enabled)
        command = np.zeros_like(self.previous)
        if active.size:
            command[active] = np.linalg.pinv(b[:, active], rcond=1e-5) @ np.asarray(virtual_command, float)
        lower = np.maximum(-self.command_limits, self.previous - self.rate_limits * self.dt)
        upper = np.minimum(self.command_limits, self.previous + self.rate_limits * self.dt)
        lower[~self.enabled] = upper[~self.enabled] = 0.0
        command = np.clip(command, lower, upper)
        self.previous = command.copy()
        achieved = b @ command
        residual = achieved - virtual_command
        saturated = np.isclose(command, lower, atol=2e-6) | np.isclose(command, upper, atol=2e-6)
        return AllocationResult(command, achieved, residual, 1, saturated)
