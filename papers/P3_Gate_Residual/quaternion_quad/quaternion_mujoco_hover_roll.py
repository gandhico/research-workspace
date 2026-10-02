import time
import numpy as np
import mujoco
import mujoco.viewer
import matplotlib.pyplot as plt

# ============================================================
# USER SETTINGS
# ============================================================
XML_PATH = r"C:\mujoco_menagerie\skydio_x2\scene.xml"

SIM_TIME = 20.0 
USE_VIEWER = True

# Reference:
#   "roll"  -> roll oscillation while hovering
#   "full3" -> 3-axis paper-style sine test
REFERENCE_MODE = "full3"

# Gravity / hover
ZERO_GRAVITY = False
Z_REF = 1.0                     # desired hover height [m]
THRUST_SIGN = +1.0             # if the drone goes DOWN hard, change to -1.0

# Keep it visually near hover in x-y
USE_XY_TETHER = True

# Gain mode:
#   "scaled" -> recommended first
#   "paper"  -> paper values Pq=20, Pw=4 with torque saturation
GAIN_MODE = "paper"

# Attitude tuning for scaled mode
WN = np.array([4.0, 4.0, 3.5], dtype=float) 
ZETA = np.array([0.95, 0.95, 0.95], dtype=float) 
ALPHA_MAX = np.array([12.0, 12.0, 10.0], dtype=float)  # rad/s^2

# Altitude / hover support tuning
KZ_ACC = 6.0                  # vertical proportional accel gain [m/s^2 per m]
DZ_ACC = 4.0                  # vertical damping accel gain [m/s^2 per (m/s)]
MAX_COLLECTIVE_FACTOR = 2.5   # cap on collective wrt mg
MIN_TILT_COS = 0.35           # prevent huge thrust when too tilted

# Weak XY tether for visual hover
KXY_ACC = 1.5                 # horizontal spring accel gain [m/s^2 per m]
DXY_ACC = 2.2                 # horizontal damping accel gain [m/s^2 per (m/s)]
MAX_XY_ACC = 3.0              # horizontal accel cap

# ============================================================
# QUATERNION UTILITIES
# Convention here follows the paper:
# q = [q0, q1, q2, q3] = [scalar, vector]
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
    cth,  sth  = np.cos(theta/2), np.sin(theta/2)
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

def quat_angle_error(q_err):
    q_err = q_normalize(q_err)
    q0 = np.clip(q_err[0], -1.0, 1.0)
    return 2.0 * np.arctan2(np.linalg.norm(q_err[1:]), max(1e-12, abs(q0)))

def mujoco_quat_to_paper_quat(q_mj):
    # Conversion used in the previous working version
    return q_conj(q_normalize(q_mj))

def wrap_to_pi(x):
    return (x + np.pi) % (2*np.pi) - np.pi

def clip_norm(v, vmax):
    n = np.linalg.norm(v)
    if n <= vmax or n < 1e-12:
        return v
    return v * (vmax / n)

# ============================================================
# REFERENCE
# ============================================================
def reference_euler(t):
    if REFERENCE_MODE == "roll":
        # hover + roll oscillation
        return np.array([
            0.25 * np.sin(0.7 * t),
            0.0,
            0.0
        ], dtype=float)

    elif REFERENCE_MODE == "full3":
        amp = np.array([0.5, 0.5, 0.5], dtype=float)
        freq = 1.0
        phase = np.array([0.0, np.pi/2.0, np.pi], dtype=float)
        return amp * np.sin(freq * t + phase)

    else:
        raise ValueError(f"Unknown REFERENCE_MODE: {REFERENCE_MODE}")

def reference_quat(t):
    phi_d, theta_d, psi_d = reference_euler(t)
    return euler_to_quat(phi_d, theta_d, psi_d)

# ============================================================
# MUJOCO HELPERS
# ============================================================
def find_freejoint(model):
    for j in range(model.njnt):
        if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
            return j
    raise RuntimeError("No freejoint found in model.")

# ============================================================
# LOAD MODEL
# ============================================================
model = mujoco.MjModel.from_xml_path(XML_PATH)
data = mujoco.MjData(model)

if ZERO_GRAVITY:
    model.opt.gravity[:] = np.array([0.0, 0.0, 0.0])

free_jid = find_freejoint(model)
body_id = model.jnt_bodyid[free_jid]
body_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body_id)

qpos_adr = model.jnt_qposadr[free_jid]   # [x, y, z, qw, qx, qy, qz]
qvel_adr = model.jnt_dofadr[free_jid]    # [vx, vy, vz, wx, wy, wz]

# Mass and gravity
TOTAL_MASS = float(np.sum(model.body_mass))
G = float(abs(model.opt.gravity[2]))

# Principal inertia in body frame
I_body = np.array(model.body_inertia[body_id], dtype=float)

# Attitude gains
if GAIN_MODE == "scaled":
    # Small-angle approximation:
    # axis_err ~ theta/2  =>  KQ = 2 I wn^2,  KW = 2 zeta wn I
    KQ = 2.0 * I_body * (WN ** 2)
    KW = 2.0 * ZETA * WN * I_body
    TAU_LIMIT = np.maximum(I_body * ALPHA_MAX, np.array([0.03, 0.03, 0.02]))
elif GAIN_MODE == "paper":
    KQ = np.array([20.0, 20.0, 20.0], dtype=float)
    KW = np.array([4.0, 4.0, 4.0], dtype=float)
    TAU_LIMIT = np.array([4.0, 4.0, 4.0], dtype=float)
else:
    raise ValueError(f"Unknown GAIN_MODE: {GAIN_MODE}")

print("Controlled body       :", body_name)
print("Total mass [kg]       :", TOTAL_MASS)
print("Gravity [m/s^2]       :", G)
print("Body inertia [kg m^2] :", I_body)
print("KQ                    :", KQ)
print("KW                    :", KW)
print("TAU_LIMIT [Nm]        :", TAU_LIMIT)
print("REFERENCE_MODE        :", REFERENCE_MODE)
print("GAIN_MODE             :", GAIN_MODE)
print("ZERO_GRAVITY          :", ZERO_GRAVITY)
print("Z_REF [m]             :", Z_REF)

# Zero actuator commands if actuators exist
if model.nu > 0:
    data.ctrl[:] = 0.0

# Initial condition: hover height
data.qpos[qpos_adr:qpos_adr+3] = np.array([0.0, 0.0, Z_REF])
data.qpos[qpos_adr+3:qpos_adr+7] = np.array([1.0, 0.0, 0.0, 0.0])
data.qvel[qvel_adr:qvel_adr+6] = 0.0
data.xfrc_applied[:] = 0.0

mujoco.mj_forward(model, data)

# ============================================================
# LOGS
# ============================================================
t_log = []
pos_log = []
vel_log = []
eul_ref_log = []
eul_meas_log = []
tau_body_log = []
omega_log = []
force_world_log = []
collective_log = []
qerr_angle_log = []

# ============================================================
# CORE STEP
# ============================================================
def step_controller():
    t = float(data.time)

    # Clear external wrench
    data.xfrc_applied[:] = 0.0

    # State
    pos = np.array(data.qpos[qpos_adr:qpos_adr+3], dtype=float)
    q_mj = q_normalize(np.array(data.qpos[qpos_adr+3:qpos_adr+7], dtype=float))
    vel = np.array(data.qvel[qvel_adr:qvel_adr+3], dtype=float)
    omega_body = np.array(data.qvel[qvel_adr+3:qvel_adr+6], dtype=float)

    # Convert MuJoCo quaternion to the paper convention
    q_meas = mujoco_quat_to_paper_quat(q_mj)

    # Reference
    q_ref = reference_quat(t)
    eul_ref = reference_euler(t)

    # Quaternion error: q_err = q_ref ⊗ q_meas*
    q_err = q_mul(q_ref, q_conj(q_meas))
    if q_err[0] < 0.0:
        q_err = -q_err

    axis_err = q_err[1:]

    # --------------------------------------------------------
    # Attitude torque (paper controller structure) in BODY frame
    # --------------------------------------------------------
    tau_body = -KQ * axis_err - KW * omega_body
    tau_body = np.clip(tau_body, -TAU_LIMIT, TAU_LIMIT)

    # BODY torque -> WORLD torque for xfrc_applied
    R_wb = data.xmat[body_id].reshape(3, 3)
    tau_world = R_wb @ tau_body

    # --------------------------------------------------------
    # Hover support force (extra layer, not part of the paper)
    # --------------------------------------------------------
    body_z_world = R_wb[:, 2]

    z = pos[2]
    vz = vel[2]

    # Desired collective magnitude along body z
    # Divide by body_z_world[2] so vertical component counters gravity even when tilted
    tilt_cos = max(MIN_TILT_COS, body_z_world[2])
    collective = TOTAL_MASS * (
        G + KZ_ACC * (Z_REF - z) + DZ_ACC * (0.0 - vz)
    ) / tilt_cos

    collective = np.clip(
        collective,
        0.0,
        MAX_COLLECTIVE_FACTOR * TOTAL_MASS * max(G, 1.0)
    )

    F_hover_world = THRUST_SIGN * collective * body_z_world

    # --------------------------------------------------------
    # Weak XY tether to keep visual hover
    # --------------------------------------------------------
    F_xy_world = np.zeros(3, dtype=float)
    if USE_XY_TETHER:
        a_xy_cmd = -KXY_ACC * pos[:2] - DXY_ACC * vel[:2]
        a_xy_cmd = clip_norm(a_xy_cmd, MAX_XY_ACC)
        F_xy_world[:2] = TOTAL_MASS * a_xy_cmd

    # Total idealized force
    F_world = F_hover_world + F_xy_world

    # Apply wrench at body COM
    data.xfrc_applied[body_id, 0:3] = F_world
    data.xfrc_applied[body_id, 3:6] = tau_world

    mujoco.mj_step(model, data)

    # Logs
    eul_meas = quat_to_euler(q_meas)
    qerr_angle = quat_angle_error(q_err)

    t_log.append(t)
    pos_log.append(pos.copy())
    vel_log.append(vel.copy())
    eul_ref_log.append(eul_ref.copy())
    eul_meas_log.append(eul_meas.copy())
    tau_body_log.append(tau_body.copy())
    omega_log.append(omega_body.copy())
    force_world_log.append(F_world.copy())
    collective_log.append(collective)
    qerr_angle_log.append(qerr_angle)

# ============================================================
# RUN
# ============================================================
if USE_VIEWER:
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running() and data.time < SIM_TIME:
            tic = time.time()
            step_controller()
            viewer.sync()

            dt = model.opt.timestep - (time.time() - tic)
            if dt > 0:
                time.sleep(dt)
else:
    while data.time < SIM_TIME:
        step_controller()

# ============================================================
# POSTPROCESS
# ============================================================
t_log = np.array(t_log)
pos_log = np.array(pos_log)
vel_log = np.array(vel_log)
eul_ref_log = np.array(eul_ref_log)
eul_meas_log = np.array(eul_meas_log)
tau_body_log = np.array(tau_body_log)
omega_log = np.array(omega_log)
force_world_log = np.array(force_world_log)
collective_log = np.array(collective_log)
qerr_angle_log = np.array(qerr_angle_log)

eul_ref_plot = np.unwrap(eul_ref_log, axis=0)
eul_meas_plot = np.unwrap(eul_meas_log, axis=0)

tracking_error = wrap_to_pi(eul_meas_log - eul_ref_log)
rmse = np.sqrt(np.mean(tracking_error**2, axis=0))

print("RMSE [phi, theta, psi] [rad] =", rmse)
print("Mean quaternion error angle  =", np.mean(qerr_angle_log))
print("Max quaternion error angle   =", np.max(qerr_angle_log))
print("Mean hover height [m]        =", np.mean(pos_log[:, 2]))
print("Height std [m]               =", np.std(pos_log[:, 2]))

# ============================================================
# PLOTS
# ============================================================
labels = [r'$\phi$', r'$\theta$', r'$\psi$']
omega_names = [r'$\omega_x$', r'$\omega_y$', r'$\omega_z$']
tau_names = [r'$\tau_x$', r'$\tau_y$', r'$\tau_z$']

plt.figure(figsize=(11, 8))
for i in range(3):
    plt.subplot(3, 1, i+1)
    plt.plot(t_log, eul_ref_plot[:, i], '--', label='reference')
    plt.plot(t_log, eul_meas_plot[:, i], '-', label='measured')
    plt.ylabel(f'{labels[i]} [rad]')
    plt.grid(True)
    if i == 0:
        plt.legend()
plt.xlabel('Time [s]')
plt.suptitle('Hover + quaternion attitude tracking')
plt.tight_layout()
plt.show()

plt.figure(figsize=(11, 6))
plt.subplot(2, 1, 1)
plt.plot(t_log, pos_log[:, 2], label='z')
plt.axhline(Z_REF, linestyle='--', label='z_ref')
plt.ylabel('z [m]')
plt.grid(True)
plt.legend()

plt.subplot(2, 1, 2)
plt.plot(t_log, pos_log[:, 0], label='x')
plt.plot(t_log, pos_log[:, 1], label='y')
plt.ylabel('x, y [m]')
plt.xlabel('Time [s]')
plt.grid(True)
plt.legend()
plt.suptitle('Position / hover behavior')
plt.tight_layout()
plt.show()

plt.figure(figsize=(11, 8))
for i in range(3):
    plt.subplot(3, 1, i+1)
    plt.plot(t_log, tau_body_log[:, i])
    plt.axhline(TAU_LIMIT[i], linestyle='--')
    plt.axhline(-TAU_LIMIT[i], linestyle='--')
    plt.ylabel(f'{tau_names[i]} [Nm]')
    plt.grid(True)
plt.xlabel('Time [s]')
plt.suptitle('Body torque command')
plt.tight_layout()
plt.show()

plt.figure(figsize=(11, 8))
for i in range(3):
    plt.subplot(3, 1, i+1)
    plt.plot(t_log, omega_log[:, i])
    plt.ylabel(f'{omega_names[i]} [rad/s]')
    plt.grid(True)
plt.xlabel('Time [s]')
plt.suptitle('Body angular velocity')
plt.tight_layout()
plt.show()

plt.figure(figsize=(11, 6))
plt.subplot(2, 1, 1)
plt.plot(t_log, collective_log)
plt.ylabel('collective [N]')
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(t_log, force_world_log[:, 0], label='Fx')
plt.plot(t_log, force_world_log[:, 1], label='Fy')
plt.plot(t_log, force_world_log[:, 2], label='Fz')
plt.ylabel('force [N]')
plt.xlabel('Time [s]')
plt.grid(True)
plt.legend()
plt.suptitle('Idealized hover support force')
plt.tight_layout()
plt.show()

plt.figure(figsize=(11, 4))
plt.plot(t_log, qerr_angle_log)
plt.ylabel('angle error [rad]')
plt.xlabel('Time [s]')
plt.grid(True)
plt.title('Quaternion error angle')
plt.tight_layout()
plt.show()