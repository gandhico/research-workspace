import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "qarm_identify_position_servo.py"
SPEC = importlib.util.spec_from_file_location("qarm_identify_position_servo", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_stable_position_servo_contract_passes_shadow_gate():
    rng = np.random.default_rng(7)
    n, delay = 900, 2
    t = np.arange(n) * 0.01
    u = np.repeat(rng.uniform(-0.5, 0.5, n // 15 + 1), 15)[:n]
    q = np.zeros(n)
    for k in range(2, n - 1):
        q[k + 1] = 1.72 * q[k] - 0.74 * q[k - 1] + 0.02 * u[k - delay]
    result = MODULE.identify(t, u, q, max_delay=4)
    assert result["shadow_ready"]
    assert result["direct_dilisic_actuation_ready"] is False
    assert result["best_model"]["delay_samples"] == delay
    assert abs(result["best_model"]["dc_gain"] - 1.0) < 1e-8


def test_constant_command_is_rejected():
    t = np.arange(100) * 0.01
    u = np.ones(100)
    q = np.zeros(100)
    try:
        MODULE.identify(t, u, q)
    except ValueError as exc:
        assert "persistently excited" in str(exc)
    else:
        raise AssertionError("constant input must not produce an identified model")
