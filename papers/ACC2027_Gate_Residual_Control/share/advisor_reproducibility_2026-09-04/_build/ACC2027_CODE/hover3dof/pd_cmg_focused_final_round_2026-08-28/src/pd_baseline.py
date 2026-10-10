"""Offline-only 3DOF Hover PD mathematics.

No Quanser import, board access, timers, or hardware writes exist in this module.
Channel order is the physically verified [Front, Back, Left, Right].
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


K_LQR_FBLR = np.array([
    [-111.8034, 132.2876, 0.0, -41.4128, 36.2268, 0.0],
    [-111.8034, -132.2876, 0.0, -41.4128, -36.2268, 0.0],
    [111.8034, 0.0, -132.2876, 41.4128, 0.0, -36.2268],
    [111.8034, 0.0, 132.2876, 41.4128, 0.0, 36.2268],
], dtype=float)


@dataclass(frozen=True)
class VendorPlant:
    torque_thrust: float = 0.0036
    force_thrust: float = 0.1188
    arm_length: float = 7.75 * 0.0254
    moving_mass: float = 2.85
    motor_rotor_inertia: float = 1.91e-6
    bias_voltage: float = 2.0
    minimum_voltage: float = 0.0
    maximum_voltage: float = 24.0

    @property
    def inertia(self) -> np.ndarray:
        section = self.motor_rotor_inertia + (self.moving_mass / 4.0) * self.arm_length**2
        return np.array([4.0 * section, 2.0 * section, 2.0 * section])

    @property
    def motor_to_torque(self) -> np.ndarray:
        kt = self.torque_thrust
        kl = self.force_thrust * self.arm_length
        return np.array([
            [-kt, -kt, kt, kt],
            [kl, -kl, 0.0, 0.0],
            [0.0, 0.0, -kl, kl],
        ])


@dataclass(frozen=True)
class StabilityPriorityAllocation:
    """Result of the Hover-only pitch/roll-priority voltage allocation."""

    voltage_fblr: np.ndarray
    realized_torque_ypr: np.ndarray
    yaw_scale: float
    pitch_roll_scale: float
    common_mode_voltage: float
    motor_floor_voltage: float


def effective_pd_matrices(
    plant: VendorPlant = VendorPlant(),
    motor_gain: np.ndarray = K_LQR_FBLR,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Return axis Kp, Kd and the largest cross-axis coupling term."""
    transformed = plant.motor_to_torque @ np.asarray(motor_gain, dtype=float)
    kp = transformed[:, :3]
    kd = transformed[:, 3:]
    offdiag = np.r_[kp[~np.eye(3, dtype=bool)], kd[~np.eye(3, dtype=bool)]]
    return kp, kd, float(np.max(np.abs(offdiag)))


def pd_torque(
    setpoint_ypr: np.ndarray,
    angle_ypr: np.ndarray,
    rate_ypr: np.ndarray,
    plant: VendorPlant = VendorPlant(),
) -> np.ndarray:
    """MuJoCo-style axis PD: tau = Kp*(q_des-q) - Kd*qdot."""
    kp, kd, _ = effective_pd_matrices(plant)
    error = np.asarray(setpoint_ypr, dtype=float) - np.asarray(angle_ypr, dtype=float)
    rate = np.asarray(rate_ypr, dtype=float)
    return kp @ error - kd @ rate


def vendor_lqr_voltage(
    setpoint_ypr: np.ndarray,
    angle_ypr: np.ndarray,
    rate_ypr: np.ndarray,
    plant: VendorPlant = VendorPlant(),
    clip: bool = True,
) -> np.ndarray:
    """Exact current Python/vendor voltage law in verified F/B/L/R order."""
    error = np.r_[
        np.asarray(setpoint_ypr, dtype=float) - np.asarray(angle_ypr, dtype=float),
        -np.asarray(rate_ypr, dtype=float),
    ]
    voltage = K_LQR_FBLR @ error + plant.bias_voltage
    if clip:
        voltage = np.clip(voltage, plant.minimum_voltage, plant.maximum_voltage)
    return voltage


def realized_torque(voltage_fblr: np.ndarray, plant: VendorPlant = VendorPlant()) -> np.ndarray:
    return plant.motor_to_torque @ np.asarray(voltage_fblr, dtype=float)


def torque_to_motor_differential(
    torque_ypr: np.ndarray,
    plant: VendorPlant = VendorPlant(),
) -> np.ndarray:
    """Minimum-norm F/B/L/R voltage differential for a yaw/pitch/roll torque."""
    g = plant.motor_to_torque
    return g.T @ np.linalg.solve(g @ g.T, np.asarray(torque_ypr, dtype=float))


def pd_voltage_raw(
    setpoint_ypr: np.ndarray,
    angle_ypr: np.ndarray,
    rate_ypr: np.ndarray,
    plant: VendorPlant = VendorPlant(),
) -> np.ndarray:
    """Explicit axis-PD -> minimum-norm mixer -> common bias, before clipping."""
    return plant.bias_voltage + torque_to_motor_differential(
        pd_torque(setpoint_ypr, angle_ypr, rate_ypr, plant), plant
    )


def residual_torque_limits_from_motor_volts(
    motor_delta_limit: float,
    plant: VendorPlant = VendorPlant(),
) -> np.ndarray:
    """Axis CMG limits whose beta-scaled extremes map to motor delta extremes.

    Returns yaw/pitch/roll limits before beta. A pure yaw residual uses all four
    motors with signs [-,-,+,+]; pitch and roll use their opposing motor pair.
    """
    v = float(motor_delta_limit)
    return np.array([
        4.0 * plant.torque_thrust * v,
        2.0 * plant.arm_length * plant.force_thrust * v,
        2.0 * plant.arm_length * plant.force_thrust * v,
    ])


def full_axis_torque_limits(plant: VendorPlant = VendorPlant()) -> np.ndarray:
    """Maximum pure-axis torque spans available inside the 0..Vmax motor box."""
    vmax = plant.maximum_voltage - plant.minimum_voltage
    return np.array([
        2.0 * plant.torque_thrust * vmax,
        plant.arm_length * plant.force_thrust * vmax,
        plant.arm_length * plant.force_thrust * vmax,
    ])


def limit_and_slew_motor_residual(
    requested_fblr: np.ndarray,
    previous_fblr: np.ndarray,
    magnitude_limit: float,
    slew_volts_per_second: float,
    dt: float,
) -> np.ndarray:
    """Apply the authority and slew bounds to the residual actually inserted."""
    requested = np.clip(np.asarray(requested_fblr, dtype=float), -magnitude_limit, magnitude_limit)
    previous = np.asarray(previous_fblr, dtype=float)
    step = max(float(slew_volts_per_second), 0.0) * max(float(dt), 0.0)
    return previous + np.clip(requested - previous, -step, step)


def allocate_exact_torque(
    torque_ypr: np.ndarray,
    plant: VendorPlant = VendorPlant(),
) -> np.ndarray:
    """Allocate a feasible 3-axis torque with a bounded common motor voltage.

    The four-actuator map has one common-mode null direction. The minimum-norm
    differential solution is shifted toward the vendor bias while preserving the
    requested torque. Infeasible requests raise instead of being silently clipped.
    """
    torque = np.asarray(torque_ypr, dtype=float)
    g = plant.motor_to_torque
    differential = torque_to_motor_differential(torque, plant)
    lower_common = float(np.max(plant.minimum_voltage - differential))
    upper_common = float(np.min(plant.maximum_voltage - differential))
    if lower_common > upper_common + 1e-12:
        raise ValueError(
            f"Torque is infeasible within voltage bounds: common-mode interval "
            f"[{lower_common:.6g}, {upper_common:.6g}] is empty"
        )
    common = float(np.clip(plant.bias_voltage, lower_common, upper_common))
    return differential + common


def allocate_stability_priority_torque(
    torque_ypr: np.ndarray,
    plant: VendorPlant = VendorPlant(),
    motor_floor_voltage: float = 2.0,
) -> StabilityPriorityAllocation:
    """Allocate torque while keeping motors active and preserving pitch/roll.

    The common motor direction is in the ideal generalized-torque nullspace.
    A voltage floor therefore can be imposed by shifting all four commands. If
    the requested differential span is too large for ``[floor, Vmax]``, the
    pitch/roll differential is retained first (uniformly scaled only when it is
    itself infeasible), and yaw is reduced to the largest feasible value.

    This is an explicitly Hover-only actuator allocation/safety layer. It does
    not change the quaternion PD, CMG dynamics, PES law, or requested torque.
    """
    torque = np.asarray(torque_ypr, dtype=float)
    floor = float(motor_floor_voltage)
    if not plant.minimum_voltage <= floor < plant.maximum_voltage:
        raise ValueError("motor_floor_voltage must be inside [minimum, maximum)")
    available_span = plant.maximum_voltage - floor

    pitch_roll_torque = np.array([0.0, torque[1], torque[2]])
    pitch_roll_diff = torque_to_motor_differential(pitch_roll_torque, plant)
    pitch_roll_span = float(np.ptp(pitch_roll_diff))
    pitch_roll_scale = min(1.0, available_span / pitch_roll_span) if pitch_roll_span > 1e-12 else 1.0
    pitch_roll_diff = pitch_roll_scale * pitch_roll_diff

    yaw_diff = torque_to_motor_differential(np.array([torque[0], 0.0, 0.0]), plant)

    def feasible(yaw_scale: float) -> bool:
        return float(np.ptp(pitch_roll_diff + yaw_scale * yaw_diff)) <= available_span + 1e-12

    if feasible(1.0):
        yaw_scale = 1.0
    else:
        lower, upper = 0.0, 1.0
        for _ in range(60):
            midpoint = 0.5 * (lower + upper)
            if feasible(midpoint):
                lower = midpoint
            else:
                upper = midpoint
        yaw_scale = lower

    differential = pitch_roll_diff + yaw_scale * yaw_diff
    lower_common = floor - float(np.min(differential))
    upper_common = plant.maximum_voltage - float(np.max(differential))
    if lower_common > upper_common + 1e-9:
        raise RuntimeError("Internal allocator error: no feasible common-mode interval")
    common = float(np.clip(plant.bias_voltage, lower_common, upper_common))
    voltage = np.clip(
        differential + common,
        floor,
        plant.maximum_voltage,
    )
    return StabilityPriorityAllocation(
        voltage_fblr=voltage,
        realized_torque_ypr=realized_torque(voltage, plant),
        yaw_scale=float(yaw_scale),
        pitch_roll_scale=float(pitch_roll_scale),
        common_mode_voltage=common,
        motor_floor_voltage=floor,
    )


def equivalent_second_order(plant: VendorPlant = VendorPlant()) -> tuple[np.ndarray, np.ndarray]:
    kp, kd, _ = effective_pd_matrices(plant)
    kp_diag = np.diag(kp)
    kd_diag = np.diag(kd)
    inertia = plant.inertia
    natural_frequency = np.sqrt(kp_diag / inertia)
    damping_ratio = kd_diag / (2.0 * np.sqrt(inertia * kp_diag))
    return natural_frequency, damping_ratio


def mujoco_pd_parameters_ypr(
    plant: VendorPlant = VendorPlant(),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Canonical drone.py quaternion-PD parameters reordered to yaw/pitch/roll.

    drone.py uses body xyz = roll/pitch/yaw, wn=[4,4,3.5],
    kq=2*J*wn^2, kw=2*.95*wn*J, and the model/inertia torque policy
    J*[12,12,10]. The Hover controller uses ypr channel order, hence reversal.
    """
    inertia_ypr = plant.inertia
    inertia_xyz = inertia_ypr[[2, 1, 0]]
    wn_xyz = np.array([4.0, 4.0, 3.5])
    kq_xyz = 2.0 * inertia_xyz * wn_xyz * wn_xyz
    kw_xyz = 2.0 * 0.95 * wn_xyz * inertia_xyz
    limits_xyz = inertia_xyz * np.array([12.0, 12.0, 10.0])
    return kq_xyz[[2, 1, 0]], kw_xyz[[2, 1, 0]], limits_xyz[[2, 1, 0]]


def euler_rates_ypr_to_body_omega_ypr(
    angle_ypr: np.ndarray,
    euler_rate_ypr: np.ndarray,
) -> np.ndarray:
    """Convert ZYX yaw/pitch/roll rates to body angular velocity, ypr order."""
    yaw, pitch, roll = np.asarray(angle_ypr, dtype=float)
    yaw_rate, pitch_rate, roll_rate = np.asarray(euler_rate_ypr, dtype=float)
    del yaw  # ZYX body-rate map does not depend explicitly on yaw.
    omega_roll = roll_rate - yaw_rate * np.sin(pitch)
    omega_pitch = pitch_rate * np.cos(roll) + yaw_rate * np.sin(roll) * np.cos(pitch)
    omega_yaw = -pitch_rate * np.sin(roll) + yaw_rate * np.cos(roll) * np.cos(pitch)
    return np.array([omega_yaw, omega_pitch, omega_roll])


def mujoco_quaternion_pd_torque_ypr(
    quaternion_error_vector_ypr: np.ndarray,
    body_omega_ypr: np.ndarray,
    plant: VendorPlant = VendorPlant(),
) -> np.ndarray:
    """Physical Hover torque equivalent of drone.py's quaternion PD law.

    The MuJoCo model/controller torque coordinate has the opposite sign from the
    verified Hover motor-torque coordinate. After that declared coordinate
    transform, -kq*eq-kw*omega becomes +kq*eq-kw*omega in Hover physical ypr.
    """
    kq, kw, limits = mujoco_pd_parameters_ypr(plant)
    torque = kq * np.asarray(quaternion_error_vector_ypr, dtype=float) - kw * np.asarray(body_omega_ypr, dtype=float)
    return np.clip(torque, -limits, limits)


def mujoco_pes_target_ypr(
    quaternion_error_vector_ypr: np.ndarray,
    body_omega_ypr: np.ndarray,
    k_error: float = 8.0,
    k_rate: float = 0.0,
) -> np.ndarray:
    """Physical-Hover form of drone.py's clipped PES teaching signal.

    In drone.py coordinates the target is ``clip(-ke*eq-kw*omega,-1,1)``.
    Applying the same declared sign/order transform as the physical torque gives
    ``clip(+ke*eq_ypr-kw*omega_ypr,-1,1)``.
    """
    target = (
        float(k_error) * np.asarray(quaternion_error_vector_ypr, dtype=float)
        - float(k_rate) * np.asarray(body_omega_ypr, dtype=float)
    )
    return np.clip(target, -1.0, 1.0)
