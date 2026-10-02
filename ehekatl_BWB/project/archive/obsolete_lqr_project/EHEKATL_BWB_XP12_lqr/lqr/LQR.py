"""
Minimal EHEKATL BWB LQR controller for X-Plane 12.

This module is intentionally dependency-light: it uses fixed gains from the
validated LTI design and only the Python standard library. Internal units are
SI units and radians. X-Plane attitude inputs are expected in degrees.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


DEG_TO_RAD = math.pi / 180.0
RAD_TO_DEG = 180.0 / math.pi

K_LON = (1.58255059, -2.53350077, -1.84584039, -22.06327663)
K_LAT = (0.11366923, 2.95176288, -0.16714788, 2.67770629)


def deg2rad(value: float) -> float:
    return value * DEG_TO_RAD


def rad2deg(value: float) -> float:
    return value * RAD_TO_DEG


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def wrapped_angle_error_deg(value_deg: float, setpoint_deg: float) -> float:
    """Return value - setpoint wrapped to [-180, 180) degrees."""
    return (value_deg - setpoint_deg + 180.0) % 360.0 - 180.0


def dot(gain: tuple[float, ...], state: tuple[float, ...]) -> float:
    return sum(k * x for k, x in zip(gain, state))


@dataclass(frozen=True)
class LQRConfig:
    pitch_sp_deg: float = 2.0
    roll_sp_deg: float = 0.0
    actuator_limit_deg: float = 25.0
    clip: float = 0.25
    mode: str = "attitude"


@dataclass(frozen=True)
class StateSample:
    pitch_deg: float
    roll_deg: float
    heading_deg: float
    pitch_rate_deg_s: float = 0.0
    roll_rate_deg_s: float = 0.0
    yaw_rate_deg_s: float = 0.0
    u_perturb_m_s: float = 0.0
    w_perturb_m_s: float = 0.0
    v_perturb_m_s: float = 0.0


@dataclass(frozen=True)
class LQRCommand:
    delta_e_raw_rad: float
    delta_a_raw_rad: float
    delta_e_limited_rad: float
    delta_a_limited_rad: float
    elevator_stick: float
    aileron_stick: float
    x_lon: tuple[float, float, float, float]
    x_lat: tuple[float, float, float, float]

    @property
    def delta_e_raw_deg(self) -> float:
        return rad2deg(self.delta_e_raw_rad)

    @property
    def delta_a_raw_deg(self) -> float:
        return rad2deg(self.delta_a_raw_rad)

    @property
    def delta_e_limited_deg(self) -> float:
        return rad2deg(self.delta_e_limited_rad)

    @property
    def delta_a_limited_deg(self) -> float:
        return rad2deg(self.delta_a_limited_rad)


class EHEKATLLQR:
    """Fixed-gain longitudinal/lateral LQR controller."""

    def __init__(self, config: LQRConfig):
        if config.mode not in {"attitude", "full"}:
            raise ValueError("mode must be 'attitude' or 'full'")
        if config.clip < 0.0 or config.clip > 1.0:
            raise ValueError("clip must be in [0, 1], where 0 disables extra clipping")
        self.config = config
        self.actuator_limit_rad = deg2rad(config.actuator_limit_deg)

    def states(self, sample: StateSample) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
        theta = deg2rad(wrapped_angle_error_deg(sample.pitch_deg, self.config.pitch_sp_deg))
        phi = deg2rad(wrapped_angle_error_deg(sample.roll_deg, self.config.roll_sp_deg))
        q = deg2rad(sample.pitch_rate_deg_s)
        p = deg2rad(sample.roll_rate_deg_s)
        r = deg2rad(sample.yaw_rate_deg_s)

        if self.config.mode == "full":
            u = sample.u_perturb_m_s
            w = sample.w_perturb_m_s
            v = sample.v_perturb_m_s
        else:
            u = 0.0
            w = 0.0
            v = 0.0

        x_lon = (u, w, q, theta)
        x_lat = (v, p, r, phi)
        return x_lon, x_lat

    def command(self, sample: StateSample) -> LQRCommand:
        x_lon, x_lat = self.states(sample)
        delta_e_raw = -dot(K_LON, x_lon)
        delta_a_raw = -dot(K_LAT, x_lat)

        delta_e_limited = clamp(delta_e_raw, -self.actuator_limit_rad, self.actuator_limit_rad)
        delta_a_limited = clamp(delta_a_raw, -self.actuator_limit_rad, self.actuator_limit_rad)

        elevator_stick = delta_e_limited / self.actuator_limit_rad
        aileron_stick = delta_a_limited / self.actuator_limit_rad

        if self.config.clip > 0.0:
            elevator_stick = clamp(elevator_stick, -self.config.clip, self.config.clip)
            aileron_stick = clamp(aileron_stick, -self.config.clip, self.config.clip)
            delta_e_limited = elevator_stick * self.actuator_limit_rad
            delta_a_limited = aileron_stick * self.actuator_limit_rad

        return LQRCommand(
            delta_e_raw_rad=delta_e_raw,
            delta_a_raw_rad=delta_a_raw,
            delta_e_limited_rad=delta_e_limited,
            delta_a_limited_rad=delta_a_limited,
            elevator_stick=elevator_stick,
            aileron_stick=aileron_stick,
            x_lon=x_lon,
            x_lat=x_lat,
        )
