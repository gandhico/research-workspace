"""
    gui_exp03_quadrotor_nef_spiking.py - NEF LIF-spiking full-quadrotor cascade.

    Launch from the project root with:

        python -m nengo_gui src/gui/gui_exp03_quadrotor_nef_spiking.py

    This Nengo-GUI model is self-contained so re-execution on edit is robust.
    Its equations, gains, references, and neuron type mirror Exp03 and quadrotor_nef.py; the
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


NEURON = nengo.LIF()


def _pd(ref_sources, rate_sources, kp, kd, r_e, r_rate, r_cmd, label):
    error = nengo.Ensemble(200, 1, radius=r_e, neuron_type=NEURON, label="error "+label)
    rate_fb = nengo.Ensemble(200, 1, radius=r_rate, neuron_type=NEURON, label="rate feedback "+label)
    command = nengo.Ensemble(300, 1, radius=r_cmd, neuron_type=NEURON, label="control feedback "+label)
    for source, gain in ref_sources:
        nengo.Connection(source, error, transform=gain, synapse=TAU)
    for source, gain in rate_sources:
        nengo.Connection(source, rate_fb, transform=gain, synapse=TAU)
    nengo.Connection(error, command, transform=kp, synapse=TAU)
    nengo.Connection(rate_fb, command, transform=kd, synapse=TAU)
    return error, rate_fb, command


model = nengo.Network(label="Exp03 - NEF spiking full quadrotor", seed=1)
with model:
    reference = nengo.Node(_refs, size_out=6, label="reference [x,dx,y,dy,z,psi]")
    plant = nengo.Node(_QuadPlant(DT), size_in=4, size_out=12, label="plant state (12)")

    error_z, rate_z, feedback_z = _pd([(reference[4],1),(plant[4],-1)], [(plant[5],-1)], KP_Z,KD_Z,.5,.5,15,"z")
    error_psi, rate_psi, feedback_psi = _pd([(plant[6],-1)], [(plant[7],-1)], KP_PSI,KD_PSI,.4,.5,8,"psi")
    error_x, rate_x, feedback_x = _pd([(reference[0],1),(plant[0],-1)], [(reference[1],1),(plant[1],-1)], KP_X,KD_X,.4,.4,2.5,"x")
    error_y, rate_y, feedback_y = _pd([(reference[2],1),(plant[2],-1)], [(reference[3],1),(plant[3],-1)], KP_Y,KD_Y,.4,.4,4,"y")

    desired_attitude = nengo.Node(_attitude_desired, size_in=3, size_out=2,
                                  label="desired attitude [theta_d,phi_d]")
    nengo.Connection(feedback_x, desired_attitude[0], synapse=TAU)
    nengo.Connection(feedback_y, desired_attitude[1], synapse=TAU)
    nengo.Connection(plant[8], desired_attitude[2], synapse=TAU)
    error_theta, rate_theta, feedback_theta = _pd([(desired_attitude[0],1),(plant[8],-1)], [(plant[9],-1)], KP_THETA,KD_THETA,.4,1,40,"theta")
    error_phi, rate_phi, feedback_phi = _pd([(desired_attitude[1],1),(plant[10],-1)], [(plant[11],-1)], KP_PHI,KD_PHI,.4,1,30,"phi")

    thrust_command = nengo.Node(_thrust, size_in=3, size_out=1, label="total thrust u")
    nengo.Connection(feedback_z, thrust_command[0], synapse=TAU)
    nengo.Connection(plant[8], thrust_command[1], synapse=TAU)
    nengo.Connection(plant[10], thrust_command[2], synapse=TAU)
    final_command = nengo.Node(size_in=4, label="final command [u,tau_psi,tau_theta,tau_phi]")
    nengo.Connection(thrust_command, final_command[0], synapse=TAU)
    nengo.Connection(feedback_psi, final_command[1], synapse=TAU)
    nengo.Connection(feedback_theta, final_command[2], synapse=TAU)
    nengo.Connection(feedback_phi, final_command[3], synapse=TAU)
    nengo.Connection(final_command, plant, synapse=0)

    tracking_error = nengo.Node(size_in=3, label="controller error [ex,ey,ez]")
    nengo.Connection(error_x, tracking_error[0], synapse=TAU)
    nengo.Connection(error_y, tracking_error[1], synapse=TAU)
    nengo.Connection(error_z, tracking_error[2], synapse=TAU)
    controller_feedback = nengo.Node(size_in=6, label="neural feedback [ux,uy,uz,tpsi,tth,tph]")
    for i, source in enumerate((feedback_x,feedback_y,feedback_z,feedback_psi,feedback_theta,feedback_phi)):
        nengo.Connection(source, controller_feedback[i], synapse=TAU)
    tracking = nengo.Node(size_in=6, label="tracking [x,y,z,x_d,y_d,z_d]")
    attitude_tracking = nengo.Node(size_in=4, label="attitude [theta,phi,theta_d,phi_d]")
    nengo.Connection(plant[[0,2,4]], tracking[0:3], synapse=TAU)
    nengo.Connection(reference[[0,2,4]], tracking[3:6], synapse=TAU)
    nengo.Connection(plant[[8,10]], attitude_tracking[0:2], synapse=TAU)
    nengo.Connection(desired_attitude, attitude_tracking[2:4], synapse=TAU)
