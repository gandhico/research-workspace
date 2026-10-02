"""Quanser 3 DOF Gyroscope parameters.

Source (vendor): Documents/Quanser/Gyroscope/Curriculum Resources/.../Reaction_Torque_1_Control_Yaw/
quanser_3dof_gyro_reaction_torque.mlx, "Load Model" and "Transfer functions" cells.

Kinematic chain: base -> gray frame (yaw psi, about z, unactuated, encoder only)
-> red gimbal (theta, about y, motor 3) -> blue gimbal (roll phi, about x, motor 2)
-> disc rotor (spin about y at the nominal pose, motor 1 speed loop).

Only the composite inertias Jx, Jy, Jz are published. The split into per-body
inertias below is an ASSUMPTION chosen so that every composite is reproduced
exactly at the nominal pose (all gimbal angles 0). Anything that depends on the
split alone (e.g. behaviour far from the nominal pose with the red gimbal free)
is not vendor-validated.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class QuanserGyroParams:
    # --- vendor values ---
    m_disc: float = 1.907                 # kg
    r_disc: float = 0.1524 / 2            # m
    Jx: float = 0.00388552                # kg m^2, about x (disc + blue gimbal)
    Jy: float = 0.02344554                # about y (disc + blue + red)
    Jz: float = 0.06632120                # about z (disc + blue + red + gray)
    kt_gimbal: float = 0.115              # N m / A (Faulhaber 3863 H048C)
    kt_disc: float = 0.0704               # N m / A (Faulhaber 2657-048 CR)
    i_max: float = 3.0                    # A
    w_ss: float = 750 * 2 * np.pi / 60    # rad/s disc reference speed
    kv_lab: float = 0.2                   # inner nutation-rate feedback (N m s/rad)
    kp_lab: float = -1.09                 # outer PD on psi, sample response in the .mlx
    kd_lab: float = -0.000238

    # --- assumed per-body split (see module docstring) ---
    blue_Iyy: float = 0.002
    blue_Izz: float = 0.002
    red_Ixx: float = 0.010
    red_Izz: float = 0.010

    @property
    def Jd(self) -> float:
        """Disc inertia about its spin axis (thin disc)."""
        return 0.5 * self.m_disc * self.r_disc**2

    @property
    def Jd_t(self) -> float:
        """Disc transverse inertia (thin disc)."""
        return 0.25 * self.m_disc * self.r_disc**2

    @property
    def h(self) -> float:
        return self.Jd * self.w_ss

    @property
    def tau_max(self) -> float:
        return self.kt_gimbal * self.i_max

    @property
    def blue_Ixx(self) -> float:
        return self.Jx - self.Jd_t

    @property
    def red_Iyy(self) -> float:
        return self.Jy - self.Jd - self.blue_Iyy

    @property
    def gray_Izz(self) -> float:
        return self.Jz - self.Jd_t - self.blue_Izz - self.red_Izz

    @property
    def nutation_hz(self) -> float:
        """Nutation frequency with the red gimbal locked: h / sqrt(Jx Jz)."""
        return self.h / np.sqrt(self.Jx * self.Jz) / (2 * np.pi)

    def check(self) -> None:
        for name in ("blue_Ixx", "red_Iyy", "gray_Izz"):
            if getattr(self, name) <= 0:
                raise ValueError(f"assumed inertia split gives non-positive {name}")


PARAMS = QuanserGyroParams()
PARAMS.check()
