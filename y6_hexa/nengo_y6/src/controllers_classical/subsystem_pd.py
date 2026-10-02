"""
subsystem_pd.py  —  classical PD controllers for the Phase-3 subsystems.

* Attitude axis (roll/pitch/yaw):   tau = Kp (a_ref - a) + Kd (rate_ref - rate)
    closed loop  a'' + Kd a' + Kp a = Kp a_ref  =>  wn = sqrt(Kp), zeta = Kd/(2 sqrt(Kp)).

* Position->attitude cascade (outer/inner):
    outer:  u_pos = Kp_p (p_ref - p) + Kd_p (0 - v)   (virtual acceleration command)
            a_des = atan2(s * u_pos, g)                (the *virtual control command*)
    inner:  tau   = Kp_a (a_des - a) + Kd_a (0 - rate)
  with the small-angle outer loop behaving as  p'' + Kd_p p' + Kp_p p = Kp_p p_ref.
  The inner (angle) loop must be faster than the outer (position) loop — classic
  time-scale separation — which the default gains respect (wn_angle = 6 >> wn_pos ~ 1.3).
"""
from dataclasses import dataclass
import numpy as np

from src.models.subsystems import G, TILT_MAX


@dataclass
class AttitudeGains:
    Kp: float
    Kd: float


@dataclass
class CascadeGains:
    Kp_p: float   # outer position P
    Kd_p: float   # outer position D
    Kp_a: float   # inner angle P
    Kd_a: float   # inner angle D


# default gains (designed for clean step responses; Victor's values noted in docs)
ATT_GAINS = {
    "roll":  AttitudeGains(Kp=36.0, Kd=8.4),   # wn=6.0, zeta=0.70
    "pitch": AttitudeGains(Kp=36.0, Kd=8.4),   # wn=6.0, zeta=0.70
    "yaw":   AttitudeGains(Kp=7.0,  Kd=3.7),   # wn=2.65, zeta=0.70  (~Victor 7/4)
}
CAS_GAINS = {
    "x": CascadeGains(Kp_p=1.6, Kd_p=2.0, Kp_a=36.0, Kd_a=8.4),  # outer wn=1.26, zeta=0.79
    "y": CascadeGains(Kp_p=3.0, Kd_p=2.4, Kp_a=36.0, Kd_a=8.4),  # outer wn=1.73, zeta=0.69
}
CAS_SIGN = {"x": +1.0, "y": -1.0}


def attitude_tau(state, ang_ref, rate_ref, G_):
    angle, rate = state
    return G_.Kp * (ang_ref - angle) + G_.Kd * (rate_ref - rate)


def cascade_control(state, pos_ref, G_, s, g=G):
    """Return (tau, a_des): outer position loop -> desired tilt -> inner angle loop."""
    pos, vel, ang, rate = state
    u_pos = G_.Kp_p * (pos_ref - pos) + G_.Kd_p * (0.0 - vel)
    a_des = np.arctan2(s * u_pos, g)
    a_des = float(np.clip(a_des, -TILT_MAX, TILT_MAX))
    tau = G_.Kp_a * (a_des - ang) + G_.Kd_a * (0.0 - rate)
    return tau, a_des


def natural_freq_att(G_):
    return float(np.sqrt(G_.Kp))


def damping_att(G_):
    return float(G_.Kd / (2.0 * np.sqrt(G_.Kp)))
