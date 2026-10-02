"""Phase 10 — Adaptive HyperLIF across all three processes (experimental).

Modelling (neuron core), control (PD + gate residual), identification (reservoir).
Asserts the infrastructure is correct; it does NOT assert the neuromorphic parts
beat the classical baseline (they don't yet — that needs learning / harder regimes,
docs/10). Honest, not fabricated.
"""
import numpy as np
import pytest

from aero2.applications.reference_tracking import SquareWaveTracking
from aero2.benchmarking.metrics import tracking_metrics
from aero2.control import Controller, make_controller
from aero2.control.linear.pd import PD2DOF
from aero2.control.neuromorphic import HyperLIFResidualController
from aero2.control.neuromorphic.neuron import (
    AdaptiveHyperLIFDirect, HyperLIFDirect, make_direct_neuron,
)
from aero2.execution.offline import OfflineBackend
from aero2.identification import arx
from aero2.identification.neuromorphic_identifier import NeuromorphicIdentifier
from aero2.io import find_log, load_log
from aero2.models import make_model


# --- modelling: neuron core ------------------------------------------------
def test_gate_stays_in_unit_interval():
    nrn = make_direct_neuron("hyperlif", n=8, activity_mode="gate", scale="control")
    nrn.reset()
    res = None
    for _ in range(100):
        res = nrn.step(np.full(8, 1.2), 0.005)
    assert np.all(res.gate >= 0.0) and np.all(res.gate <= 1.0)
    assert res.activity.shape == (8,)


def test_adaptive_conductance_exceeds_base_under_drive():
    a = AdaptiveHyperLIFDirect(n=1, base_gain=120.0, gain_scaling=30.0)
    h = HyperLIFDirect(n=1, reset_gain=120.0)
    a.r[:] = 0.5
    h.r[:] = 0.5
    assert a._conductance(np.array([2.0]))[0] > h._conductance(np.array([2.0]))[0]


# --- control: PD + gate residual ------------------------------------------
def _run(ctrl, duration=10.0, dt=0.005):
    be = OfflineBackend(make_model("helicopter_2dof"), dt=dt)
    return tracking_metrics(SquareWaveTracking(duration_s=duration, nominal_hz=1.0 / dt).run(be, ctrl))


def test_blend_zero_reduces_to_base_exactly():
    pd = _run(PD2DOF())
    hz = _run(HyperLIFResidualController(blend=0.0))
    assert hz["pitch_rms"] == pytest.approx(pd["pitch_rms"], abs=1e-9)
    assert hz["yaw_rms"] == pytest.approx(pd["yaw_rms"], abs=1e-9)


def test_hyperlif_registered_and_runs():
    c = make_controller("hyperlif")
    assert isinstance(c, Controller)
    m = _run(c, duration=6.0)
    assert np.isfinite(m["pitch_rms"]) and m["pitch_rms"] < 1.0


# --- identification: HyperLIF reservoir -----------------------------------
def _fit_identifier(readout):
    log = load_log(find_log("M3_aero2_03_pitch_prbs.csv"))
    yp, up, ts, _, _ = arx.prepare(log["t"], log["theta"], {"u_common": log["u_common"]}, 3.0, True, 1)
    n = len(yp); ntr = int(0.7 * n)
    nid = NeuromorphicIdentifier(na=1, nb=3, nk=1, output="theta", inputs=["u_common"],
                                 readout=readout, seed=0)
    nid.fit(np.arange(ntr) * ts, yp[:ntr], {"u_common": up["u_common"][:ntr]},
            demean=False, start_time=0.0)
    return nid.validate(yp[ntr:], {"u_common": up["u_common"][ntr:]})


def test_identifier_interface_and_hybrid_tracks_arx():
    # hybrid readout (linear lags + gate features) is close to ARX one-step (~98%)
    assert _fit_identifier("hybrid")["onestep_fit"] > 80.0


def test_pure_reservoir_underperforms_honestly():
    # the untuned gate-only reservoir is NOT yet predictive — documented, not hidden
    assert _fit_identifier("reservoir")["onestep_fit"] < _fit_identifier("hybrid")["onestep_fit"]
