"""Small ODE integrators used for Julia-style reference checks."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


Derivative = Callable[[np.ndarray, float], np.ndarray]


def euler_integrate(
    derivative: Derivative,
    initial_state: np.ndarray,
    current: np.ndarray,
    dt: float,
) -> np.ndarray:
    """Explicit Euler integration for ``x' = f(x, J)``."""

    current = np.asarray(current, dtype=float)
    state = np.asarray(initial_state, dtype=float).copy()
    trace = np.zeros((current.size, state.size), dtype=float)

    for k, j in enumerate(current):
        state = state + dt * derivative(state, float(j))
        trace[k] = state

    return trace


def rk4_integrate(
    derivative: Derivative,
    initial_state: np.ndarray,
    current: np.ndarray,
    dt: float,
) -> np.ndarray:
    """Fourth-order Runge-Kutta integration for ``x' = f(x, J)``."""

    current = np.asarray(current, dtype=float)
    state = np.asarray(initial_state, dtype=float).copy()
    trace = np.zeros((current.size, state.size), dtype=float)

    for k, j in enumerate(current):
        j = float(j)
        k1 = derivative(state, j)
        k2 = derivative(state + 0.5 * dt * k1, j)
        k3 = derivative(state + 0.5 * dt * k2, j)
        k4 = derivative(state + dt * k3, j)
        state = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        trace[k] = state

    return trace
