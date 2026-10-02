"""Small discrete-time LQR implementation used by the X-Plane bridge."""

from __future__ import annotations

import numpy as np


def dlqr(A, B, Q, R, *, tolerance=1e-10, max_iterations=10000):
    """Return the infinite-horizon discrete LQR gain and Riccati matrix."""
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    Q = np.asarray(Q, dtype=float)
    R = np.asarray(R, dtype=float)
    P = Q.copy()
    for _ in range(max_iterations):
        gain = np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)
        next_p = Q + A.T @ P @ A - A.T @ P @ B @ gain
        if np.max(np.abs(next_p - P)) < tolerance:
            P = next_p
            break
        P = next_p
    else:
        raise RuntimeError("discrete Riccati iteration did not converge")
    K = np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)
    return K, P


class LQRController:
    """Track roll and pitch using state [roll, pitch, roll_rate, pitch_rate]."""

    def __init__(self, A, B, Q, R, trim_input, rate_alpha=0.35):
        self.A = np.asarray(A, dtype=float)
        self.B = np.asarray(B, dtype=float)
        self.K, self.P = dlqr(self.A, self.B, Q, R)
        self.trim_input = np.asarray(trim_input, dtype=float)
        self.rate_alpha = float(rate_alpha)
        self._last_angles = None
        self._rates = np.zeros(2)

    @property
    def closed_loop_eigenvalues(self):
        return np.linalg.eigvals(self.A - self.B @ self.K)

    def reset(self):
        self._last_angles = None
        self._rates[:] = 0.0

    def update(self, roll_deg, pitch_deg, roll_sp_deg, pitch_sp_deg, dt):
        angles = np.array([roll_deg, pitch_deg], dtype=float)
        if self._last_angles is not None and dt > 0:
            measured = (angles - self._last_angles) / dt
            self._rates += self.rate_alpha * (measured - self._rates)
        self._last_angles = angles
        state = np.r_[angles, self._rates]
        reference = np.array([roll_sp_deg, pitch_sp_deg, 0.0, 0.0])
        command = self.trim_input - self.K @ (state - reference)
        return command, state
