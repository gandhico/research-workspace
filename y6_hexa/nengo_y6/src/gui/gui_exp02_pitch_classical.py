"""
    gui_exp02_pitch_classical.py - classical pitch controller.

    Launch from the project root with:

        python -m nengo_gui src/gui/gui_exp02_pitch_classical.py

    This Nengo-GUI model is self-contained so re-execution on edit is robust.
    Its equations, gains, references, and neuron type mirror Exp02 and subsystem_pd.py/subsystem_nef.py; the
    benchmark remains the source of truth.
    """

import numpy as np
import nengo

KP, KD = 36.0, 8.4
TARGET, T_STEP = 0.2, 1.0
DT, TAU = 0.001, 0.01
AXIS_SYMBOL = "theta"

class _AttitudePlant:
    """Inertia-normalized RK4 plant: tau -> [angle, angular_rate]."""
    def __init__(self, dt):
        self.dt = dt
        self.state = np.zeros(2)

    @staticmethod
    def _f(state, torque):
        return np.array([state[1], torque])

    def __call__(self, t, value):
        torque, h, state = float(value[0]), self.dt, self.state
        k1 = self._f(state, torque)
        k2 = self._f(state + 0.5*h*k1, torque)
        k3 = self._f(state + 0.5*h*k2, torque)
        k4 = self._f(state + h*k3, torque)
        self.state = state + h*(k1 + 2*k2 + 2*k3 + k4)/6.0
        return self.state


def _reference(t):
    return TARGET if t >= T_STEP else 0.0

model = nengo.Network(label="Exp02 - classical pitch")
with model:
    reference = nengo.Node(_reference, label="reference theta_ref [rad]")
    plant = nengo.Node(_AttitudePlant(DT), size_in=1, size_out=2,
                       label="plant state [theta, dtheta]")
    error = nengo.Node(size_in=1, label="controller error e_theta")
    rate_feedback = nengo.Node(lambda t, x: -KD*x[0], size_in=1, size_out=1,
                               label="rate feedback -Kd*dtheta")
    controller_feedback = nengo.Node(size_in=1, label="PD torque feedback")
    final_command = nengo.Node(size_in=1, label="final command tau_theta")
    tracking = nengo.Node(size_in=2, label="tracking [theta, theta_ref]")

    nengo.Connection(reference, error, synapse=0)
    nengo.Connection(plant[0], error, transform=-1.0, synapse=0)
    nengo.Connection(plant[1], rate_feedback, synapse=0)
    nengo.Connection(error, controller_feedback, transform=KP, synapse=0)
    nengo.Connection(rate_feedback, controller_feedback, synapse=0)
    nengo.Connection(controller_feedback, final_command, synapse=0)
    nengo.Connection(final_command, plant, synapse=0)
    nengo.Connection(plant[0], tracking[0], synapse=TAU)
    nengo.Connection(reference, tracking[1], synapse=TAU)
