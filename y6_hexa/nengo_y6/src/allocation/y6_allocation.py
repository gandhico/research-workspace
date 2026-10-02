"""
y6_allocation.py  —  control allocation for the coaxial Y6 trirotor (Phase 5).

THE structural difference from the quadrotor.  The quad controller emits virtual
commands [u, tau_phi, tau_theta, tau_psi] and feeds them straight to the plant (no
per-rotor step).  The Y6 is over-actuated (6 rotors) and under-determined by the 4
virtual commands, so it needs an explicit allocator:

    [F1..F6]^T = A_mix @ [T, tau_x, tau_y, tau_z]^T          (6x4 mixer)

then each rotor thrust is inverted to a speed:  Omega_i = sqrt(F_i / KF), clipped.

Mixer sign structure from Czyba [C, Eq.11]; lever magnitudes from Mehndiratta [M].
``allocate`` (closed form) and ``build_mixer_matrix`` (the 6x4 matrix) are
numerically identical — the matrix form is what the NEF allocator decodes.
"""
import numpy as np

from src.models.coaxial_trirotor import TrirotorParams


def allocate(T, tau_x, tau_y, tau_z, P: TrirotorParams = TrirotorParams()):
    """Closed-form map (total thrust, body moments) -> 6 per-rotor thrust demands."""
    k1 = 1.0 / (P.l1 + P.l3)
    kpsi = P.KF / (6.0 * P.Ktau)            # yaw moment -> top/bottom thrust split

    S_back = (P.l1 * T - tau_y) * k1        # F_BR + F_BL
    F_front = T - S_back                    # F3 + F4
    F_BR = 0.5 * (S_back - tau_x / P.l2)
    F_BL = 0.5 * (S_back + tau_x / P.l2)
    delta = kpsi * tau_z

    return np.array([
        0.5 * F_BR + delta,     # rotor 1 (back-right, top)
        0.5 * F_BR - delta,     # rotor 2 (back-right, bottom)
        0.5 * F_front + delta,  # rotor 3 (front, top)
        0.5 * F_front - delta,  # rotor 4 (front, bottom)
        0.5 * F_BL + delta,     # rotor 5 (back-left, top)
        0.5 * F_BL - delta,     # rotor 6 (back-left, bottom)
    ])


def build_mixer_matrix(P: TrirotorParams = TrirotorParams()):
    """The same map as ``allocate`` written as a 6x4 matrix.

    Rows F1..F6, columns [T, tau_x, tau_y, tau_z].  Used by the NEF allocator,
    which represents the 4 virtual commands in one ensemble and decodes six linear
    functions (one per rotor).
    """
    k1 = 1.0 / (P.l1 + P.l3)
    kpsi = P.KF / (6.0 * P.Ktau)
    return np.array([
        [0.5 * P.l1 * k1 / 2, -1.0 / (4 * P.l2), -k1 / 4,  kpsi],   # F1 back-right top
        [0.5 * P.l1 * k1 / 2, -1.0 / (4 * P.l2), -k1 / 4, -kpsi],   # F2 back-right bottom
        [0.5 * (1 - P.l1 * k1), 0.0,              k1 / 2,  kpsi],   # F3 front top
        [0.5 * (1 - P.l1 * k1), 0.0,              k1 / 2, -kpsi],   # F4 front bottom
        [0.5 * P.l1 * k1 / 2,  1.0 / (4 * P.l2), -k1 / 4,  kpsi],   # F5 back-left top
        [0.5 * P.l1 * k1 / 2,  1.0 / (4 * P.l2), -k1 / 4, -kpsi],   # F6 back-left bottom
    ])


def thrust_to_omega(F_cmd, P: TrirotorParams = TrirotorParams()):
    """Invert F = KF*Omega^2 (healthy rotors), then clip to [0, omega_max]."""
    omega = np.sqrt(np.clip(F_cmd, 0.0, None) / P.KF)
    return np.clip(omega, 0.0, P.omega_max)
