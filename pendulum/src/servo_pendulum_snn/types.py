from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class QubeState:
    time_s: float
    theta_rad: float
    theta_dot_rad_s: float
    alpha_rad: float
    alpha_dot_rad_s: float
    motor_current_a: float
    amplifier_fault: float
    motor_stall_detected: float
    motor_stall_error: float


@dataclass(frozen=True)
class QubeCommand:
    voltage: float
    baseline_voltage: float
    residual_voltage: float = 0.0
    gate_pos: float = 0.0
    gate_neg: float = 0.0
    control_mode: str = "zero"
    info: dict[str, Any] = field(default_factory=dict)
