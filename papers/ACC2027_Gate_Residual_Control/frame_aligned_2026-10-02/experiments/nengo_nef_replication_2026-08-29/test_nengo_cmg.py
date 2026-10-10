"""Numerical conformance tests for the Nengo CMG/PES translation."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))

from gra_control.gate import CMGResidualAugmentor  # noqa: E402
from nengo_cmg import NengoCMGPESAugmentor  # noqa: E402


class TestNengoCMG(unittest.TestCase):
    def test_pes_learning_rate_conversion(self):
        augmentor = NengoCMGPESAugmentor(3, np.ones(3), dt=5e-4, learning_rate=8e-4)
        try:
            self.assertAlmostEqual(augmentor.nengo_learning_rate, 9.6, places=12)
        finally:
            augmentor.close()

    def test_states_and_commands_match_numpy_reference(self):
        dt = 5e-4
        limits = np.array([0.10, 0.08, 0.05])
        direct = CMGResidualAugmentor(
            3, limits, "online_pes", True, beta=0.5, learning_rate=8e-4
        )
        nengo_impl = NengoCMGPESAugmentor(
            3, limits, dt=dt, beta=0.5, learning_rate=8e-4
        )
        max_command_difference = 0.0
        try:
            for i in range(1000):
                baseline = limits * np.sin(np.array([0.010, 0.013, 0.017]) * i)
                target = np.array(
                    [0.4 * np.sin(0.007 * i), -0.3 * np.cos(0.011 * i), 0.2]
                )
                direct_out = direct.step(baseline, dt, target)
                nengo_out = nengo_impl.step(baseline, target)
                np.testing.assert_allclose(direct.units.v, nengo_impl.v, atol=1e-14, rtol=0)
                np.testing.assert_allclose(direct.units.r, nengo_impl.r, atol=1e-14, rtol=0)
                np.testing.assert_allclose(
                    direct_out.activity, nengo_out.activity, atol=1e-14, rtol=0
                )
                max_command_difference = max(
                    max_command_difference,
                    float(np.max(np.abs(direct_out.command - nengo_out.command))),
                )
            self.assertLess(max_command_difference, 1e-6)
            # Nengo schedules the teaching-error connection with one simulator
            # step of graph latency; the decoder therefore agrees to within one
            # PES increment while the applied command agrees below 1e-6.
            np.testing.assert_allclose(direct.W, nengo_impl.W, atol=5e-4, rtol=0)
        finally:
            nengo_impl.close()


if __name__ == "__main__":
    unittest.main()
