import unittest
from types import SimpleNamespace
from lqr.run_stage5_rate_lqr_xp12 import abort_reason, half_sine_reference

class Stage5RateRunnerTests(unittest.TestCase):
    def test_reference_is_single_bounded_half_sine(self):
        self.assertEqual(half_sine_reference(9.9,10,2,.2),0)
        self.assertAlmostEqual(half_sine_reference(11,10,2,.2),.2)
        self.assertAlmostEqual(half_sine_reference(12,10,2,.2),0)
        self.assertEqual(half_sine_reference(12.1,10,2,.2),0)
    def test_abort_is_latched_by_caller_on_rate_envelope(self):
        args=SimpleNamespace(max_abs_pitch_deg=10,max_abs_roll_deg=10,max_abs_rate_deg_s=20)
        m={"p_deg_s":0,"q_deg_s":21,"r_deg_s":0,"sim_paused":0,"sim_speed":1,"replay_mode":0}
        self.assertEqual(abort_reason(args,0,0,m),"body-rate envelope exceeded")

if __name__ == "__main__": unittest.main()
