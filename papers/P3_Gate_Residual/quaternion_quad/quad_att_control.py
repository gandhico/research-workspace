# ================================================================
# Full Quaternion-Based Attitude Control for a Quadrotor
# ------------------------------------------------
# Single-file Python implementation of the paper-style model:
#
#   q_dot     = -0.5 * [0, wx, wy, wz] ⊗ q
#   omega_dot = I^{-1} ( tau - omega x (I omega) )
#
# with quaternion P2 control law:
#
#   q_err = q_ref ⊗ conj(q_meas)
#   tau   = -Pq * vec(q_err) - Pw * omega_meas
#
# Notes:
# - This is an ATTITUDE-ONLY model (7 states), not full translation.
# - Input is BODY TORQUE [tau_x, tau_y, tau_z], exactly in the spirit
#   of the paper's simplified control-to-torque setup.
# - The code includes three reference modes:
#       1) step
#       2) sine
#       3) flip
# - For flip mode, shortest-path correction is disabled so the system
#   follows the long path (0 -> 2*pi), which is closer to the paper's
#   flip test description.
#
# Dependencies:
#   pip install numpy matplotlib
# ================================================================

import numpy as np
import matplotlib.pyplot as plt


# ================================================================
# 1) Quaternion utilities
# Convention:
#   q = [q0, q1, q2, q3] = [w, x, y, z]
# where q0 is scalar part and [q1, q2, q3] is vector part.
# ================================================================

def quat_normalize(q):
    """Normalize quaternion to unit norm."""
    q = np.asarray(q, dtype=float)
    n = np.linalg.norm(q)
    if n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    return q / n


def quat_conj(q):
    """Quaternion conjugate."""
    q = np.asarray(q, dtype=float)
    return np.array([q[0], -q[1], -q[2], -q[3]], dtype=float)


def quat_mul(p, q):
    """
    Quaternion product p ⊗ q.
    Both p and q are [q0, q1, q2, q3].
    """
    p0, p1, p2, p3 = p
    q0, q1, q2, q3 = q
    return np.array([
        p0*q0 - p1*q1 - p2*q2 - p3*q3,
        p0*q1 + p1*q0 + p2*q3 - p3*q2,
        p0*q2 - p1*q3 + p2*q0 + p3*q1,
        p0*q3 + p1*q2 - p2*q1 + p3*q0
    ], dtype=float)


def axis_angle_to_quat(axis, angle):
    """
    Convert axis-angle to quaternion.
    axis: 3-vector
    angle: radians
    """
    axis = np.asarray(axis, dtype=float)
    n = np.linalg.norm(axis)
    if n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    axis = axis / n
    half = 0.5 * angle
    return quat_normalize(np.array([
        np.cos(half),
        axis[0] * np.sin(half),
        axis[1] * np.sin(half),
        axis[2] * np.sin(half)
    ], dtype=float))


def euler_to_quat(phi, theta, psi):
    """
    Convert ZYX Euler angles (roll, pitch, yaw) to quaternion.
    """
    cphi, sphi = np.cos(phi / 2.0), np.sin(phi / 2.0)
    cth,  sth  = np.cos(theta / 2.0), np.sin(theta / 2.0)
    cpsi, spsi = np.cos(psi / 2.0), np.sin(psi / 2.0)

    q = np.array([
        cphi*cth*cpsi + sphi*sth*spsi,
        sphi*cth*cpsi - cphi*sth*spsi,
        cphi*sth*cpsi + sphi*cth*spsi,
        cphi*cth*spsi - sphi*sth*cpsi
    ], dtype=float)
    return quat_normalize(q)


def quat_to_euler(q):
    """
    Convert quaternion to ZYX Euler angles (roll, pitch, yaw).
    Output is [phi, theta, psi] in radians.

    Note:
    - Around flips or large rotations, Euler angles may wrap and look
      discontinuous. That is expected. Quaternion plots remain cleaner.
    """
    q = quat_normalize(q)
    q0, q1, q2, q3 = q

    # Roll
    phi = np.arctan2(
        2.0 * (q0*q1 + q2*q3),
        q0*q0 - q1*q1 - q2*q2 + q3*q3
    )

    # Pitch
    s_theta = 2.0 * (q0*q2 - q3*q1)
    s_theta = np.clip(s_theta, -1.0, 1.0)
    theta = np.arcsin(s_theta)

    # Yaw
    psi = np.arctan2(
        2.0 * (q0*q3 + q1*q2),
        q0*q0 + q1*q1 - q2*q2 - q3*q3
    )

    return np.array([phi, theta, psi], dtype=float)


def angle_wrap_pi(angle):
    """Wrap angle to [-pi, pi]."""
    return (angle + np.pi) % (2.0 * np.pi) - np.pi


def angle_wrap_vec_pi(a):
    """Wrap vector of angles to [-pi, pi]."""
    return np.array([angle_wrap_pi(x) for x in a], dtype=float)


# ================================================================
# 2) Paper attitude model
# State:
#   x = [q0, q1, q2, q3, wx, wy, wz]
#
# Dynamics:
#   q_dot     = -0.5 * [0, wx, wy, wz] ⊗ q
#   omega_dot = I^{-1} ( tau - omega x (I omega) )
# ================================================================

def quaternion_kinematics_paper(q, omega_body):
    """
    Quaternion kinematics in the paper's sign convention:
        q_dot = -0.5 * [0, omega] ⊗ q
    where omega = [wx, wy, wz] is body angular velocity.
    """
    omega_quat = np.array([0.0, omega_body[0], omega_body[1], omega_body[2]], dtype=float)
    qdot = -0.5 * quat_mul(omega_quat, q)
    return qdot


def rigid_body_rates(omega_body, tau_body, I):
    """
    Rigid-body rotational dynamics:
        omega_dot = I^{-1} ( tau - omega x (I omega) )
    """
    omega_body = np.asarray(omega_body, dtype=float)
    tau_body = np.asarray(tau_body, dtype=float)
    return np.linalg.solve(I, tau_body - np.cross(omega_body, I @ omega_body))


def dynamics(x, tau_body, I):
    """
    Full attitude dynamics for state x = [q(4), omega(3)].
    """
    x = np.asarray(x, dtype=float)
    q = quat_normalize(x[:4])
    omega = x[4:7]

    qdot = quaternion_kinematics_paper(q, omega)
    wdot = rigid_body_rates(omega, tau_body, I)

    dx = np.zeros_like(x)
    dx[:4] = qdot
    dx[4:7] = wdot
    return dx


def rk4_step(x, tau_body, dt, I):
    """
    One RK4 integration step.
    Quaternion is renormalized after integration.
    """
    k1 = dynamics(x, tau_body, I)
    k2 = dynamics(x + 0.5 * dt * k1, tau_body, I)
    k3 = dynamics(x + 0.5 * dt * k2, tau_body, I)
    k4 = dynamics(x + dt * k3, tau_body, I)

    x_next = x + (dt / 6.0) * (k1 + 2.0*k2 + 2.0*k3 + k4)
    x_next[:4] = quat_normalize(x_next[:4])
    return x_next


# ================================================================
# 3) Quaternion P2 controller
#
#   q_err = q_ref ⊗ conj(q_meas)
#   e_q   = vector part of q_err
#   tau   = -Pq * e_q - Pw * omega_meas
#
# Optional "shortest_path":
# - True : if q_err[0] < 0, flip sign of vector error so the
#          controller takes the shorter rotation.
# - False: do not flip. Useful for long-path flip tests.
# ================================================================

def quaternion_p2_controller(q_ref, q_meas, omega_meas,
                             Pq=20.0, Pw=4.0, tau_max=4.0,
                             shortest_path=True):
    """
    Paper-style quaternion P2 controller.

    Parameters
    ----------
    q_ref : desired quaternion
    q_meas : measured quaternion
    omega_meas : measured body rates [wx, wy, wz]
    Pq : quaternion error gain
    Pw : angular-rate damping gain
    tau_max : scalar saturation bound applied componentwise
    shortest_path : whether to use shortest-path correction

    Returns
    -------
    tau_cmd : commanded body torque [tau_x, tau_y, tau_z]
    q_err   : quaternion error
    e_q     : vector part used by controller
    """
    q_ref = quat_normalize(q_ref)
    q_meas = quat_normalize(q_meas)
    omega_meas = np.asarray(omega_meas, dtype=float)

    # Error quaternion
    q_err = quat_mul(q_ref, quat_conj(q_meas))
    q_err = quat_normalize(q_err)

    # Vector part is the axis-related error used by controller
    e_q = q_err[1:].copy()

    # Shortest-path correction
    if shortest_path and q_err[0] < 0.0:
        e_q = -e_q

    # P2 control law
    tau_cmd = -Pq * e_q - Pw * omega_meas

    # Torque saturation
    tau_cmd = np.clip(tau_cmd, -tau_max, tau_max)

    return tau_cmd, q_err, e_q


# ================================================================
# 4) Reference generation
# Modes:
#   - "step" : sequential 1-rad attitude commands
#   - "sine" : 0.5-rad sinusoidal tracking
#   - "flip" : 0 -> 2*pi roll ramp
# ================================================================

def reference_quaternion(t, mode="step"):
    """
    Generate desired attitude quaternion.
    """

    if mode == "step":
        # Sequential 1-rad steps, similar in spirit to the paper
        if t < 1.0:
            phi, theta, psi = 0.0, 0.0, 0.0
        elif t < 5.0:
            phi, theta, psi = 1.0, 0.0, 0.0
        elif t < 9.0:
            phi, theta, psi = 1.0, 1.0, 0.0
        else:
            phi, theta, psi = 1.0, 1.0, 1.0
        return euler_to_quat(phi, theta, psi)

    elif mode == "sine":
        # 0.5-rad amplitude, 1 rad/s frequency, phase-shifted channels
        phi   = 0.5 * np.sin(1.0 * t)
        theta = 0.5 * np.sin(1.0 * t - 0.8)
        psi   = 0.5 * np.sin(1.0 * t - 1.6)
        return euler_to_quat(phi, theta, psi)

    elif mode == "flip":
        # Roll flip: ramp from 0 to 2*pi so controller follows a full flip
        t0 = 1.0
        tf = 2.5
        if t <= t0:
            alpha = 0.0
        elif t >= tf:
            alpha = 2.0 * np.pi
        else:
            alpha = 2.0 * np.pi * (t - t0) / (tf - t0)

        # Rotation around body/inertial x-axis represented in quaternion form
        return axis_angle_to_quat([1.0, 0.0, 0.0], alpha)

    else:
        raise ValueError("mode must be one of: 'step', 'sine', 'flip'")


def controller_shortest_path_flag(mode):
    """
    For step and sine, shortest-path correction is desirable.
    For flip, disable it so the vehicle follows the long path.
    """
    return mode in ("step", "sine")


# ================================================================
# 5) Simulation
# ================================================================

def simulate(mode="step",
             T=15.0,
             dt=0.002,
             Pq=20.0,
             Pw=4.0,
             tau_max=4.0,
             noise_std_q=0.0,
             noise_std_w=0.0,
             seed=1):
    """
    Simulate the quaternion attitude system.

    Parameters
    ----------
    mode : 'step', 'sine', or 'flip'
    T : simulation duration [s]
    dt : timestep [s]
    Pq, Pw : controller gains
    tau_max : torque saturation bound [Nm]
    noise_std_q : additive quaternion measurement noise magnitude
    noise_std_w : additive angular-rate measurement noise magnitude
    seed : random seed for reproducibility

    Returns
    -------
    data : dict of time histories
    """
    rng = np.random.default_rng(seed)

    # Paper simulation inertias
    Ixx = 6.5e-4
    Iyy = 6.5e-4
    Izz = 1.2e-3
    I = np.diag([Ixx, Iyy, Izz])

    N = int(np.floor(T / dt))
    t_hist = np.linspace(0.0, N * dt, N + 1)

    # Initial state: identity quaternion, zero angular rates
    x = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=float)

    # Histories
    x_hist = np.zeros((N + 1, 7))
    qref_hist = np.zeros((N + 1, 4))
    qerr_hist = np.zeros((N + 1, 4))
    eq_hist = np.zeros((N + 1, 3))
    tau_hist = np.zeros((N + 1, 3))
    euler_hist = np.zeros((N + 1, 3))
    euler_ref_hist = np.zeros((N + 1, 3))
    omega_hist = np.zeros((N + 1, 3))
    omega_meas_hist = np.zeros((N + 1, 3))

    # Initial logging
    x_hist[0] = x
    omega_hist[0] = x[4:7]
    euler_hist[0] = quat_to_euler(x[:4])
    qref0 = reference_quaternion(0.0, mode=mode)
    qref_hist[0] = qref0
    euler_ref_hist[0] = quat_to_euler(qref0)

    use_shortest_path = controller_shortest_path_flag(mode)

    for k in range(N):
        t = t_hist[k]

        # True state
        q_true = quat_normalize(x[:4])
        omega_true = x[4:7].copy()

        # Desired reference
        q_ref = reference_quaternion(t, mode=mode)

        # Simulated noisy measurements
        q_meas = q_true.copy()
        w_meas = omega_true.copy()

        if noise_std_q > 0.0:
            q_meas = quat_normalize(q_meas + noise_std_q * rng.standard_normal(4))

        if noise_std_w > 0.0:
            w_meas = w_meas + noise_std_w * rng.standard_normal(3)

        # Controller
        tau_cmd, q_err, e_q = quaternion_p2_controller(
            q_ref=q_ref,
            q_meas=q_meas,
            omega_meas=w_meas,
            Pq=Pq,
            Pw=Pw,
            tau_max=tau_max,
            shortest_path=use_shortest_path
        )

        # Integrate dynamics
        x = rk4_step(x, tau_cmd, dt, I)

        # Log
        x_hist[k + 1] = x
        qref_hist[k + 1] = q_ref
        qerr_hist[k + 1] = q_err
        eq_hist[k + 1] = e_q
        tau_hist[k + 1] = tau_cmd
        euler_hist[k + 1] = quat_to_euler(x[:4])
        euler_ref_hist[k + 1] = quat_to_euler(q_ref)
        omega_hist[k + 1] = x[4:7]
        omega_meas_hist[k + 1] = w_meas

    data = {
        "t": t_hist,
        "x": x_hist,
        "q": x_hist[:, :4],
        "omega": omega_hist,
        "omega_meas": omega_meas_hist,
        "q_ref": qref_hist,
        "q_err": qerr_hist,
        "e_q": eq_hist,
        "tau": tau_hist,
        "euler": euler_hist,
        "euler_ref": euler_ref_hist,
        "I": I,
        "mode": mode,
        "Pq": Pq,
        "Pw": Pw,
        "tau_max": tau_max,
    }
    return data


# ================================================================
# 6) Plotting
# ================================================================

def plot_results(data):
    """
    Plot:
      1) Euler-angle tracking
      2) Body rates
      3) Body torque
      4) Quaternion tracking
    """
    t = data["t"]
    euler = data["euler"]
    euler_ref = data["euler_ref"]
    omega = data["omega"]
    tau = data["tau"]
    q = data["q"]
    q_ref = data["q_ref"]
    mode = data["mode"]

    # 1) Euler-angle tracking
    fig1, ax1 = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    angle_labels = [r"roll $\phi$ [rad]", r"pitch $\theta$ [rad]", r"yaw $\psi$ [rad]"]
    for i in range(3):
        ax1[i].plot(t, euler_ref[:, i], "--", linewidth=2, label="reference")
        ax1[i].plot(t, euler[:, i], linewidth=2, label="output")
        ax1[i].set_ylabel(angle_labels[i])
        ax1[i].grid(True)
        ax1[i].legend(loc="best")
    ax1[-1].set_xlabel("time [s]")
    fig1.suptitle(f"Euler-angle tracking ({mode})")

    # 2) Body angular rates
    fig2, ax2 = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    rate_labels = [r"$\omega_x$ [rad/s]", r"$\omega_y$ [rad/s]", r"$\omega_z$ [rad/s]"]
    for i in range(3):
        ax2[i].plot(t, omega[:, i], linewidth=2)
        ax2[i].set_ylabel(rate_labels[i])
        ax2[i].grid(True)
    ax2[-1].set_xlabel("time [s]")
    fig2.suptitle(f"Body angular rates ({mode})")

    # 3) Body torque
    fig3, ax3 = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    tau_labels = [r"$\tau_x$ [Nm]", r"$\tau_y$ [Nm]", r"$\tau_z$ [Nm]"]
    for i in range(3):
        ax3[i].plot(t, tau[:, i], linewidth=2)
        ax3[i].set_ylabel(tau_labels[i])
        ax3[i].grid(True)
    ax3[-1].set_xlabel("time [s]")
    fig3.suptitle(f"Control torque ({mode})")

    # 4) Quaternion tracking
    fig4, ax4 = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
    qlabels = [r"$q_0$", r"$q_1$", r"$q_2$", r"$q_3$"]
    for i in range(4):
        ax4[i].plot(t, q_ref[:, i], "--", linewidth=2, label="reference")
        ax4[i].plot(t, q[:, i], linewidth=2, label="output")
        ax4[i].set_ylabel(qlabels[i])
        ax4[i].grid(True)
        ax4[i].legend(loc="best")
    ax4[-1].set_xlabel("time [s]")
    fig4.suptitle(f"Quaternion tracking ({mode})")

    plt.tight_layout()
    plt.show()


# ================================================================
# 7) Main
# Change "mode" below to:
#   - "step"
#   - "sine"
#   - "flip"
# ================================================================

if __name__ == "__main__":

    # ------------------------------------------------------------
    # Choose reference mode
    # ------------------------------------------------------------
    mode = "step"     # "step", "sine", or "flip"

    # ------------------------------------------------------------
    # Simulation settings
    # ------------------------------------------------------------
    if mode == "flip":
        T = 5.0
    else:
        T = 15.0

    dt = 0.002

    # Paper-style gains
    Pq = 20.0
    Pw = 4.0

    # Torque saturation bound
    tau_max = 4.0

    # Optional measurement noise
    # You can set these > 0 to test robustness
    noise_std_q = 0.0
    noise_std_w = 0.0

    # ------------------------------------------------------------
    # Run simulation
    # ------------------------------------------------------------
    data = simulate(
        mode=mode,
        T=T,
        dt=dt,
        Pq=Pq,
        Pw=Pw,
        tau_max=tau_max,
        noise_std_q=noise_std_q,
        noise_std_w=noise_std_w,
        seed=1
    )

    # ------------------------------------------------------------
    # Print final state summary
    # ------------------------------------------------------------
    final_q = data["q"][-1]
    final_euler = data["euler"][-1]
    final_omega = data["omega"][-1]

    print("\n================================================")
    print("Final simulation summary")
    print("================================================")
    print(f"Mode          : {mode}")
    print(f"Final q       : {final_q}")
    print(f"Final Euler   : {final_euler}  [rad]")
    print(f"Final omega   : {final_omega}  [rad/s]")
    print("================================================\n")

    # ------------------------------------------------------------
    # Plot results
    # ------------------------------------------------------------
    plot_results(data)

    # ------------------------------------------------------------
    # Optional: save arrays to file for later analysis
    # ------------------------------------------------------------
    # np.savez("quat_p2_results.npz", **data)