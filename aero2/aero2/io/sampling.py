"""Sampling / zero-order hold (Ref 1, Eqs. 1, 2, 25).

ZOH models the actuator side of a sampled-data loop: the digital command u_d(k)
is held constant over [k*Ts, (k+1)*Ts). The OfflineBackend already realizes this
(it holds the last applied command between reads); this module makes the concept
explicit and reusable for replaying logged input schedules.
"""
from __future__ import annotations

import numpy as np


def ts_from_fs(fs: float) -> float:
    """Sampling period Ts = 1/fs (Ref 1, Eq. 2)."""
    return 1.0 / float(fs)


class ZeroOrderHold:
    """Hold u_d(k) over the sample interval (Ref 1, Eq. 25)."""

    def __init__(self, initial=0.0) -> None:
        self._held = initial

    def update(self, u_d):
        self._held = u_d
        return self._held

    @property
    def value(self):
        return self._held

    def reset(self, initial=0.0) -> None:
        self._held = initial


def zoh_resample(t_query, t_samples, u_samples) -> np.ndarray:
    """Evaluate a ZOH-held signal u(t)=u(k) for k = max index with t_samples<=t."""
    t_query = np.atleast_1d(np.asarray(t_query, dtype=float))
    t_samples = np.asarray(t_samples, dtype=float)
    u_samples = np.asarray(u_samples, dtype=float)
    idx = np.searchsorted(t_samples, t_query, side="right") - 1
    idx = np.clip(idx, 0, len(u_samples) - 1)
    return u_samples[idx]


__all__ = ["ts_from_fs", "ZeroOrderHold", "zoh_resample"]
