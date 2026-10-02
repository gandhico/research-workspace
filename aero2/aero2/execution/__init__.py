"""Execution backends — one contract, three plants (offline / virtual-twin / hardware)."""
from __future__ import annotations

from aero2.execution.backend import Backend, Measurement
from aero2.execution.offline import OfflineBackend
from aero2.execution.virtual_twin import VirtualTwinBackend
from aero2.execution.hardware import HardwareBackend

#: name -> backend class, for config-driven `execution_mode` selection
BACKENDS = {
    "offline": OfflineBackend,
    "virtual_twin": VirtualTwinBackend,
    "hardware": HardwareBackend,
}

__all__ = [
    "Backend", "Measurement",
    "OfflineBackend", "VirtualTwinBackend", "HardwareBackend", "BACKENDS",
]
