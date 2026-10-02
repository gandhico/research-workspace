import unittest
import inspect
import json
from pathlib import Path
from lqr.discrete_cascade_roll_lqr import COMMAND_LIMIT,SLEW_LIMIT,DiscreteCascadeRollLQR
from scripts import run_rich_r3_roll_lqr_observe_xp12,run_rich_r3_roll_lqr_pilot_xp12
from scripts import design_rich_r3_roll_lqr_disturbance
class DiscreteCascadeRollLQRTests(unittest.TestCase):
 def test_zero_state_zero_command(self):self.assertEqual(DiscreteCascadeRollLQR().update(0,0,0)['command'],0)
 def test_magnitude_and_slew_are_bounded(self):
  c=DiscreteCascadeRollLQR();values=[c.update(100,1,1)['command'] for _ in range(20)]
  self.assertTrue(all(abs(x)<=COMMAND_LIMIT for x in values));self.assertTrue(all(abs(b-a)<=SLEW_LIMIT+1e-15 for a,b in zip([0]+values,values)))
 def test_reset_clears_command_memory(self):
  c=DiscreteCascadeRollLQR();c.update(1,0,0);c.reset();self.assertEqual(c.previous_command,0)
 def test_observe_integration_has_no_control_send_path(self):
  source=inspect.getsource(run_rich_r3_roll_lqr_observe_xp12);self.assertNotIn('sendCTRL',source);self.assertNotIn('sendDREF',source);self.assertNotIn('--engage',source)
 def test_pilot_defaults_observe_and_requires_explicit_engagement(self):
  args=run_rich_r3_roll_lqr_pilot_xp12.parser().parse_args(['--out','unused.csv']);self.assertFalse(args.engage)
 def test_pilot_has_permanent_fallback_and_restoration(self):
  source=inspect.getsource(run_rich_r3_roll_lqr_pilot_xp12);self.assertIn("if reason and not latch",source);self.assertNotIn('latch=False',source.split('while time.monotonic()-start<a.duration:',1)[1]);self.assertIn('if owned:',source);self.assertIn('ROLL_OVERRIDE,0',source);self.assertIn('PITCH_OVERRIDE,0',source)
 def test_frozen_disturbance_is_small_paired_and_bounded(self):
  d=design_rich_r3_roll_lqr_disturbance;self.assertEqual(d.AMPLITUDE,5e-5);self.assertEqual(d.DURATION,.2);self.assertEqual(d.disturbance(d.STARTS[0]+d.DURATION/2),d.AMPLITUDE);self.assertEqual(d.disturbance(d.STARTS[1]+d.DURATION/2),-d.AMPLITUDE)
 def test_matched_options_remain_explicit_and_default_off(self):
  p=run_rich_r3_roll_lqr_pilot_xp12.parser();a=p.parse_args(['--out','unused.csv']);self.assertEqual(a.controller,'lqr');self.assertFalse(a.disturbance);self.assertFalse(a.engage)
 def test_baseline_startup_transfer_uses_unchanged_limits(self):
  source=inspect.getsource(run_rich_r3_roll_lqr_pilot_xp12);self.assertIn('bounded_baseline_perturbation-SLEW_LIMIT',source);self.assertIn('min(COMMAND_LIMIT,fallback_roll',source)
 def test_failed_pair_score_gate_remains_frozen(self):
  source=inspect.getsource(__import__('scripts.score_rich_r3_roll_matched_pair',fromlist=['main']));self.assertIn("integral_improvement':integral<=.70",source)
 def test_statistical_redesign_does_not_replace_failed_score(self):
  source=inspect.getsource(__import__('scripts.design_rich_r3_roll_statistical_comparison',fromlist=['main']));self.assertIn('proposal_not_flight_authorized',source);self.assertIn("upper confidence bound for LQR/baseline integral ratio <1.0",source)
 def test_power_audit_is_deterministic_and_requires_eighty_percent(self):
  source=inspect.getsource(__import__('scripts.audit_rich_r3_roll_statistical_power',fromlist=['main']));self.assertIn('default_rng(20260712)',source);self.assertIn("'required_power':.8",source)
 def test_pulse_count_audit_caps_initial_search_at_48(self):
  module=__import__('scripts.audit_rich_r3_roll_pulse_count_power',fromlist=['main']);self.assertEqual(module.COUNTS,(6,12,24,48));self.assertEqual(module.TRIALS,300)
 def test_highrate_logger_includes_propulsion_scheduling_channels(self):
  fields={x[0] for x in __import__('scripts.run_rich_r3_roll_highrate_observe_xp12',fromlist=['FIELDS']).FIELDS};self.assertTrue({'alpha_deg','tas_m_s','air_density_kg_m3','cockpit_throttle_engine_0','hardware_throttle_engine_0','engine_used_ratio_0','throttle_engine_0','throttle_engine_1','throttle_used_engine_0','throttle_used_engine_1','n1_engine_0_pct','n1_engine_1_pct','thrust_engine_0_n','thrust_engine_1_n'}<=fields)
 def test_r4_fastpath_has_hard_run_caps_and_lower_excitation(self):
  c=json.loads((Path(__file__).parents[1]/'configs/rich_R4_roll_fastpath.json').read_text());self.assertEqual(c['excitation']['amplitude'],.0001);self.assertEqual(c['hard_stop_rules']['maximum_design_identification_runs'],1);self.assertEqual(c['hard_stop_rules']['maximum_confirmation_runs'],1)
 def test_r4_observe_wrapper_cannot_engage(self):
  source=(Path(__file__).parents[1]/'scripts/run_rich_r4_roll_dualrate_observe.sh').read_text();self.assertNotIn('--engage',source);self.assertIn('rich_R4_roll_highrate_design.json',source)
if __name__=='__main__':unittest.main()
