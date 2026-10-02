"""
coaxial_trirotor.py  —  Co-axial Y6 trirotor plant (Phase 5, the paper's headline airframe).

Full body-frame rigid-body model, ported from 01_Code/y6_model.py (read-only reference),
which itself follows:
  [M] Mehndiratta & Kayacan, "Reconfigurable Fault-tolerant NMPC for a Y6 Coaxial
      Tricopter ...", IEEE CCTA 2018  -> plant + parameters (Table I)
  [C] Czyba et al., "Development of Co-Axial Y6-Rotor UAV", ICUAS 2015  -> mixer

Airframe: 3 arms in an equilateral triangle, each carrying a COAXIAL rotor pair
(top + bottom) => 6 rotors.  Rotor numbering ([M]): front arm = 3,4; back-right = 1,2;
back-left = 5,6; odd (1,3,5) = top, even (2,4,6) = bottom.

State (12), body-frame velocities, z-up:
    0:X 1:Y 2:Z   3:u 4:v 5:w   6:phi 7:theta 8:psi   9:p 10:q 11:r

=== WHAT IS NEW vs. the quadrotor (Phases 2-4) ===
  * 6 rotors in 3 coaxial pairs (vs 4); thrust F_i = KF*Omega_i^2.
  * Triangular geometry: levers l1 (front), l2 (lateral), l3 (longitudinal back).
  * Yaw is made by the coaxial TOP-vs-BOTTOM drag-torque split (Eq. 10z), not by
    a +/-/+/- rotor pattern.
  * Gyroscopic moments from the coaxial pairs (Eq. 11).
  * Full Ixz-coupled moment equations (here Ixz=0 -> positive-definite tensor).
  * A genuine 6x4 control-allocation matrix is required (see src/allocation).
"""
from dataclasses import dataclass
import numpy as np

# state indices
IX, IY, IZ, IU, IV, IW, IPHI, ITHE, IPSI, IP, IQ, IR = range(12)


@dataclass(frozen=True)
class TrirotorParams:
    m: float = 1.412            # kg
    g: float = 9.81             # m/s^2
    l1: float = 0.28            # m   front-arm lever (arm radius)
    l2: float = 0.243           # m   lateral lever of the two back arms (l1*sin60)
    l3: float = 0.14            # m   longitudinal lever of the back arms (l1*cos60)
    Ixx: float = 0.014965       # kg m^2
    Iyy: float = 0.021915       # kg m^2
    Izz: float = 0.034433       # kg m^2
    Ixz: float = 0.0            # kg m^2 (0 -> positive-definite; see y6_model notes)
    Jp: float = 6e-5            # kg m^2 propeller inertia (gyroscopic)
    KF: float = 6.85e-6         # N s^2   F_i   = KF  * Omega_i^2
    Ktau: float = 3.35e-7       # N m s^2 tau_i = Ktau* Omega_i^2
    omega_max: float = 900.0    # rad/s


def R_EB(phi, theta, psi):
    """Rotation body -> Earth (z-up)."""
    cph, sph = np.cos(phi), np.sin(phi)
    cth, sth = np.cos(theta), np.sin(theta)
    cps, sps = np.cos(psi), np.sin(psi)
    return np.array([
        [cth * cps, sph * sth * cps - sps * cph, cph * sth * cps + sph * sps],
        [cth * sps, sph * sth * sps + cps * cph, cph * sth * sps - sph * cps],
        [-sth,      sph * cth,                   cph * cth],
    ])


def T_EB(phi, theta):
    """[phidot,thetadot,psidot] = T_EB * [p,q,r]."""
    cph, sph = np.cos(phi), np.sin(phi)
    cth, tth = np.cos(theta), np.tan(theta)
    return np.array([
        [1.0, sph * tth,  cph * tth],
        [0.0, cph,       -sph],
        [0.0, sph / cth,  cph / cth],
    ])


def rotor_forces(omega, alpha, P: TrirotorParams):
    """Per-rotor thrust and drag torque from commanded speeds.

    alpha in [0,1] is the per-rotor health (1 healthy, 0 dead) -> fault-tolerance hook.
    """
    omega = np.asarray(omega, float)
    alpha = np.asarray(alpha, float)
    Om = alpha * omega
    F = P.KF * Om ** 2
    tau_drag = P.Ktau * Om ** 2
    return F, tau_drag, Om


def state_derivative(state, omega, alpha, P: TrirotorParams):
    u, v, w = state[IU], state[IV], state[IW]
    phi, theta, psi = state[IPHI], state[ITHE], state[IPSI]
    p, q, r = state[IP], state[IQ], state[IR]

    F, tau_drag, Om = rotor_forces(omega, alpha, P)
    F1, F2, F3, F4, F5, F6 = F

    Fz = F1 + F2 + F3 + F4 + F5 + F6                       # total body-z thrust

    # propeller reaction moments (coaxial Y6 structure)
    tpx = ((F5 + F6) - (F1 + F2)) * P.l2                   # roll: back-left vs back-right
    tpy = (F3 + F4) * P.l1 - (F1 + F2 + F5 + F6) * P.l3    # pitch: front vs back arms
    tpz = (tau_drag[0] + tau_drag[2] + tau_drag[4]) \
        - (tau_drag[1] + tau_drag[3] + tau_drag[5])         # yaw: top vs bottom drag

    # gyroscopic moments from the coaxial pairs
    sum_odd = Om[0] + Om[2] + Om[4]
    sum_even = Om[1] + Om[3] + Om[5]
    tgx = P.Jp * q * (sum_even - sum_odd)
    tgy = P.Jp * p * (sum_odd - sum_even)

    tau_x, tau_y, tau_z = tpx + tgx, tpy + tgy, tpz

    # force equations (body frame)
    udot = r * v - q * w + P.g * np.sin(theta)
    vdot = p * w - r * u - P.g * np.sin(phi) * np.cos(theta)
    wdot = q * u - p * v - P.g * np.cos(phi) * np.cos(theta) + Fz / P.m

    # moment equations (full Ixz-coupled form; Ixz=0 here)
    D = P.Ixx * P.Izz - P.Ixz ** 2
    pdot = (1.0 / D) * (
        (-p * q * P.Ixz + q * r * (P.Iyy - P.Izz)) * P.Izz
        - (q * r * P.Ixz + p * q * (P.Ixx - P.Iyy)) * P.Ixz
        + tau_x * P.Izz - tau_z * P.Ixz)
    qdot = p * r * (P.Izz - P.Ixx) / P.Iyy - (r ** 2 - p ** 2) * (P.Ixz / P.Iyy) + tau_y / P.Iyy
    rdot = (1.0 / D) * (
        (q * r * P.Ixz + p * q * (P.Ixx - P.Iyy)) * P.Ixx
        - (-p * q * P.Ixz + q * r * (P.Iyy - P.Izz)) * P.Ixz
        + tau_z * P.Ixx - tau_x * P.Ixz)

    pos_dot = R_EB(phi, theta, psi) @ np.array([u, v, w])
    euler_dot = T_EB(phi, theta) @ np.array([p, q, r])

    xdot = np.empty(12)
    xdot[IX:IZ + 1] = pos_dot
    xdot[IU:IW + 1] = [udot, vdot, wdot]
    xdot[IPHI:IPSI + 1] = euler_dot
    xdot[IP:IR + 1] = [pdot, qdot, rdot]
    return xdot


def rk4_step(state, omega, alpha, dt, P: TrirotorParams):
    k1 = state_derivative(state, omega, alpha, P)
    k2 = state_derivative(state + 0.5 * dt * k1, omega, alpha, P)
    k3 = state_derivative(state + 0.5 * dt * k2, omega, alpha, P)
    k4 = state_derivative(state + dt * k3, omega, alpha, P)
    return state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


class TrirotorPlantNode:
    """Stateful nengo Node: input = 6 rotor speeds [rad/s], output = 12 states."""

    def __init__(self, dt, x0=None, alpha_fn=None, P: TrirotorParams = TrirotorParams()):
        self.dt = dt
        self.P = P
        self.alpha_fn = alpha_fn or (lambda t: np.ones(6))
        self.state = np.zeros(12) if x0 is None else np.array(x0, float)

    def __call__(self, t, omega):
        self.state = rk4_step(self.state, np.asarray(omega, float),
                              self.alpha_fn(t), self.dt, self.P)
        return self.state
