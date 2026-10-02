from __future__ import annotations

import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from .filters import DerivativeFilter, wrap_to_pi
from .types import QubeState


DEFAULT_QAL_DIR = Path(
    os.environ.get("QAL_DIR", Path.home() / "Documents" / "Quanser")
)
DEFAULT_QUANSER_PYTHON = Path(
    os.environ.get("QUANSER_PYTHON", DEFAULT_QAL_DIR / "0_libraries" / "python")
)


def as_float(value: Any) -> float:
    arr = np.asarray(value, dtype=float)
    return float(arr.reshape(-1)[0])


def ensure_quanser_python(path: str | Path | None = None) -> Path:
    quanser_python = Path(path or os.environ.get("QUANSER_PYTHON", DEFAULT_QUANSER_PYTHON))
    if not quanser_python.exists():
        raise FileNotFoundError(
            f"Quanser Python path not found: {quanser_python}. "
            "Set QUANSER_PYTHON or pass --quanser-python."
        )
    sys.path.insert(0, str(quanser_python))
    return quanser_python


def get_qube_class(version: int):
    try:
        from pal.products.qube import QubeServo2, QubeServo3
    except ModuleNotFoundError as exc:
        if exc.name == "quanser":
            raise ModuleNotFoundError(
                "Quanser API bindings are not installed in this Python environment. "
                "Run .\\scripts\\setup_env.ps1 from the project root, then activate .venv."
            ) from exc
        raise

    if int(version) == 2:
        return QubeServo2
    if int(version) == 3:
        return QubeServo3
    raise ValueError("Qube version must be 2 or 3.")


def safe_stop_qube(qube: Any) -> None:
    if qube is None:
        return
    try:
        for _ in range(4):
            qube.write_voltage(0.0)
            time.sleep(0.02)
    except Exception:
        pass
    try:
        qube.terminate()
    except Exception:
        pass


def read_state(
    qube: Any,
    time_s: float,
    theta_filter: DerivativeFilter,
    alpha_filter: DerivativeFilter,
    sample_time_s: float,
    use_tachometer: bool = True,
    alpha_offset_rad: float = math.pi,
) -> QubeState:
    qube.read_outputs()

    theta = -as_float(qube.motorPosition)
    # Encoder zero is the RESTING (hanging) position; shift by alpha_offset_rad (pi by
    # default) so alpha=0 == UPRIGHT, matching runners\twin_swingup_balance.py and
    # twin_acc2027_gate_residual.py. Fixed 2026-09-03 for run_online_qube.py, which
    # previously used the "legacy" no-shift convention those twin scripts' docstrings
    # warn regulates to HANGING, not upright.
    #
    # Callers that apply their OWN upright offset on top of this (e.g.
    # simulink_balance_runner.py's --alpha-upright-offset-deg) must pass
    # alpha_offset_rad=0.0 here — otherwise the two shifts stack to 2*pi and silently
    # cancel out, which is exactly the bug hit on 2026-09-03: the pendulum's real
    # upright position stopped being recognized because it was being read back as
    # hanging-down again.
    alpha = wrap_to_pi(as_float(qube.pendulumPosition) - alpha_offset_rad)

    if use_tachometer and hasattr(qube, "motorSpeed"):
        theta_dot = -as_float(qube.motorSpeed)
    else:
        theta_dot = theta_filter.step(theta, sample_time_s)

    if use_tachometer and hasattr(qube, "pendulumSpeed"):
        alpha_dot = as_float(qube.pendulumSpeed)
    else:
        alpha_dot = alpha_filter.step(alpha, sample_time_s)

    return QubeState(
        time_s=float(time_s),
        theta_rad=float(theta),
        theta_dot_rad_s=float(theta_dot),
        alpha_rad=float(alpha),
        alpha_dot_rad_s=float(alpha_dot),
        motor_current_a=as_float(getattr(qube, "motorCurrent", 0.0)),
        amplifier_fault=as_float(getattr(qube, "amplifierFault", 0.0)),
        motor_stall_detected=as_float(getattr(qube, "motorStallDetected", 0.0)),
        motor_stall_error=as_float(getattr(qube, "motorStallError", 0.0)),
    )
