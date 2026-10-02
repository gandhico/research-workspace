"""Validate the MuJoCo twin against Quanser's published model (quanser_3dof_gyro_reaction_torque.mlx)."""
import mujoco
import numpy as np

from gyro3dof import reference_model as ref
from gyro3dof.controllers import ReactionTorqueController
from gyro3dof.mjcf import load, qadr
from gyro3dof.params import PARAMS as P
from gyro3dof.sim import run


def test_composite_inertias_match_vendor():
    m, d = load(red_locked=False)
    mujoco.mj_forward(m, d)
    M = np.zeros((m.nv, m.nv))
    mujoco.mj_fullM(m, d, M)  # MuJoCo 3.11 signature: (model, data, dst)
    diag = {j: M[qadr(m, j)[1], qadr(m, j)[1]] for j in ("psi", "theta", "phi")}
    assert np.isclose(diag["psi"], P.Jz, rtol=1e-9)
    assert np.isclose(diag["theta"], P.Jy, rtol=1e-9)
    assert np.isclose(diag["phi"], P.Jx, rtol=1e-9)


def test_nutation_frequency_matches_h_over_sqrt_JxJz():
    t, x, _, _ = run(None, 3.0, dphi0=0.05, ctrl_dt=5e-4)
    phi = x[:, 0] - x[:, 0].mean()
    crossings = np.flatnonzero((phi[:-1] < 0) & (phi[1:] >= 0))
    f = (len(crossings) - 1) / (t[crossings[-1]] - t[crossings[0]])
    assert abs(f - P.nutation_hz) / P.nutation_hz < 0.01, (f, P.nutation_hz)


def test_momentum_exchange_psi_dot_equals_minus_h_over_Jz_delta_phi():
    t, x, _, _ = run(None, 2.0, dphi0=0.05)
    resid = x[:, 3] + P.h / P.Jz * (x[:, 0] - x[0, 0])
    assert np.max(np.abs(resid)) < 0.01 * np.max(np.abs(x[:, 3]))


def lab_step(psi_ref=np.radians(15)):
    c = ReactionTorqueController()
    return lambda t, x: c(psi_ref, x[2], x[1], x[3])


def test_lab_controller_mujoco_matches_linear_reference():
    tm, xm, um, _ = run(lab_step(), 6.0)
    tr, xr, ur = ref.simulate(lab_step(), np.zeros(4), 6.0)
    step = np.radians(15)
    assert np.max(np.abs(xm[:, 1] - xr[:, 1])) < 0.02 * step   # psi
    assert np.max(np.abs(xm[:, 0] - xr[:, 0])) < 0.02 * step   # phi
    assert abs(xm[-1, 1] - step) < 0.02 * step                 # reaches the reference
