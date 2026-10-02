"""`Controller` interface (brief §5).

A controller is backend-agnostic: it never knows whether it runs offline, on
the virtual twin, or on hardware. It receives an estimated state, a reference,
and the ACTUAL measured `dt` (from `Backend.dt_actual()`), and returns the
virtual command u = [u_p, u_y].

`compute(...)` returns only `u` to keep the contract clean. Controllers that
expose diagnostics (feedforward, raw command, sliding surface, ...) stash them
on `self.info` after each call; runners may log `controller.info`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

import numpy as np


@dataclass
class Reference:
    """Setpoint for the tracked outputs y = [theta, psi], with optional rates."""
    theta: float = 0.0
    psi: float = 0.0
    theta_dot: float = 0.0
    psi_dot: float = 0.0

    def as_state(self) -> np.ndarray:
        """Reference expressed in the full state layout [theta, theta_dot, psi, psi_dot]."""
        return np.array([self.theta, self.theta_dot, self.psi, self.psi_dot], dtype=float)


@runtime_checkable
class Controller(Protocol):
    """Closed-loop control law contract."""

    def reset(self) -> None:
        """Clear internal state (filters, observers, integrators)."""
        ...

    def compute(self, x_est: np.ndarray, ref: Reference, dt: float) -> np.ndarray:
        """Return command u = [u_p, u_y]; `dt` is the measured loop period."""
        ...


class BaseController:
    """Optional convenience base providing `info` and a no-op `reset`."""

    name: str = "controller"

    def __init__(self) -> None:
        self.info: dict = {}

    def reset(self) -> None:
        self.info = {}

    def compute(self, x_est: np.ndarray, ref: Reference, dt: float) -> np.ndarray:  # pragma: no cover
        raise NotImplementedError


__all__ = ["Reference", "Controller", "BaseController"]
