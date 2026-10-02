"""Assert physical plant params match the papers / implemented code (brief §15.1).

Expected values are the literature/code truth; the test fails if config drifts.
Sources: Ref 3 (modelling) and aero2_minimal_control/src/aero2_model.py.
"""
import pytest

from aero2.config import params


def test_geometry_and_inertias():
    assert params.DT_ARM == 0.16743
    # Computed exactly as in code: m/1000 * (0.001)^2
    assert params.J_PITCH == pytest.approx(23188500.45 / 1000.0 * 0.001 ** 2, rel=0, abs=0)
    assert params.J_YAW == pytest.approx(23810415.95 / 1000.0 * 0.001 ** 2, rel=0, abs=0)
    assert params.J_PITCH == pytest.approx(0.02318850045)
    assert params.J_YAW == pytest.approx(0.02381041595)


def test_stiffness_damping_cross_terms():
    assert params.KSP == 0.00744
    assert params.DP == 0.00199
    assert params.KPP == 0.00321
    assert params.KPY == 0.00137
    assert params.DY == 0.00192
    assert params.KYY == 0.00610
    assert params.KYP == -0.00319          # negative cross term


def test_implementation_details_not_dropped():
    # cos(theta) clip — brief §17 forbids dropping this.
    assert params.MIN_COS_THETA == 0.25


def test_encoders_and_limits():
    assert params.PITCH_COUNTS_PER_REV == 2880
    assert params.YAW_COUNTS_PER_REV == 4096
    assert params.V_MAX == 24.0
    assert params.V_DIFF_MAX == 12.0
    assert params.U0_TRIM == 1.4
