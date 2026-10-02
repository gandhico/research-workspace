import unittest
from pathlib import Path

import numpy as np

from dilisic.experiments.flexible_arm_mas import run


class ExperimentTests(unittest.TestCase):
    def test_multi_agent_quick_run_writes_csv(self):
        output = Path.cwd() / "runs" / "test_experiment"
        result = run(duration=0.02, dt=0.001, output=output, plot=False)
        csv_path = Path(result["csv"])
        self.assertTrue(csv_path.exists())
        data = np.genfromtxt(csv_path, delimiter=",", names=True)
        self.assertGreaterEqual(data.size, 2)
        self.assertAlmostEqual(float(data["t"][0]), 0.0)
        self.assertAlmostEqual(float(data["t"][-1]), 0.02)
        self.assertTrue(np.isfinite(result["final_com_error"]))
        self.assertTrue(np.isfinite(result["max_weight_norm"]))


if __name__ == "__main__":
    unittest.main()
