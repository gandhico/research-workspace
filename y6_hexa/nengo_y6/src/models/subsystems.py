"""
subsystems.py  —  Phase-3 quadrotor subsystem plants (Victor's decoupled model).

Two reusable plants, both z-up and matching Quad_control_2026.py:

1. AttitudeAxis  (roll phi, pitch theta, yaw psi)
   A single rotational axis is a double integrator with the (mass-normalised)
   torque as input — exactly Victor's form  d^2(angle)/dt^2 = tau
   (inertia folded into the gains, as in Quad_control_2026.py:52-56).
       state = [angle, rate],   input = tau

2. CascadeAxis  (x via pitch, y via roll)
   The underactuated horizontal channel: position is driven by tilt.
       x_ddot = s * g * tan(theta),   theta_ddot = tau         (s = +1)
       y_ddot = s * g * tan(phi),     phi_ddot   = tau         (s = -1)
   so one parameter ``s = +/-1`` covers both.  tan() is the exact coupling
   (Victor's x-control p.28); the angle is clipped to +/- tilt_max.
       state = [pos, vel, angle, rate],   input = tau (inner torque)
"""
from dataclasses import dataclass
import numpy as np

G = 9.81
TILT_MAX = np.radians(35.0)


# ===========================================================================
# 1. single rotational axis  (roll / pitch / yaw)
# ===========================================================================
def attitude_deriv(state, tau):
    angle, rate = state
    return np.array([rate, tau])


def attitude_rk4(state, tau, dt):
    k1 = attitude_deriv(state, tau)
    k2 = attitude_deriv(state + 0.5 * dt * k1, tau)
    k3 = attitude_deriv(state + 0.5 * dt * k2, tau)
    k4 = attitude_deriv(state + dt * k3, tau)
    return state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


class AttitudePlantNode:
    """Stateful nengo Node: input tau -> output [angle, rate]."""

    def __init__(self, dt, x0=(0.0, 0.0)):
        self.dt = dt
        self.state = np.array(x0, float)

    def __call__(self, t, tau):
        self.state = attitude_rk4(self.state, float(np.atleast_1d(tau)[0]), self.dt)
        return self.state


# ===========================================================================
# 2. position->attitude cascade  (x via pitch, y via roll)
# ===========================================================================
def cascade_deriv(state, tau, s, g=G):
    pos, vel, ang, rate = state
    a = np.clip(ang, -TILT_MAX, TILT_MAX)
    return np.array([vel, s * g * np.tan(a), rate, tau])


def cascade_rk4(state, tau, s, dt, g=G):
    k1 = cascade_deriv(state, tau, s, g)
    k2 = cascade_deriv(state + 0.5 * dt * k1, tau, s, g)
    k3 = cascade_deriv(state + 0.5 * dt * k2, tau, s, g)
    k4 = cascade_deriv(state + dt * k3, tau, s, g)
    return state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


class CascadePlantNode:
    """Stateful nengo Node: input tau -> output [pos, vel, angle, rate].

    s = +1 for the x/pitch channel, s = -1 for the y/roll channel.
    """

    def __init__(self, dt, s, x0=(0.0, 0.0, 0.0, 0.0), g=G):
        self.dt = dt
        self.s = s
        self.g = g
        self.state = np.array(x0, float)

    def __call__(self, t, tau):
        self.state = cascade_rk4(self.state, float(np.atleast_1d(tau)[0]),
                                 self.s, self.dt, self.g)
        return self.state
