import math
from pathlib import Path
import sys
import unittest

TEST_DIR = Path(__file__).resolve().parent
BRIDGE_DIR = TEST_DIR.parent / "lqr"
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

from LQR import DampedAttitudeConfig, DampedAttitudeController, EHEKATLLQR, LQRConfig, StateSample
from run_lqr_xp12 import (
    StateReader,
    command_sticks,
    control_vector,
    control_vector_from_sticks,
    divergence_stop_reason,
    excitation_value,
    safety_stop_reason,
    slew_limit,
    start_attitude_block_reason,
    start_attitude_allowed,
    trim_bias_from_ctrl,
)


class FakeRateClient:
    def getDREFs(self, names):
        assert names == [
            "sim/flightmodel/position/P",
            "sim/flightmodel/position/Q",
            "sim/flightmodel/position/R",
        ]
        return [[0.1], [0.2], [-0.3]]


class LQRConventionTests(unittest.TestCase):
    def test_positive_pitch_error_commands_positive_xplane_elevator_stick(self):
        controller = EHEKATLLQR(LQRConfig(pitch_sp_deg=2.0, roll_sp_deg=0.0, clip=0.0))
        command = controller.command(StateSample(pitch_deg=4.0, roll_deg=0.0, heading_deg=0.0))

        self.assertGreater(command.delta_e_limited_deg, 0.0)
        self.assertGreater(command.elevator_stick, 0.0)

    def test_negative_roll_error_commands_negative_xplane_aileron_stick(self):
        controller = EHEKATLLQR(LQRConfig(pitch_sp_deg=2.0, roll_sp_deg=0.0, clip=0.0))
        command = controller.command(StateSample(pitch_deg=2.0, roll_deg=-5.0, heading_deg=0.0))

        self.assertGreater(command.delta_a_limited_deg, 0.0)
        self.assertLess(command.aileron_stick, 0.0)

    def test_pqr_datarefs_are_converted_from_rad_s_to_deg_s(self):
        reader = StateReader(mode="attitude", rate_units="rad_s", u_trim=0.0, w_trim=0.0, v_trim=0.0)

        pitch_rate, roll_rate, yaw_rate = reader.read_rates(
            FakeRateClient(), now=1.0, pitch=0.0, roll=0.0, heading=0.0
        )

        self.assertAlmostEqual(pitch_rate, math.degrees(0.2))
        self.assertAlmostEqual(roll_rate, math.degrees(0.1))
        self.assertAlmostEqual(yaw_rate, math.degrees(-0.3))

    def test_axis_selector_zeroes_unused_stick_axis(self):
        controller = EHEKATLLQR(LQRConfig(pitch_sp_deg=2.0, roll_sp_deg=0.0, clip=0.2))
        command = controller.command(StateSample(pitch_deg=4.0, roll_deg=-5.0, heading_deg=0.0))

        pitch_only = control_vector(command, routing="corrected", axis="pitch", rudder=0.0, throttle=-998.0)
        roll_only = control_vector(command, routing="corrected", axis="roll", rudder=0.0, throttle=-998.0)

        self.assertEqual(pitch_only[0], 0.0)
        self.assertNotEqual(pitch_only[1], 0.0)
        self.assertNotEqual(roll_only[0], 0.0)
        self.assertEqual(roll_only[1], 0.0)

    def test_incremental_trim_bias_preserves_inactive_axis(self):
        controller = DampedAttitudeController(DampedAttitudeConfig(pitch_sp_deg=2.0, roll_sp_deg=0.0, clip=0.2))
        command = controller.command(StateSample(pitch_deg=6.0, roll_deg=-5.0, heading_deg=0.0))

        ail, ele = command_sticks(
            command,
            axis="pitch",
            aileron_bias=0.12,
            elevator_bias=-0.03,
            trim_mode="incremental",
        )

        self.assertAlmostEqual(ail, 0.12)
        self.assertAlmostEqual(ele, -0.03 + command.elevator_stick)

    def test_absolute_trim_bias_only_preserves_inactive_axis(self):
        controller = DampedAttitudeController(DampedAttitudeConfig(pitch_sp_deg=2.0, roll_sp_deg=0.0, clip=0.2))
        command = controller.command(StateSample(pitch_deg=6.0, roll_deg=-5.0, heading_deg=0.0))

        ail, ele = command_sticks(
            command,
            axis="roll",
            aileron_bias=0.12,
            elevator_bias=-0.03,
            trim_mode="absolute",
        )

        self.assertAlmostEqual(ail, command.aileron_stick)
        self.assertAlmostEqual(ele, -0.03)

    def test_current_ctrl_trim_bias_matches_routing(self):
        current_ctrl = (0.11, -0.07, 0.0, -998.0)

        self.assertEqual(trim_bias_from_ctrl(current_ctrl, "corrected"), (0.11, -0.07))
        self.assertEqual(trim_bias_from_ctrl(current_ctrl, "legacy"), (-0.07, 0.11))

    def test_zero_incremental_command_preserves_current_ctrl_for_both_routings(self):
        controller = DampedAttitudeController(DampedAttitudeConfig(pitch_sp_deg=2.0, roll_sp_deg=0.0, clip=0.2))
        command = controller.command(StateSample(pitch_deg=2.0, roll_deg=0.0, heading_deg=0.0))
        current_ctrl = (0.11, -0.07, 0.0, -998.0)

        for routing in ("corrected", "legacy"):
            ail_bias, ele_bias = trim_bias_from_ctrl(current_ctrl, routing)
            ail, ele = command_sticks(command, "both", ail_bias, ele_bias, "incremental")
            ctrl = control_vector_from_sticks(ail, ele, routing, rudder=0.0, throttle=-998.0)
            self.assertAlmostEqual(ctrl[0], current_ctrl[0])
            self.assertAlmostEqual(ctrl[1], current_ctrl[1])

    def test_slew_limit_bounds_stick_step(self):
        self.assertAlmostEqual(slew_limit(0.08, -0.08, 0.01), -0.07)
        self.assertAlmostEqual(slew_limit(-0.08, 0.08, 0.01), 0.07)

    def test_slew_limit_zero_disables_rate_limit(self):
        self.assertAlmostEqual(slew_limit(0.08, -0.08, 0.0), 0.08)

    def test_prbs_excitation_is_bounded_and_changes_sign(self):
        values = [excitation_value(i * 1.0, 0.015, 1.0, "prbs") for i in range(6)]

        self.assertIn(0.015, values)
        self.assertIn(-0.015, values)
        self.assertTrue(all(abs(v) <= 0.015 for v in values))

    def test_doublet_excitation_returns_to_zero(self):
        values = [excitation_value(i * 1.0, 0.02, 1.0, "doublet") for i in range(4)]

        self.assertEqual(values, [0.02, -0.02, 0.0, 0.0])

    def test_start_gate_uses_selected_axis(self):
        self.assertTrue(start_attitude_allowed("pitch", 2.0, 30.0, 8.0, 8.0))
        self.assertFalse(start_attitude_allowed("pitch", 30.0, 2.0, 8.0, 8.0))
        self.assertTrue(start_attitude_allowed("roll", 30.0, 2.0, 8.0, 8.0))
        self.assertFalse(start_attitude_allowed("roll", 2.0, 30.0, 8.0, 8.0))
        self.assertFalse(start_attitude_allowed("both", 2.0, 30.0, 8.0, 8.0))

    def test_start_block_reason_requests_manual_trim_instead_of_terminal_stop(self):
        sample = StateSample(pitch_deg=20.0, roll_deg=1.0, heading_deg=0.0)

        reason = start_attitude_block_reason("pitch", sample, 2.0, 0.0, 8.0, 8.0)

        self.assertIn("waiting for manual trim", reason)

    def test_start_block_reason_clears_after_manual_trim(self):
        sample = StateSample(pitch_deg=3.0, roll_deg=1.0, heading_deg=0.0)

        reason = start_attitude_block_reason("pitch", sample, 2.0, 0.0, 8.0, 8.0)

        self.assertEqual("", reason)

    def test_safety_stop_reason_reports_first_exceeded_limit(self):
        sample = StateSample(
            pitch_deg=31.0,
            roll_deg=20.0,
            heading_deg=0.0,
            pitch_rate_deg_s=12.0,
            roll_rate_deg_s=8.0,
            yaw_rate_deg_s=4.0,
        )

        self.assertIn("abs pitch", safety_stop_reason(sample, 30.0, 45.0, 60.0))
        self.assertEqual("", safety_stop_reason(sample, 0.0, 45.0, 60.0))
        self.assertIn("body rate", safety_stop_reason(sample, 0.0, 45.0, 10.0))

    def test_divergence_stop_reason_reports_controlled_pitch_runaway(self):
        sample = StateSample(
            pitch_deg=5.0,
            roll_deg=30.0,
            heading_deg=0.0,
            pitch_rate_deg_s=12.0,
            roll_rate_deg_s=20.0,
        )

        reason = divergence_stop_reason(sample, "pitch", 2.0, 0.0, 2.0, 10.0)

        self.assertIn("pitch error diverging", reason)

    def test_divergence_stop_reason_ignores_inactive_axis(self):
        sample = StateSample(
            pitch_deg=2.0,
            roll_deg=30.0,
            heading_deg=0.0,
            pitch_rate_deg_s=0.0,
            roll_rate_deg_s=20.0,
        )

        reason = divergence_stop_reason(sample, "pitch", 2.0, 0.0, 2.0, 10.0)

        self.assertEqual("", reason)

    def test_divergence_stop_reason_ignores_converging_rate(self):
        sample = StateSample(
            pitch_deg=5.0,
            roll_deg=-6.0,
            heading_deg=0.0,
            pitch_rate_deg_s=-12.0,
            roll_rate_deg_s=12.0,
        )

        reason = divergence_stop_reason(sample, "both", 2.0, 0.0, 2.0, 10.0)

        self.assertEqual("", reason)

    def test_damped_controller_commands_toward_setpoints(self):
        controller = DampedAttitudeController(DampedAttitudeConfig(pitch_sp_deg=2.0, roll_sp_deg=0.0, clip=0.2))
        command = controller.command(StateSample(pitch_deg=6.0, roll_deg=-5.0, heading_deg=0.0))

        self.assertGreater(command.elevator_stick, 0.0)
        self.assertGreater(command.aileron_stick, 0.0)

    def test_damped_controller_respects_stick_signs(self):
        controller = DampedAttitudeController(
            DampedAttitudeConfig(
                pitch_sp_deg=2.0,
                roll_sp_deg=0.0,
                clip=0.2,
                elevator_stick_sign=-1.0,
                aileron_stick_sign=-1.0,
            )
        )
        command = controller.command(StateSample(pitch_deg=6.0, roll_deg=-5.0, heading_deg=0.0))

        self.assertLess(command.elevator_stick, 0.0)
        self.assertLess(command.aileron_stick, 0.0)


if __name__ == "__main__":
    unittest.main()
