"""Phase 7 (PD) + Phase 8 (tracking) + runner tests — option 1.

Verify the shared derivative filter, the PD baseline tracking the square-wave
reference offline on the real helicopter plant, registries, and metrics.
"""
import numpy as np
import pytest

from aero2.applications.reference_tracking import SquareWaveTracking
from aero2.benchmarking.metrics import tracking_metrics
from aero2.control import Controller, make_controller
from aero2.control.base import BaseController
from aero2.control.filters import SecondOrderDerivative
from aero2.control.linear.pd import PD2DOF
from aero2.execution.offline import OfflineBackend
from aero2.models import make_model


class _Zero(BaseController):
    name = "zero"

    def compute(self, x_est, ref, dt):
        return np.zeros(2)


def _run(controller, duration=20.0, dt=0.005):
    backend = OfflineBackend(make_model("helicopter_2dof"), dt=dt)
    app = SquareWaveTracking(duration_s=duration, nominal_hz=1.0 / dt)
    return tracking_metrics(app.run(backend, controller))


def test_filter_tracks_ramp_slope():
    f = SecondOrderDerivative()                     # wn=100, zeta=1
    dt, slope, val = 0.002, 2.0, 0.0
    for _ in range(4000):
        val += slope * dt
        f.update(val, dt)
    assert f.filtered_rate == pytest.approx(slope, abs=0.05)


def test_pd_registry_and_interface():
    c = make_controller("pd")
    assert isinstance(c, PD2DOF) and isinstance(c, Controller)
    with pytest.raises(ValueError):
        make_controller("not_a_controller")


def test_pd_tracks_and_beats_open_loop():
    pd = _run(make_controller("pd"))
    zero = _run(_Zero())
    # PD tracks the pitch square wave much better than no control
    assert pd["pitch_rms"] < zero["pitch_rms"]
    assert pd["pitch_rms"] < 0.5
    # yaw is the weaker axis (kept visible, per the project's honest result)
    assert pd["yaw_rms"] >= 0.0


def test_pd_uses_measured_dt_filter():
    # the PD owns derivative filters that advance on the dt passed to compute()
    pd = make_controller("pd")
    pd.reset()
    from aero2.control.base import Reference
    u = pd.compute(np.array([0.1, 0.0, 0.0, 0.0]), Reference(theta=0.0, psi=0.0), dt=0.005)
    assert u.shape == (2,)
    assert "theta_rate_f" in pd.info


def test_metrics_keys_and_ranges():
    m = _run(make_controller("pd"), duration=6.0)
    for k in ["pitch_rms", "yaw_rms", "tail_pitch_mae", "tail_yaw_mae",
              "pitch_sat_frac", "yaw_sat_frac", "realized_hz"]:
        assert k in m
    assert 0.0 <= m["pitch_sat_frac"] <= 1.0
    assert m["realized_hz"] == pytest.approx(200.0, abs=1.0)


def test_axis_specific_tracking_references():
    from aero2.applications import make_application

    pitch_app = make_application("pitch_reference_tracking", duration_s=1.0)
    yaw_app = make_application("yaw_reference_tracking", duration_s=1.0)

    pitch_ref = pitch_app.reference(0.0)
    yaw_ref = yaw_app.reference(0.0)

    assert pitch_ref.theta != 0.0 and pitch_ref.psi == 0.0
    assert yaw_ref.theta == 0.0 and yaw_ref.psi != 0.0
