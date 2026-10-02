import unittest

import numpy as np

from scripts.identify_stage3_models import autocorrelations


class Stage3IdentificationTests(unittest.TestCase):
    def test_residual_autocorrelation_count_and_bounds(self):
        values = np.asarray([1.0, -1.0, 0.5, -0.5, 0.25, -0.25])
        result = autocorrelations(values, 3)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(-1.0 <= value <= 1.0 for value in result))


if __name__ == "__main__":
    unittest.main()
