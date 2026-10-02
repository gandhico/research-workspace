import ast
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_rich_r3_roll_deepc_observe_xp12.py"


class TestR3RollDeePCObserve(unittest.TestCase):
    def test_runner_has_no_engagement_or_control_write_calls(self):
        source = RUNNER.read_text()
        tree = ast.parse(source)
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        self.assertNotIn("sendCTRL", attributes)
        self.assertNotIn("sendDREF", attributes)
        self.assertNotIn("--engage", source)
        self.assertIn('"controls_sent": 0', source)
        self.assertIn('"ownership_requested": 0', source)

    def test_history_fields_are_ordered(self):
        spec = importlib.util.spec_from_file_location("deepc_observe_runner", RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.history_fields("x", [1, 2, 3]), {"x_0": 1.0, "x_1": 2.0, "x_2": 3.0})

    def test_cli_is_observe_only(self):
        spec = importlib.util.spec_from_file_location("deepc_observe_runner_cli", RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        options = {option for action in module.parser()._actions for option in action.option_strings}
        self.assertNotIn("--engage", options)
        self.assertIn("--out", options)


if __name__ == "__main__":
    unittest.main()
