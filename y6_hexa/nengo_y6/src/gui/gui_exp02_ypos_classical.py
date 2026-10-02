"""
    gui_exp02_ypos_classical.py - classical y-position/phi cascade.

    Launch from the project root with:

        python -m nengo_gui src/gui/gui_exp02_ypos_classical.py

    This Nengo-GUI model is self-contained so re-execution on edit is robust.
    Its equations, gains, references, and neuron type mirror Exp02 and subsystem_pd.py/subsystem_nef.py; the
    benchmark remains the source of truth.
    """

import numpy as np
import nengo

KP_POS, KD_POS = 3.0, 2.4
KP_ANG, KD_ANG = 36.0, 8.4
SIGN, GRAVITY = -1.0, 9.81
TARGET, T_STEP = 2.0, 1.0
DT, TAU = 0.001, 0.01
TILT_MAX = np.radians(35.0)

class _CascadePlant:
    """RK4 cascade plant: tau -> [position, velocity, angle, rate]."""
    def __init__(self, dt):
        self.dt = dt
        self.state = np.zeros(4)

    @staticmethod
    def _f(state, torque):
        angle = np.clip(state[2], -TILT_MAX, TILT_MAX)
        return np.array([state[1], SIGN*GRAVITY*np.tan(angle), state[3], torque])

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


def _desired_angle(t, value):
    return float(np.clip(np.arctan2(SIGN*value[0], GRAVITY), -TILT_MAX, TILT_MAX))

model = nengo.Network(label="Exp02 - classical y/phi cascade")
with model:
    reference = nengo.Node(_reference, label="reference y_ref [m]")
    plant = nengo.Node(_CascadePlant(DT), size_in=1, size_out=4,
                       label="plant state [y, dy, phi, dphi]")
    position_error = nengo.Node(size_in=1, label="outer error e_y")
    outer_feedback = nengo.Node(lambda t, x: KP_POS*x[0] - KD_POS*x[1],
                                size_in=2, size_out=1, label="outer PD feedback u_y")
    desired_attitude = nengo.Node(_desired_angle, size_in=1, size_out=1,
                                  label="desired attitude phi_cmd")
    attitude_error = nengo.Node(size_in=1, label="inner error e_phi")
    controller_feedback = nengo.Node(lambda t, x: KP_ANG*x[0] - KD_ANG*x[1],
                                     size_in=2, size_out=1, label="inner PD torque")
    final_command = nengo.Node(size_in=1, label="final command tau_phi")
    tracking = nengo.Node(size_in=2, label="tracking [y, y_ref]")
    attitude_tracking = nengo.Node(size_in=2, label="attitude [phi, phi_cmd]")

    nengo.Connection(reference, position_error, synapse=0)
    nengo.Connection(plant[0], position_error, transform=-1.0, synapse=0)
    nengo.Connection(position_error, outer_feedback[0], synapse=0)
    nengo.Connection(plant[1], outer_feedback[1], synapse=0)
    nengo.Connection(outer_feedback, desired_attitude, synapse=0)
    nengo.Connection(desired_attitude, attitude_error, synapse=0)
    nengo.Connection(plant[2], attitude_error, transform=-1.0, synapse=0)
    nengo.Connection(attitude_error, controller_feedback[0], synapse=0)
    nengo.Connection(plant[3], controller_feedback[1], synapse=0)
    nengo.Connection(controller_feedback, final_command, synapse=0)
    nengo.Connection(final_command, plant, synapse=0)
    nengo.Connection(plant[0], tracking[0], synapse=TAU)
    nengo.Connection(reference, tracking[1], synapse=TAU)
    nengo.Connection(plant[2], attitude_tracking[0], synapse=TAU)
    nengo.Connection(desired_attitude, attitude_tracking[1], synapse=TAU)
