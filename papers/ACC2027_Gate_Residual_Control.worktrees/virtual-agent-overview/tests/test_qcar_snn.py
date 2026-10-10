import unittest
import numpy as np

from gra_control.perception.qcar_snn import TemporalContrastLaneSNN


class QCarSNNTests(unittest.TestCase):
    def test_temporal_lane_event_decodes_right_side(self):
        snn = TemporalContrastLaneSNN(width=32, threshold=0.05, spike_threshold=1.0)
        first = np.zeros((12, 32))
        second = first.copy()
        second[:, 24:27] = 1.0
        self.assertFalse(snn.step(first).valid)
        estimate = snn.step(second)
        self.assertTrue(estimate.valid)
        self.assertGreater(estimate.lane_error, 0.0)


if __name__ == "__main__":
    unittest.main()

