"""
    gui_exp01_altitude_classical.py - classical PD altitude controller.

    Launch from the project root with:

        python -m nengo_gui src/gui/gui_exp01_altitude_classical.py

    This Nengo-GUI model is self-contained so re-execution on edit is robust.
    Its equations, gains, references, and neuron type mirror experiments/exp01_altitude_1dof/run_exp01.py; the
    benchmark remains the source of truth.
    """

import numpy as np
import nengo

MASS, GRAVITY = 0.9, 9.81
KP, KD = 8.0, 4.0
DT, TAU = 0.001, 0.01
T_STEP, Z_TARGET = 1.0, 1.0
HOVER = MASS * GRAVITY
THRUST_MAX = 2.5 * HOVER

class _AltitudePlant:
    """RK4 plant node: thrust [N] -> [z, zdot]."""
    def __init__(self, dt):
        self.dt = dt
        self.state = np.zeros(2)

    @staticmethod
    def _f(state, thrust):
        return np.array([state[1], thrust / MASS - GRAVITY])

    def __call__(self, t, value):
        thrust = float(np.clip(value[0], 0.0, THRUST_MAX))
        h, state = self.dt, self.state
        k1 = self._f(state, thrust)
        k2 = self._f(state + 0.5 * h * k1, thrust)
        k3 = self._f(state + 0.5 * h * k2, thrust)
        k4 = self._f(state + h * k3, thrust)
        self.state = state + h * (k1 + 2*k2 + 2*k3 + k4) / 6.0
        return self.state


def _altitude_reference(t):
    return Z_TARGET if t >= T_STEP else 0.0


model = nengo.Network(label="Exp01 - classical altitude PD")
with model:
    reference = nengo.Node(_altitude_reference, label="reference z_ref [m]")
    plant = nengo.Node(_AltitudePlant(DT), size_in=1, size_out=2,
                       label="plant state [z, zdot]")
    controller_error = nengo.Node(size_in=1, label="controller error e_z")
    rate_feedback = nengo.Node(lambda t, x: -KD * x[0], size_in=1, size_out=1,
                               label="rate feedback -Kd*zdot")
    controller_feedback = nengo.Node(size_in=1, label="PD feedback [N]")
    hover_feedforward = nengo.Node(HOVER, label="mg feed-forward")
    final_command = nengo.Node(size_in=1, label="final thrust command u [N]")
    tracking = nengo.Node(size_in=2, label="tracking [z, z_ref]")

    nengo.Connection(reference, controller_error, synapse=0)
    nengo.Connection(plant[0], controller_error, transform=-1.0, synapse=0)
    nengo.Connection(plant[1], rate_feedback, synapse=0)
    nengo.Connection(controller_error, controller_feedback, transform=KP, synapse=0)
    nengo.Connection(rate_feedback, controller_feedback, synapse=0)
    nengo.Connection(hover_feedforward, final_command, synapse=0)
    nengo.Connection(controller_feedback, final_command, synapse=0)
    nengo.Connection(final_command, plant, synapse=0)
    nengo.Connection(plant[0], tracking[0], synapse=TAU)
    nengo.Connection(reference, tracking[1], synapse=TAU)
