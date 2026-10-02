"""Phase 5 identification tests — reproduce Table II behavior from migrated logs."""
import numpy as np
import pytest

from aero2.identification import arx, excitation, ss_realize, validation
from aero2.io import find_log, load_log


def _fit_pitch(val_frac=0.30):
    log = load_log(find_log("M3_aero2_03_pitch_prbs.csv"))
    y, u, ts, _, _ = arx.prepare(log["t"], log["theta"], {"u_common": log["u_common"]},
                                 start_time=3.0, demean=True)
    Z, Y, start = arx.build_regressor(y, u, na=1, nb=3, nk=1)
    ntr = int((1 - val_frac) * len(Y))
    theta, rank, cond = arx.estimate_ls(Z[:ntr], Y[:ntr])
    model = arx.ArxModel("theta", ["u_common"], 1, 3, 1, theta, ts, rank=rank, cond=cond)
    onestep = arx.fit_metric(Y[ntr:], Z[ntr:] @ theta)
    return model, y, u, start, ntr, onestep


# --- ARX reproduces Table II pitch SISO -----------------------------------
def test_pitch_siso_reproduces_table_ii():
    model, y, u, start, ntr, onestep = _fit_pitch()
    assert onestep == pytest.approx(98.23, abs=1.0)            # Table II: 98.231 %
    ysim = arx.free_run_simulate(model, y, u)
    freerun = arx.fit_metric(y[start + ntr:], ysim[start + ntr:])
    assert freerun < onestep                                   # the central result
    assert freerun < 50.0                                      # free-run is poor


def test_fit_metric_bounds():
    y = np.array([0.0, 1.0, 2.0, 3.0, 2.0, 1.0])
    assert arx.fit_metric(y, y) == pytest.approx(100.0)        # perfect
    assert arx.fit_metric(y, np.full_like(y, y.mean())) == pytest.approx(0.0)  # mean predictor


def test_regressor_shape():
    y = np.arange(20.0)
    Z, Y, start = arx.build_regressor(y, {"u": np.ones(20)}, na=2, nb=2, nk=1)
    assert Z.shape[1] == 1 + 2 + 2                              # c + na + nb
    assert start == 2 and len(Y) == 20 - start


# --- state-space realization ----------------------------------------------
def test_darx_to_ss_and_ranks():
    A, B, C, D = ss_realize.darx_to_ss([1.0, -0.9], [0.1, 0.05, 0.01])  # na=1, nb=3
    assert A.shape[0] == 3                                       # order = max(na,nb)
    r = ss_realize.ranks(A, B, C)
    assert 0 <= r["ctrb_rank"] <= r["n"] and 0 <= r["obsv_rank"] <= r["n"]


# --- excitation ------------------------------------------------------------
def test_excitation_generators():
    p = excitation.prbs(50, amplitude=0.075, seed=1)
    assert set(np.unique(np.abs(p))) <= {0.075}
    t = np.linspace(0, 4, 400)
    d = excitation.doublet(t, 1.0, 1.0, 0.5)
    assert d.max() == 1.0 and d.min() == -1.0
    c = excitation.chirp(t, 0.1, 1.0, 6.0)
    assert np.all(np.abs(c) <= 6.0 + 1e-9)
    uL, uR = excitation.pure_differential(np.array([1.0, 2.0]))
    assert np.allclose(uL, -uR)                                  # pure differential


# --- validation helpers ----------------------------------------------------
def test_uncertainty_and_robust_check():
    G = np.array([1.0 + 0j, 2.0 + 1j])
    assert np.allclose(validation.multiplicative_uncertainty(G, G), 0.0)   # meas==nom
    assert validation.robust_stable(np.array([0.1, 0.2]), np.array([0.5, 0.5])) is True
    assert validation.robust_stable(np.array([3.0]), np.array([1.0])) is False
