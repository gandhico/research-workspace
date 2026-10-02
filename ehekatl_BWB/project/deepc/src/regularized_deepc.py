"""Minimal NumPy-only regularized DeePC predictor and constrained optimizer."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def block_hankel(signal: np.ndarray, depth: int) -> np.ndarray:
    signal = np.asarray(signal, dtype=float)
    if signal.ndim == 1:
        signal = signal[:, None]
    columns = signal.shape[0] - depth + 1
    if columns <= 0:
        raise ValueError("Hankel depth exceeds available samples")
    return np.vstack([signal[k : k + columns].T for k in range(depth)])


@dataclass(frozen=True)
class OptimizationResult:
    future_u: np.ndarray
    predicted_y: np.ndarray
    objective: float
    iterations: int
    converged: bool
    maximum_input: float
    maximum_slew: float


class RegularizedDeePC:
    """Ridge-regularized behavioral predictor with constrained input search.

    The ridge solution maps [u_ini, y_ini, u_future] to y_future. This is the
    condensed form of regularized DeePC used for the offline feasibility audit.
    """

    def __init__(
        self,
        u_data: np.ndarray,
        y_data: np.ndarray,
        t_ini: int,
        horizon: int,
        lambda_g: float,
    ) -> None:
        self.t_ini = int(t_ini)
        self.horizon = int(horizon)
        depth = self.t_ini + self.horizon
        hu = block_hankel(u_data, depth)
        hy = block_hankel(y_data, depth)
        if hu.shape[0] != depth or hy.shape[0] != depth:
            raise ValueError("current implementation is scalar-input/scalar-output")
        up, uf = hu[: self.t_ini], hu[self.t_ini :]
        yp, yf = hy[: self.t_ini], hy[self.t_ini :]
        a = np.vstack([up, yp, uf])
        regularized = a @ a.T + float(lambda_g) * np.eye(a.shape[0])
        mapping = yf @ a.T @ np.linalg.solve(regularized, np.eye(a.shape[0]))
        self._past_map = mapping[:, : 2 * self.t_ini]
        self._future_input_map = mapping[:, 2 * self.t_ini :]

    @staticmethod
    def _project_input(
        candidate: np.ndarray, previous: float, limit: float, slew: float
    ) -> np.ndarray:
        result = np.empty_like(candidate)
        prior = float(previous)
        for index, value in enumerate(candidate):
            # Scalar comparisons are equivalent to the former scalar np.clip
            # calls and avoid thousands of temporary arrays in the online loop.
            bounded = float(value)
            if bounded < -limit:
                bounded = -limit
            elif bounded > limit:
                bounded = limit
            lower = prior - slew
            upper = prior + slew
            if bounded < lower:
                bounded = lower
            elif bounded > upper:
                bounded = upper
            if bounded < -limit:
                bounded = -limit
            elif bounded > limit:
                bounded = limit
            result[index] = bounded
            prior = bounded
        return result

    def predict(self, u_ini: np.ndarray, y_ini: np.ndarray, future_u: np.ndarray) -> np.ndarray:
        past = np.concatenate([np.asarray(u_ini).reshape(-1), np.asarray(y_ini).reshape(-1)])
        return self._past_map @ past + self._future_input_map @ np.asarray(future_u).reshape(-1)

    def optimize(
        self,
        u_ini: np.ndarray,
        y_ini: np.ndarray,
        reference: np.ndarray,
        input_limit: float,
        slew_limit: float,
        q_y: float = 1.0,
        r_u: float = 0.01,
        r_du: float = 0.05,
        max_iterations: int = 500,
        tolerance: float = 1e-9,
    ) -> OptimizationResult:
        reference = np.asarray(reference, dtype=float).reshape(self.horizon)
        previous = float(np.asarray(u_ini).reshape(-1)[-1])
        constant = self._past_map @ np.concatenate(
            [np.asarray(u_ini).reshape(-1), np.asarray(y_ini).reshape(-1)]
        )
        m = self._future_input_map
        difference = np.eye(self.horizon)
        difference[1:, :-1] -= np.eye(self.horizon - 1)
        previous_vector = np.zeros(self.horizon)
        previous_vector[0] = previous
        hessian = q_y * (m.T @ m) + r_u * np.eye(self.horizon) + r_du * (difference.T @ difference)
        linear = q_y * m.T @ (constant - reference) - r_du * difference.T @ previous_vector
        largest = float(np.linalg.eigvalsh(hessian)[-1])
        step = 0.95 / max(largest, 1e-12)
        u = self._project_input(
            np.full(self.horizon, previous), previous, input_limit, slew_limit
        )
        converged = False
        iterations = max_iterations
        for iteration in range(1, max_iterations + 1):
            candidate = self._project_input(
                u - step * (hessian @ u + linear),
                previous,
                input_limit,
                slew_limit,
            )
            if np.max(np.abs(candidate - u)) <= tolerance:
                u = candidate
                converged = True
                iterations = iteration
                break
            u = candidate
        predicted = constant + m @ u
        delta = np.diff(np.concatenate([[previous], u]))
        objective = float(
            q_y * np.sum((predicted - reference) ** 2)
            + r_u * np.sum(u**2)
            + r_du * np.sum(delta**2)
        )
        return OptimizationResult(
            future_u=u,
            predicted_y=predicted,
            objective=objective,
            iterations=iterations,
            converged=converged,
            maximum_input=float(np.max(np.abs(u))),
            maximum_slew=float(np.max(np.abs(delta))),
        )
