"""Plant models. All variants subclass `Model` and are selectable by name.

    helicopter_2dof  primary coupled nonlinear plant (Ref 3)
    linear_2dof      linear realization of the above (LQR/LQG/MPC backbone)
    pitch_only       1-DOF pitch about trim (near-integrating)
    yaw_only         1-DOF yaw, pure differential drive + breakaway/stiction
    half_rotor       half-quadrotor — FUTURE WORK, hardware NotValidated
"""
from __future__ import annotations

from aero2.models.base import Model
from aero2.models.half_rotor import HalfRotor
from aero2.models.helicopter_2dof import Helicopter2DOF
from aero2.models.linear_2dof import Linear2DOF, linear_plant_matrices
from aero2.models.pitch_only import PitchOnly
from aero2.models.yaw_only import YawOnly

#: name -> Model class, for config-driven `model_variant` selection (runners, P12)
MODELS = {
    "helicopter_2dof": Helicopter2DOF,
    "linear_2dof": Linear2DOF,
    "pitch_only": PitchOnly,
    "yaw_only": YawOnly,
    "half_rotor": HalfRotor,
}


def make_model(name: str, **kwargs) -> Model:
    """Instantiate a model variant by name."""
    key = name.lower()
    if key not in MODELS:
        raise ValueError(f"unknown model variant: {name!r}; choose from {sorted(MODELS)}")
    return MODELS[key](**kwargs)


__all__ = [
    "Model", "MODELS", "make_model",
    "Helicopter2DOF", "Linear2DOF", "linear_plant_matrices",
    "PitchOnly", "YawOnly", "HalfRotor",
]
