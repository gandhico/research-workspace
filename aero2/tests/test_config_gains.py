"""Assert controller gains match Ref 3 / implemented code (brief §15.1, §9)."""
from aero2.config import gains


def test_derivative_filter():
    assert gains.DERIV_FILTER_WN == 100.0
    assert gains.DERIV_FILTER_ZETA == 1.0


def test_pd_baseline_gains_full_precision():
    # Ref 3 rounds to 4 d.p.; code (and config) keep full precision.
    assert gains.PD_KP_PITCH == 116.24203523333735
    assert gains.PD_KD_PITCH == 99.698951398313469
    assert gains.PD_KP_YAW == 35.8625570008741
    assert gains.PD_KD_YAW == 38.028899215266975
    # Rounded values quoted in the paper:
    assert round(gains.PD_KP_PITCH, 4) == 116.2420
    assert round(gains.PD_KD_PITCH, 4) == 99.6990
    assert round(gains.PD_KP_YAW, 4) == 35.8626
    assert round(gains.PD_KD_YAW, 4) == 38.0289


def test_lqr_lqg():
    assert gains.LQR_Q_DIAG == (180.0, 4.0, 60.0, 2.0)
    assert gains.LQR_R_DIAG == (0.30, 0.30)
    assert gains.LQG_PROCESS_DIAG == (2e-3, 3e-2, 2e-3, 3e-2)
    assert gains.LQG_MEASUREMENT_DIAG == (6e-4, 8e-4)


def test_backstepping():
    assert (gains.BS_K1_THETA, gains.BS_K2_THETA) == (2.0, 3.0)
    assert (gains.BS_K1_PSI, gains.BS_K2_PSI) == (1.2, 2.2)
    assert (gains.BS_YAWBOOST_K1_PSI, gains.BS_YAWBOOST_K2_PSI) == (4.0, 3.5)


def test_smc():
    assert (gains.SMC_LAMBDA_THETA, gains.SMC_ETA_THETA, gains.SMC_PHI_THETA) == (2.5, 0.7, 0.10)
    assert (gains.SMC_LAMBDA_PSI, gains.SMC_ETA_PSI, gains.SMC_PHI_PSI) == (2.0, 0.8, 0.15)
    assert (gains.SMC_YAWBOOST_LAMBDA_PSI, gains.SMC_YAWBOOST_ETA_PSI, gains.SMC_YAWBOOST_PHI_PSI) == (4.0, 3.0, 0.25)


def test_nmpc_realtime():
    assert gains.NMPC_RT_HORIZON == 5
    assert gains.NMPC_RT_DT_P == 0.06
    assert gains.NMPC_RT_Q_DIAG == (80.0, 2.5, 50.0, 1.5)
    assert gains.NMPC_RT_R_DIAG == (0.10, 0.10)
    assert gains.NMPC_RT_TERMINAL_SCALE == 1.5
    assert gains.NMPC_RT_OFFSET_GRID == (-2.5, 0.0, 2.5)
