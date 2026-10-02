"""Loader for the recorded hardware CSV logs migrated into data/raw_logs/.

Returns a dict of column-name -> 1-D numpy array. The M1-M3 logs share a common
schema (k, t, Ts, fs, theta, psi, gyro_x/y/z, accel_x/y/z, u_left, u_right, ...);
see data/raw_logs/MANIFEST.md for provenance.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
RAW_LOGS = REPO / "data" / "raw_logs"


def load_log(path) -> dict:
    """Load a CSV log into {column: np.ndarray(float)}."""
    path = Path(path)
    if not path.is_absolute() and not path.exists():
        # allow paths relative to data/raw_logs/
        candidate = RAW_LOGS / path
        if candidate.exists():
            path = candidate
    arr = np.genfromtxt(path, delimiter=",", names=True, dtype=float)
    names = arr.dtype.names
    # np.genfromtxt collapses a single data row to 0-d; normalize to 1-D
    return {name: np.atleast_1d(arr[name]).astype(float) for name in names}


def find_log(filename: str) -> Path:
    """Locate a migrated log by filename anywhere under data/raw_logs/."""
    matches = list(RAW_LOGS.rglob(filename))
    if not matches:
        raise FileNotFoundError(f"{filename} not found under {RAW_LOGS}")
    return matches[0]


__all__ = ["RAW_LOGS", "load_log", "find_log"]
