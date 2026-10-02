"""Canonical CMG online-PES residual at the Omnicopter body-wrench level.

The six learned channels are ``Fx, Fy, Fz, Mx, My, Mz`` in body axes.  The
result is always sent through :class:`hover.BoundedAllocator`; this module never
uses ``xfrc_applied`` or any other force bypass.
"""
from __future__ import annotations

import numpy as np

try:
    from gra_control.gate import CMGResidualAugmentor
except ImportError as exc:  # pragma: no cover - environment guidance
    raise ImportError(
        "The CMG-PES controller requires the ACC2027_Gate_Residual_Control "
        "package. Run with that repository's .venv or install it editable."
    ) from exc

from hover import attitude_error


class PESWrenchAugmentor:
    """Add a bounded online-PES residual to a classical six-axis wrench."""

    def __init__(self, controller, beta=0.05, learning_rate=8e-4, leak=1e-6):
        self.controller = controller
        # These are explicit software normalization/clipping envelopes, not an
        # assertion that all six extrema are simultaneously actuator-feasible.
        # The final coupled feasibility constraint is the bounded 6x8 allocator.
        row_authority = np.sum(np.abs(controller.matrix)
                               * controller.allocator.upper[None, :], axis=1)
        self.limits = np.minimum(row_authority, np.array([45., 40., 40., 2., 2., 2.]))
        self.augmentor = CMGResidualAugmentor(
            channels=6, limits=self.limits, mode="online_pes",
            adaptive_conductance=True, beta=beta,
            learning_rate=learning_rate, leak=leak)
        self.beta = float(beta)
        self.learning_rate = float(learning_rate)
        self.leak = float(leak)
        self.position_scale_m = .15
        self.velocity_scale_m_s = .75
        self.attitude_scale_rad = np.deg2rad(15.)
        self.rate_scale_rad_s = 1.5

    def reset(self):
        self.augmentor.reset()

    def learning_target(self, data):
        """Dimensionless tracking-error target, expressed in body axes."""
        c = self.controller
        r = data.xmat[c.bid].reshape(3, 3)
        omega = data.qvel[3:6].copy()
        velocity_com = data.qvel[:3] + r @ np.cross(omega, c.com)
        position_signal = ((c.target_com - data.xipos[c.bid]) / self.position_scale_m
                           + (c.target_velocity_com - velocity_com) / self.velocity_scale_m_s)
        attitude_signal = (attitude_error(data.qpos[3:7], c.target_q) / self.attitude_scale_rad
                           + (c.target_omega - omega) / self.rate_scale_rad_s)
        return np.clip(np.r_[r.T @ position_signal, attitude_signal], -1., 1.)

    def command(self, data, dt):
        baseline, metrics = self.controller.desired_wrench(data)
        target = self.learning_target(data)
        out = self.augmentor.step(baseline, dt, target)
        controls, allocation_metrics = self.controller.allocate(out.command)
        metrics.update(allocation_metrics)
        metrics.update({
            "baseline_wrench": out.baseline.copy(),
            "commanded_wrench": out.command.copy(),
            "pes_residual_wrench": out.residual.copy(),
            "pes_learning_target": target.copy(),
            "pes_activity_mean": float(np.mean(out.activity)),
            "pes_gate_mean": float(np.mean(out.gate)),
            "pes_decoder_norm": float(np.linalg.norm(self.augmentor.W)),
            "pes_residual_norm": float(np.linalg.norm(out.residual)),
        })
        return controls, metrics


def controller_metadata(pes):
    return {
        "architecture": "canonical CMGResidualAugmentor, online_pes, adaptive conductance",
        "channels": ["body_Fx", "body_Fy", "body_Fz", "body_Mx", "body_My", "body_Mz"],
        "paired_units": 12,
        "wrench_limits": pes.limits.tolist(),
        "beta": pes.beta,
        "learning_rate": pes.learning_rate,
        "leak": pes.leak,
        "target_scales": {
            "position_m": pes.position_scale_m,
            "velocity_m_s": pes.velocity_scale_m_s,
            "attitude_rad": pes.attitude_scale_rad,
            "rate_rad_s": pes.rate_scale_rad_s,
        },
        "actuation_path": "CMG-PES wrench -> bounded 6x8 allocator -> data.ctrl; no xfrc_applied",
    }
