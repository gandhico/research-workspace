"""Minimal pendulum control plant + PD demonstrator (Stage-2 probe foundation).

A reference-tracking task: drive the pendulum angle to a moving reference theta_ref(t). The
``drive`` knob scales the reference amplitude/speed — higher drive demands larger control torque,
pushing toward the **sustained high-drive regime** where Adaptive HyperLIF's conductance/gate/origin
are theorized to matter (and where the perception benchmarks showed them inert). Torque saturates at
``u_max``, so high drive also exercises saturation — the failure mode the adaptive law is designed for.

This module is pure NumPy (no neuron), so it's cheap to validate. The spiking controller that learns
to imitate / replace the PD controller is built on top of this after Phase 2.
"""

from __future__ import annotations

import numpy as np


class Pendulum:
    """theta'' = -(g/l) sin(theta) - b*omega + u/(m l^2). Stable hanging at theta=0."""

    def __init__(self, g=9.81, l=1.0, m=1.0, b=0.25, dt=0.02, u_max=10.0):
        self.g, self.l, self.m, self.b, self.dt, self.u_max = g, l, m, b, dt, u_max

    def step(self, state, u):
        theta, omega = float(state[0]), float(state[1])
        u = float(np.clip(u, -self.u_max, self.u_max))
        domega = -(self.g / self.l) * np.sin(theta) - self.b * omega + u / (self.m * self.l**2)
        omega = omega + self.dt * domega
        theta = theta + self.dt * omega
        return np.array([theta, omega], dtype=np.float32), u


def pd_torque(state, theta_ref, kp=14.0, kd=3.5):
    theta, omega = float(state[0]), float(state[1])
    return kp * (theta_ref - theta) - kd * omega


def make_reference(T, dt, drive=1.0, kind="sine", seed=0):
    """Reference angle trajectory; ``drive`` scales how demanding it is (amplitude * speed)."""
    rng = np.random.default_rng(seed)
    t = np.arange(T) * dt
    if kind == "sine":
        return (0.35 * drive * np.sin(2 * np.pi * (0.45 * drive) * t)).astype(np.float32)
    if kind == "steps":
        ref = np.zeros(T, dtype=np.float32)
        hold = max(1, int(0.8 / dt))
        k = 0.0
        for i in range(T):
            if i % hold == 0:
                k = (rng.random() * 2 - 1) * 0.5 * drive
            ref[i] = k
        return ref
    return np.zeros(T, dtype=np.float32)


def rollout_pd(plant: Pendulum, ref, kp=14.0, kd=3.5, x0=None):
    """Roll out the PD controller. Returns features ``[T,2]`` = (error, omega), torques ``[T]``,
    angles ``[T]`` — features+torques are the imitation demonstrations for the spiking controller."""
    T = len(ref)
    state = np.array([0.0, 0.0], dtype=np.float32) if x0 is None else np.asarray(x0, np.float32)
    feats = np.zeros((T, 2), dtype=np.float32)
    us = np.zeros(T, dtype=np.float32)
    angles = np.zeros(T, dtype=np.float32)
    for i in range(T):
        u = pd_torque(state, ref[i], kp, kd)
        feats[i] = (ref[i] - state[0], state[1])
        angles[i] = state[0]
        state, u_applied = plant.step(state, u)
        us[i] = u_applied
    return feats, us, angles


def tracking_rmse(angles, ref):
    return float(np.sqrt(np.mean((np.asarray(angles) - np.asarray(ref)) ** 2)))


def make_demos(plant: Pendulum, T=200, n=24, drive=1.0, kind="sine", seed=0):
    """A batch of PD demonstrations for imitation training: feats ``[n,T,2]``, torques ``[n,T]``."""
    feats, us = [], []
    for s in range(n):
        ref = make_reference(T, plant.dt, drive=drive, kind=kind, seed=seed + s)
        f, u, _ = rollout_pd(plant, ref)
        feats.append(f)
        us.append(u)
    return np.stack(feats, 0), np.stack(us, 0)
