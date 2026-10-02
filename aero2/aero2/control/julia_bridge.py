"""Optional Julia policy controller bridge.

Bridge 1 keeps Python in charge of plant I/O and timing while a Julia function
supplies the control policy. This module is intentionally optional: importing it
does not require ``juliacall``. The dependency is only needed when a controller
loads a Julia policy from a module path.
"""
from __future__ import annotations

import os
import importlib.util
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from aero2.config import params
from aero2.control.base import BaseController, Reference


class JuliaBridgeUnavailable(RuntimeError):
    """Raised when the optional Julia/Python bridge dependency is unavailable."""


class JuliaPolicyController(BaseController):
    """Controller wrapper for a Julia policy callable.

    The wrapped policy receives ``theta, theta_dot, psi, psi_dot, ref_theta,
    ref_psi, dt`` and returns two command values ``[u_pitch, u_yaw]``. A Python
    callable can be injected for tests; otherwise the controller loads a Julia
    function through ``juliacall`` on first use.
    """

    name = "julia_policy"

    def __init__(
        self,
        policy: Optional[Callable[..., object]] = None,
        module_path: str | Path | None = None,
        function_name: str = "Aero2PolicySmoke.pd_policy",
        voltage_limit: float = params.V_MAX,
        julia: str = "julia",
        julia_timeout: float = 30.0,
    ) -> None:
        super().__init__()
        self.policy = policy
        self.module_path = self._default_module_path() if module_path is None else Path(module_path)
        self.function_name = function_name
        self.voltage_limit = abs(float(voltage_limit))
        self.julia = str(julia)
        self.julia_timeout = float(julia_timeout)

    def reset(self) -> None:
        super().reset()
        if self.policy is None:
            self.policy = self._load_julia_policy()

    def compute(self, x_est: np.ndarray, ref: Reference, dt: float) -> np.ndarray:
        if self.policy is None:
            self.policy = self._load_julia_policy()

        x = np.asarray(x_est, dtype=float).reshape(-1)
        theta, theta_dot, psi, psi_dot = float(x[0]), float(x[1]), float(x[2]), float(x[3])
        raw = self.policy(theta, theta_dot, psi, psi_dot, float(ref.theta), float(ref.psi), float(dt))
        u = np.asarray(raw, dtype=float).reshape(2)
        u = np.clip(u, -self.voltage_limit, self.voltage_limit)
        self.info = {
            "bridge": "julia_policy",
            "function_name": self.function_name,
            "u_raw": np.asarray(raw, dtype=float).reshape(2),
        }
        return u

    def _load_julia_policy(self):
        if self.module_path is None:
            raise JuliaBridgeUnavailable("module_path is required when no policy callable is injected.")

        if importlib.util.find_spec("juliacall") is None:
            raise JuliaBridgeUnavailable(
                "juliacall is not installed. Install the optional Julia bridge "
                "dependency before using JuliaPolicyController with module_path."
            )

        self._configure_juliacall_environment()
        module_path = Path(self.module_path).resolve()
        if not module_path.exists():
            raise JuliaBridgeUnavailable(f"Julia policy module does not exist: {module_path}")

        try:
            from juliacall import Main
        except Exception as exc:  # pragma: no cover - depends on optional dependency
            raise JuliaBridgeUnavailable(
                "juliacall is not installed. Install the optional Julia bridge "
                "dependency before using JuliaPolicyController with module_path."
            ) from exc

        Main.include(str(module_path))
        return Main.seval(self.function_name)

    @staticmethod
    def _default_module_path() -> Path:
        return Path(__file__).resolve().parents[2] / "julia" / "aero2_policy_smoke.jl"

    def _configure_juliacall_environment(self) -> None:
        if "PYTHON_JULIACALL_EXE" not in os.environ:
            julia_cmd = shutil.which(self.julia)
            if julia_cmd is None and not Path(self.julia).exists():
                raise JuliaBridgeUnavailable(
                    f"Julia executable not found: {self.julia!r}. "
                    "Install Julia or pass a valid julia executable path."
                )
            julia_cmd = self.julia if Path(self.julia).exists() else str(julia_cmd)
            bindir = self._run_julia(julia_cmd, "print(Sys.BINDIR)")
            exe = Path(bindir) / ("julia.exe" if os.name == "nt" else "julia")
            os.environ["PYTHON_JULIACALL_EXE"] = str(exe)

        if "PYTHON_JULIACALL_PROJECT" not in os.environ:
            julia_cmd = os.environ["PYTHON_JULIACALL_EXE"]
            active_project = self._run_julia(julia_cmd, "print(Base.active_project())")
            os.environ["PYTHON_JULIACALL_PROJECT"] = str(Path(active_project).parent)

    def _run_julia(self, julia_cmd: str, expression: str) -> str:
        try:
            result = subprocess.run(
                [julia_cmd, "--startup-file=no", "-e", expression],
                text=True,
                capture_output=True,
                check=True,
                timeout=self.julia_timeout,
            )
        except Exception as exc:  # pragma: no cover - depends on local Julia install
            raise JuliaBridgeUnavailable(f"Julia environment probe failed for {julia_cmd!r}: {exc}") from exc
        return result.stdout.strip()


__all__ = ["JuliaBridgeUnavailable", "JuliaPolicyController"]
