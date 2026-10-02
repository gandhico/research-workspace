import unittest
from pathlib import Path
from scripts.analyze_stage5_model_residual import ROOT

class Stage5ResidualTests(unittest.TestCase):
    def test_stage3_model_artifact_exists(self):
        self.assertTrue((ROOT/'configs/stage3_models.json').is_file())

if __name__=='__main__': unittest.main()
