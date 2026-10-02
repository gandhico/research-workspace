"""
Rotor mixer: convert [collective_thrust, tau_x, tau_y, tau_z] to motor commands.

For Skydio X2:
    Motor layout  (from scene.xml site positions):
      thrust1: (-0.14, -0.18, 0.05)  yaw gear = -0.0201  (CW)
      thrust2: (-0.14,  0.18, 0.05)  yaw gear = +0.0201  (CCW)
      thrust3: ( 0.14,  0.18, 0.08)  yaw gear = -0.0201  (CW)
      thrust4: ( 0.14, -0.18, 0.08)  yaw gear = +0.0201  (CCW)

    Mixer B satisfies: [T, τx, τy, τz]^T = B @ [u1,u2,u3,u4]^T
    Motor commands: u = B_inv @ [T, τx, τy, τz]^T

For CF2:
    CF2 uses virtual wrench actuators; this module provides the X2 mixer only.
    CF2 commands are applied via bridge.apply_cf2_wrench().
"""
from __future__ import annotations
import numpy as np

from quad.models import DroneParams


def wrench_to_motors(T: float, tau: np.ndarray, params: DroneParams,
                     clip: bool = True) -> np.ndarray:
    """
    Convert [collective_thrust T (N), tau=[τx,τy,τz] (Nm)] to motor commands.

    Returns u: array of shape (4,), clipped to [ctrl_min, ctrl_max] if clip=True.
    Raises ValueError if params.actuator_mode != "rotor4".
    """
    if params.actuator_mode != "rotor4":
        raise ValueError(
            f"wrench_to_motors requires actuator_mode='rotor4', got '{params.actuator_mode}'."
        )
    if params.mixer_B_inv is None:
        raise ValueError("mixer_B_inv not populated in DroneParams.")

    wrench = np.array([T, tau[0], tau[1], tau[2]], dtype=float)
    u = params.mixer_B_inv @ wrench

    if clip:
        u = np.clip(u, params.ctrl_min_vector(), params.ctrl_max_vector())

    return u


def motors_to_wrench(u: np.ndarray, params: DroneParams) -> tuple[float, np.ndarray]:
    """
    Convert motor commands back to [T, tau_x, tau_y, tau_z].
    Returns (T, tau) where T is scalar and tau is (3,) array.
    """
    if params.mixer_B is None:
        raise ValueError("mixer_B not populated in DroneParams.")
    wrench = params.mixer_B @ np.asarray(u, dtype=float)
    return float(wrench[0]), wrench[1:].copy()


def hover_wrench(params: DroneParams, state_pos: np.ndarray,
                 state_vel: np.ndarray, R_wb: np.ndarray,
                 z_ref: float = 1.0,
                 kz: float = 6.0, kdz: float = 4.0) -> float:
    """
    Compute collective thrust for altitude stabilization.
    Returns T (N), the total vertical thrust magnitude.
    """
    body_z_world = R_wb[:, 2]
    tilt_cos = max(0.35, body_z_world[2])

    T = params.total_mass * (
        params.gravity + kz * (z_ref - state_pos[2]) + kdz * (0.0 - state_vel[2])
    ) / tilt_cos
    T_max = 2.5 * params.total_mass * max(params.gravity, 1.0)
    return float(np.clip(T, 0.0, T_max))


def saturation_flags(u: np.ndarray, params: DroneParams,
                     tol: float = 1e-6) -> np.ndarray:
    """Return boolean array of which motors hit their limits."""
    u = np.asarray(u)
    lo = params.ctrl_min_vector()
    hi = params.ctrl_max_vector()
    return (np.abs(u - lo) < tol) | (np.abs(u - hi) < tol)
