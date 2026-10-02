"""
trirotor_pd.py  —  classical cascaded controller for the coaxial Y6 trirotor (Phase 5).

Identical cascade *recipe* to the quadrotor (outer position PD -> attitude set-points,
inner attitude PD -> body moments), then the Y6-specific allocation:

    position PD  ->  (T, phi*, theta*, psi*)
    attitude PD  ->  (tau_x, tau_y, tau_z)
    allocate     ->  6 rotor thrusts  ->  thrust_to_omega -> 6 rotor speeds

Gains from 01_Code/y6_model.py (read-only reference).
"""
from dataclasses import dataclass
import numpy as np

from src.models.coaxial_trirotor import (TrirotorParams, R_EB,
                                         IX, IY, IZ, IU, IW, IPHI, ITHE, IPSI, IP, IQ, IR)
from src.allocation.y6_allocation import allocate, thrust_to_omega


@dataclass(frozen=True)
class TrirotorIntegralGains:
    """Outer-loop integral gains for the NEF controller (Phase 5a).

    Reject the constant neural-decode bias that a pure-PD loop leaves as a
    steady-state position/yaw offset.  Used only by the NEF builder.
    """
    Ki_xy: float = 0.5
    Ki_z: float = 2.0
    Ki_psi: float = 0.4


@dataclass(frozen=True)
class TrirotorGains:
    Kp_xy: float = 2.0; Kd_xy: float = 2.6
    Kp_z: float = 9.0;  Kd_z: float = 5.2
    Kp_phi: float = 1.3; Kd_phi: float = 0.28
    Kp_the: float = 1.8; Kd_the: float = 0.36
    Kp_psi: float = 1.0; Kd_psi: float = 0.32
    tilt_max: float = np.radians(35.0)
    T_to_w: float = 2.5            # thrust limit = T_to_w * m g


def position_controller(state, ref, P: TrirotorParams, G: TrirotorGains):
    """Outer loop: position error -> (total thrust T, phi*, theta*, psi*)."""
    x, y, z = state[IX], state[IY], state[IZ]
    phi, theta, psi = state[IPHI], state[ITHE], state[IPSI]
    vx, vy, vz = R_EB(phi, theta, psi) @ state[IU:IW + 1]
    x_des, y_des, z_des, psi_des = ref

    ax_des = G.Kp_xy * (x_des - x) - G.Kd_xy * vx
    ay_des = G.Kp_xy * (y_des - y) - G.Kd_xy * vy

    cps, sps = np.cos(psi), np.sin(psi)
    theta_des = np.clip((ax_des * cps + ay_des * sps) / P.g, -G.tilt_max, G.tilt_max)
    phi_des = np.clip((ax_des * sps - ay_des * cps) / P.g, -G.tilt_max, G.tilt_max)

    ez = z_des - z
    T = (P.m * P.g + G.Kp_z * ez - G.Kd_z * vz) / max(np.cos(phi) * np.cos(theta), 0.5)
    T = np.clip(T, 0.0, G.T_to_w * P.m * P.g)
    return T, phi_des, theta_des, psi_des


def attitude_controller(state, att_des, G: TrirotorGains):
    """Inner loop: attitude error -> body moments (tau_x, tau_y, tau_z)."""
    phi, theta, psi = state[IPHI], state[ITHE], state[IPSI]
    p, q, r = state[IP], state[IQ], state[IR]
    phi_des, theta_des, psi_des = att_des
    tau_x = G.Kp_phi * (phi_des - phi) - G.Kd_phi * p
    tau_y = G.Kp_the * (theta_des - theta) - G.Kd_the * q
    tau_z = G.Kp_psi * (psi_des - psi) - G.Kd_psi * r
    return tau_x, tau_y, tau_z


def baseline_control(state, ref, P: TrirotorParams, G: TrirotorGains):
    """Full cascade -> 6 rotor speed commands [rad/s] (+ info dict)."""
    T, phi_des, theta_des, psi_des = position_controller(state, ref, P, G)
    tau_x, tau_y, tau_z = attitude_controller(state, (phi_des, theta_des, psi_des), G)
    F_cmd = allocate(T, tau_x, tau_y, tau_z, P)
    omega = thrust_to_omega(F_cmd, P)
    return omega, dict(T=T, att_des=(phi_des, theta_des, psi_des),
                       tau=(tau_x, tau_y, tau_z), F=F_cmd)
