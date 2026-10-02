import unittest
from pathlib import Path

import numpy as np

from dilisic.experiments.flexible_arm_mas import run
from dilisic.experiments.plot_flexible_arm_mas import summarize


class DILISICPlotTests(unittest.TestCase):
    def test_summary_reads_experiment_csv(self):
        output = Path.cwd() / "runs" / "test_dilisic_plot"
        result = run(duration=0.02, dt=0.001, output=output, plot=False)
        summary = summarize(Path(result["csv"]))
        self.assertEqual(summary["samples"], 21.0)
        self.assertTrue(np.isfinite(summary["max_abs_control"]))
        self.assertTrue(np.isfinite(summary["max_position_spread"]))


if __name__ == "__main__":
    unittest.main()
