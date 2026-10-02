"""DILISIC wrapper that makes a fourth-order plant imitate a double integrator."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .lisic import LISICController, LISICParameters


@dataclass
class DILISICState:
    """Reference-model state and finite-difference memory for one agent."""

    x_ref: np.ndarray
    filtered_u_di: float = 0.0
    previous_u_di: float = 0.0
    previous_u_di_dot: float = 0.0
    has_previous_u_di: bool = False


@dataclass
class DILISICWrapper:
    """Inner-loop controller around one flexible-link arm."""

    lisic: LISICController = field(
        default_factory=lambda: LISICController(LISICParameters())
    )
    reference_filter_tau: float = 0.05

    def initialize(self, plant_state: np.ndarray) -> DILISICState:
        x_ref = np.zeros(5, dtype=float)
        x_ref[0] = plant_state[0]
        x_ref[1] = plant_state[1]
        return DILISICState(x_ref=x_ref)

    def step(
        self,
        plant_state: np.ndarray,
        ref_state: DILISICState,
        u_di: float,
        dt: float,
    ) -> tuple[float, dict[str, float]]:
        if ref_state.has_previous_u_di:
            alpha = dt / max(self.reference_filter_tau + dt, dt)
            ref_state.filtered_u_di += alpha * (u_di - ref_state.filtered_u_di)
            u_di_used = ref_state.filtered_u_di
            u_di_dot = (u_di_used - ref_state.previous_u_di) / dt
            u_di_ddot = (u_di_dot - ref_state.previous_u_di_dot) / dt
        else:
            ref_state.filtered_u_di = u_di
            u_di_used = u_di
            u_di_dot = 0.0
            u_di_ddot = 0.0
            ref_state.has_previous_u_di = True

        ref_state.x_ref[2] = u_di_used
        ref_state.x_ref[3] = u_di_dot
        ref_state.x_ref[4] = u_di_ddot

        info = self.lisic.control(plant_state, ref_state.x_ref)
        u_h = info["f_hat"] + info["q_a"] + self.lisic.params.k * info["s"] - info["u_r"]
        self.lisic.update(dt, info["s"], u_h)

        # Double-integrator reference model: q_ddot = u_DI.
        ref_state.x_ref[0] += dt * ref_state.x_ref[1]
        ref_state.x_ref[1] += dt * u_di_used
        ref_state.previous_u_di = u_di_used
        ref_state.previous_u_di_dot = u_di_dot

        # Equation (31) requires the same u_DI to drive both the reference
        # model and the physical plant.  Using the raw outer command here while
        # integrating the filtered command above creates an undocumented
        # mismatch that LISIC must fight as a disturbance.
        total_u = u_di_used + info["u"]
        info["u_di"] = float(u_di)
        info["u_di_filtered"] = float(u_di_used)
        info["u_lisic"] = info["u"]
        info["u_total"] = float(total_u)
        return float(total_u), info
