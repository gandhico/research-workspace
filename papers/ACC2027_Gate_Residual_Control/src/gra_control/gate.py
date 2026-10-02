from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class CMGConfig:
    """Parameters of one continuous coupled membrane--gate (CMG) unit.

    The controller decodes the continuous gate state ``r``.  The unit is not a
    conventional spike/reset LIF neuron and no spike events are emitted.
    """
    tau: float = 0.05
    tau_r: float = 0.005
    v_rest: float = 0.0
    v_reset: float = 0.0
    v_threshold: float = 1.0
    alpha: float = 50.0
    gamma: float = 2.0
    base_gain: float = 120.0
    gain_scaling: float = 30.0
    current_bias: float = 0.75
    current_gain: float = 1.25
    gate_gain: float = 1.0e5


class CoupledMembraneGateBank:
    """Bank of continuous CMG units. Output is ``r``, not spike events."""

    def __init__(self, size: int, adaptive_conductance: bool, cfg: CMGConfig):
        self.cfg = cfg
        self.adaptive = adaptive_conductance
        self.v = np.full(size, cfg.v_rest, dtype=float)
        self.r = np.zeros(size, dtype=float)

    def reset(self) -> None:
        self.v.fill(self.cfg.v_rest)
        self.r.fill(0.0)

    def step(self, current: np.ndarray, dt: float) -> np.ndarray:
        p = self.cfg
        current = np.asarray(current, dtype=float)
        x = np.clip(p.alpha*(self.v-(p.v_threshold-p.gamma*self.r)), -60.0, 60.0)
        target = 1.0/(1.0+np.exp(-x))
        self.r += dt*(target-self.r)/p.tau_r
        self.r[:] = np.clip(self.r, 0.0, 1.0)

        gain = p.base_gain + (p.gain_scaling*np.abs(current) if self.adaptive else 0.0)
        conductance = gain*self.r*self.r
        lam = 1.0/p.tau + conductance
        drive = p.v_rest/p.tau + current/p.tau + conductance*p.v_reset
        decay = np.exp(-lam*dt)
        self.v[:] = self.v*decay + (drive/np.maximum(lam, 1e-12))*(1.0-decay)
        return self.r.copy()


@dataclass
class AugmentorOutput:
    command: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    activity: np.ndarray
    gate: np.ndarray


class CMGResidualAugmentor:
    """Canonical bounded residual augmentation using paired CMG units.

    ``residual`` is baseline preserving: u = sat(u0 + beta*delta).
    ``blend`` reproduces the legacy paper code: u=(1-beta)u0+beta*u_neural.
    ``online_pes`` learns the decoder online but still uses additive residual output.
    """

    def __init__(
        self,
        channels: int,
        limits: np.ndarray,
        mode: str = "residual",
        adaptive_conductance: bool = True,
        beta: float = 0.2,
        learning_rate: float = 2e-4,
        leak: float = 1e-6,
        cfg: CMGConfig | None = None,
    ):
        if mode not in {"residual", "blend", "online_pes"}:
            raise ValueError(f"Unsupported augmentation mode: {mode}")
        self.channels = channels
        self.limits = np.asarray(limits, dtype=float)
        self.mode = mode
        self.beta = float(beta)
        self.learning_rate = float(learning_rate)
        self.leak = float(leak)
        self.cfg = cfg or CMGConfig()
        self.units = CoupledMembraneGateBank(2*channels, adaptive_conductance, self.cfg)
        # Compatibility attribute for archived analysis notebooks.
        self.neurons = self.units
        self.W = np.concatenate([np.eye(channels), -np.eye(channels)], axis=1)

    def reset(self) -> None:
        self.units.reset()
        self.W[:] = np.concatenate([np.eye(self.channels), -np.eye(self.channels)], axis=1)

    def step(
        self,
        baseline: np.ndarray,
        dt: float,
        learning_target: np.ndarray | None = None,
    ) -> AugmentorOutput:
        u0 = np.clip(np.asarray(baseline, dtype=float), -self.limits, self.limits)
        normalized = np.divide(u0, self.limits, out=np.zeros_like(u0), where=self.limits > 1e-12)
        current = np.concatenate([
            self.cfg.current_bias + self.cfg.current_gain*np.maximum(normalized, 0.0),
            self.cfg.current_bias + self.cfg.current_gain*np.maximum(-normalized, 0.0),
        ])
        gate = self.units.step(current, dt)
        activity = np.clip(self.cfg.gate_gain*gate, 0.0, 1.0)
        signed = np.clip(self.W@activity, -1.0, 1.0)

        if self.mode == "online_pes" and learning_target is not None:
            target = np.clip(np.asarray(learning_target, dtype=float), -1.0, 1.0)
            self.W += self.learning_rate*np.outer(target-signed, activity) - self.leak*self.W
            self.W[:] = np.clip(self.W, -6.0, 6.0)

        neural = signed*self.limits
        if self.mode == "blend":
            command = (1.0-self.beta)*u0 + self.beta*neural
            residual = command-u0
        else:
            residual = self.beta*neural
            command = u0+residual
        command = np.clip(command, -self.limits, self.limits)
        residual = command-u0
        return AugmentorOutput(command, u0, residual, activity, gate)


# Backward-compatible import names for historical runners and saved notebooks.
# New paper-facing code should use CMGConfig, CoupledMembraneGateBank, and
# CMGResidualAugmentor.  These aliases intentionally do not change numerical
# behavior or invalidate hashes of previously saved result artifacts.
HyperLIFConfig = CMGConfig
HyperLIFBank = CoupledMembraneGateBank
GateStateAugmentor = CMGResidualAugmentor
