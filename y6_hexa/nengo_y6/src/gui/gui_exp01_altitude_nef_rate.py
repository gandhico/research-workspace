"""
    gui_exp01_altitude_nef_rate.py - NEF rate-neuron altitude PD controller.

    Launch from the project root with:

        python -m nengo_gui src/gui/gui_exp01_altitude_nef_rate.py

    This Nengo-GUI model is self-contained so re-execution on edit is robust.
    Its equations, gains, references, and neuron type mirror src/controllers_nengo/altitude_nef.py and Exp01; the
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


RATE = nengo.RectifiedLinear()
model = nengo.Network(label="Exp01 - NEF rate altitude PD", seed=1)
with model:
    reference = nengo.Node(_altitude_reference, label="reference z_ref [m]")
    plant = nengo.Node(_AltitudePlant(DT), size_in=1, size_out=2,
                       label="plant state [z, zdot]")
    error = nengo.Ensemble(200, 1, radius=1.5, neuron_type=RATE,
                           label="controller error e_z")
    rate_feedback = nengo.Ensemble(200, 1, radius=3.0, neuron_type=RATE,
                                   label="rate feedback de_z")
    controller_feedback = nengo.Ensemble(400, 1, radius=12.0, neuron_type=RATE,
                                         label="neural PD feedback u_fb")
    hover_feedforward = nengo.Node(HOVER, label="mg feed-forward")
    final_command = nengo.Node(size_in=1, label="final thrust command u [N]")
    tracking = nengo.Node(size_in=2, label="tracking [z, z_ref]")

    nengo.Connection(reference, error, synapse=TAU)
    nengo.Connection(plant[0], error, transform=-1.0, synapse=TAU)
    nengo.Connection(plant[1], rate_feedback, transform=-1.0, synapse=TAU)
    nengo.Connection(error, controller_feedback, transform=KP, synapse=TAU)
    nengo.Connection(rate_feedback, controller_feedback, transform=KD, synapse=TAU)
    nengo.Connection(hover_feedforward, final_command, synapse=TAU)
    nengo.Connection(controller_feedback, final_command, synapse=TAU)
    nengo.Connection(final_command, plant, synapse=0)
    nengo.Connection(plant[0], tracking[0], synapse=TAU)
    nengo.Connection(reference, tracking[1], synapse=TAU)
