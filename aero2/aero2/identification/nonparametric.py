"""Nonparametric identification (Ref 3 §V): step DC gain, empirical FRF, FFT.

Used for linearity checks and the correlation/FFT comparison. Note (Ref 3): the
primary yaw FRF is ω_z,c / v_yaw (not ψ / v_yaw), because the yaw angle is
encoder-limited; the pitch sensitive band is ~0.6-0.8 Hz.
"""
from __future__ import annotations

import numpy as np


def step_dc_gain(y, u_amplitude: float) -> float:
    y = np.asarray(y, dtype=float)
    return float((y[-1] - y[0]) / u_amplitude) if u_amplitude != 0 else float("nan")


def fft_spectrum(x, fs: float):
    x = np.asarray(x, dtype=float)
    return np.fft.rfftfreq(len(x), 1.0 / fs), np.abs(np.fft.rfft(x))


def empirical_frf(u, y, fs: float):
    """Crude FRF estimate G(f) = Y(f)/U(f)."""
    u = np.asarray(u, dtype=float)
    y = np.asarray(y, dtype=float)
    U = np.fft.rfft(u)
    Y = np.fft.rfft(y)
    f = np.fft.rfftfreq(len(u), 1.0 / fs)
    G = Y / np.where(np.abs(U) < 1e-12, 1e-12, U)
    return f, G


__all__ = ["step_dc_gain", "fft_spectrum", "empirical_frf"]
