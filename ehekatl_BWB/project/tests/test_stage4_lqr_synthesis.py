import unittest

import numpy as np

from scripts.synthesize_stage4_lqr import augment_delay, augment_delay_mismatch, c2d_rk4, scalar_rate_design, solve_dare


class Stage4SynthesisTests(unittest.TestCase):
    def test_delay_augmentation_and_lqr_stabilization(self):
        ac = np.array([[0.0, 1.0], [-2.0, -0.2]])
        bc = np.array([[0.0], [-200.0]])
        ad, bd = c2d_rk4(ac, bc)
        aa, ba = augment_delay(ad, bd, 3)
        self.assertEqual(aa.shape, (5, 5))
        gain, _ = solve_dare(aa, ba, np.diag([0.25, 0.25, 0, 0, 0]), np.array([[1 / 0.003**2]]))
        self.assertLess(np.max(np.abs(np.linalg.eigvals(aa - ba @ gain))), 1.0)

    def test_delay_mismatch_uses_common_history_dimension(self):
        ad = np.eye(2)
        bd = np.ones((2, 1))
        matrices = [augment_delay_mismatch(ad, bd, delay) for delay in (2, 3, 4)]
        self.assertTrue(all(a.shape == (6, 6) and b.shape == (6, 1) for a, b in matrices))
        self.assertTrue(np.all(matrices[0][0][:2, 3] == 1.0))
        self.assertTrue(np.all(matrices[2][0][:2, 5] == 1.0))

    def test_rate_design_has_no_angle_state(self):
        aa, ba, _, _, gain = scalar_rate_design(-0.2, -200.0)
        self.assertEqual(aa.shape, (4, 4))
        self.assertEqual(ba.shape, (4, 1))
        self.assertEqual(gain.shape, (1, 4))
        self.assertLess(np.max(np.abs(np.linalg.eigvals(aa - ba @ gain))), 1.0)


if __name__ == "__main__":
    unittest.main()
