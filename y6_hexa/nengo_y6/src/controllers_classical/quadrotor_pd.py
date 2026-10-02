"""
quadrotor_pd.py  —  full cascaded classical controller (faithful port of Victor's
Quad_control_2026.py:61-80).  Gains are Victor's exact values.

Hierarchy (outer -> inner):
    x -> theta_d (pitch)     theta_d = atan2(-(kp_x ex + kv_x dex), g)
    y -> phi_d   (roll)      phi_d   = atan2((kp_y ey + kv_y dey) cos theta, g)
    z (altitude, with 1/cos cos)   u = (-kv_z dz - kp_z(z-z_d) + m g)/(cos theta cos phi)
    psi (yaw, set-point 0)
    inner torques:           tau_a = -kv_a da - kp_a (a - a_d)
"""
from dataclasses import dataclass
import numpy as np

from src.models.quadrotor import QuadParams


@dataclass
class QuadGains:
    kp_z: float = 40.0; kv_z: float = 5.0
    kp_x: float = 1.6;  kv_x: float = 2.0
    kp_y: float = 3.0;  kv_y: float = 2.0
    kp_phi: float = 40.0;   kv_phi: float = 8.0
    kp_theta: float = 120.0; kv_theta: float = 8.0
    kp_psi: float = 7.0;    kv_psi: float = 4.0


def quad_control(X, refs, K: QuadGains, P: QuadParams = QuadParams()):
    """Return (u, tau_psi, tau_theta, tau_phi, theta_d, phi_d) for state X.

    refs = (x_d, dx_d, y_d, dy_d, z_d, psi_d).
    """
    x, dx, y, dy, z, dz, psi, dpsi, theta, dtheta, phi, dphi = X
    x_d, dx_d, y_d, dy_d, z_d, psi_d = refs
    m, g = P.m, P.g

    theta_d = np.arctan2(-(K.kp_x * (x - x_d) + K.kv_x * (dx - dx_d)), g)
    phi_d = np.arctan2((K.kp_y * (y - y_d) + K.kv_y * (dy - dy_d)) * np.cos(theta), g)

    u = (-K.kv_z * dz - K.kp_z * (z - z_d) + m * g) / (np.cos(theta) * np.cos(phi))
    tau_psi = -K.kv_psi * dpsi - K.kp_psi * (psi - psi_d)
    tau_theta = -K.kv_theta * dtheta - K.kp_theta * (theta - theta_d)
    tau_phi = -K.kv_phi * dphi - K.kp_phi * (phi - phi_d)
    return u, tau_psi, tau_theta, tau_phi, theta_d, phi_d
