"""Neuron models: validated NumPy reference + PyTorch implementations."""

from .hyperlif_torch import (
    HyperLIFConfig,
    HyperLIFLayer,
    alif_step,
    hyperlif_step,
    lif_step,
    lif_surrogate_step,
    simulate_torch,
)

__all__ = [
    "HyperLIFConfig",
    "HyperLIFLayer",
    "alif_step",
    "hyperlif_step",
    "lif_step",
    "lif_surrogate_step",
    "simulate_torch",
]
