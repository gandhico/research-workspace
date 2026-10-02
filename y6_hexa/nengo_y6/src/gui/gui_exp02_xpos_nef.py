"""
    gui_exp02_xpos_nef.py - NEF LIF-spiking x-position/theta cascade.

    Launch from the project root with:

        python -m nengo_gui src/gui/gui_exp02_xpos_nef.py

    This Nengo-GUI model is self-contained so re-execution on edit is robust.
    Its equations, gains, references, and neuron type mirror Exp02 and subsystem_pd.py/subsystem_nef.py; the
    benchmark remains the source of truth.
    """

import numpy as np
import nengo

KP_POS, KD_POS = 1.6, 2.0
KP_ANG, KD_ANG = 36.0, 8.4
SIGN, GRAVITY = 1.0, 9.81
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

model = nengo.Network(label="Exp02 - NEF LIF x/theta cascade", seed=1)
with model:
    reference = nengo.Node(_reference, label="reference x_ref [m]")
    plant = nengo.Node(_CascadePlant(DT), size_in=1, size_out=4,
                       label="plant state [x, dx, theta, dtheta]")
    position_error = nengo.Ensemble(200, 1, radius=3.0, neuron_type=nengo.LIF(),
                                    label="outer error e_x")
    position_rate = nengo.Ensemble(200, 1, radius=2.0, neuron_type=nengo.LIF(),
                                   label="outer damping -dx")
    outer_feedback = nengo.Ensemble(300, 1, radius=12.0, neuron_type=nengo.LIF(),
                                    label="outer feedback u_x")
    desired_attitude = nengo.Node(_desired_angle, size_in=1, size_out=1,
                                  label="desired attitude theta_cmd")
    attitude_error = nengo.Ensemble(200, 1, radius=1.0, neuron_type=nengo.LIF(),
                                    label="inner error e_theta")
    attitude_rate = nengo.Ensemble(200, 1, radius=4.0, neuron_type=nengo.LIF(),
                                   label="inner damping -dtheta")
    controller_feedback = nengo.Ensemble(400, 1, radius=50.0, neuron_type=nengo.LIF(),
                                         label="inner neural torque")
    final_command = nengo.Node(size_in=1, label="final command tau_theta")
    tracking = nengo.Node(size_in=2, label="tracking [x, x_ref]")
    attitude_tracking = nengo.Node(size_in=2, label="attitude [theta, theta_cmd]")

    nengo.Connection(reference, position_error, synapse=TAU)
    nengo.Connection(plant[0], position_error, transform=-1.0, synapse=TAU)
    nengo.Connection(plant[1], position_rate, transform=-1.0, synapse=TAU)
    nengo.Connection(position_error, outer_feedback, transform=KP_POS, synapse=TAU)
    nengo.Connection(position_rate, outer_feedback, transform=KD_POS, synapse=TAU)
    nengo.Connection(outer_feedback, desired_attitude, synapse=TAU)
    nengo.Connection(desired_attitude, attitude_error, synapse=TAU)
    nengo.Connection(plant[2], attitude_error, transform=-1.0, synapse=TAU)
    nengo.Connection(plant[3], attitude_rate, transform=-1.0, synapse=TAU)
    nengo.Connection(attitude_error, controller_feedback, transform=KP_ANG, synapse=TAU)
    nengo.Connection(attitude_rate, controller_feedback, transform=KD_ANG, synapse=TAU)
    nengo.Connection(controller_feedback, final_command, synapse=TAU)
    nengo.Connection(final_command, plant, synapse=TAU)
    nengo.Connection(plant[0], tracking[0], synapse=TAU)
    nengo.Connection(reference, tracking[1], synapse=TAU)
    nengo.Connection(plant[2], attitude_tracking[0], synapse=TAU)
    nengo.Connection(desired_attitude, attitude_tracking[1], synapse=TAU)
