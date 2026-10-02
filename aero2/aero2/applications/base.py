"""`Application` interface + the single shared closed-loop runner (brief §5, §10).

An Application owns the reference generator and/or disturbance schedule and
runs the closed loop against ANY (Backend, Controller, StateEstimator) tuple,
logging to a standard record. Reference-tracking and regulation-under-disturbance
differ ONLY in their `reference()` and `disturbance()` schedules — they share
this one loop, so yaw's known weakness stays visible rather than hidden.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from aero2.control.base import Controller, Reference
from aero2.execution.backend import Backend, Measurement
from aero2.io.state_estimation import PassThroughEstimator, StateEstimator


@dataclass
class ClosedLoopRecord:
    """Standard per-run log (one row per control cycle)."""
    t: List[float] = field(default_factory=list)
    x_est: List[np.ndarray] = field(default_factory=list)
    u: List[np.ndarray] = field(default_factory=list)
    ref: List[np.ndarray] = field(default_factory=list)
    dt: List[float] = field(default_factory=list)
    meas: List[Measurement] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def append(self, t, x_est, u, ref, dt, meas) -> None:
        self.t.append(float(t))
        self.x_est.append(np.asarray(x_est, dtype=float))
        self.u.append(np.asarray(u, dtype=float))
        self.ref.append(np.asarray(ref, dtype=float))
        self.dt.append(float(dt))
        self.meas.append(meas)

    @property
    def realized_hz(self) -> float:
        """Mean realized loop rate [Hz] — every runner should print this."""
        dts = [d for d in self.dt if d > 0]
        return (1.0 / (sum(dts) / len(dts))) if dts else float("nan")


class Application(ABC):
    """Base closed-loop experiment. Subclasses define references/disturbances."""

    name: str = "application"

    def __init__(self, duration_s: float, nominal_hz: float = 100.0) -> None:
        self.duration_s = float(duration_s)
        self.nominal_dt = 1.0 / float(nominal_hz)

    # --- subclass hooks ----------------------------------------------------
    @abstractmethod
    def reference(self, t: float) -> Reference:
        """Setpoint at time t."""

    def disturbance(self, t: float) -> Optional[np.ndarray]:
        """Additive command/torque disturbance at time t (None = none)."""
        return None

    # --- the one shared loop ----------------------------------------------
    def run(
        self,
        backend: Backend,
        controller: Controller,
        estimator: Optional[StateEstimator] = None,
        x0: Optional[np.ndarray] = None,
    ) -> ClosedLoopRecord:
        estimator = estimator or PassThroughEstimator()
        x0 = np.zeros(4) if x0 is None else np.asarray(x0, dtype=float)

        controller.reset()
        estimator.reset()
        meas = backend.reset(x0)

        rec = ClosedLoopRecord(meta={
            "application": self.name,
            "controller": getattr(controller, "name", type(controller).__name__),
            "duration_s": self.duration_s,
        })

        t = float(meas.t)
        t0 = t
        dt = self.nominal_dt
        try:
            while (t - t0) < self.duration_s:
                x_est = estimator.estimate(meas, dt)
                ref = self.reference(t - t0)
                u = np.asarray(controller.compute(x_est, ref, dt), dtype=float).reshape(-1)

                d = self.disturbance(t - t0)
                u_applied = u if d is None else u + np.asarray(d, dtype=float).reshape(-1)

                backend.apply(u_applied)
                rec.append(t - t0, x_est, u_applied, ref.as_state(), dt, meas)

                meas = backend.read()
                dt = backend.dt_actual()
                t = float(meas.t)
        finally:
            backend.close()
        return rec


__all__ = ["ClosedLoopRecord", "Application"]
