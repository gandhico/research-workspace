"""
altitude_1dof.py  —  1-DOF vertical (altitude) plant. Phase-2 pedagogical anchor.

z-up convention. State s = [z, zdot].

    z_ddot = u/m - g

with u the total thrust [N], m the mass [kg], and g gravity [m/s^2].

Roll and pitch are held at zero, so the full vertical channel

    z_ddot = u * cos(theta) * cos(phi) / m - g

collapses to the 1-DOF form above because cos(0)*cos(0) = 1.

This module is the single source of truth for the altitude dynamics: the
classical controller and the Nengo controller both drive this plant, so the
benchmark compares controllers on an identical plant.

Plant of record: Victor's quad mass m = 0.9 kg.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class AltitudeParams:
    """
    Parameters for the 1-DOF altitude plant.
    """

    m: float = 0.9                 # kg, vehicle mass
    g: float = 9.81                # m/s^2, gravity
    thrust_to_weight: float = 2.5  # actuator upper limit as multiple of weight

    @property
    def u_hover(self) -> float:
        """
        Hover thrust [N].

        This is the feed-forward thrust that exactly cancels gravity.
        """
        return self.m * self.g

    @property
    def u_min(self) -> float:
        """
        Lower actuator saturation limit [N].

        Rotors cannot produce downward thrust in this simplified model.
        """
        return 0.0

    @property
    def u_max(self) -> float:
        """
        Upper actuator saturation limit [N].
        """
        return self.thrust_to_weight * self.u_hover


def clip_thrust(u, P: AltitudeParams) -> float:
    """
    Saturate commanded thrust to the physical actuator range.
    """
    return float(np.clip(u, P.u_min, P.u_max))


def dynamics(state, u: float, P: AltitudeParams) -> np.ndarray:
    """
    Continuous-time altitude dynamics.

        state = [z, zdot]
        z_dot = zdot
        zdot_dot = u/m - g
    """
    z, zdot = state

    # Keep the plant itself physically consistent.
    u_sat = clip_thrust(u, P)

    zddot = u_sat / P.m - P.g
    return np.array([zdot, zddot])


def rk4_step(state, u: float, dt: float, P: AltitudeParams) -> np.ndarray:
    """
    One fixed-step RK4 integration with zero-order hold on thrust u.

    For this linear plant, RK4 is very accurate, but we keep RK4 so the
    integrator structure matches the higher-DOF phases that follow.
    """
    k1 = dynamics(state, u, P)
    k2 = dynamics(state + 0.5 * dt * k1, u, P)
    k3 = dynamics(state + 0.5 * dt * k2, u, P)
    k4 = dynamics(state + dt * k3, u, P)

    return state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def step_reference(
    t: float,
    t_step: float = 1.0,
    z_target: float = 1.0,
    z0: float = 0.0,
) -> float:
    """
    Altitude set-point.

    Holds z0 until t_step, then steps to z_target.
    """
    return z_target if t >= t_step else z0


class AltitudePlantNode:
    """
    Stateful callable for use as a nengo.Node.

    size_in = 1
    size_out = 2

    Each simulator tick receives commanded thrust u [N], clips it to the
    actuator range, integrates the plant by one dt using RK4, and returns the
    new state [z, zdot].

    Holding the state here closes the loop inside Nengo.
    """

    def __init__(self, P: AltitudeParams, dt: float, x0=(0.0, 0.0)):
        self.P = P
        self.dt = dt
        self.state = np.array(x0, dtype=float)
        self.last_u = P.u_hover

    def __call__(self, t, u):
        u_cmd = clip_thrust(np.atleast_1d(u)[0], self.P)
        self.last_u = u_cmd
        self.state = rk4_step(self.state, u_cmd, self.dt, self.P)
        return self.state
