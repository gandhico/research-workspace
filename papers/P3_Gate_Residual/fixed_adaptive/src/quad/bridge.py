"""
MuJoCo simulation bridge.
Handles state extraction, control application (body-torque OR rotor-level),
and altitude stabilization hover support.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from quad.math_utils import quat_normalize, mujoco_quat_to_body
from quad.models import DroneParams


@dataclass
class SimState:
    """Snapshot of drone state from MuJoCo."""
    t: float
    pos: np.ndarray        # [x, y, z] world frame
    vel: np.ndarray        # [vx, vy, vz] world frame
    q: np.ndarray          # quaternion [w,x,y,z] body orientation
    omega: np.ndarray      # body angular velocity [wx, wy, wz]
    R_wb: np.ndarray       # rotation matrix world←body (3x3)


def get_state(mj_model, mj_data, params: DroneParams) -> SimState:
    """Extract drone state from MuJoCo data structures."""
    pa = params.qpos_adr
    va = params.qvel_adr

    pos   = np.array(mj_data.qpos[pa:pa+3], dtype=float)
    q_mj  = quat_normalize(np.array(mj_data.qpos[pa+3:pa+7], dtype=float))
    vel   = np.array(mj_data.qvel[va:va+3], dtype=float)
    omega = np.array(mj_data.qvel[va+3:va+6], dtype=float)

    q_body = mujoco_quat_to_body(q_mj)  # paper convention
    R_wb   = np.array(mj_data.xmat[params.body_id], dtype=float).reshape(3, 3)

    return SimState(t=float(mj_data.time), pos=pos, vel=vel,
                    q=q_body, omega=omega, R_wb=R_wb)


def compute_hover_force(state: SimState, params: DroneParams,
                        z_ref: float = 1.0,
                        kz: float = 6.0, kdz: float = 4.0,
                        kxy: float = 1.5, kdxy: float = 2.2,
                        xy_accel_max: float = 3.0) -> np.ndarray:
    """
    Compute world-frame force for altitude + lateral stabilization.
    Returns 3D force vector in world frame.
    This is the 'external hover support' layer — a practical MuJoCo aid
    that is NOT part of the attitude controller.
    """
    pos, vel = state.pos, state.vel
    body_z_world = state.R_wb[:, 2]
    tilt_cos = max(0.35, body_z_world[2])

    collective = params.total_mass * (
        params.gravity + kz * (z_ref - pos[2]) + kdz * (0.0 - vel[2])
    ) / tilt_cos
    collective = np.clip(collective, 0.0, 2.5 * params.total_mass * max(params.gravity, 1.0))

    force = collective * body_z_world
    a_xy  = -kxy * pos[:2] - kdxy * vel[:2]
    mag   = np.linalg.norm(a_xy)
    if mag > xy_accel_max:
        a_xy = a_xy * (xy_accel_max / mag)
    force[:2] += params.total_mass * a_xy
    return force


def apply_body_torque(mj_data, params: DroneParams,
                      tau_body: np.ndarray,
                      hover_force_world: np.ndarray) -> None:
    """
    Apply control via xfrc_applied (external force/torque injection).
    This is the legacy body-torque control path.
    tau_body is in body frame; it is rotated to world frame here.
    """
    mj_data.xfrc_applied[params.body_id, 0:3] = hover_force_world
    R_wb = np.array(mj_data.xmat[params.body_id], dtype=float).reshape(3, 3)
    mj_data.xfrc_applied[params.body_id, 3:6] = R_wb @ tau_body


def apply_rotor_commands(mj_model, mj_data, params: DroneParams,
                         u: np.ndarray) -> None:
    """
    Apply 4-motor commands for Skydio X2 (rotor-level control).
    u: array of 4 motor commands [u1,u2,u3,u4] in model units (N).
    Commands are clipped to actuator limits before application.
    """
    if params.actuator_mode != "rotor4":
        raise ValueError(f"apply_rotor_commands only valid for rotor4, got {params.actuator_mode}")

    import mujoco
    thrust_names = ["thrust1", "thrust2", "thrust3", "thrust4"]
    act_ids = np.array(
        [mujoco.mj_name2id(mj_model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in thrust_names],
        dtype=int,
    )
    u_clipped = np.clip(u, params.ctrl_min_vector(), params.ctrl_max_vector())
    mj_data.ctrl[act_ids] = u_clipped


def apply_cf2_wrench(mj_model, mj_data, params: DroneParams,
                     collective_N: float, tau_body: np.ndarray) -> None:
    """
    Apply control via CF2's virtual wrench actuators.
    collective_N: collective thrust in Newtons.
    tau_body: [τx, τy, τz] in Nm.
    """
    if params.actuator_mode != "wrench4":
        raise ValueError(f"apply_cf2_wrench only valid for wrench4, got {params.actuator_mode}")

    import mujoco
    act_names = ["body_thrust", "x_moment", "y_moment", "z_moment"]
    act_ids = np.array(
        [mujoco.mj_name2id(mj_model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in act_names],
        dtype=int,
    )
    ctrl_min = params.ctrl_min_vector()
    ctrl_max = params.ctrl_max_vector()
    mg = params.moment_gear  # [gx, gy, gz]

    cmd = np.array([
        collective_N,                                  # body_thrust (N)
        -tau_body[0] / max(mg[0], 1e-15),             # x_moment (sign from gear)
        -tau_body[1] / max(mg[1], 1e-15),             # y_moment
        -tau_body[2] / max(mg[2], 1e-15),             # z_moment
    ], dtype=float)
    mj_data.ctrl[act_ids] = np.clip(cmd, ctrl_min, ctrl_max)
