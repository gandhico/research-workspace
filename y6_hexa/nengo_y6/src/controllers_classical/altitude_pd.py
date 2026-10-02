"""
altitude_pd.py  —  classical PD + gravity feed-forward altitude controller.

Control law (the same one Victor uses, Quad_control_2026.py:61-62):

    u = m g + Kp (z_ref - z) + Kd (zdot_ref - zdot)      (then clipped)

The  m g  term cancels the -g in the plant (feedback linearisation), leaving a
clean second-order error system  e = z_ref - z :

    m e'' + Kd e' + Kp e = 0
      =>  omega_n = sqrt(Kp/m),   zeta = Kd / (2 sqrt(Kp m)).

Gains below give omega_n ~ 3 rad/s, zeta ~ 0.75 for m = 0.9 kg: a crisp, lightly
damped step with a transient thrust (~1.9 x hover) that stays inside the 2.5 x
actuator limit.  (Victor's original kp=40/kd=5 were tuned for a *smooth* sigmoid
reference; on a hard step they would demand ~5 x hover and saturate, so we retune
for the step benchmark and document it.)
"""
from dataclasses import dataclass
import numpy as np

from src.models.altitude_1dof import AltitudeParams, clip_thrust


@dataclass
class AltitudeGains:
    Kp: float = 8.0
    Kd: float = 4.0


def classical_thrust(state, z_ref: float, zdot_ref: float,
                     P: AltitudeParams, G: AltitudeGains) -> float:
    """PD + gravity feed-forward thrust command [N]."""
    z, zdot = state
    u = P.m * P.g + G.Kp * (z_ref - z) + G.Kd * (zdot_ref - zdot)
    return clip_thrust(u, P)


def natural_freq(P: AltitudeParams, G: AltitudeGains) -> float:
    return float(np.sqrt(G.Kp / P.m))


def damping_ratio(P: AltitudeParams, G: AltitudeGains) -> float:
    return float(G.Kd / (2.0 * np.sqrt(G.Kp * P.m)))
