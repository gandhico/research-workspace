"""aero2 — Quanser Aero2 modelling, identification, and control.

A clean, math-traceable refactor of the original Aero2 system-ID/control work,
restructured around four composable interfaces (Model x Backend x Controller x
Application) with a first-class separation between offline / virtual-twin /
hardware execution modes, and scaffolded for a future Adaptive HyperLIF
(neuromorphic) research phase.

See CLAUDE.md for working notes and docs/ for the math <-> code mapping.
"""
from __future__ import annotations

__version__ = "0.1.0"
