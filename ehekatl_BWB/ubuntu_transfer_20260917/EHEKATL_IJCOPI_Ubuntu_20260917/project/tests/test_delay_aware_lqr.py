import unittest

from lqr.delay_aware_lqr import DelayAwareRateLQR


class DelayAwareRateLQRTests(unittest.TestCase):
    def test_zero_rate_starts_at_trim(self):
        controller = DelayAwareRateLQR("pitch", 0.15)
        total, perturbation = controller.step(0.0)
        self.assertAlmostEqual(total, 0.15)
        self.assertEqual(perturbation, 0.0)

    def test_slew_and_magnitude_are_bounded(self):
        controller = DelayAwareRateLQR("roll", 0.0)
        perturbations = [controller.step(1000.0)[1] for _ in range(20)]
        self.assertTrue(all(abs(value) <= 0.003 for value in perturbations))
        self.assertTrue(all(abs(b - a) <= 0.0005 + 1e-12 for a, b in zip([0.0] + perturbations, perturbations)))

    def test_reset_clears_delay_history_and_changes_trim(self):
        controller = DelayAwareRateLQR("roll", 0.0)
        controller.step(2.0)
        controller.reset(trim_control=0.2)
        self.assertEqual(controller.history, [0.0, 0.0, 0.0])
        self.assertEqual(controller.previous_perturbation, 0.0)
        self.assertAlmostEqual(controller.step(0.0)[0], 0.2)

    def test_additive_disturbance_is_limited_and_recorded_in_history(self):
        controller = DelayAwareRateLQR("pitch", 0.15)
        _, perturbation = controller.step(0.0, 0.0005)
        self.assertAlmostEqual(perturbation, 0.0005)
        self.assertAlmostEqual(controller.history[0], perturbation)


if __name__ == "__main__":
    unittest.main()
