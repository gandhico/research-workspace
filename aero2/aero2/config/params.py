"""Physical plant parameters for the Quanser Aero2 — the single source of truth.

Every physical constant used anywhere in the codebase is defined here and
imported. No controller, model, or runner may redefine these numbers.

Provenance
----------
All values are ground-truthed against the *implemented* code (the brief's
"code = truth" rule), specifically:
    aero2_minimal_control/src/aero2_model.py
    aero2_minimal_control/src/controllers/linear_2dof.py
and cross-checked against Ref 3 (final paper, "Modelling, Identification, and
Control of the Quanser Aero2 System"), Sec. "Mathematical Modelling".

State / input / output convention (Ref 3, Eq. 1)
------------------------------------------------
    x = [theta, theta_dot, psi, psi_dot]^T      (pitch, pitch rate, yaw, yaw rate) [rad, rad/s]
    u = [u_p, u_y]^T                            (virtual pitch / yaw voltage)        [V]
    y = [theta, psi]^T                          (measured angles)                    [rad]

Motor mapping (Ref 2, Eq. 2):
    u_c = (v_f + v_r) / 2   (collective -> excites pitch)
    u_d = (v_f - v_r) / 2   (differential -> excites yaw)
"""
from __future__ import annotations

# --- Rotor / arm geometry -------------------------------------------------
DT_ARM: float = 0.16743          # effective thrust moment arm term [m] (Ref 3; code: DT_ARM)

# --- Inertias (computed EXACTLY as in code to avoid precision drift) -------
# Ref 3: J_P = 23188500.45/1000 * (0.001)^2,  J_Y = 23810415.95/1000 * (0.001)^2
J_PITCH: float = 23188500.45 / 1000.0 * 0.001 ** 2   # ~= 0.02318850045 [kg m^2]
J_YAW: float = 23810415.95 / 1000.0 * 0.001 ** 2     # ~= 0.02381041595 [kg m^2]

# --- Stiffness / damping / cross terms (Ref 3 drift b and input matrix M) --
KSP: float = 0.00744    # pitch gravitational/stiffness term (multiplies sin(theta))
DP: float = 0.00199     # pitch viscous damping
KPP: float = 0.00321    # pitch-from-pitch-command effectiveness
KPY: float = 0.00137    # pitch-from-yaw-command cross effectiveness
DY: float = 0.00192     # yaw viscous damping
KYY: float = 0.00610    # yaw-from-yaw-command effectiveness
KYP: float = -0.00319   # yaw-from-pitch-command cross effectiveness (note: negative)

# --- Nonlinear-model implementation detail (DO NOT DROP, brief §17) --------
# Yaw input effectiveness is scaled by cos(theta), clipped so |cos(theta)| >= 0.25.
# This bounds yaw authority at large pitch and materially affects results.
MIN_COS_THETA: float = 0.25

# --- Encoders (Ref 3 "Experimental setup"; DirectHilAero2IO.read) ----------
# theta = 2*pi*n_theta / 2880 ,  psi = 2*pi*n_psi / 4096
PITCH_COUNTS_PER_REV: int = 2880
YAW_COUNTS_PER_REV: int = 4096

# --- Actuation limits ------------------------------------------------------
V_MAX: float = 24.0          # HIL command clip [V] (Ref 3; all controllers saturate to +/-24)
V_DIFF_MAX: float = 12.0     # max |u_L - u_R| seen in pure-differential yaw chirp (Ref 1, Eq. 42)

# --- Operating point -------------------------------------------------------
U0_TRIM: float = 1.4         # collective trim voltage [V] (Ref 1 Eq. 27 / Ref 2 §IV)

# --- Offline-model approximations (NOT paper-measured constants) ------------
# Qualitative stiction model for the yaw_only OFFLINE plant only. Grounded in the
# observation that the first clear yaw motion appeared around v_yaw ~ 2.0 V
# (Ref 1 §F / Ref 2): small differential does not overcome yaw breakaway. These
# are modelling choices for simulation, not identified plant parameters.
YAW_BREAKAWAY_V: float = 2.0      # |u_y| below this cannot start yaw from rest [V]
YAW_STICTION_RATE: float = 0.02   # |psi_dot| below this counts as "at rest" [rad/s]

__all__ = [
    "DT_ARM", "J_PITCH", "J_YAW",
    "KSP", "DP", "KPP", "KPY", "DY", "KYY", "KYP",
    "MIN_COS_THETA",
    "PITCH_COUNTS_PER_REV", "YAW_COUNTS_PER_REV",
    "V_MAX", "V_DIFF_MAX", "U0_TRIM",
    "YAW_BREAKAWAY_V", "YAW_STICTION_RATE",
]
