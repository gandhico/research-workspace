"""Model validation: one-step vs free-run + multiplicative uncertainty (Ref 3 §VII).

The central result is reported as two separate numbers (never averaged):
strong one-step prediction, weaker free-run simulation. Robust-stability uses the
multiplicative uncertainty Δm and the weight W_m(s) (Ref 3, Eqs. 35-36).
"""
from __future__ import annotations

import numpy as np

from aero2.identification import arx
from aero2.identification.arx import ArxModel


def validate_model(model: ArxModel, y, u_dict) -> dict:
    """Report one-step AND free-run fit % on a (held-out) dataset."""
    yhat = arx.one_step_predict(model, y, u_dict)
    ysim = arx.free_run_simulate(model, y, u_dict)
    return {
        "onestep_fit": arx.fit_metric(y, yhat),
        "freerun_fit": arx.fit_metric(y, ysim),
    }


def multiplicative_uncertainty(G_meas, G_nom) -> np.ndarray:
    """Δm(jω) = (G_meas - G_nom) / G_nom (Ref 3, Eq. 35)."""
    G_nom = np.asarray(G_nom, dtype=complex)
    return (np.asarray(G_meas, dtype=complex) - G_nom) / G_nom


def uncertainty_weight(omega, k: float, omega_z: float, omega_p: float) -> np.ndarray:
    """W_m(s) = k (1 + s/ωz) / (1 + s/ωp), s = jω (Ref 3, Eq. 36)."""
    s = 1j * np.asarray(omega, dtype=float)
    return k * (1.0 + s / omega_z) / (1.0 + s / omega_p)


def robust_stable(T, W_m) -> bool:
    """Robust-stability check |T(jω) W_m(jω)| < 1 for all ω."""
    return bool(np.all(np.abs(np.asarray(T) * np.asarray(W_m)) < 1.0))


__all__ = ["validate_model", "multiplicative_uncertainty", "uncertainty_weight", "robust_stable"]
