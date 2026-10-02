"""Phase 7 full controller suite: LQR/LQG/MPC + nonlinear, offline + estimator-in-loop."""
import numpy as np
import pytest

from aero2.applications.reference_tracking import SquareWaveTracking
from aero2.benchmarking.metrics import tracking_metrics
from aero2.control import CONTROLLERS, make_controller
from aero2.execution.offline import OfflineBackend
from aero2.io import make_estimator
from aero2.models import make_model


def _run(controller, duration=8.0, dt=0.005, estimator="passthrough", emit_gyro=False):
    be = OfflineBackend(make_model("helicopter_2dof"), dt=dt, emit_gyro=emit_gyro)
    app = SquareWaveTracking(duration_s=duration, nominal_hz=1.0 / dt)
    return tracking_metrics(app.run(be, controller, make_estimator(estimator)))


@pytest.mark.parametrize("name", sorted(CONTROLLERS))
def test_controller_runs_offline(name):
    m = _run(make_controller(name))
    assert np.isfinite(m["pitch_rms"]) and m["pitch_rms"] < 1.0
    assert 0.0 <= m["pitch_sat_frac"] <= 1.0


def test_pd_best_pitch_among_linear():
    pitch = {n: _run(make_controller(n), duration=24.0)["pitch_rms"] for n in ["pd", "lqr", "lqg", "mpc"]}
    assert pitch["pd"] == min(pitch.values())             # PD strongest on pitch (Table IV)


def test_linear_controllers_underdrive():
    # LQR/LQG/MPC avoid saturation (conservative) vs PD which drives harder
    assert _run(make_controller("lqr"), duration=24.0)["pitch_sat_frac"] == 0.0
    assert _run(make_controller("pd"), duration=24.0)["pitch_sat_frac"] > 0.0


def test_smc_yawboost_reduces_yaw_error():
    base = _run(make_controller("smc"), duration=24.0)["yaw_rms"]
    boost = _run(make_controller("smc", yawboost=True), duration=24.0)["yaw_rms"]
    assert boost < base


def test_aero2_estimator_in_loop_matches_passthrough():
    # no noise: gyro estimator recovers true rate -> backstepping (uses state rate) unchanged
    base = _run(make_controller("backstepping"), duration=12.0)["pitch_rms"]
    gyro = _run(make_controller("backstepping"), duration=12.0, estimator="aero2", emit_gyro=True)["pitch_rms"]
    assert gyro == pytest.approx(base, abs=0.02)
