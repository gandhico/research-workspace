"""Controllers — all implement the `Controller` interface; selectable by name.
linear/ has PD (done); LQR/LQG/MPC and nonlinear/ + neuromorphic/ follow (P7, P10)."""
from __future__ import annotations

from aero2.control.base import BaseController, Controller, Reference
from aero2.control.linear.lqg import LQG2DOF
from aero2.control.linear.lqr import LQR2DOF
from aero2.control.linear.mpc_linear import MPC2DOF
from aero2.control.linear.pd import PD2DOF
from aero2.control.nonlinear.backstepping import Backstepping2DOF
from aero2.control.nonlinear.nmpc import NMPC2DOF
from aero2.control.nonlinear.smc import SlidingMode2DOF
from aero2.control.neuromorphic.hyperlif_residual import HyperLIFResidualController
from aero2.control.neuromorphic.gate_residual import GateResidualController
from aero2.control.quaternion_yaw import QuaternionYawPD
from aero2.control.julia_bridge import JuliaBridgeUnavailable, JuliaPolicyController

#: name -> Controller class. `hyperlif`/`qpd` are experimental (Phase 10+).
CONTROLLERS = {
    "pd": PD2DOF,
    "lqr": LQR2DOF,
    "lqg": LQG2DOF,
    "mpc": MPC2DOF,
    "backstepping": Backstepping2DOF,
    "smc": SlidingMode2DOF,
    "nmpc": NMPC2DOF,
    "hyperlif": HyperLIFResidualController,
    "gate_residual": GateResidualController,
    "qpd": QuaternionYawPD,
    "julia_policy": JuliaPolicyController,
}


def make_controller(name: str, **kwargs) -> Controller:
    key = name.lower()
    if key not in CONTROLLERS:
        raise ValueError(f"unknown controller: {name!r}; choose from {sorted(CONTROLLERS)}")
    return CONTROLLERS[key](**kwargs)


__all__ = [
    "Controller", "Reference", "BaseController", "CONTROLLERS", "make_controller",
    "PD2DOF", "LQR2DOF", "LQG2DOF", "MPC2DOF",
    "Backstepping2DOF", "SlidingMode2DOF", "NMPC2DOF", "HyperLIFResidualController",
    "GateResidualController", "QuaternionYawPD",
    "JuliaBridgeUnavailable", "JuliaPolicyController",
]
