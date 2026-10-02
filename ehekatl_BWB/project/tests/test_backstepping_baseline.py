from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKSTEPPING_DIR = PROJECT_ROOT / "backstepping"
if str(BACKSTEPPING_DIR) not in sys.path:
    sys.path.insert(0, str(BACKSTEPPING_DIR))

import Backstepping
from run_backstepping_baseline_xp12 import (
    MEASUREMENTS, calculate_command, read_measurements, smooth_recovery_pulse,
    send_control, start_block_reasons, tapered_multisine,
)


class FakeClient:
    def getDREFs(self, datarefs):
        values = []
        for number, dataref in enumerate(datarefs, start=1):
            if dataref == "sim/flightmodel/engine/ENGN_thro":
                values.append([0.25, 0.75])
            elif dataref == "sim/weather/rho":
                values.append([1.2])
            elif dataref == "sim/flightmodel/position/true_airspeed":
                values.append([10.0])
            else:
                values.append([float(number)])
        return values


class BaselineRunnerTests(unittest.TestCase):
    def test_owned_roll_command_is_written_to_verified_dataref(self):
        class Client:
            def __init__(self):
                self.calls = []

            def sendCTRL(self, command):
                self.calls.append(("CTRL", tuple(command)))

            def sendDREF(self, dataref, value):
                self.calls.append(("DREF", dataref, value))

        client = Client()
        command = [0.1, 0.005, 0.0, -998.0]
        send_control(
            client, command, routing="legacy",
            direct_roll_axis=True, direct_pitch_axis=True,
        )
        self.assertEqual(client.calls[0], ("CTRL", tuple(command)))
        self.assertEqual(
            client.calls[1],
            ("DREF", "sim/joystick/yoke_roll_ratio", 0.005),
        )
        self.assertEqual(
            client.calls[2],
            ("DREF", "sim/joystick/yoke_pitch_ratio", 0.1),
        )

    def test_direct_axis_routing_respects_corrected_mapping(self):
        class Client:
            def __init__(self):
                self.calls = []

            def sendCTRL(self, command):
                self.calls.append(("CTRL", tuple(command)))

            def sendDREF(self, dataref, value):
                self.calls.append(("DREF", dataref, value))

        client = Client()
        send_control(
            client, [0.005, 0.1, 0.0, -998.0], routing="corrected",
            direct_roll_axis=True, direct_pitch_axis=True,
        )
        self.assertEqual(client.calls[1][2], 0.005)
        self.assertEqual(client.calls[2][2], 0.1)

    def test_legacy_command_matches_original_equations_without_clipping(self):
        roll = Backstepping.Backstepping(0.001, 33.0, 0.03)
        pitch = Backstepping.Backstepping(0.001, 39.0, 0.03)
        roll.SetPoint = 0.0
        pitch.SetPoint = 6.0
        ctrl = [0.06, -0.02, 0.0, 0.4]

        result = calculate_command(
            roll, pitch, roll=4.0, pitch=8.0, ctrl=ctrl,
            routing="legacy", clip=0.0, rudder=0.0, throttle=-998.0,
        )

        def expected(feedback, setpoint, control, k, ku, tau):
            error = feedback - setpoint
            desired = -k * error
            control_error = control - desired
            derivative = -k * (control_error - desired)
            return control + tau * (derivative - error - ku * control_error)

        expected_roll = expected(4.0, 0.0, ctrl[0], 0.001, 33.0, 0.03)
        expected_pitch = expected(8.0, 6.0, ctrl[1], 0.001, 39.0, 0.03)
        self.assertAlmostEqual(result["raw_roll_output"], expected_roll)
        self.assertAlmostEqual(result["raw_pitch_output"], expected_pitch)
        self.assertAlmostEqual(result["sent_ctrl_0"], expected_pitch)
        self.assertAlmostEqual(result["sent_ctrl_1"], expected_roll)
        self.assertEqual(result["sent_ctrl_3"], -998.0)

    def test_trim_relative_legacy_command_preserves_trim_feedforward(self):
        roll = Backstepping.Backstepping(0.001, 33.0, 0.03)
        pitch = Backstepping.Backstepping(0.001, 39.0, 0.03)
        roll.SetPoint = 0.0
        pitch.SetPoint = 1.3
        trim = (0.148, 0.0004, 0.0, 0.0235)
        result = calculate_command(
            roll, pitch, roll=0.0, pitch=1.3, ctrl=trim,
            routing="legacy", clip=0.0, rudder=0.0, throttle=-998.0,
            control_trim=trim,
        )
        self.assertAlmostEqual(result["sent_ctrl_0"], trim[0])
        self.assertAlmostEqual(result["sent_ctrl_1"], trim[1])

    def test_measurement_batch_extracts_both_engines_and_dynamic_pressure(self):
        values = read_measurements(FakeClient())
        self.assertEqual(values["throttle_engine_0"], 0.25)
        self.assertEqual(values["throttle_engine_1"], 0.75)
        self.assertAlmostEqual(values["dynamic_pressure_pa"], 60.0)
        self.assertEqual(set(values) - {"dynamic_pressure_pa"}, {field for field, _, _ in MEASUREMENTS})

    def test_start_gate_accepts_frozen_baseline_condition(self):
        class Args:
            target_altitude_m = 5000.0
            altitude_tolerance_m = 200.0
            target_ias_kts = 100.0
            ias_tolerance_kts = 5.0
            pitch_sp = 6.0
            roll_sp = 0.0
            max_start_pitch_error_deg = 3.0
            max_start_roll_error_deg = 3.0
            max_start_rate_deg_s = 3.0
            target_throttle = 0.669723
            throttle_tolerance = 0.02

        measurements = {
            "ias_kts": 100.0, "p_deg_s": 0.0, "q_deg_s": 0.0, "r_deg_s": 0.0,
            "throttle_engine_0": 0.669723, "throttle_engine_1": 0.669723,
            "autopilot_on": 0.0, "autopilot_servos_on": 0.0, "autothrottle_on": 0.0,
            "sim_paused": 0.0, "sim_speed": 1.0, "replay_mode": 0.0,
        }
        self.assertEqual(start_block_reasons(Args, 5000.0, 6.0, 0.0, measurements), [])
        measurements["autopilot_on"] = 1.0
        self.assertIn("autopilot is on", start_block_reasons(Args, 5000.0, 6.0, 0.0, measurements))

    def test_start_gate_rejects_paused_or_replay_state(self):
        class Args:
            target_altitude_m = 5000.0
            altitude_tolerance_m = 200.0
            target_ias_kts = 100.0
            ias_tolerance_kts = 5.0
            pitch_sp = 6.0
            roll_sp = 0.0
            max_start_pitch_error_deg = 3.0
            max_start_roll_error_deg = 3.0
            max_start_rate_deg_s = 3.0
            target_throttle = 0.669723
            throttle_tolerance = 0.02

        measurements = {
            "ias_kts": 100.0, "p_deg_s": 0.0, "q_deg_s": 0.0, "r_deg_s": 0.0,
            "throttle_engine_0": 0.669723, "throttle_engine_1": 0.669723,
            "autopilot_on": 0.0, "autopilot_servos_on": 0.0, "autothrottle_on": 0.0,
            "sim_paused": 1.0, "sim_speed": 0.0, "replay_mode": 7.0,
        }
        reasons = start_block_reasons(Args, 5000.0, 6.0, 0.0, measurements)
        self.assertIn("simulator is paused", reasons)
        self.assertIn("simulation speed is zero", reasons)
        self.assertIn("simulator is in replay mode", reasons)

    def test_recovery_pulse_is_single_smooth_window(self):
        self.assertEqual(smooth_recovery_pulse(9.9, 10.0, 0.5, 0.005), 0.0)
        self.assertAlmostEqual(smooth_recovery_pulse(10.25, 10.0, 0.5, 0.005), 0.005)
        self.assertAlmostEqual(smooth_recovery_pulse(10.0, 10.0, 0.5, 0.005), 0.0)
        self.assertAlmostEqual(smooth_recovery_pulse(10.5, 10.0, 0.5, 0.005), 0.0, places=12)
        self.assertEqual(smooth_recovery_pulse(10.6, 10.0, 0.5, 0.005), 0.0)

    def test_identification_multisine_is_bounded_and_tapered(self):
        frequencies = (0.1, 0.2, 0.35, 0.55, 0.8)
        phases = (0.0, 1.0, 2.0, 3.0, 4.0)
        values = [
            tapered_multisine(t / 100.0, 10.0, 40.0, 2.0, 0.003, frequencies, phases)
            for t in range(0, 6001)
        ]
        self.assertEqual(values[0], 0.0)
        self.assertAlmostEqual(tapered_multisine(10.0, 10.0, 40.0, 2.0, 0.003, frequencies, phases), 0.0)
        self.assertAlmostEqual(tapered_multisine(50.0, 10.0, 40.0, 2.0, 0.003, frequencies, phases), 0.0, places=12)
        self.assertEqual(tapered_multisine(50.1, 10.0, 40.0, 2.0, 0.003, frequencies, phases), 0.0)
        self.assertLessEqual(max(abs(value) for value in values), 0.003)


if __name__ == "__main__":
    unittest.main()
