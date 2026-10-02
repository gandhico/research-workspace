"""Excitation signal design (Ref 2, Ref 3 §VI-A).

Trim search, pitch doublet, PRBS common-mode, yaw chirp (pure differential),
coupled. The recorded campaigns live in data/raw_logs/; these generators
reproduce the excitation design for new offline/virtual runs.
"""
from __future__ import annotations

import numpy as np

from aero2.config import params


def prbs(n: int, amplitude: float = 1.0, min_dwell: int = 1, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    seq = []
    while len(seq) < n:
        seq.extend([amplitude if rng.random() < 0.5 else -amplitude] * max(1, min_dwell))
    return np.asarray(seq[:n], dtype=float)


def doublet(t, amplitude: float, t_start: float, width: float) -> np.ndarray:
    t = np.asarray(t, dtype=float)
    u = np.zeros_like(t)
    u[(t >= t_start) & (t < t_start + width)] = amplitude
    u[(t >= t_start + width) & (t < t_start + 2 * width)] = -amplitude
    return u


def chirp(t, f0: float, f1: float, amplitude: float, duration: float = None) -> np.ndarray:
    t = np.asarray(t, dtype=float)
    T = duration if duration is not None else (t[-1] - t[0])
    k = (f1 - f0) / T if T > 0 else 0.0
    return amplitude * np.sin(2.0 * np.pi * (f0 * t + 0.5 * k * t * t))


def prbs_common_mode(n: int, u0: float = params.U0_TRIM, v_pitch: float = 0.075, **kw):
    """Pitch PRBS about trim: u_left = u_right = U0 + v_pitch (Ref 3 §VI-A)."""
    v = prbs(n, v_pitch, **kw)
    return u0 + v, u0 + v


def pure_differential(v_yaw):
    """Yaw drive u_L = -v_psi, u_R = +v_psi (Ref 1 §F, Ref 3 Eq. 27)."""
    v = np.asarray(v_yaw, dtype=float)
    return -v, v


def trim_levels(low: float = 1.2, high: float = 2.0, step: float = 0.2) -> np.ndarray:
    """Equal-voltage sweep for the trim search (-> U0 ~ 1.4 V)."""
    return np.arange(low, high + 1e-9, step)


__all__ = ["prbs", "doublet", "chirp", "prbs_common_mode", "pure_differential", "trim_levels"]
