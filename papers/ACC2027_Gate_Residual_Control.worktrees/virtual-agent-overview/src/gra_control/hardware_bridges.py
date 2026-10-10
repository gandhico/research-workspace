from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from gra_control.gate import CMGResidualAugmentor


@dataclass
class SafeCommand:
    baseline: np.ndarray
    residual: np.ndarray
    command: np.ndarray
    gate_mean: float
    armed: bool


class SafeGateBridge:
    """Backend-independent controller bridge for existing hardware loops.

    The class never talks to hardware. It receives a reviewed baseline command and
    returns a bounded augmented command. With ``armed=False`` it returns zero output.
    This keeps PAL/Quanser/QUARC ownership, watchdogs, and kill switches in their
    existing platform runner.
    """

    def __init__(
        self,
        limits: np.ndarray,
        mode: str = "residual",
        adaptive_conductance: bool = True,
        beta: float = 0.2,
        slew_per_second: np.ndarray | None = None,
    ):
        limits = np.asarray(limits, dtype=float)
        self.limits = limits
        self.augmentor = CMGResidualAugmentor(
            limits.size, limits, mode, adaptive_conductance, beta,
        )
        self.slew = np.asarray(slew_per_second, dtype=float) if slew_per_second is not None else None
        self.previous = np.zeros_like(limits)

    def reset(self) -> None:
        self.augmentor.reset()
        self.previous.fill(0.0)

    def step(
        self,
        baseline: np.ndarray,
        learning_target: np.ndarray,
        dt: float,
        armed: bool = False,
    ) -> SafeCommand:
        baseline = np.clip(np.asarray(baseline, dtype=float), -self.limits, self.limits)
        out = self.augmentor.step(baseline, dt, learning_target)
        command = out.command.copy()
        if self.slew is not None:
            delta = np.clip(command-self.previous, -self.slew*dt, self.slew*dt)
            command = self.previous+delta
        command = np.clip(command, -self.limits, self.limits)
        if not armed:
            command = np.zeros_like(command)
        self.previous[:] = command
        return SafeCommand(
            baseline=baseline,
            residual=out.residual,
            command=command,
            gate_mean=float(np.mean(out.gate)),
            armed=armed,
        )


def qube_bridge(max_voltage: float = 0.20, beta: float = 0.2) -> SafeGateBridge:
    """One motor-voltage channel; call from the existing Qube hardware loop."""
    return SafeGateBridge(np.array([max_voltage]), beta=beta, slew_per_second=np.array([2.0]))


def qcar_bridge(max_steering: float = 0.35, beta: float = 0.2) -> SafeGateBridge:
    """One steering channel; throttle remains owned by the QCar safety scheduler."""
    return SafeGateBridge(np.array([max_steering]), beta=beta, slew_per_second=np.array([0.8]))


def hover3dof_bridge(max_motor_delta_voltage: float = 1.0, beta: float = 0.2) -> SafeGateBridge:
    """Four bounded voltage residuals around the identified hover bias voltages."""
    return SafeGateBridge(
        np.full(4, max_motor_delta_voltage), beta=beta,
        slew_per_second=np.full(4, 4.0),
    )
