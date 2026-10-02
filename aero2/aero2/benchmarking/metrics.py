"""Benchmark metrics (Ref 3, §XI-XII / Table IV).

Computed from a `ClosedLoopRecord`: pitch/yaw RMS error, tail mean-absolute error,
saturation fraction, realized loop rate, and angle ranges. Full Table-IV
reproduction (per-controller sweep + figures) is Phase 11; this provides the core
metrics the control runner reports now.
"""
from __future__ import annotations

import numpy as np

from aero2.applications.base import ClosedLoopRecord
from aero2.config import params


def tracking_metrics(rec: ClosedLoopRecord, tail_frac: float = 0.25) -> dict:
    x = np.asarray(rec.x_est, dtype=float)      # (N, 4)
    ref = np.asarray(rec.ref, dtype=float)      # (N, 4)
    u = np.asarray(rec.u, dtype=float)          # (N, 2)
    n = len(x)
    if n == 0:
        return {"n": 0}

    e_pitch = x[:, 0] - ref[:, 0]
    e_yaw = x[:, 2] - ref[:, 2]
    tail = max(1, int(n * tail_frac))
    vmax = params.V_MAX
    sat = np.abs(u) >= (vmax - 1e-6)

    return {
        "n": n,
        "duration_s": float(rec.t[-1] - rec.t[0]) if n > 1 else 0.0,
        "realized_hz": float(rec.realized_hz),
        "pitch_rms": float(np.sqrt(np.mean(e_pitch ** 2))),
        "yaw_rms": float(np.sqrt(np.mean(e_yaw ** 2))),
        "tail_pitch_mae": float(np.mean(np.abs(e_pitch[-tail:]))),
        "tail_yaw_mae": float(np.mean(np.abs(e_yaw[-tail:]))),
        "pitch_sat_frac": float(np.mean(sat[:, 0])),
        "yaw_sat_frac": float(np.mean(sat[:, 1])),
        "theta_range": (float(x[:, 0].min()), float(x[:, 0].max())),
        "psi_range": (float(x[:, 2].min()), float(x[:, 2].max())),
    }


__all__ = ["tracking_metrics"]
