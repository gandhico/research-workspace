"""Smoke test for the four core interfaces (brief §5).

Proves Model x Backend x Controller x Application compose and run a closed loop
offline with no conditionals — the contract the whole project rests on.
"""
import numpy as np

from aero2.applications.base import Application, ClosedLoopRecord
from aero2.control.base import BaseController, Controller, Reference
from aero2.execution.backend import Backend, Measurement
from aero2.execution.offline import OfflineBackend
from aero2.io.state_estimation import PassThroughEstimator, StateEstimator
from aero2.models.base import Model


class DoubleIntegrator2DOF(Model):
    """Trivial decoupled double integrator in the canonical 4-state layout."""
    state_dim, input_dim, output_dim = 4, 2, 2
    name = "double_integrator"

    def f(self, x, u, t=0.0):
        x = np.asarray(x, float); u = np.asarray(u, float)
        return np.array([x[1], u[0], x[3], u[1]])

    def output(self, x):
        x = np.asarray(x, float)
        return np.array([x[0], x[2]])


class ZeroController(BaseController):
    name = "zero"

    def compute(self, x_est, ref, dt):
        self.info = {"dt": dt}
        return np.zeros(2)


class HoldZeroApp(Application):
    name = "hold_zero"

    def reference(self, t):
        return Reference(theta=0.0, psi=0.0)


def test_protocol_membership():
    assert isinstance(OfflineBackend(DoubleIntegrator2DOF()), Backend)
    assert isinstance(ZeroController(), Controller)
    assert isinstance(PassThroughEstimator(), StateEstimator)


def test_offline_closed_loop_runs():
    model = DoubleIntegrator2DOF()
    backend = OfflineBackend(model, dt=0.01)
    app = HoldZeroApp(duration_s=0.1, nominal_hz=100.0)

    rec = app.run(backend, ZeroController())

    assert isinstance(rec, ClosedLoopRecord)
    assert len(rec.t) >= 9                      # ~10 cycles over 0.1 s
    assert np.isclose(rec.realized_hz, 100.0, atol=1.0)
    # zero command from rest -> state stays at origin
    assert np.allclose(rec.x_est[-1], np.zeros(4))


def test_linearize_default_jacobian():
    A, B, C, D = DoubleIntegrator2DOF().linearize(np.zeros(4), np.zeros(2))
    assert A.shape == (4, 4) and B.shape == (4, 2) and C.shape == (2, 4)
    # d(theta_dot)/d(u_p) = 1
    assert np.isclose(B[1, 0], 1.0, atol=1e-4)
    assert np.isclose(C[0, 0], 1.0, atol=1e-4)


def test_measurement_state_helper():
    m = Measurement(t=0.0, theta=0.1, psi=0.2, theta_dot=0.3, psi_dot=0.4)
    assert np.allclose(m.state(), [0.1, 0.3, 0.2, 0.4])
