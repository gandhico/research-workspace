"""Analytical helpers for HyperLIF dynamics.

These functions derive interpretable quantities (depolarized fixed points,
depolarization-block onset current, and the adaptive stabilization condition)
directly from the same parameter objects used by the simulators. Every
analytical claim made in the paper is intended to be reproducible through this
module and cross-checked against simulation in the experiment scripts.
"""

from .depolarization_block import (
    adaptive_asymptotic_voltage,
    adaptive_is_db_free,
    coupled_equilibria,
    db_onset_current,
    gate_knee_voltage,
    latched_voltage,
)

__all__ = [
    "adaptive_asymptotic_voltage",
    "adaptive_is_db_free",
    "coupled_equilibria",
    "db_onset_current",
    "gate_knee_voltage",
    "latched_voltage",
]
