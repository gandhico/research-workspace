"""Numerical linearization of the Option-A cascade closed loop around hover
equilibrium, to find exactly which eigenvalue is unstable (rather than more
empirical patching -- three separate mitigations each reduced the growth
rate without eliminating it, which is the signature of nudging an unstable
pole without crossing zero; see PROGRESS_2026-08-31.md).

State (reduced to the y-position/roll subsystem, which the diagnostic trace
pinned as the coupled unstable pair -- x/pitch is symmetric, z/yaw are
separately actuated with no cascade coupling since z is part of the thrust
magnitude directly and yaw_des is fixed):
  x = [y, vy, phi, omega_x]   (phi = roll angle, small-angle)

Dynamics are standard rigid-body physics (Newton's second law for
translation, Euler's equation for rotation) -- not re-derived by hand here,
these are textbook and dt-independent. The CONTROL law reuses the actual
thrust_vector_to_attitude/quat_error functions from run_6dof_cascade.py,
not a hand-approximation of them, to avoid repeating today's derivation
errors.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gra_control.math3d import euler_to_quat, quat_error  # noqa: E402
from run_6dof_cascade import thrust_vector_to_attitude  # noqa: E402

MASS = 1.325     # X2 total mass, kg -- verified against the actual loaded model
J_XX = 0.06071129  # X2 body_inertia[0] (roll axis), kg*m^2 -- verified against the actual loaded model
GRAVITY = 9.81
WN_POS = np.array([1.0, 1.0, 1.2])
KP_POS_Y = MASS*WN_POS[1]**2
KD_POS_Y = MASS*2.0*0.75*WN_POS[1]
WN_ATT = 4.0
KQ_X = 2.0*J_XX*WN_ATT**2
KW_X = 2.0*0.95*WN_ATT*J_XX


def state_dot(x: np.ndarray, use_rate_feedforward: bool, dt_for_ff: float = 1e-4) -> np.ndarray:
    y, vy, phi, omega_x = x
    F0_y = -KP_POS_Y*y-KD_POS_Y*vy
    F = np.array([0.0, F0_y, MASS*GRAVITY])
    q_des, thrust = thrust_vector_to_attitude(F, 0.0, 0.05*MASS*GRAVITY)

    q_meas = euler_to_quat(phi, 0.0, 0.0)
    _, eq = quat_error(q_des, q_meas)

    if use_rate_feedforward:
        # Finite-difference the actual function at +/- a small dt to get omega_des,
        # exactly mirroring what run_6dof_cascade.py does at runtime (not a
        # hand-derived approximation).
        y_next = y+vy*dt_for_ff
        vy_next = vy+F0_y/MASS*dt_for_ff
        F_next = np.array([0.0, -KP_POS_Y*y_next-KD_POS_Y*vy_next, MASS*GRAVITY])
        q_des_next, _ = thrust_vector_to_attitude(F_next, 0.0, 0.05*MASS*GRAVITY)
        _, dq_vec = quat_error(q_des_next, q_des)
        omega_des_x = 2.0*dq_vec[0]/dt_for_ff
    else:
        omega_des_x = 0.0

    tau_x = -KQ_X*eq[0]-KW_X*(omega_x-omega_des_x)

    # Standard rigid-body physics: actual thrust direction from the ACTUAL
    # (not desired) attitude phi, Newton's 2nd law, Euler's equation (no
    # gyroscopic cross-coupling needed for this 1-axis reduction).
    z_world_y = -np.sin(phi)  # body z-axis y-component in world frame, R_x(phi) convention
    F_actual_y = thrust*z_world_y
    return np.array([vy, F_actual_y/MASS, omega_x, tau_x/J_XX])


def jacobian(f, x0: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    n = len(x0)
    J = np.zeros((n, n))
    for i in range(n):
        dx = np.zeros(n); dx[i] = eps
        J[:, i] = (f(x0+dx)-f(x0-dx))/(2*eps)
    return J


if __name__ == "__main__":
    x0 = np.zeros(4)
    for label, use_ff in [("without rate feedforward", False), ("with rate feedforward", True)]:
        J = jacobian(lambda x: state_dot(x, use_ff), x0)
        eigvals, eigvecs = np.linalg.eig(J)
        print(f"\n=== {label} ===")
        print("Jacobian:\n", np.round(J, 4))
        print("eigenvalues:", eigvals)
        for i, ev in enumerate(eigvals):
            if ev.real > 1e-9:
                print(f"  UNSTABLE mode {i}: eigenvalue={ev:.6f}, eigenvector={np.round(eigvecs[:, i].real, 4)} "
                      f"(states: y, vy, phi, omega_x)")
