"""Offline tests for the matched Nengo neuron-family residuals."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from nengo_neuron_family import FAMILIES, NengoNeuronFamilyAugmentor


HERE = Path(__file__).resolve().parent


class TestNeuronFamilies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calibration = json.loads((HERE / "feature_calibration.json").read_text(encoding="utf-8"))

    def make(self, family, mode):
        item = self.calibration["families"][family]
        return NengoNeuronFamilyAugmentor(
            family=family, limits=np.array([0.12, 0.28, 0.28]), dt=5e-4,
            mode=mode, feature_scale=item["feature_scale"],
            native_current_scale=item.get("native_current_scale", 1.0),
        )

    def test_all_families_are_finite_and_bounded(self):
        for family in FAMILIES:
            with self.subTest(family=family):
                controller = self.make(family, "pes")
                try:
                    for _ in range(800):
                        out = controller.step(
                            np.array([0.12, -0.28, 0.28]),
                            np.array([-0.8, 0.6, -0.4]),
                        )
                    diagnostic = controller.diagnostics()
                    self.assertTrue(np.all(np.isfinite(out.command)))
                    self.assertTrue(np.all(np.isfinite(diagnostic["activity"])))
                    self.assertLessEqual(np.max(np.abs(out.command)), 0.28 + 1e-12)
                    self.assertEqual(diagnostic["weights"].shape, (3, 6))
                finally:
                    controller.close()

    def test_fixed_decoder_does_not_change(self):
        for family in FAMILIES:
            with self.subTest(family=family):
                controller = self.make(family, "fixed")
                initial = controller.W
                try:
                    for _ in range(300):
                        controller.step(np.array([0.12, -0.28, 0.28]), np.ones(3))
                    np.testing.assert_allclose(controller.W, initial, atol=0, rtol=0)
                finally:
                    controller.close()


if __name__ == "__main__":
    unittest.main()
