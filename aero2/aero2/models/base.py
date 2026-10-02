"""`Model` interface — pure plant dynamics, no I/O (brief §5).

A Model knows only how the plant evolves. It never reads sensors or commands
actuators; that is the Backend's job. Every variant (2-DOF helicopter, pitch-only,
yaw-only, half-rotor) subclasses `Model` and is therefore interchangeable to
identification, control, and applications.

Convention (config.params): x = [theta, theta_dot, psi, psi_dot], u = [u_p, u_y],
y = [theta, psi]. Subclasses with fewer DOF document their reduced layout.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class Model(ABC):
    """Continuous-time plant with optional analytic linearization."""

    #: subclasses set these
    state_dim: int
    input_dim: int
    output_dim: int
    name: str = "model"

    # --- required dynamics -------------------------------------------------
    @abstractmethod
    def f(self, x: np.ndarray, u: np.ndarray, t: float = 0.0) -> np.ndarray:
        """Continuous nonlinear dynamics: return xdot = f(x, u, t)."""

    @abstractmethod
    def output(self, x: np.ndarray) -> np.ndarray:
        """Measurement map y = h(x)."""

    # --- provided defaults (override for speed / exactness) ----------------
    def step(self, x: np.ndarray, u: np.ndarray, dt: float, t: float = 0.0) -> np.ndarray:
        """Discrete one-step update via RK4 of `f` (override for closed-form)."""
        x = np.asarray(x, dtype=float)
        u = np.asarray(u, dtype=float)
        dt = float(dt)
        k1 = self.f(x, u, t)
        k2 = self.f(x + 0.5 * dt * k1, u, t + 0.5 * dt)
        k3 = self.f(x + 0.5 * dt * k2, u, t + 0.5 * dt)
        k4 = self.f(x + dt * k3, u, t + dt)
        return x + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    def linearize(self, x0: np.ndarray, u0: np.ndarray, eps: float = 1e-6):
        """Numerical Jacobians (A, B, C, D) about (x0, u0).

        Variants with an analytic linear model (e.g. the 2-DOF helicopter)
        should override this to return the exact paper matrices.
        """
        x0 = np.asarray(x0, dtype=float)
        u0 = np.asarray(u0, dtype=float)
        n, m, p = self.state_dim, self.input_dim, self.output_dim
        A = np.zeros((n, n))
        B = np.zeros((n, m))
        C = np.zeros((p, n))
        D = np.zeros((p, m))
        f0 = self.f(x0, u0)
        y0 = self.output(x0)
        for i in range(n):
            dx = np.zeros(n); dx[i] = eps
            A[:, i] = (self.f(x0 + dx, u0) - f0) / eps
            C[:, i] = (self.output(x0 + dx) - y0) / eps
        for j in range(m):
            du = np.zeros(m); du[j] = eps
            B[:, j] = (self.f(x0, u0 + du) - f0) / eps
        return A, B, C, D


__all__ = ["Model"]
