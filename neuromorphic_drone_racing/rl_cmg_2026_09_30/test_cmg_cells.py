"""Parity and observable-bound tests for the new CMG RL study."""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

from cmg_cells import CMGPopulation, CMGParams, policy_preset

ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
sys.path.insert(0, str(ACC / "experiments" / "nengo_nef_replication_2026-08-29"))
from nengo_cmg import CoupledMembraneGate  # noqa: E402


def test_nengo_cell_parity():
    for p in (CMGParams(), policy_preset("graded")):
        cell = CMGPopulation(6, "graded", p)
        ref = CoupledMembraneGate(tau=p.tau, tau_r=p.tau_r,
                                 v_rest=p.v_rest, v_reset=p.v_reset,
                                 v_threshold=p.v_threshold, alpha=p.alpha,
                                 gamma=p.gamma, base_gain=p.base_gain,
                                 gain_scaling=p.gain_scaling,
                                 gate_gain=p.gate_gain, adaptive=p.adaptive)
        v = np.zeros(6); r = np.zeros(6); a = np.zeros(6)
        rng = np.random.default_rng(11)
        for _ in range(1200):
            j = rng.uniform(0.1, 2.5, 6)
            actual = cell.step(j, 0.0005)
            ref.step(0.0005, j, a, v, r)
            assert np.allclose(cell.v, v, atol=1e-12)
            assert np.allclose(cell.r, r, atol=1e-12)
            assert np.allclose(actual, a, atol=1e-12)


def test_event_definitions():
    p = policy_preset("graded")
    units = [CMGPopulation(1, mode, p) for mode in CMGPopulation.MODES]
    for _ in range(2000):
        for cell in units:
            cell.step(np.array([2.0]), 0.0005)
            assert 0 <= cell.r[0] <= 1
            assert 0 <= cell.features()[0] <= 1
            assert cell.last_events[0] in (0, 1)
    assert np.allclose(units[0].v, units[1].v)
    assert np.allclose(units[0].r, units[1].r)
    assert np.allclose(units[2].v, units[3].v)
    assert np.allclose(units[2].r, units[3].r)
    assert units[3].event_total[0] >= units[1].event_total[0]


if __name__ == "__main__":
    test_nengo_cell_parity()
    test_event_definitions()
    print("CMG parity and observable checks passed")
