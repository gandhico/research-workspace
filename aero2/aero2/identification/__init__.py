"""System identification (Refs 2 & 3): excitation, nonparametric, ARX/DARX,
validation (one-step vs free-run), state-space realization."""
from __future__ import annotations

from aero2.identification import excitation, nonparametric, ss_realize, validation
from aero2.identification.arx import (
    ArxModel,
    fit_arx,
    fit_metric,
    free_run_simulate,
    one_step_predict,
    prepare,
)

__all__ = [
    "excitation", "nonparametric", "ss_realize", "validation",
    "ArxModel", "fit_arx", "fit_metric", "free_run_simulate", "one_step_predict", "prepare",
]
