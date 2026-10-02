"""Recursive (Lyapunov) backstepping for quaternion attitude tracking, plain and adaptive.

Requested by Gandhi (2026-10-01): a *real* backstepping controller, designed step by step as in his EHEKATL BWB
thesis (Ch. 3, "Backstepping" and "Adaptive Backstepping": strict-feedback form, tracking errors z1, z2, virtual
control with the cross-coupling term, V = sum of quadratic forms, La Salle-Yoshizawa). The existing
AdvancedBaseline "backstepping" family is computed torque (PD + inverse dynamics); it is kept unchanged.

Strict-feedback form (passive quaternion convention of the paper, P-(3), P-(7)-(8)):
    x1 = z1 = e_q = sgn+(q_e0) q_ev,     z1_dot = 1/2 T(q_e) w_e,   T = |q_e0| I + [z1]x
    w_e = w - wbar_d,  wbar_d = R(q_e)^T w_d            (desired rate carried into the body frame)
    J w_dot = -w x J w + tau (+ d)                       (Euler; d: unknown slowly varying torque)

Step 1. V1 = 2 (1 - |q_e0|)  =>  V1_dot = z1^T w_e.  Virtual rate  w_e^d = -K1 z1.
Step 2. z2 = w_e - w_e^d = w_e + K1 z1.  V = c V1 + 1/2 z2^T J z2 (+ 1/2 dt^T G^-1 dt, adaptive).
    tau = w x J w + J (wbar_d_dot - K1 z1_dot) - c z1 - K2 z2 (- d_hat)
    V_dot = -c z1^T K1 z1 - z2^T K2 z2 <= 0          (no saturation, exact model, d = d_hat in the plain law)
    adaptive:  d_hat_dot = Proj_{|d_hat_i| <= D_i}( G z2 )
The cross term -c z1 is the backstepping coupling term (-g1^T z1 in the thesis notation).

Gain choice: the linearization about z = 0 is z1_dd + (k1/2 + k2/J) z1_d + (c + k1 k2)/(2J) z1 = 0 per axis. Choose
k1 = 2 lam1, k2 = J lam2 with lam1 + lam2 = 2 zeta w and lam1 lam2 + c/(2J) = w^2, w = rho*wn: the plain law then
has exactly the small-error poles of the paper's PD+ff (-11.4 +- 3.75j on roll), so any difference between the two
families comes from the backstepping structure (cross term, gyroscopic cancellation, rate transport and its
derivative), not from bandwidth. One scalar c serves all axes (V1 is a scalar); it is the smallest value for which
lam1, lam2 are real on every axis. lam1 (outer, kinematic) <= lam2 (inner, rate).
"""
from __future__ import annotations

import numpy as np

from gra_control.math3d import quat_conj, quat_error, quat_mul


def rot(q: np.ndarray) -> np.ndarray:
    """R(q) with R(q) v = vec(q (x) [0, v] (x) q*)."""
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ])


def design_gains(J: np.ndarray, w: np.ndarray, zeta: float):
    """Return k1 (1/s), k2 (N m s), c (N m) and lam1, lam2 per axis (see module docstring)."""
    J, w = np.asarray(J, float), np.asarray(w, float)
    c = float(np.max(2.0 * J * w ** 2 * (1.0 - zeta ** 2)))          # smallest c with real lam1, lam2 on all axes
    if np.any(c > 2.0 * J * w ** 2):
        raise ValueError("no positive lam1*lam2 for this inertia spread; change zeta")
    disc = np.sqrt(np.maximum((zeta * w) ** 2 - w ** 2 + c / (2.0 * J), 0.0))
    lam1, lam2 = zeta * w - disc, zeta * w + disc
    return 2.0 * lam1, J * lam2, c, lam1, lam2


class TrueBackstepping:
    """Same interface as AdvancedBaseline: torque(t, eq, omega, q_meas) -> saturated torque in the box."""

    def __init__(self, inertia, limits, wn, reference_rate, mission, duration, rho=3.0, zeta=0.95,
                 adaptive=False, adapt_frac=0.3, d_max_frac=0.25, dt=5e-4, rate_ff="left-neg"):
        self.J = np.asarray(inertia, float)
        self.lim = np.asarray(limits, float)
        self.w = np.asarray(wn, float) * rho
        self.zeta = zeta
        self.k1, self.k2, self.c, self.lam1, self.lam2 = design_gains(self.J, self.w, zeta)
        self._rr, self.mission, self.duration, self.mode = reference_rate, mission, duration, rate_ff
        self.adaptive, self.dt = adaptive, dt
        # adaptation gain: makes the integral action on z1 comparable to the PID family (k_I = 0.3 w^2 per unit
        # inertia):  d_hat ~ G \int z2 ~ G k1 \int z1, so G = 0.3 * 2 J w^2 / k1 (torque per unit z2 per second).
        self.G = adapt_frac * 2.0 * self.J * self.w ** 2 / self.k1
        self.D = d_max_frac * self.lim
        self.d_hat = np.zeros(3)
        self.V_log = []
        self.n_proj = 0
        self.n = 0

    # -- reference rate and its derivative (same central differences as AdvancedBaseline) ------------------------
    def _wd(self, t):
        return self._rr(t, self.mission, self.duration, self.mode)

    def _wd_dot(self, t, h=1e-3):
        t0 = max(t - h, 0.0)
        return (self._wd(t + h) - self._wd(t0)) / ((t + h) - t0)

    def signals(self, t, q_meas, omega):
        """Backstepping variables at (t, q, w): z1, z2, w_e, z1_dot, wbar_d, wbar_d_dot, |q_e0|."""
        from gra_control.math3d import reference_quat
        qd = reference_quat(t, self.mission, self.duration)
        qe, z1 = quat_error(qd, q_meas)
        a0 = abs(qe[0])
        wd, wd_dot = self._wd(t), self._wd_dot(t)
        Rt = rot(qe).T
        wbar = Rt @ wd
        we = omega - wbar
        z1_dot = 0.5 * (a0 * we + np.cross(z1, we))
        wbar_dot = Rt @ wd_dot - np.cross(we, wbar)
        z2 = we + self.k1 * z1
        return z1, z2, we, z1_dot, wbar, wbar_dot, a0

    def torque(self, t, eq, omega, q_meas):
        z1, z2, we, z1_dot, wbar, wbar_dot, a0 = self.signals(t, q_meas, omega)
        tau = (np.cross(omega, self.J * omega) + self.J * (wbar_dot - self.k1 * z1_dot)
               - self.c * z1 - self.k2 * z2)
        if self.adaptive:
            tau = tau - self.d_hat
            step = self.G * z2 * self.dt
            new = self.d_hat + step
            clipped = np.clip(new, -self.D, self.D)          # projection onto the box |d_hat_i| <= D_i
            self.n_proj += int(np.any(clipped != new))
            self.d_hat = clipped
        self.n += 1
        if self.n % 200 == 1:
            V = self.c * 2.0 * (1.0 - a0) + 0.5 * float(np.sum(self.J * z2 ** 2))
            self.V_log.append(V)
        return np.clip(tau, -self.lim, self.lim)

    def stats(self):
        return {"family": "backstepping-true-adaptive" if self.adaptive else "backstepping-true",
                "k1": self.k1.tolist(), "k2": self.k2.tolist(), "c": self.c, "lam1": self.lam1.tolist(),
                "lam2": self.lam2.tolist(), "w": self.w.tolist(), "zeta": self.zeta,
                "adaptive": self.adaptive, "G": self.G.tolist(), "D": self.D.tolist(),
                "d_hat_final": self.d_hat.tolist(), "projection_active_fraction": self.n_proj / max(self.n, 1),
                "lyapunov_V_first_last": [self.V_log[0], self.V_log[-1]] if self.V_log else None}
