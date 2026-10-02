import inspect, json, unittest
from pathlib import Path
from scripts.rich_mission import gate_reasons, load_campaign, run_manifest
from scripts import run_rich_mission_observe_xp12
from scripts import run_rich_r3_roll_highrate_observe_xp12
from scripts import run_rich_r3_roll_dualrate_xp12

class RichMissionTests(unittest.TestCase):
    def setUp(self): self.campaign=load_campaign()
    def sample(self):
        return {"altitude_m":1700,"ias_kts":39,"pitch_deg":1,"roll_deg":0,"p_deg_s":0,"q_deg_s":0,"r_deg_s":0,"art_stab_on":1,"paused":0,"sim_speed":1,"replay":0,"override_joystick":0,"override_roll":0,"override_pitch":0,"override_flightcontrol":0,"override_surfaces":0}
    def test_six_regimes_and_frozen_allocation(self):
        manifest=run_manifest(self.campaign)
        self.assertEqual(len(manifest),54)
        self.assertEqual(sum(x["partition"]=="validation" for x in manifest),24)
        self.assertEqual(len({x["run_id"] for x in manifest}),54)
        self.assertEqual(self.campaign["baseline"]["identification_amplitude"],0)
        self.assertEqual(self.campaign["baseline"]["recovery_pulse_amplitude"],0)
    def test_reference_regime_gate_passes(self): self.assertEqual(gate_reasons(self.campaign,"R3",self.sample()),[])
    def test_gate_rejects_wrong_regime_and_override(self):
        sample=self.sample();sample["ias_kts"]=48;sample["override_pitch"]=1
        reasons=gate_reasons(self.campaign,"R3",sample)
        self.assertIn("IAS outside regime envelope",reasons);self.assertIn("control override already active",reasons)
    def test_observe_runner_has_no_control_send_path(self):
        source=inspect.getsource(run_rich_mission_observe_xp12)
        self.assertNotIn("sendCTRL",source);self.assertNotIn("sendDREF",source);self.assertNotIn("--engage",source)
    def test_r3_excitation_design_uses_smallest_passing_candidates(self):
        design=json.loads(Path('configs/rich_R3_excitation_design.json').read_text())
        self.assertEqual(design['axes']['pitch']['selected_amplitude'],.001)
        self.assertEqual(design['axes']['roll']['selected_amplitude'],.0002)
        for axis in ('pitch','roll'):
            selected=design['axes'][axis]['selected_nominal_response']
            self.assertGreaterEqual(selected['minimum_input_spectral_snr'],2)
            self.assertGreaterEqual(selected['predicted_rate_snr'],5)
            self.assertEqual(design['axes'][axis]['uncertainty_delay_cases'],81)
    def test_revised_pitch_design_passes_retention_and_uncertainty_gates(self):
        design=json.loads(Path('configs/rich_R3_pitch_revised_design.json').read_text())
        self.assertEqual(design['frequencies_hz'],[.35,.55,.8,1.1])
        self.assertEqual(design['amplitude'],.001)
        self.assertGreaterEqual(design['minimum_projected_input_spectral_snr'],2)
        self.assertEqual(design['uncertainty_delay_cases'],81)
        self.assertLess(design['uncertainty_peak_rate_range_deg_s'][1],20)
    def test_r3_pitch_model_is_training_only_and_delay_frozen(self):
        model=json.loads(Path('configs/rich_R3_pitch_model.json').read_text())
        self.assertEqual(model['validation_files_opened'],[])
        self.assertEqual(model['selected']['name'],'local')
        self.assertEqual(model['selected']['delay_samples'],3)
        self.assertEqual(model['selected']['fields'],['pitch_deg','q_deg_s','total_pitch_ratio'])
    def test_r3_pitch_confirmation_gate_requires_new_no_refit_run(self):
        gate=json.loads(Path('configs/rich_R3_pitch_validation_gate.json').read_text())
        self.assertEqual(gate['required_new_confirmation_runs'],1)
        self.assertTrue(gate['no_refit_or_reselection'])
        self.assertLessEqual(gate['maximum_validation_to_training_qdot_nrmse_ratio'],1.15)
        self.assertLessEqual(gate['maximum_validation_to_training_recursive_mean_nrmse_ratio'],1.15)
    def test_r3_roll_training_richness_artifact_passes(self):
        result=json.loads(Path('configs/rich_R3_roll_training_01_analysis.json').read_text())
        self.assertTrue(result['pass'])
        self.assertGreaterEqual(min(result['realized_input_snr']),2)
        self.assertGreaterEqual(min(result['rate_response_snr']),5)
    def test_r3_roll_model_and_gate_are_frozen_before_validation(self):
        model=json.loads(Path('configs/rich_R3_roll_model.json').read_text());gate=json.loads(Path('configs/rich_R3_roll_validation_gate.json').read_text())
        self.assertEqual(model['validation_files_opened'],[])
        self.assertEqual(model['selected']['name'],'surface_aerodynamic')
        self.assertEqual(model['selected']['delay_samples'],0)
        self.assertTrue(gate['frozen_before_validation']);self.assertTrue(gate['no_refit_or_reselection'])
    def test_r3_roll_frf_gate_excludes_unrepeatable_low_frequencies(self):
        gate=json.loads(Path('configs/rich_R3_roll_frf_gate.json').read_text());ref=json.loads(Path('configs/rich_R3_roll_frf_reference.json').read_text())
        self.assertEqual(gate['validated_frequency_candidates_hz'],[.35,.55,.8,1.1])
        self.assertEqual(gate['excluded_low_frequencies_hz'],[.1,.2])
        self.assertEqual(gate['required_new_confirmation_runs'],1)
        self.assertEqual(ref['file'],'rich_R3_roll_training_01_20260712_184050.csv')
    def test_roll_frf_realization_is_not_promoted_to_lqr_model(self):
        result=json.loads(Path('configs/rich_R3_roll_frf_realization.json').read_text())
        self.assertEqual(result['status'],'rejected_for_state_space_lqr')
        self.assertFalse(result['dynamic_time_constant_resolved_at_10hz'])
        self.assertLess(result['best_joint_candidate']['relative_complex_rmse'],.10)
    def test_highrate_roll_runner_is_structurally_read_only(self):
        source=inspect.getsource(run_rich_r3_roll_highrate_observe_xp12)
        self.assertNotIn('sendCTRL',source);self.assertNotIn('sendDREF',source);self.assertNotIn('--engage',source)
        self.assertIn("default=35",source)
    def test_highrate_roll_design_respects_nyquist_and_amplitude(self):
        design=json.loads(Path('configs/rich_R3_roll_highrate_design.json').read_text())
        self.assertEqual(design['sample_rate_hz'],35)
        self.assertLessEqual(max(design['frequencies_hz']),.6*design['nyquist_hz'])
        self.assertEqual(design['amplitude'],.0002)
        self.assertIn('audit-only',design['derivative_policy'])
    def test_dualrate_runner_defaults_observe_only_and_preserves_rates(self):
        args=run_rich_r3_roll_dualrate_xp12.parser().parse_args(['--out','unused.csv'])
        self.assertFalse(args.engage);self.assertEqual(args.io_hz,35);self.assertEqual(args.controller_hz,10)
        source=inspect.getsource(run_rich_r3_roll_dualrate_xp12)
        self.assertIn("finally:",source);self.assertIn("excitation=0. if latch",source)
    def test_highrate_cascade_is_not_promoted_when_times_are_unresolved(self):
        result=json.loads(Path('configs/rich_R3_roll_highrate_cascade.json').read_text())
        self.assertEqual(result['decision'],'rejected_for_dynamic_lqr_realization')
        self.assertFalse(result['all_dynamic_times_sample_resolved'])
        self.assertTrue(result['all_stage_fit_rmse_below_0_25'])
    def test_discrete_cascade_and_confirmation_gate_are_frozen(self):
        model=json.loads(Path('configs/rich_R3_roll_discrete_cascade.json').read_text());gate=json.loads(Path('configs/rich_R3_roll_discrete_cascade_gate.json').read_text())
        self.assertEqual(model['validation_files_opened'],[])
        self.assertEqual((model['yoke_to_total']['selected']['na'],model['yoke_to_total']['selected']['nb']),(1,2))
        self.assertEqual((model['surface_to_p']['selected']['na'],model['surface_to_p']['selected']['nb']),(1,1))
        self.assertTrue(gate['frozen_before_confirmation']);self.assertTrue(gate['no_refit_or_reselection'])
    def test_discrete_cascade_confirmation_passes_without_refit(self):
        score=json.loads(Path('configs/rich_R3_roll_discrete_cascade_confirmation_score.json').read_text())
        self.assertTrue(score['pass']);self.assertTrue(score['no_refit_or_reselection'])
        self.assertLessEqual(score['yoke_to_total_ratio'],1.25)
        self.assertLessEqual(score['surface_to_p_ratio'],1.25)

if __name__=="__main__":unittest.main()
