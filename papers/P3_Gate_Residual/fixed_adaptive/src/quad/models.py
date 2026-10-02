"""
Drone parameter extraction from MuJoCo XML models.
Provides DroneParams dataclass with mass, inertia, mixer matrix, and
actuator limits for both Skydio X2 (4-motor) and Crazyflie 2 (virtual wrench).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# Path resolution: models live in models/mujoco_menagerie relative to project root.
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[3]  # v2_clean/../.. = 01_HyperLIF_Gate_Residual
_MENAGERIE = _PROJECT_ROOT / "models" / "mujoco_menagerie"

KNOWN_QUADS = {
    "skydio_x2":           _MENAGERIE / "skydio_x2" / "scene.xml",
    "bitcraze_crazyflie_2": _MENAGERIE / "bitcraze_crazyflie_2" / "scene.xml",
}


@dataclass
class MotorActuator:
    name: str
    ctrl_min: float
    ctrl_max: float
    hover_cmd: float  # nominal hover command value


@dataclass
class DroneParams:
    """Physical and actuator parameters for a quadrotor model."""
    name: str
    xml_path: Path

    total_mass: float          # kg
    gravity: float             # m/s²
    body_inertia: np.ndarray   # [Ixx, Iyy, Izz] kg·m²
    body_id: int
    free_joint_id: int
    qpos_adr: int
    qvel_adr: int

    # Actuator interface: "rotor4" for 4-motor quads, "wrench4" for body-torque quads
    actuator_mode: str         # "rotor4" | "wrench4"
    actuators: list[MotorActuator] = field(default_factory=list)

    # Rotor-level mixer matrix B: [T, τx, τy, τz] = B @ [u1,u2,u3,u4]
    # Only populated for actuator_mode == "rotor4"
    mixer_B: np.ndarray | None = None
    mixer_B_inv: np.ndarray | None = None

    # Gain presets (computed from inertia and desired bandwidth)
    kq: np.ndarray | None = None       # attitude proportional gains
    kw: np.ndarray | None = None       # angular-rate damping gains
    tau_limit: np.ndarray | None = None  # body torque limits [Nm]

    # CF2-specific: gear scaling for virtual torque actuators
    moment_gear: np.ndarray | None = None  # [gx, gy, gz] Nm/unit

    def hover_cmd_vector(self) -> np.ndarray:
        return np.array([a.hover_cmd for a in self.actuators], dtype=float)

    def ctrl_min_vector(self) -> np.ndarray:
        return np.array([a.ctrl_min for a in self.actuators], dtype=float)

    def ctrl_max_vector(self) -> np.ndarray:
        return np.array([a.ctrl_max for a in self.actuators], dtype=float)


def load_drone(quad_name: str) -> DroneParams:
    """Load and parse a quadrotor model, returning populated DroneParams."""
    import mujoco

    if quad_name not in KNOWN_QUADS:
        raise ValueError(f"Unknown quad '{quad_name}'. Known: {sorted(KNOWN_QUADS)}")

    xml_path = KNOWN_QUADS[quad_name]
    if not xml_path.exists():
        raise FileNotFoundError(f"MuJoCo XML not found: {xml_path}")

    m = mujoco.MjModel.from_xml_path(str(xml_path))

    # Find free joint
    free_jid = -1
    for j in range(m.njnt):
        if m.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
            free_jid = j
            break
    if free_jid < 0:
        raise RuntimeError("No freejoint found in model.")

    body_id  = int(m.jnt_bodyid[free_jid])
    qpos_adr = int(m.jnt_qposadr[free_jid])
    qvel_adr = int(m.jnt_dofadr[free_jid])

    total_mass = float(np.sum(m.body_mass))
    gravity    = float(abs(m.opt.gravity[2]))
    body_inert = np.array(m.body_inertia[body_id], dtype=float)

    # Build actuator list and detect interface type
    n_act = m.nu
    actuator_names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or f"act{i}"
                      for i in range(n_act)]

    # --- Skydio X2: 4 rotor motors with physical sites ---
    if quad_name == "skydio_x2":
        thrust_names = ["thrust1", "thrust2", "thrust3", "thrust4"]
        act_ids = np.array(
            [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in thrust_names],
            dtype=int,
        )
        site_ids = np.array(
            [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, n) for n in thrust_names],
            dtype=int,
        )
        if np.any(act_ids < 0) or np.any(site_ids < 0):
            raise RuntimeError("Skydio X2 thrust actuators/sites not found.")

        site_pos  = m.site_pos[site_ids].copy()   # (4, 3) rotor positions [m]
        x_pos = site_pos[:, 0]
        y_pos = site_pos[:, 1]
        yaw_k = m.actuator_gear[act_ids, 5].copy()  # yaw torque coefficient

        ctrl_min = m.actuator_ctrlrange[act_ids, 0].copy()
        ctrl_max = m.actuator_ctrlrange[act_ids, 1].copy()

        hover_total   = total_mass * gravity
        hover_per_mot = hover_total / 4.0

        actuators = [
            MotorActuator(name=thrust_names[i],
                          ctrl_min=float(ctrl_min[i]),
                          ctrl_max=float(ctrl_max[i]),
                          hover_cmd=hover_per_mot)
            for i in range(4)
        ]

        # Mixer B: [T, τx, τy, τz] = B @ u
        # Force F_i = [0,0,u_i] at r_i = [x_i, y_i, z_i]
        # Moment: r_i × F_i = [y_i*u_i, -x_i*u_i, 0]  + yaw term kappa_i*u_i in z
        B = np.vstack([
            np.ones(4),   # collective thrust
            y_pos,        # roll torque
            -x_pos,       # pitch torque
            yaw_k,        # yaw torque (gear-defined reaction torque)
        ])
        B_inv = np.linalg.inv(B)

        kq, kw, tau_lim = _compute_gains(body_inert)

        return DroneParams(
            name=quad_name,
            xml_path=xml_path,
            total_mass=total_mass,
            gravity=gravity,
            body_inertia=body_inert,
            body_id=body_id,
            free_joint_id=free_jid,
            qpos_adr=qpos_adr,
            qvel_adr=qvel_adr,
            actuator_mode="rotor4",
            actuators=actuators,
            mixer_B=B,
            mixer_B_inv=B_inv,
            kq=kq, kw=kw, tau_limit=tau_lim,
        )

    # --- Crazyflie 2: virtual wrench actuators ---
    elif quad_name == "bitcraze_crazyflie_2":
        wrench_names = ["body_thrust", "x_moment", "y_moment", "z_moment"]
        act_ids = np.array(
            [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in wrench_names],
            dtype=int,
        )
        if np.any(act_ids < 0):
            raise RuntimeError("CF2 virtual wrench actuators not found.")

        ctrl_min = m.actuator_ctrlrange[act_ids, 0].copy()
        ctrl_max = m.actuator_ctrlrange[act_ids, 1].copy()

        hover_thrust = total_mass * gravity
        gear_z  = abs(float(m.actuator_gear[act_ids[0], 2]))  # thrust gear (≈1)
        gear_mx = abs(float(m.actuator_gear[act_ids[1], 3]))  # x-moment gear
        gear_my = abs(float(m.actuator_gear[act_ids[2], 4]))  # y-moment gear
        gear_mz = abs(float(m.actuator_gear[act_ids[3], 5]))  # z-moment gear
        moment_gear = np.array([gear_mx, gear_my, gear_mz], dtype=float)

        hover_cmd_thrust = hover_thrust / max(gear_z, 1e-12)

        actuators = [
            MotorActuator("body_thrust", float(ctrl_min[0]), float(ctrl_max[0]),
                          hover_cmd=np.clip(hover_cmd_thrust, ctrl_min[0], ctrl_max[0])),
            MotorActuator("x_moment", float(ctrl_min[1]), float(ctrl_max[1]), hover_cmd=0.0),
            MotorActuator("y_moment", float(ctrl_min[2]), float(ctrl_max[2]), hover_cmd=0.0),
            MotorActuator("z_moment", float(ctrl_min[3]), float(ctrl_max[3]), hover_cmd=0.0),
        ]

        kq, kw, tau_lim = _compute_gains(body_inert)

        return DroneParams(
            name=quad_name,
            xml_path=xml_path,
            total_mass=total_mass,
            gravity=gravity,
            body_inertia=body_inert,
            body_id=body_id,
            free_joint_id=free_jid,
            qpos_adr=qpos_adr,
            qvel_adr=qvel_adr,
            actuator_mode="wrench4",
            actuators=actuators,
            moment_gear=moment_gear,
            kq=kq, kw=kw, tau_limit=tau_lim,
        )

    raise ValueError(f"No parser implemented for: {quad_name}")


def _compute_gains(inertia: np.ndarray,
                   wn: np.ndarray | None = None,
                   zeta: np.ndarray | None = None,
                   alpha_max: np.ndarray | None = None
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute kq, kw, tau_limit from inertia and desired closed-loop bandwidth.
    Using wn = natural frequency, zeta = damping ratio.
    """
    if wn is None:
        wn = np.array([4.0, 4.0, 3.5], dtype=float)
    if zeta is None:
        zeta = np.array([0.95, 0.95, 0.95], dtype=float)
    if alpha_max is None:
        alpha_max = np.array([12.0, 12.0, 10.0], dtype=float)

    kq = 2.0 * inertia * (wn ** 2)
    kw = 2.0 * zeta * wn * inertia
    tau_limit = np.maximum(inertia * alpha_max, np.array([1e-6, 1e-6, 1e-6]))
    return kq, kw, tau_limit
