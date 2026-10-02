"""Research CMG-PES bank for platform-general residual-wrench experiments.

This is intentionally separate from the frozen canonical implementation.  It
preserves the same principles (continuous coupled membrane/gate state, online
PES decoder, additive bounded residual) while testing equilibrium-centred
features, heterogeneous cells, cell-count normalization, and actuator-headroom
projection.
"""
from __future__ import annotations

import numpy as np

from hover import attitude_error


class HeterogeneousCMGBank:
    def __init__(self, cells: int, dimensions: int, seed: int):
        if cells < 2 * dimensions or cells % 2:
            raise ValueError("At least one positive/negative cell pair per dimension is required")
        self.cells = cells
        rng = np.random.default_rng(seed)
        pairs = cells // 2
        extra = rng.normal(size=(pairs-dimensions, dimensions))
        if len(extra):
            extra /= np.linalg.norm(extra, axis=1, keepdims=True)
            directions = np.vstack((np.eye(dimensions), extra))
        else:
            directions = np.eye(dimensions)
        self.encoders = np.vstack((directions, -directions))
        # Heterogeneity changes actual tuning; duplicated identical cells would
        # not add representational rank.  Each +/- pair shares intrinsic
        # parameters so its zero-feature output cancels exactly.
        pair_intercept = np.r_[np.zeros(dimensions), rng.uniform(-.35, .55, len(extra))]
        self.intercept = np.tile(pair_intercept, 2)
        def paired(values):
            return np.tile(values, 2)
        self.current_bias = paired(rng.uniform(.62, .88, pairs))
        self.current_gain = paired(rng.uniform(.85, 1.65, pairs))
        self.tau = paired(.05*np.exp(rng.uniform(np.log(.55), np.log(1.8), pairs)))
        self.tau_r = paired(.005*np.exp(rng.uniform(np.log(.55), np.log(1.8), pairs)))
        self.threshold = paired(rng.uniform(.88, 1.12, pairs))
        self.alpha = paired(rng.uniform(38., 62., pairs))
        self.gamma = paired(rng.uniform(1.6, 2.4, pairs))
        self.base_gain = paired(rng.uniform(95., 145., pairs))
        self.gain_scaling = paired(rng.uniform(20., 40., pairs))
        self.v = np.zeros(cells)
        self.r = np.zeros(cells)

    def reset(self):
        self.v.fill(0.)
        self.r.fill(0.)

    def step(self, features, dt):
        projection = self.encoders @ np.asarray(features)
        current = self.current_bias + self.current_gain * np.maximum(
            projection - self.intercept, 0.)
        logistic_argument = np.clip(
            self.alpha * (self.v - (self.threshold - self.gamma*self.r)), -60., 60.)
        target_gate = 1. / (1. + np.exp(-logistic_argument))
        self.r += dt * (target_gate-self.r) / self.tau_r
        self.r[:] = np.clip(self.r, 0., 1.)
        conductance = (self.base_gain + self.gain_scaling*np.abs(current)) * self.r**2
        lam = 1./self.tau + conductance
        drive = current/self.tau
        decay = np.exp(-lam*dt)
        self.v[:] = self.v*decay + drive/np.maximum(lam, 1e-12)*(1.-decay)
        return np.clip(1e5*self.r, 0., 1.)


class HeadroomProjectedCMGPES:
    """Zero-start CMG-PES residual whose motor increment is always feasible."""

    def __init__(self, controller, cells=48, seed=0, learning_rate_per_s=8.,
                 leak_per_s=.01, beta=.25):
        self.controller = controller
        self.cells = int(cells)
        self.bank = HeterogeneousCMGBank(self.cells, 6, seed)
        # Analytic paired decoder gives an immediate error-aligned residual yet
        # exactly zero residual at zero feature.  Scaling keeps initial decoder
        # authority comparable as the number of cells grows.
        self.initial_W = self.bank.encoders.T * (12./self.cells)
        self.W = self.initial_W.copy()
        self.learning_rate_per_s = float(learning_rate_per_s)
        self.leak_per_s = float(leak_per_s)
        self.beta = float(beta)
        self.residual_authority = np.array([3., 3., 3., .18, .18, .18])
        self.position_scale_m = .15
        self.velocity_scale_m_s = .75
        self.attitude_scale_rad = np.deg2rad(15.)
        self.rate_scale_rad_s = 1.5
        self.deadzone = .02

    def reset(self):
        self.bank.reset()
        self.W[:] = self.initial_W

    def features(self, data):
        c = self.controller
        r = data.xmat[c.bid].reshape(3, 3)
        omega = data.qvel[3:6].copy()
        velocity_com = data.qvel[:3] + r @ np.cross(omega, c.com)
        translation = r.T @ ((c.target_com-data.xipos[c.bid])/self.position_scale_m
                              + (c.target_velocity_com-velocity_com)/self.velocity_scale_m_s)
        rotation = (attitude_error(data.qpos[3:7], c.target_q)/self.attitude_scale_rad
                    + (c.target_omega-omega)/self.rate_scale_rad_s)
        feature = np.clip(np.r_[translation, rotation], -1., 1.)
        feature[np.abs(feature) < self.deadzone] = 0.
        return feature

    def command(self, data, dt, learn=True):
        c = self.controller
        baseline_wrench, metrics = c.desired_wrench(data)
        baseline_controls, baseline_allocation = c.allocate(baseline_wrench)
        feature = self.features(data)
        activity = self.bank.step(feature, dt)
        decoded = np.clip(self.W @ activity, -1., 1.)
        if learn:
            rate = self.learning_rate_per_s * dt / self.cells
            self.W += rate*np.outer(feature-decoded, activity) - self.leak_per_s*dt*self.W
            self.W[:] = np.clip(self.W, -6., 6.)
        desired_residual = self.beta*self.residual_authority*decoded
        lower = c.allocator.lower - baseline_controls
        upper = c.allocator.upper - baseline_controls
        # The minimum-norm residual mixer is fixed.  Scale its direction by the
        # exact remaining motor headroom; this is deterministic, allocation-safe
        # and avoids constructing an active-set optimizer at 500 Hz.
        delta_raw = c.allocator.pinv @ (c.allocator.weight*desired_residual)
        ratios = [1.]
        ratios.extend(upper[i]/value for i, value in enumerate(delta_raw) if value > 1e-12)
        ratios.extend(lower[i]/value for i, value in enumerate(delta_raw) if value < -1e-12)
        scale = float(np.clip(min(ratios), 0., 1.))
        delta_controls = scale*delta_raw
        controls = baseline_controls + delta_controls
        applied_residual = c.matrix @ delta_controls
        total_wrench = c.matrix @ controls
        allocation_error = total_wrench - (baseline_wrench + desired_residual)
        metrics.update({
            "force_residual_N": float(np.linalg.norm(allocation_error[:3])),
            "torque_residual_Nm": float(np.linalg.norm(allocation_error[3:])),
            "saturated": bool(np.any(np.isclose(controls, c.allocator.lower, atol=1e-7))
                              or np.any(np.isclose(controls, c.allocator.upper, atol=1e-7))),
            "pes_residual_norm": float(np.linalg.norm(applied_residual)),
            "pes_requested_residual_norm": float(np.linalg.norm(desired_residual)),
            "pes_decoder_norm": float(np.linalg.norm(self.W)),
            "pes_activity_mean": float(np.mean(activity)),
            "pes_feature_norm": float(np.linalg.norm(feature)),
        })
        return controls, metrics
