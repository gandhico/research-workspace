"""Phase 3 model-variant tests (brief §6).

Verify paper-faithful dynamics, the cos(theta) clip, analytic vs numerical
linearization consistency, LS inverse dynamics, 1-DOF frozen-axis behavior,
yaw breakaway/stiction, and that every variant composes with OfflineBackend.
"""
import math

import numpy as np
import pytest

from aero2.config import params
from aero2.execution.offline import OfflineBackend
from aero2.models import (
    HalfRotor, Helicopter2DOF, Linear2DOF, MODELS, PitchOnly, YawOnly, make_model,
)
from aero2.models.base import Model
from aero2.models.helicopter_2dof import drift, input_matrix
from aero2.models.linear_2dof import linear_plant_matrices


# --- registry --------------------------------------------------------------
def test_registry_complete():
    assert set(MODELS) == {"helicopter_2dof", "linear_2dof", "pitch_only", "yaw_only", "half_rotor"}
    assert isinstance(make_model("helicopter_2dof"), Helicopter2DOF)
    with pytest.raises(ValueError):
        make_model("does_not_exist")


# --- helicopter (primary nonlinear) ---------------------------------------
def test_drift_and_input_matrix_match_config():
    M = input_matrix(0.0)
    assert M[0, 0] == pytest.approx(params.DT_ARM * params.KPP / params.J_PITCH)
    assert M[1, 1] == pytest.approx(params.KYY / params.J_YAW)   # cos 0 = 1
    b = drift(0.3, 0.1, 0.0, 0.2)
    assert b[0] == pytest.approx((-params.KSP * math.sin(0.3) - params.DP * 0.1) / params.J_PITCH)
    assert b[1] == pytest.approx((-params.DY * 0.2) / params.J_YAW)


def test_cos_theta_clip_active():
    # at theta = pi/2, cos ~ 0 must be clipped to MIN_COS_THETA (yaw authority floor)
    M_big = input_matrix(math.pi / 2)
    assert M_big[1, 1] == pytest.approx(params.MIN_COS_THETA * params.KYY / params.J_YAW)
    assert M_big[1, 1] != pytest.approx(0.0)


def test_analytic_linearization_matches_paper_and_numerical():
    heli = Helicopter2DOF()
    A, B, C, D = heli.linearize(np.zeros(4), np.zeros(2))
    Aexp, Bexp, Cexp = linear_plant_matrices()
    assert np.allclose(A, Aexp) and np.allclose(B, Bexp) and np.allclose(C, Cexp)
    assert A[1, 0] == pytest.approx(-params.KSP / params.J_PITCH)
    assert B[3, 1] == pytest.approx(params.KYY / params.J_YAW)
    # analytic == base-class numerical Jacobian at the origin
    An, Bn, Cn, Dn = Model.linearize(heli, np.zeros(4), np.zeros(2))
    assert np.allclose(A, An, atol=1e-3) and np.allclose(B, Bn, atol=1e-3)


def test_inverse_dynamics_recovers_command():
    heli = Helicopter2DOF()
    x = np.array([0.1, 0.0, 0.2, 0.0])
    u_test = np.array([1.5, -0.8])
    accel = drift(*x) + input_matrix(x[0]) @ u_test            # achievable target
    u, u_raw = heli.inverse_dynamics(x, accel)
    assert np.allclose(u_raw, u_test, atol=1e-6)
    assert np.all(np.abs(u) <= params.V_MAX)


def test_helicopter_step_shapes():
    heli = Helicopter2DOF()
    x1 = heli.step(np.zeros(4), np.array([2.0, 0.5]), 0.01)
    assert x1.shape == (4,) and np.all(np.isfinite(x1))


# --- linear realization ----------------------------------------------------
def test_linear_2dof_is_linear():
    lin = Linear2DOF()
    assert np.allclose(lin.f(np.zeros(4), np.zeros(2)), np.zeros(4))
    x, u = np.array([0.1, 0.2, 0.3, 0.4]), np.array([1.0, -1.0])
    assert np.allclose(lin.f(2 * x, 2 * u), 2 * lin.f(x, u))    # superposition


# --- pitch-only (yaw inert, near-integrating) ------------------------------
def test_pitch_only_yaw_frozen_and_u_y_ignored():
    m = PitchOnly()
    xdot_a = m.f(np.array([0.05, 0.0, 0.0, 0.0]), np.array([1.0, 5.0]))
    xdot_b = m.f(np.array([0.05, 0.0, 0.0, 0.0]), np.array([1.0, -5.0]))
    assert xdot_a[2] == 0.0 and xdot_a[3] == 0.0               # yaw inert
    assert np.allclose(xdot_a, xdot_b)                         # u_y has no effect
    assert xdot_a[1] != 0.0                                    # pitch responds to u_p


# --- yaw-only (pitch inert, breakaway/stiction) ----------------------------
def test_yaw_only_breakaway():
    m = YawOnly(breakaway_v=params.YAW_BREAKAWAY_V)
    rest = np.zeros(4)
    small = m.f(rest, np.array([0.0, 0.5 * params.YAW_BREAKAWAY_V]))   # below breakaway
    big = m.f(rest, np.array([0.0, 2.0 * params.YAW_BREAKAWAY_V]))     # above breakaway
    assert small[3] == 0.0                                    # stuck at rest
    assert big[3] != 0.0                                      # breaks away
    # once moving, even a small command produces dynamics
    moving = np.array([0.0, 0.0, 0.0, 0.5])
    assert m.f(moving, np.array([0.0, 0.1]))[3] != 0.0
    assert m.f(rest, np.array([0.0, 5.0]))[0] == 0.0          # pitch inert


# --- half-rotor (NotValidated) --------------------------------------------
def test_half_rotor_flagged_notvalidated():
    m = HalfRotor()
    assert m.validated is False
    assert m.hardware_status == "NotValidated"
    assert m.f(np.zeros(4), np.array([1.0, 1.0])).shape == (4,)


# --- composition: every variant runs through the offline backend ----------
@pytest.mark.parametrize("name", sorted(MODELS))
def test_variant_runs_offline(name):
    model = make_model(name)
    be = OfflineBackend(model, dt=0.01)
    be.reset(np.zeros(model.state_dim))
    be.apply(np.array([2.0, 1.0]))
    for _ in range(10):
        meas = be.read()
    assert np.all(np.isfinite(meas.state()))
    be.close()
