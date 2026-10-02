"""Adaptive HyperLIF neuromorphic control (Phase 10; experimental).

Neuron core (`neuron.py`) + the PD gate-state residual controller
(`hyperlif_residual.py`). See docs/10_neuromorphic_hyperlif.md. The classical
pipeline runs unaffected; HyperLIF results on Aero2 do not exist yet.
"""
from __future__ import annotations

from aero2.control.neuromorphic.eprop import EpropSNN, HyperLIFLayer, HyperLIFParams
from aero2.control.neuromorphic.hyperlif_residual import HyperLIFResidualController
from aero2.control.neuromorphic.neuron import (
    AdaptiveHyperLIFDirect,
    HyperLIFDirect,
    NeuronStepResult,
    StandardLIFDirect,
    make_direct_neuron,
)

__all__ = [
    "HyperLIFResidualController",
    "make_direct_neuron", "NeuronStepResult",
    "StandardLIFDirect", "HyperLIFDirect", "AdaptiveHyperLIFDirect",
    "EpropSNN", "HyperLIFLayer", "HyperLIFParams",
]
