import unittest

import numpy as np

from deepc.src.regularized_deepc import RegularizedDeePC, block_hankel


class TestRegularizedDeePC(unittest.TestCase):
    def test_hankel_shape(self):
        matrix = block_hankel(np.arange(10.0), 4)
        self.assertEqual(matrix.shape, (4, 7))

    def test_optimizer_respects_constraints(self):
        rng = np.random.default_rng(4)
        u = rng.normal(scale=0.2, size=200)
        y = np.zeros_like(u)
        for index in range(1, len(y)):
            y[index] = 0.7 * y[index - 1] + 0.4 * u[index - 1]
        controller = RegularizedDeePC(u, y, 5, 8, 1.0)
        result = controller.optimize(
            u[-5:], y[-5:], np.zeros(8), input_limit=0.1, slew_limit=0.02
        )
        self.assertTrue(result.converged)
        self.assertLessEqual(result.maximum_input, 0.1 + 1e-12)
        self.assertLessEqual(result.maximum_slew, 0.02 + 1e-12)


if __name__ == "__main__":
    unittest.main()

