import time
import numpy as np
import mujoco
import mujoco.viewer
import matplotlib.pyplot as plt


# ============================================================
# EDIT THIS PATH
# ============================================================
XML_PATH = r"C:\GHYN\mujoco_menagerie\skydio_x2\scene.xml"
#XML_PATH = r"C:\GHYN\mujoco_menagerie\skydio_x2\scene.xml"
XML_PATH = r"C:\mujoco_menagerie\skydio_x2\scene.xml"

# ============================================================
# Simulation / controller settings
# ============================================================
SIM_TIME = 15.0

# Paper gains
P_Q = 20.0
P_W = 4.0
TAU_LIMIT = 4.0  # Nm, paper-style torque bound

# Sine reference
# Paper says 0.5 rad amplitude, 1 rad/s, with phase shifts on y and z.
REF_AMP = np.array([0.5, 0.5, 0.5], dtype=float)
REF_FREQ = 1.0
REF_PHASE = np.array([0.0, np.pi / 2.0, np.pi], dtype=float)

# Practical MuJoCo aid:
# not part of the paper; this approximately compensates lift loss during tilt.
USE_COLLECTIVE_COMPENSATION = True


# ============================================================
# Quaternion utilities
# Convention: q = [w, x, y, z]
# ============================================================
def q_mul(p, q):
    p0, p1, p2, p3 = p
    q0, q1, q2, q3 = q
    return np.array([
        p0*q0 - p1*q1 - p2*q2 - p3*q3,
        p0*q1 + p1*q0 + p2*q3 - p3*q2,
        p0*q2 - p1*q3 + p2*q0 + p3*q1,
        p0*q3 + p1*q2 - p2*q1 + p3*q0
    ], dtype=float)


def q_conj(q):
    return np.array([q[0], -q[1], -q[2], -q[3]], dtype=float)


def q_normalize(q):
    n = np.linalg.norm(q)
    if n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    return q / n


def euler_to_quat(phi, theta, psi):
    cphi, sphi = np.cos(phi/2), np.sin(phi/2)
    cth, sth = np.cos(theta/2), np.sin(theta/2)
    cpsi, spsi = np.cos(psi/2), np.sin(psi/2)

    q = np.array([
        cphi*cth*cpsi + sphi*sth*spsi,
        sphi*cth*cpsi - cphi*sth*spsi,
        cphi*sth*cpsi + sphi*cth*spsi,
        cphi*cth*spsi - sphi*sth*cpsi
    ], dtype=float)
    return q_normalize(q)


def quat_to_euler(q):
    q = q_normalize(q)
    q0, q1, q2, q3 = q

    phi = np.arctan2(
        2*(q0*q1 + q2*q3),
        q0*q0 - q1*q1 - q2*q2 + q3*q3
    )

    s = 2*(q0*q2 - q3*q1)
    s = np.clip(s, -1.0, 1.0)
    theta = np.arcsin(s)

    psi = np.arctan2(
        2*(q0*q3 + q1*q2),
        q0*q0 + q1*q1 - q2*q2 - q3*q3
    )

    return np.array([phi, theta, psi], dtype=float)


def quat_to_rotmat(q):
    q = q_normalize(q)
    q0, q1, q2, q3 = q
    return np.array([
        [1 - 2*(q2*q2 + q3*q3),     2*(q1*q2 - q0*q3),     2*(q1*q3 + q0*q2)],
        [    2*(q1*q2 + q0*q3), 1 - 2*(q1*q1 + q3*q3),     2*(q2*q3 - q0*q1)],
        [    2*(q1*q3 - q0*q2),     2*(q2*q3 + q0*q1), 1 - 2*(q1*q1 + q2*q2)],
    ], dtype=float)


# ============================================================
# Reference
# ============================================================
def reference_euler(t):
    return REF_AMP * np.sin(REF_FREQ * t + REF_PHASE)


def reference_quat(t):
    phi_d, theta_d, psi_d = reference_euler(t)
    return euler_to_quat(phi_d, theta_d, psi_d)


# ============================================================
# Sensor helper
# ============================================================
def get_sensor_data(model, data, sensor_name):
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, sensor_name)
    if sid < 0:
        raise ValueError(f"Sensor '{sensor_name}' not found.")
    adr = model.sensor_adr[sid]
    dim = model.sensor_dim[sid]
    return np.array(data.sensordata[adr:adr+dim], dtype=float)


# ============================================================
# Load model
# ============================================================
model = mujoco.MjModel.from_xml_path(XML_PATH)
data = mujoco.MjData(model)

# Actuator/site names from the Menagerie model
actuator_names = ["thrust1", "thrust2", "thrust3", "thrust4"]
site_names = ["thrust1", "thrust2", "thrust3", "thrust4"]

act_ids = np.array(
    [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in actuator_names],
    dtype=int
)
site_ids = np.array(
    [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, n) for n in site_names],
    dtype=int
)

if np.any(act_ids < 0):
    raise ValueError("One or more actuators not found.")
if np.any(site_ids < 0):
    raise ValueError("One or more thrust sites not found.")

# Local rotor positions in the body frame
site_pos = model.site_pos[site_ids].copy()      # shape (4, 3)
x = site_pos[:, 0]
y = site_pos[:, 1]

# Yaw torque coefficient comes from the 6th gear component
yaw_coeff = model.actuator_gear[act_ids, 5].copy()

# Control ranges from the model
ctrl_min = model.actuator_ctrlrange[act_ids, 0].copy()
ctrl_max = model.actuator_ctrlrange[act_ids, 1].copy()

# Mixer:
# [Fz, tau_x, tau_y, tau_z]^T = B @ u
# where u = [u1, u2, u3, u4]^T are motor commands
#
# For a force F=[0,0,ui] at r=[x,y,z], moment is r x F = [y*ui, -x*ui, 0].
# Yaw moment is given by the actuator gear coefficient.
B = np.vstack([
    np.ones(4),   # collective thrust
    y,            # roll torque
    -x,           # pitch torque
    yaw_coeff     # yaw torque
])
B_inv = np.linalg.inv(B)

# Hover thrust from total mass
total_mass = float(np.sum(model.body_mass))
g = float(abs(model.opt.gravity[2]))
hover_per_motor = total_mass * g / 4.0
hover_total = 4.0 * hover_per_motor

print("Total mass [kg]:", total_mass)
print("Hover thrust per motor:", hover_per_motor)
print("Yaw coeffs:", yaw_coeff)
print("Mixer B:\n", B)

# Initial condition
data.qpos[:] = 0.0
data.qpos[0:3] = np.array([0.0, 0.0, 1.0])      # x,y,z
data.qpos[3:7] = np.array([1.0, 0.0, 0.0, 0.0]) # qw,qx,qy,qz
data.qvel[:] = 0.0
data.ctrl[:] = hover_per_motor
mujoco.mj_forward(model, data)

# Logs
t_log = []
eul_ref_log = []
eul_meas_log = []
tau_cmd_log = []
u_log = []

# ============================================================
# Simulation loop
# ============================================================
with mujoco.viewer.launch_passive(model, data) as viewer:
    while viewer.is_running() and data.time < SIM_TIME:
        step_start = time.time()
        t = float(data.time)

        # State
        q = q_normalize(np.array(data.qpos[3:7], dtype=float))
        w = get_sensor_data(model, data, "body_gyro")  # body angular rate [wx, wy, wz]

        # Reference
        q_ref = reference_quat(t)
        eul_ref = reference_euler(t)

        # Quaternion error: q_err = q_ref ⊗ q_meas*
        q_err = q_mul(q_ref, q_conj(q))

        # Shortest rotation
        if q_err[0] < 0.0:
            q_err = -q_err

        axis_err = q_err[1:]

        # Paper-style torque command
        tau_cmd = -P_Q * axis_err - P_W * w
        tau_cmd = np.clip(tau_cmd, -TAU_LIMIT, TAU_LIMIT)

        # Collective command
        # Optional practical compensation to reduce altitude loss during tilt.
        if USE_COLLECTIVE_COMPENSATION:
            R = quat_to_rotmat(q)
            c33 = max(0.35, R[2, 2])  # body-z vertical component
            collective = hover_total / c33
        else:
            collective = hover_total

        # Motor mixing
        wrench = np.array([collective, tau_cmd[0], tau_cmd[1], tau_cmd[2]], dtype=float)
        u = B_inv @ wrench
        u = np.clip(u, ctrl_min, ctrl_max)

        # Apply control
        data.ctrl[act_ids] = u

        # Step physics
        mujoco.mj_step(model, data)
        viewer.sync()

        # Log
        t_log.append(t)
        eul_ref_log.append(eul_ref)
        eul_meas_log.append(quat_to_euler(q))
        tau_cmd_log.append(tau_cmd.copy())
        u_log.append(u.copy())

        # Real-time pacing
        dt = model.opt.timestep - (time.time() - step_start)
        if dt > 0:
            time.sleep(dt)

# ============================================================
# Plot results
# ============================================================
t_log = np.array(t_log)
eul_ref_log = np.array(eul_ref_log)
eul_meas_log = np.array(eul_meas_log)
tau_cmd_log = np.array(tau_cmd_log)
u_log = np.array(u_log)

labels = [r'$\phi$', r'$\theta$', r'$\psi$']

plt.figure(figsize=(10, 8))
for i in range(3):
    plt.subplot(3, 1, i+1)
    plt.plot(t_log, eul_ref_log[:, i], '--', label='reference')
    plt.plot(t_log, eul_meas_log[:, i], '-', label='measured')
    plt.ylabel(f'{labels[i]} [rad]')
    plt.grid(True)
    if i == 0:
        plt.legend()
plt.xlabel('Time [s]')
plt.suptitle('Skydio X2 in MuJoCo: quaternion attitude tracking')
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 8))
tau_names = [r'$\tau_x$', r'$\tau_y$', r'$\tau_z$']
for i in range(3):
    plt.subplot(3, 1, i+1)
    plt.plot(t_log, tau_cmd_log[:, i])
    plt.axhline(TAU_LIMIT, linestyle='--')
    plt.axhline(-TAU_LIMIT, linestyle='--')
    plt.ylabel(f'{tau_names[i]} [Nm]')
    plt.grid(True)
plt.xlabel('Time [s]')
plt.suptitle('Body torque command')
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 8))
for i in range(4):
    plt.subplot(4, 1, i+1)
    plt.plot(t_log, u_log[:, i])
    plt.axhline(ctrl_min[i], linestyle='--')
    plt.axhline(ctrl_max[i], linestyle='--')
    plt.ylabel(f'u{i+1}')
    plt.grid(True)
plt.xlabel('Time [s]')
plt.suptitle('Motor commands')
plt.tight_layout()
plt.show()