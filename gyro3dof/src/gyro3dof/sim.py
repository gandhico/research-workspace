"""Run the MuJoCo gyroscope with a controller in the loop."""
from __future__ import annotations

from typing import Callable

import mujoco
import numpy as np

from .mjcf import load, qadr
from .params import PARAMS


def spun_up(red_locked=True, w=PARAMS.w_ss, **kw):
    """Model and data with the disc already at speed w (the lab's spin-up is assumed done)."""
    m, d = load(red_locked=red_locked, **kw)
    _, dv = qadr(m, "spin")
    d.qvel[dv] = w
    d.ctrl[m.actuator("disc_speed").id] = w
    mujoco.mj_forward(m, d)
    return m, d


def run(controller: Callable[[float, np.ndarray], float] | None, t_end: float,
        phi0=0.0, dphi0=0.0, ctrl_dt=1e-3, frame_cb=None, **kw):
    """controller(t, [phi, psi, phi_dot, psi_dot]) -> tau2; sampled every ctrl_dt (ZOH).

    Returns t, x (N x 4), tau2, disc speed. frame_cb(m, d, t) is called at ctrl_dt.
    """
    m, d = spun_up(**kw)
    qp_phi, dv_phi = qadr(m, "phi")
    qp_psi, dv_psi = qadr(m, "psi")
    _, dv_spin = qadr(m, "spin")
    d.qpos[qp_phi] = phi0
    d.qvel[dv_phi] = dphi0
    mujoco.mj_forward(m, d)
    a2 = m.actuator("tau2").id
    sub = int(round(ctrl_dt / m.opt.timestep))
    if sub < 1 or abs(sub * m.opt.timestep - ctrl_dt) > 1e-12:
        # Otherwise the logged time would not match the simulated time.
        raise ValueError(f"ctrl_dt={ctrl_dt} must be a whole multiple of timestep={m.opt.timestep}")
    n = int(round(t_end / ctrl_dt))
    ts, xs, us, ws = [], [], [], []
    for k in range(n + 1):
        x = np.array([d.qpos[qp_phi], d.qpos[qp_psi], d.qvel[dv_phi], d.qvel[dv_psi]])
        u = 0.0 if controller is None else float(controller(k * ctrl_dt, x))
        u = float(np.clip(u, -PARAMS.tau_max, PARAMS.tau_max))
        ts.append(k * ctrl_dt); xs.append(x); us.append(u); ws.append(d.qvel[dv_spin])
        if frame_cb is not None:
            frame_cb(m, d, k * ctrl_dt)
        if k == n:
            break
        d.ctrl[a2] = u
        for _ in range(sub):
            mujoco.mj_step(m, d)
    return np.array(ts), np.array(xs), np.array(us), np.array(ws)
