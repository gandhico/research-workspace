import unittest

import numpy as np

from elevon_allocation.allocator import EffectivenessModel
from elevon_allocation.mission_comparison import DT, ThesisGroupedACS, simulate_architecture


class MissionComparisonTests(unittest.TestCase):
    def test_thesis_grouping_matches_primary_surface_roles(self):
        allocator = ThesisGroupedACS(EffectivenessModel.research_prior(), DT)
        grouping = allocator.grouping
        np.testing.assert_array_equal(grouping[[0, 1, 4, 5], 0], np.ones(4))
        np.testing.assert_array_equal(grouping[[2, 3], 1], -np.ones(2))
        np.testing.assert_array_equal(grouping[[6, 7], 1], np.ones(2))
        np.testing.assert_array_equal(grouping[[8, 9], 2], np.ones(2))

    def test_distributed_allocation_improves_post_fault_tracking(self):
        grouped, _ = simulate_architecture("thesis_grouped_acs", seed=20260917)
        distributed, _ = simulate_architecture("distributed_elevon_qp", seed=20260917)
        self.assertLess(distributed.post_fault_rmse_deg, grouped.post_fault_rmse_deg)
        self.assertLess(distributed.allocation_rmse_deg_s2, grouped.allocation_rmse_deg_s2)


if __name__ == "__main__":
    unittest.main()
