from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from aero2.control.base import Reference
from aero2.control.julia_bridge import JuliaBridgeUnavailable, JuliaPolicyController


def test_julia_policy_controller_accepts_injected_policy():
    calls = []

    def policy(theta, theta_dot, psi, psi_dot, ref_theta, ref_psi, dt):
        calls.append((theta, theta_dot, psi, psi_dot, ref_theta, ref_psi, dt))
        return (1.5, -2.5)

    controller = JuliaPolicyController(policy=policy, voltage_limit=2.0)
    u = controller.compute(
        np.array([0.1, 0.2, -0.3, -0.4]),
        Reference(theta=0.5, psi=-0.1),
        0.005,
    )

    assert np.allclose(u, [1.5, -2.0])
    assert calls == [(0.1, 0.2, -0.3, -0.4, 0.5, -0.1, 0.005)]
    assert controller.info["bridge"] == "julia_policy"


def test_julia_policy_controller_reports_missing_juliacall():
    if importlib.util.find_spec("juliacall") is not None:
        pytest.skip("juliacall is installed; missing-dependency path is not applicable")

    controller = JuliaPolicyController(
        module_path=Path("julia/aero2_policy_smoke.jl"),
        function_name="Aero2PolicySmoke.pd_policy",
    )
    with pytest.raises(JuliaBridgeUnavailable, match="juliacall is not installed"):
        controller.compute(np.zeros(4), Reference(), 0.005)
