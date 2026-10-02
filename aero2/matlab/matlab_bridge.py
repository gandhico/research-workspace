"""MATLAB <-> QLabs Aero2 bridge.

Wraps ``aero2.execution.virtual_twin.VirtualTwinBackend`` so MATLAB can drive the
QLabs Aero2 digital twin through a single low-latency ``step()`` call while the
controller is implemented natively in MATLAB. This is the cross-platform
(Python <-> MATLAB) validation path: identical twin, identical I/O, controller
re-implemented on each platform.

Usage (from MATLAB, out-of-process pyenv):
    br  = py.matlab_bridge.TwinBridge(quanser_python, repo);
    out = double(br.step(u_pitch, u_yaw));   % -> [t, theta, psi, theta_dot, psi_dot]
    br.close();

Requires: QLabs Aero2 open (listening on localhost:18950); the `hyperlif`
env with `quanser` + `qvl`; `repo` = the Aero2 working copy (for `aero2.*`).
"""
from __future__ import annotations

import os
import sys

import numpy as np


class TwinBridge:
    def __init__(self, quanser_python: str, repo: str, frequency: float = 200.0,
                 output_mode: str = "mixed", voltage_limit: float = 15.0,
                 backend: str = "twin"):
        if repo not in sys.path:
            sys.path.insert(0, repo)
        if quanser_python not in sys.path:
            sys.path.insert(0, quanser_python)
        os.environ.setdefault("QUANSER_PYTHON", quanser_python)
        os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

        if str(backend) == "hardware":
            from aero2.execution.hardware import HardwareBackend as _Backend
        else:
            from aero2.execution.virtual_twin import VirtualTwinBackend as _Backend

        self.be = _Backend(
            aero_id="0",
            frequency=float(frequency),
            output_mode=output_mode,
            voltage_limit=float(voltage_limit),
            quanser_python=quanser_python,
        )
        self.be.reset(np.zeros(4))
        # Warm-up throwaway: the twin's FIRST commanded pulse after connect
        # reads zero (documented quirk); discard it before the real loop.
        self.be.apply(np.zeros(2))
        self.be.read()

    def step(self, u_p, u_y):
        """Apply [u_p, u_y] (virtual pitch/yaw volts), return the new measurement."""
        self.be.apply(np.array([float(u_p), float(u_y)], dtype=float))
        m = self.be.read()
        td = 0.0 if m.theta_dot is None else float(m.theta_dot)
        pd = 0.0 if m.psi_dot is None else float(m.psi_dot)
        return [float(m.t), float(m.theta), float(m.psi), td, pd]

    def close(self):
        try:
            self.be.close()
        except Exception:
            pass
