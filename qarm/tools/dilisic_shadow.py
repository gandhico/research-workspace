"""DILISIC shadow controller for one QArm joint (runbook 2026-09-09, step 5).

Nothing here touches hardware. `ShadowDILISIC.step` takes a measured joint
position and the baseline reference, and returns what DILISIC *would* request.
The caller keeps sending the baseline position command to the servo.

Estimator: steady-state Kalman filter on a quadruple integrator driven by
white snap noise, giving the 4th-order state [q, qd, qdd, qddd] that the paper
assumes. Its noise/bandwidth trade-off is set by
    sigma_q    measurement noise (encoder: 4096 counts/rev -> 0.0015 rad/count;
               the at-rest std measured 2026-09-27 was ~0.0007 rad)
    sigma_snap process noise on q^(4)
and the resulting closed-loop bandwidth is reported by `estimator_bandwidth_hz`.
Default sigma_snap=2 gives ~2.1 Hz. On a 0.3 rad / 0.25 Hz sine quantized to 4096
counts/rev (tests/test_dilisic_shadow.py), the worst-case errors after convergence are:
q 0.0008 rad, qd 3%, qdd 21%, qddd 72% of amplitude. Faster settings are worse
(sigma_snap=500: qdd error 4x the signal). **The jerk estimate is noise-dominated**, which
is a runbook no-go for actuation; for shadow diagnostics it is recorded, not hidden.
The servo velocity channel (3003) is informative but quantized at 0.024 rad/s and
lagged (~0.78x during motion); fusing it is a possible follow-up.

Reference model anchoring (shadow-mode adaptation): in the paper, u_DI comes from
the outer loop on the *measured* plant, and the DI reference model integrates it open
loop. That is consistent only because DILISIC then forces plant ~ reference. In shadow
mode nothing corrects the plant, so the open-loop reference drifts (2 rad in 20 s in a
synthetic test) and s grows without bound. Here u_DI is therefore computed from the
*reference-model* state (PD toward the baseline), which keeps the reference on the
baseline; DILISIC's request then measures the plant's departure from ideal
double-integrator behaviour. With DILISIC in the loop (plant ~ reference) both forms coincide.

Contract caveat: the wrist is a vendor position servo, not the paper's affine
q^(4) = f + g u plant. DILISIC's output here is a diagnostic in the paper's
input units. It is NOT a validated position-command correction.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.linalg import expm, solve_discrete_are

from dilisic.controllers import DILISICWrapper
from dilisic.controllers.lisic import LISICController, LISICParameters


def chain_model(dt: float):
    a = np.diag(np.ones(3), 1)
    b = np.array([0.0, 0.0, 0.0, 1.0])
    f = expm(a * dt)
    # Exact integral of the snap input over one sample: [dt^4/24, dt^3/6, dt^2/2, dt].
    g = np.array([dt**4 / 24, dt**3 / 6, dt**2 / 2, dt])
    return f, g, np.array([[1.0, 0.0, 0.0, 0.0]])


@dataclass
class ChainKalman:
    dt: float
    sigma_q: float = 7.0e-4
    sigma_snap: float = 2.0
    x: np.ndarray = field(default_factory=lambda: np.zeros(4))

    def __post_init__(self):
        self.f, self.g, self.h = chain_model(self.dt)
        q = self.sigma_snap**2 * np.outer(self.g, self.g) / self.dt
        r = np.array([[self.sigma_q**2]])
        p = solve_discrete_are(self.f.T, self.h.T, q, r)
        s = self.h @ p @ self.h.T + r
        self.k = (p @ self.h.T / s).ravel()

    def reset(self, q0: float):
        self.x = np.array([q0, 0.0, 0.0, 0.0])

    def update(self, q_meas: float) -> np.ndarray:
        x_pred = self.f @ self.x
        self.x = x_pred + self.k * (q_meas - x_pred[0])
        return self.x.copy()

    def estimator_bandwidth_hz(self) -> float:
        closed = (np.eye(4) - np.outer(self.k, self.h[0])) @ self.f
        z = np.linalg.eigvals(closed)
        return float(np.max(np.abs(np.log(z))) / self.dt / (2 * np.pi))


@dataclass
class ShadowDILISIC:
    dt: float
    kp: float = 50.0                       # same outer gains as the dilisic scaffold
    kd: float = float(2.0 * np.sqrt(50.0))
    u_di_limit: float = 2.0e4
    correction_bound: float = 5.0e3        # declared shadow authority budget (paper units)
    sigma_q: float = 7.0e-4
    sigma_snap: float = 2.0
    # False freezes the RBF weights at their initial values (xi still integrates).
    # The adaptation laws assume DILISIC's u acts on the plant; in shadow mode it
    # does not, so adapting "learns" from an open loop (h_hat 1.2 -> 267 on hardware).
    adapt: bool = True

    def __post_init__(self):
        self.kf = ChainKalman(self.dt, self.sigma_q, self.sigma_snap)
        self.ctrl = DILISICWrapper(lisic=LISICController(LISICParameters()))
        self.ref_state = None

    def reset(self, q0: float, qd0: float = 0.0):
        self.kf.reset(q0)
        self.kf.x[1] = qd0
        self.ctrl = DILISICWrapper(lisic=LISICController(LISICParameters()))
        self.ref_state = self.ctrl.initialize(self.kf.x)

    def step(self, q_meas: float, q_ref: float, qd_ref: float, qdd_ref: float) -> dict:
        x = self.kf.update(q_meas)
        xr = self.ref_state.x_ref
        u_di = qdd_ref - self.kp * (xr[0] - q_ref) - self.kd * (xr[1] - qd_ref)
        u_di = float(np.clip(u_di, -self.u_di_limit, self.u_di_limit))
        x_ref_before = self.ref_state.x_ref.copy()
        lis = self.ctrl.lisic
        frozen = None if self.adapt else [w.copy() for w in (lis.v_f, lis.w_f, lis.v_h, lis.w_h)]
        u_total, info = self.ctrl.step(x, self.ref_state, u_di, self.dt)
        if frozen is not None:
            lis.v_f, lis.w_f, lis.v_h, lis.w_h = frozen
        # s used [q, qd] of the reference before its integration and [qdd, qddd] as set this step.
        xr = self.ref_state.x_ref
        e = x - np.array([x_ref_before[0], x_ref_before[1], xr[2], xr[3]])
        l1, l2, l3 = lis.params.lambdas
        limit = self.ctrl.lisic.params.control_limit
        u_l = info["u_lisic"]
        norms = self.ctrl.lisic.weight_norms()
        return {
            "q_hat": x[0], "qd_hat": x[1], "qdd_hat": x[2], "qddd_hat": x[3],
            "x_ref_q": x_ref_before[0], "x_ref_qd": x_ref_before[1],
            "u_di": u_di, "u_di_filtered": info["u_di_filtered"],
            "u_lisic_raw": u_l,
            "u_lisic_bounded": float(np.clip(u_l, -self.correction_bound, self.correction_bound)),
            "u_total": u_total,
            "lisic_saturated": bool(limit is not None and abs(u_l) >= limit),
            "shadow_bound_hit": bool(abs(u_l) > self.correction_bound),
            "s": info["s"], "f_hat": info["f_hat"], "h_hat": info["h_hat"], "u_r": info["u_r"],
            # Contributions to s = e3 + l3 e2 + l2 e1 + l1 e0 (e = estimate - reference model).
            "s_e3": float(e[3]), "s_e2": float(l3 * e[2]), "s_e1": float(l2 * e[1]), "s_e0": float(l1 * e[0]),
            "w_norm_max": max(norms.values()),
        }
