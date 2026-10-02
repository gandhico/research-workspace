"""
    gui_exp03_quadrotor_classical.py - classical full-quadrotor cascade.

    Launch from the project root with:

        python -m nengo_gui src/gui/gui_exp03_quadrotor_classical.py

    This Nengo-GUI model is self-contained so re-execution on edit is robust.
    Its equations, gains, references, and neuron type mirror Exp03, quadrotor.py, and quadrotor_pd.py; the
    benchmark remains the source of truth.
    """

import numpy as np
import nengo

MASS, GRAVITY = 0.9, 9.81
DT, TAU = 0.001, 0.01
KP_Z, KD_Z = 40.0, 5.0
KP_X, KD_X = 1.6, 2.0
KP_Y, KD_Y = 3.0, 2.0
KP_PHI, KD_PHI = 40.0, 8.0
KP_THETA, KD_THETA = 120.0, 8.0
KP_PSI, KD_PSI = 7.0, 4.0
X0 = np.array([0.1, 0, -0.1, 0, 0, 0, 0.1, 0, 0, 0, 0, 0], float)


def _refs(t):
    x = np.sin(0.1*t); dx = 0.1*np.cos(0.1*t)
    y = np.sin(0.1*t); dy = 0.1*np.cos(0.1*t)
    if t < 10.0:
        z = t/10.0
    elif t < 20.0:
        z = 1.0
    elif t < 30.0:
        z = 2.0 - 0.05*t
    else:
        z = 0.5
    return [x, dx, y, dy, z, 0.0]


class _QuadPlant:
    """Full 12-state RK4 plant; input [u,tau_psi,tau_theta,tau_phi]."""
    def __init__(self, dt):
        self.dt = dt
        self.state = X0.copy()

    @staticmethod
    def _f(s, c):
        x, dx, y, dy, z, dz, psi, dpsi, theta, dtheta, phi, dphi = s
        u, tpsi, ttheta, tphi = c
        out = np.empty(12)
        out[0] = dx
        out[1] = u*(np.sin(phi)*np.sin(psi) + np.cos(phi)*np.cos(psi)*np.sin(theta))/MASS
        out[2] = dy
        out[3] = u*(np.cos(phi)*np.sin(theta)*np.sin(psi) - np.cos(psi)*np.sin(phi))/MASS
        out[4] = dz
        out[5] = u*np.cos(theta)*np.cos(phi)/MASS - GRAVITY
        out[6], out[7] = dpsi, tpsi
        out[8], out[9] = dtheta, ttheta
        out[10], out[11] = dphi, tphi
        return out

    def __call__(self, t, command):
        h, s = self.dt, self.state
        k1 = self._f(s, command)
        k2 = self._f(s + 0.5*h*k1, command)
        k3 = self._f(s + 0.5*h*k2, command)
        k4 = self._f(s + h*k3, command)
        self.state = s + h*(k1 + 2*k2 + 2*k3 + k4)/6.0
        return self.state


def _attitude_desired(t, v):
    ux, uy, theta = v
    return [np.arctan2(ux, GRAVITY), np.arctan2(-uy*np.cos(theta), GRAVITY)]


def _thrust(t, v):
    return (v[0] + MASS*GRAVITY)/(np.cos(v[1])*np.cos(v[2]))


model = nengo.Network(label="Exp03 - classical full quadrotor")
with model:
    reference = nengo.Node(_refs, size_out=6, label="reference [x,dx,y,dy,z,psi]")
    plant = nengo.Node(_QuadPlant(DT), size_in=4, size_out=12, label="plant state (12)")
    tracking_error = nengo.Node(size_in=4, label="controller error [ex,ey,ez,epsi]")
    outer_feedback = nengo.Node(
        lambda t, v: [KP_X*v[0] + KD_X*v[1], KP_Y*v[2] + KD_Y*v[3], KP_Z*v[4] - KD_Z*v[5]],
        size_in=6, size_out=3, label="position feedback [ux,uy,u_fb_z]")
    desired_attitude = nengo.Node(_attitude_desired, size_in=3, size_out=2,
                                  label="desired attitude [theta_d,phi_d]")
    attitude_error = nengo.Node(size_in=3, label="attitude error [e_psi,e_theta,e_phi]")
    attitude_feedback = nengo.Node(
        lambda t, v: [KP_PSI*v[0]-KD_PSI*v[1], KP_THETA*v[2]-KD_THETA*v[3], KP_PHI*v[4]-KD_PHI*v[5]],
        size_in=6, size_out=3, label="attitude feedback [tau_psi,tau_theta,tau_phi]")
    thrust_command = nengo.Node(_thrust, size_in=3, size_out=1, label="total thrust u")
    final_command = nengo.Node(size_in=4, label="final command [u,tau_psi,tau_theta,tau_phi]")
    tracking = nengo.Node(size_in=6, label="tracking [x,y,z,x_d,y_d,z_d]")
    attitude_tracking = nengo.Node(size_in=4, label="attitude [theta,phi,theta_d,phi_d]")

    for ref_i, state_i, err_i in ((0,0,0),(2,2,1),(4,4,2),(5,6,3)):
        nengo.Connection(reference[ref_i], tracking_error[err_i], synapse=0)
        nengo.Connection(plant[state_i], tracking_error[err_i], transform=-1.0, synapse=0)
    nengo.Connection(tracking_error[0], outer_feedback[0], synapse=0)
    nengo.Connection(reference[1], outer_feedback[1], synapse=0)
    nengo.Connection(plant[1], outer_feedback[1], transform=-1.0, synapse=0)
    nengo.Connection(tracking_error[1], outer_feedback[2], synapse=0)
    nengo.Connection(reference[3], outer_feedback[3], synapse=0)
    nengo.Connection(plant[3], outer_feedback[3], transform=-1.0, synapse=0)
    nengo.Connection(tracking_error[2], outer_feedback[4], synapse=0)
    nengo.Connection(plant[5], outer_feedback[5], synapse=0)
    nengo.Connection(outer_feedback[0], desired_attitude[0], synapse=0)
    nengo.Connection(outer_feedback[1], desired_attitude[1], synapse=0)
    nengo.Connection(plant[8], desired_attitude[2], synapse=0)
    nengo.Connection(tracking_error[3], attitude_error[0], synapse=0)
    nengo.Connection(desired_attitude[0], attitude_error[1], synapse=0)
    nengo.Connection(plant[8], attitude_error[1], transform=-1.0, synapse=0)
    nengo.Connection(desired_attitude[1], attitude_error[2], synapse=0)
    nengo.Connection(plant[10], attitude_error[2], transform=-1.0, synapse=0)
    nengo.Connection(attitude_error[0], attitude_feedback[0], synapse=0)
    nengo.Connection(plant[7], attitude_feedback[1], synapse=0)
    nengo.Connection(attitude_error[1], attitude_feedback[2], synapse=0)
    nengo.Connection(plant[9], attitude_feedback[3], synapse=0)
    nengo.Connection(attitude_error[2], attitude_feedback[4], synapse=0)
    nengo.Connection(plant[11], attitude_feedback[5], synapse=0)
    nengo.Connection(outer_feedback[2], thrust_command[0], synapse=0)
    nengo.Connection(plant[8], thrust_command[1], synapse=0)
    nengo.Connection(plant[10], thrust_command[2], synapse=0)
    nengo.Connection(thrust_command, final_command[0], synapse=0)
    nengo.Connection(attitude_feedback, final_command[1:4], synapse=0)
    nengo.Connection(final_command, plant, synapse=0)
    nengo.Connection(plant[[0,2,4]], tracking[0:3], synapse=TAU)
    nengo.Connection(reference[[0,2,4]], tracking[3:6], synapse=TAU)
    nengo.Connection(plant[[8,10]], attitude_tracking[0:2], synapse=TAU)
    nengo.Connection(desired_attitude, attitude_tracking[2:4], synapse=TAU)
