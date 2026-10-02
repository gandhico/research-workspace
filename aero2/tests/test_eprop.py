"""Python e-prop architecture — gradient-correctness validation (vs finite differences).

Mirrors the Julia gate-eligibility validation (METHODS.md §3.1): the architecture
is proven by matching finite-difference gradients, not by a tuned learning result.
"""
import numpy as np
import pytest

from aero2.control.neuromorphic.eprop import EpropSNN, HyperLIFParams

SOFT = dict(tau=1.0, tau_r=0.3, alpha=8.0, gamma=1.0, g_base=8.0, beta=2.0, dt=0.2)


def _cos(a, b):
    return float((a * b).sum() / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def _fd(net, U, Y, arr, eps=1e-6):
    g = np.zeros_like(arr)
    it = np.nditer(arr, flags=["multi_index"])
    for _ in it:
        k = it.multi_index
        o = arr[k]
        arr[k] = o + eps; Lp = net.loss(U, Y)
        arr[k] = o - eps; Lm = net.loss(U, Y)
        arr[k] = o
        g[k] = (Lp - Lm) / (2 * eps)
    return g


def _small_net_data():
    net = EpropSNN(2, (4,), 1, params=HyperLIFParams(**SOFT),
                   psi_rule="gate_exact", credit="exact", hidden_bias=1.0, seed=1)
    rng = np.random.default_rng(0)
    return net, rng.uniform(-1, 1, (15, 2)), rng.uniform(-0.5, 0.5, (15, 1))


def test_gate_exact_equals_gate_jacobian():
    p = HyperLIFParams()
    kappa = np.exp(-p.dt / p.tau_r)

    def r_next(v, r):
        eff = p.v_thresh - p.gamma * r
        rstar = 1 / (1 + np.exp(-p.alpha * (v - eff)))
        return r * kappa + rstar * (1 - kappa)

    v, r, eps = 0.4, 0.2, 1e-6
    eff = p.v_thresh - p.gamma * r
    rstar = 1 / (1 + np.exp(-p.alpha * (v - eff)))
    psi = (1 - kappa) * p.alpha * rstar * (1 - rstar)
    fd = (r_next(v + eps, r) - r_next(v - eps, r)) / (2 * eps)
    assert abs(psi - fd) / abs(fd) < 1e-5            # exact gate Jacobian


def test_readout_gradient_is_exact():
    net, U, Y = _small_net_data()
    dWo, _, _, _ = net.gradients(U, Y)
    assert _cos(dWo, _fd(net, U, Y, net.W_out)) > 0.9999


def test_hidden_gradient_matches_bptt():
    net, U, Y = _small_net_data()
    _, _, dW, _ = net.gradients(U, Y)
    assert _cos(dW[0], _fd(net, U, Y, net.layers[0].W)) > 0.8   # e-prop ≈ BPTT


def test_eprop_learns():
    rng = np.random.default_rng(0)
    U = rng.uniform(-1.2, 1.2, (300, 3))
    Y = (0.5 * np.tanh(2 * U[:, 0]) + 0.3 * U[:, 1] - 0.2 * U[:, 2] ** 2).reshape(-1, 1)
    net = EpropSNN(3, (32,), 1, params=HyperLIFParams(**SOFT),
                   psi_rule="gate_exact", credit="exact", hidden_bias=1.0, seed=2)
    L = net.fit(U, Y, epochs=150, lr=0.5, clip=10.0)
    assert L[-1] < 0.9 * L[0]                         # clearly decreases


@pytest.mark.parametrize("credit", ["exact", "dfa", "ss"])
def test_credit_routings_run(credit):
    rng = np.random.default_rng(0)
    U = rng.uniform(-1, 1, (40, 3))
    Y = rng.uniform(-0.5, 0.5, (40, 1))
    net = EpropSNN(3, (8,), 1, params=HyperLIFParams(**SOFT),
                   psi_rule="surrogate", credit=credit, hidden_bias=1.0, seed=1)
    L = net.fit(U, Y, epochs=10, lr=0.2)
    assert np.all(np.isfinite(L))
