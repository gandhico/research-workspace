import ast,importlib.util,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];RUNNER=ROOT/'scripts/run_rich_r3_roll_deepc_pilot_xp12.py'
class TestR3RollDeePCPilot(unittest.TestCase):
 def load(self):
  spec=importlib.util.spec_from_file_location('deepc_pilot',RUNNER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_engagement_is_explicit(self):
  m=self.load();opts={o for a in m.parser()._actions for o in a.option_strings};self.assertIn('--engage',opts);self.assertFalse(m.parser().parse_args(['--out','x']).engage)
 def test_writes_are_guarded_and_restoration_is_finally_scoped(self):
  source=RUNNER.read_text();tree=ast.parse(source);self.assertIn('finally:',source);self.assertIn("if a.engage:c.sendCTRL",source);self.assertIn("DEEPC FALLBACK LATCHED",source);self.assertIn("Both-axis ownership: RESTORED",source);self.assertGreaterEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='sendDREF' for n in ast.walk(tree)),6)
 def test_frozen_protocol_is_conservative(self):
  c=json.loads((ROOT/'deepc/configs/rich_R3_deepc_pilot.json').read_text());self.assertEqual(c['disturbance']['amplitude'],.00005);self.assertEqual(c['limits']['command'],.0002);self.assertEqual(c['limits']['slew_per_sample'],.00005);self.assertEqual(c['held_out_response_files_opened'],[])
if __name__=='__main__':unittest.main()
