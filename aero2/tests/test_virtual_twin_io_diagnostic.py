from __future__ import annotations

from runners.run_virtual_twin_io_diagnostic import pulse_value, summarize


def test_pulse_value_profile():
    assert pulse_value(0.25, 3.0) == 0.0
    assert pulse_value(0.75, 3.0) == 3.0
    assert pulse_value(1.75, 3.0) == 0.0
    assert pulse_value(2.25, 3.0) == -3.0
    assert pulse_value(3.25, 3.0) == 0.0


def test_summarize_detects_yaw_encoder_motion():
    rows = [
        {
            "t": 0.0,
            "theta": 0.0,
            "psi": 0.0,
            "theta_dot": 0.0,
            "psi_dot": 0.0,
            "enc3": 0.0,
            "motor1_v": 0.0,
            "test": "yaw",
        },
        {
            "t": 1.0,
            "theta": 0.01,
            "psi": 0.001,
            "theta_dot": 0.1,
            "psi_dot": 0.2,
            "enc3": 3.0,
            "motor1_v": 3.0,
            "test": "yaw",
        },
    ]
    summary = summarize(rows)
    assert summary["pitch_motion_detected"] is False
    assert summary["yaw_motion_detected"] is True
    assert summary["yaw_encoder_count_range"] == 3.0
    assert summary["per_test"]["yaw"]["yaw_motion_detected"] is True
