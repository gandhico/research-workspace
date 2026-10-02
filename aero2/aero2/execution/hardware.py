"""HardwareBackend — real-time HIL/PAL on the physical Aero2 (brief §5).

Same PAL wrapper as the digital twin, but ``hardware=1`` opens the PHYSICAL
Aero 2 (HIL/USB) instead of the QLabs virtual device at localhost:18950.
Encoder->angle scaling, gyro rates, direction-safe motor mixing and the measured
``dt_actual()`` are all inherited from ``VirtualTwinBackend`` (the twin was built
to expose the identical ``Backend`` contract), so a controller runs unchanged
across offline / virtual_twin / hardware — a single config field, per the brief.

SAFETY: the physical rotors spin. Start with low open-loop voltages, keep
``voltage_limit`` conservative, and be ready to cut power. The half-rotor
hardware path remains ``NotValidated``.
"""
from __future__ import annotations

from pathlib import Path

from aero2.execution.virtual_twin import DEFAULT_QUANSER_PYTHON, VirtualTwinBackend


class HardwareBackend(VirtualTwinBackend):
    name = "hardware"

    def __init__(self, aero_id: str | int = "0", frequency: float = 200.0,
                 read_mode: int = 1, output_mode: str = "mixed",
                 voltage_limit: float = 15.0,
                 quanser_python: Path | str | None = DEFAULT_QUANSER_PYTHON, **kwargs) -> None:
        super().__init__(
            aero_id=aero_id, frequency=frequency, read_mode=read_mode,
            output_mode=output_mode, voltage_limit=voltage_limit,
            hardware=1, quanser_python=quanser_python, **kwargs,
        )


__all__ = ["HardwareBackend"]
