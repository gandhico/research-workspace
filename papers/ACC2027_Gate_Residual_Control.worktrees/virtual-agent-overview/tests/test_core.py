import unittest
import numpy as np

from gra_control.gate import CMGResidualAugmentor, GateStateAugmentor
from gra_control.hardware_bridges import qcar_bridge


class GateControllerTests(unittest.TestCase):
    def test_zero_beta_preserves_baseline(self):
        gate = CMGResidualAugmentor(2, np.array([1.0, 2.0]), beta=0.0)
        baseline = np.array([0.25, -0.50])
        out = gate.step(baseline, 0.001)
        np.testing.assert_allclose(out.command, baseline)

    def test_output_is_bounded(self):
        gate = CMGResidualAugmentor(1, np.array([0.2]), beta=1.0)
        for _ in range(500):
            out = gate.step(np.array([0.2]), 0.001)
        self.assertLessEqual(abs(out.command[0]), 0.2)

    def test_hardware_bridge_is_disarmed_by_default(self):
        bridge = qcar_bridge()
        result = bridge.step(np.array([0.1]), np.array([0.2]), 0.01)
        np.testing.assert_allclose(result.command, 0.0)
        self.assertFalse(result.armed)

    def test_legacy_gate_state_name_is_compatible_alias(self):
        self.assertIs(GateStateAugmentor, CMGResidualAugmentor)


if __name__ == "__main__":
    unittest.main()
