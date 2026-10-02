"""Controller gains — single source of truth (Ref 3, §Control; code-exact).

No controller module hard-codes a gain; everything is imported from here.
Full-precision PD values are kept exactly as in
    aero2_minimal_control/src/controllers/linear_2dof.py
(the paper rounds them to 4 d.p.). "yawboost" variants are the higher-authority
yaw retunes from the final hardware experiments.
"""
from __future__ import annotations

# ===========================================================================
# Shared second-order derivative filter (Ref 3, Eqs. 28-30)
#   x1_dot = wn*x2 ;  x2_dot = wn*((y - x1) - 2*zeta*x2) ;  y_f_dot = wn*x2
# Explicit Euler with ACTUAL measured dt (see config.timing).
# ===========================================================================
DERIV_FILTER_WN: float = 100.0
DERIV_FILTER_ZETA: float = 1.0

# ===========================================================================
# PD baseline (Ref 3, Eqs. 39-41) — the benchmark every controller is judged against.
# No integral term. Commands clipped to +/- V_MAX (config.params).
# ===========================================================================
PD_KP_PITCH: float = 116.24203523333735
PD_KD_PITCH: float = 99.698951398313469
PD_KP_YAW: float = 35.8625570008741
PD_KD_YAW: float = 38.028899215266975

# ===========================================================================
# LQR (Ref 3, Eqs. 43-44). CARE; u_ff by least squares for zero accel at ref.
# ===========================================================================
LQR_Q_DIAG = (180.0, 4.0, 60.0, 2.0)
LQR_R_DIAG = (0.30, 0.30)

# ===========================================================================
# LQG (Ref 3, Eq. 45) — LQR gain + Luenberger observer, Euler with actual dt.
# Observer designed via CARE on (A^T, C^T) with these process/meas covariances.
# ===========================================================================
LQG_PROCESS_DIAG = (2e-3, 3e-2, 2e-3, 3e-2)
LQG_MEASUREMENT_DIAG = (6e-4, 8e-4)

# ===========================================================================
# Linear MPC (Ref 3, Eqs. 46-47) — unconstrained finite-horizon FIRST-MOVE
# with final clip (NOT an online QP). Tuning is code-resident and distinct
# from LQR Q/R (see aero2_minimal_control/src/controllers/mpc.py default).
# ===========================================================================
MPC_PREDICTION_DT: float = 0.02
MPC_HORIZON: int = 120
MPC_Q_DIAG = (220.0, 3.0, 90.0, 1.5)
MPC_R_DIAG = (0.45, 0.45)

# ===========================================================================
# Backstepping / computed torque (Ref 3, Eqs. 48-50). LS inverse dynamics.
# ===========================================================================
BS_K1_THETA: float = 2.0
BS_K2_THETA: float = 3.0
BS_K1_PSI: float = 1.2
BS_K2_PSI: float = 2.2
BS_YAWBOOST_K1_PSI: float = 4.0
BS_YAWBOOST_K2_PSI: float = 3.5

# ===========================================================================
# Sliding-mode control (Ref 3, Eqs. 51-53). Boundary-layer sat, not sign.
#   s = e_dot + lambda*e ;  v = -lambda*q_dot - eta*sat(s/phi)
# ===========================================================================
SMC_LAMBDA_THETA: float = 2.5
SMC_ETA_THETA: float = 0.7
SMC_PHI_THETA: float = 0.10
SMC_LAMBDA_PSI: float = 2.0
SMC_ETA_PSI: float = 0.8
SMC_PHI_PSI: float = 0.15
SMC_YAWBOOST_LAMBDA_PSI: float = 4.0
SMC_YAWBOOST_ETA_PSI: float = 3.0
SMC_YAWBOOST_PHI_PSI: float = 0.25

# ===========================================================================
# Nonlinear MPC (Ref 3, Eqs. 54-55) — lightweight real-time grid search around
# the inverse-dynamics nominal, RK4 prediction, terminal scaling.
# ===========================================================================
NMPC_NOMINAL_HORIZON: int = 10
NMPC_NOMINAL_DT_P: float = 0.035
# Realtime variant (the one benchmarked in Table IV):
NMPC_RT_HORIZON: int = 5
NMPC_RT_DT_P: float = 0.06
NMPC_RT_Q_DIAG = (80.0, 2.5, 50.0, 1.5)
NMPC_RT_R_DIAG = (0.10, 0.10)
NMPC_RT_TERMINAL_SCALE: float = 1.5
NMPC_RT_OFFSET_GRID = (-2.5, 0.0, 2.5)
# Nominal inverse-dynamics command gains for the NMPC search center (code default)
NMPC_NOMINAL_K1_PITCH: float = 1.6
NMPC_NOMINAL_K2_PITCH: float = 2.6
NMPC_NOMINAL_K1_YAW: float = 1.0
NMPC_NOMINAL_K2_YAW: float = 1.8

# ===========================================================================
# M5 loop-shaping conservative PITCH regulator (Methodology M5) — safe but
# low-authority; kept for the regulation/disturbance application baseline.
# ===========================================================================
M5_PITCH_KP: float = -3.9657593774
M5_PITCH_U0: float = 1.4
M5_PITCH_VPITCH_MAX: float = 0.060

__all__ = [
    "DERIV_FILTER_WN", "DERIV_FILTER_ZETA",
    "PD_KP_PITCH", "PD_KD_PITCH", "PD_KP_YAW", "PD_KD_YAW",
    "LQR_Q_DIAG", "LQR_R_DIAG",
    "LQG_PROCESS_DIAG", "LQG_MEASUREMENT_DIAG",
    "MPC_PREDICTION_DT", "MPC_HORIZON", "MPC_Q_DIAG", "MPC_R_DIAG",
    "BS_K1_THETA", "BS_K2_THETA", "BS_K1_PSI", "BS_K2_PSI",
    "BS_YAWBOOST_K1_PSI", "BS_YAWBOOST_K2_PSI",
    "SMC_LAMBDA_THETA", "SMC_ETA_THETA", "SMC_PHI_THETA",
    "SMC_LAMBDA_PSI", "SMC_ETA_PSI", "SMC_PHI_PSI",
    "SMC_YAWBOOST_LAMBDA_PSI", "SMC_YAWBOOST_ETA_PSI", "SMC_YAWBOOST_PHI_PSI",
    "NMPC_NOMINAL_HORIZON", "NMPC_NOMINAL_DT_P",
    "NMPC_RT_HORIZON", "NMPC_RT_DT_P", "NMPC_RT_Q_DIAG", "NMPC_RT_R_DIAG",
    "NMPC_RT_TERMINAL_SCALE", "NMPC_RT_OFFSET_GRID",
    "NMPC_NOMINAL_K1_PITCH", "NMPC_NOMINAL_K2_PITCH", "NMPC_NOMINAL_K1_YAW", "NMPC_NOMINAL_K2_YAW",
    "M5_PITCH_KP", "M5_PITCH_U0", "M5_PITCH_VPITCH_MAX",
    "QPD_KP_YAW", "QPD_KD_YAW", "QPD_YAW_SLEW_RATE",
]

# ===========================================================================
# Quaternion yaw PD (wrap-aware, rate-limited setpoint) — experimental (P10+).
# Damped gains + a slew-rate limit on the INTERNAL yaw setpoint let the
# shortest-path (quaternion) error position at large / continuous 360 deg+
# targets without limit-cycling (see docs / WORKFLOW insight #9). Pitch reuses
# the standard PD gains above.
# ===========================================================================
QPD_KP_YAW: float = 12.0
QPD_KD_YAW: float = 9.0
QPD_YAW_SLEW_RATE: float = 2.0943951023931953   # 120 deg/s [rad/s] max setpoint slew
