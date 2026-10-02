from __future__ import annotations

import unittest

import numpy as np

from elevon_allocation.allocator import BoxQPAllocator, EffectivenessModel


class AllocatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = EffectivenessModel.research_prior()

    def test_limits_and_slew_are_enforced(self) -> None:
        allocator = BoxQPAllocator(self.model, 1.0 / 35.0)
        first = allocator.allocate(np.array([50.0, 50.0, 30.0])).command
        self.assertTrue(np.all(np.abs(first) <= allocator.rate_limits / 35.0 + 1e-12))
        for _ in range(80):
            previous = allocator.previous.copy()
            current = allocator.allocate(np.array([50.0, 50.0, 30.0])).command
            self.assertTrue(np.all(np.abs(current) <= allocator.command_limits + 1e-12))
            self.assertTrue(np.all(np.abs(current - previous) <= allocator.rate_limits / 35.0 + 1e-12))

    def test_failed_surface_is_zero(self) -> None:
        allocator = BoxQPAllocator(self.model, 1.0 / 35.0)
        allocator.configure_failure("elevon_L4", 0.0)
        for _ in range(20):
            result = allocator.allocate(np.array([35.0, 10.0, 5.0]))
            self.assertEqual(result.command[3], 0.0)

    def test_symmetric_pitch_and_antisymmetric_roll(self) -> None:
        allocator = BoxQPAllocator(self.model, 1.0 / 35.0)
        for _ in range(30):
            pitch = allocator.allocate(np.array([0.0, 20.0, 0.0])).command
        self.assertGreater(np.mean(pitch[:8]), 0.0)
        allocator.reset()
        for _ in range(30):
            roll = allocator.allocate(np.array([20.0, 0.0, 0.0])).command
        self.assertLess(np.mean(roll[:4]), 0.0)
        self.assertGreater(np.mean(roll[4:8]), 0.0)


if __name__ == "__main__":
    unittest.main()
