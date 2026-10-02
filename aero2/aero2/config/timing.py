"""Sampling rates and the project's headline timing rule (Refs 1 & 3).

THE TIMING RULE (brief §9, Ref 3 Discussion / Eq. 42)
-----------------------------------------------------
Derivative filters and discrete updates MUST use the *actual measured* loop
period each iteration (`dt_actual()` from the backend), never the nominal
commanded period. The PD baseline only became the strongest controller after
this fix. This is the single most important implementation lesson of the
project; it is enforced by threading `dt` through `Controller.compute(...)`.
"""
from __future__ import annotations

# --- Nominal sampling frequencies [Hz] -------------------------------------
SAMPLING_HZ: float = 100.0        # Ref 1 sampling / IMU characterization (Ts = 0.01 s)
STATE_EST_HZ: float = 200.0       # Ref 1 bias-corrected state estimation (Ts = 0.005 s)
CONTROL_NOMINAL_HZ: float = 500.0 # commanded controller rate (Ref 3)

# --- Measured (honest) loop rates [Hz] -------------------------------------
# Python hardware logs do NOT achieve the commanded 500 Hz. These are the
# observed means used in Table IV; loops must run on measured dt, not these.
CONTROL_MEASURED_HZ: float = 380.0   # ~382.9 mean for PD; ~380-384 for PD/LQR/LQG/MPC/BS/SMC
NMPC_MEASURED_HZ: float = 303.0      # fast/realtime NMPC (heavy compute)

# --- Excitation preprocessing (Ref 3 §VI-A) --------------------------------
TRIM_DISCARD_S: float = 3.0       # drop t < 3 s and demean in PRBS/trim pipelines


def ts(hz: float) -> float:
    """Sampling period [s] for a given frequency [Hz] (Ref 1, Eq. 2: Ts = 1/fs)."""
    return 1.0 / float(hz)


__all__ = [
    "SAMPLING_HZ", "STATE_EST_HZ", "CONTROL_NOMINAL_HZ",
    "CONTROL_MEASURED_HZ", "NMPC_MEASURED_HZ", "TRIM_DISCARD_S", "ts",
]
