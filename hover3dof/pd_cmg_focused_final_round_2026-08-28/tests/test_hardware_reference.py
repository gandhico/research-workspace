"""Offline tests for the logged hardware mission-reference adaptations."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))
sys.path.insert(0, str(Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\src")))

from hover3dof_hil_pd_cmg_control import (  # noqa: E402
    HARDSTEP_TARGETS_RPY,
    experiment_reference_euler,
)
from gra_control.math3d import reference_euler  # noqa: E402


class HardwareReferenceTests(unittest.TestCase):
    def test_zero_transition_exactly_matches_canonical_hardstep(self) -> None:
        for t in np.linspace(0.0, 12.0, 121):
            np.testing.assert_allclose(
                experiment_reference_euler(t, "hardstep", 25.0, 1.0, 0.0),
                reference_euler(t, "hardstep", 25.0),
            )

    def test_shaped_hardstep_is_continuous_at_phase_change(self) -> None:
        before = experiment_reference_euler(3.0 - 1e-9, "hardstep", 25.0, 0.7, 0.5)
        at_change = experiment_reference_euler(3.0, "hardstep", 25.0, 0.7, 0.5)
        np.testing.assert_allclose(before, at_change, atol=1e-8)
        np.testing.assert_allclose(at_change, 0.7 * HARDSTEP_TARGETS_RPY[0])

    def test_shaped_hardstep_reaches_scaled_target(self) -> None:
        np.testing.assert_allclose(
            experiment_reference_euler(1.5, "hardstep", 25.0, 0.7, 0.5),
            0.7 * HARDSTEP_TARGETS_RPY[0],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
