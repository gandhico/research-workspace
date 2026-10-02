"""
subsystem_nef.py  —  NEF/Nengo controllers for the Phase-3 subsystems.

Same neuromorphic recipe as the altitude controller (error + rate ensembles ->
PD-decoded command), now for:

* build_attitude_net : single rotational axis (roll/pitch/yaw)
* build_cascade_net  : position->attitude cascade, where the *virtual control
                       command* a_des = atan2(s*u_pos, g) is the only nonlinear
                       node; the two PD laws (outer position, inner angle) are
                       both computed by neuron populations.
"""
import numpy as np
import nengo

from src.models.subsystems import (AttitudePlantNode, CascadePlantNode, G, TILT_MAX)


def build_attitude_net(gains, dt, ref_fn, x0=(0.0, 0.0), neuron_type=None,
                       n_err=200, n_rate=200, n_u=400, tau=0.01, seed=1,
                       r_err=0.6, r_rate=3.0, r_u=40.0):
    neuron_type = neuron_type if neuron_type is not None else nengo.LIF()
    net = nengo.Network(label="Attitude NEF", seed=seed)
    with net:
        plant = nengo.Node(AttitudePlantNode(dt, x0), size_in=1, size_out=2,
                           label="plant[a,rate]")
        ref = nengo.Node(ref_fn, label="a_ref")
        e = nengo.Ensemble(n_err, 1, radius=r_err, neuron_type=neuron_type, label="e")
        de = nengo.Ensemble(n_rate, 1, radius=r_rate, neuron_type=neuron_type, label="de")
        u = nengo.Ensemble(n_u, 1, radius=r_u, neuron_type=neuron_type, label="tau")

        nengo.Connection(ref, e, transform=1.0, synapse=tau)
        nengo.Connection(plant[0], e, transform=-1.0, synapse=tau)
        nengo.Connection(plant[1], de, transform=-1.0, synapse=tau)
        nengo.Connection(e, u, transform=gains.Kp, synapse=tau)
        nengo.Connection(de, u, transform=gains.Kd, synapse=tau)
        nengo.Connection(u, plant, synapse=tau)

        net.p_state = nengo.Probe(plant, synapse=None)
        net.p_u = nengo.Probe(u, synapse=0.01)
        net.p_ref = nengo.Probe(ref, synapse=None)
    return net


def build_cascade_net(gains, s, dt, ref_fn, x0=(0.0, 0.0, 0.0, 0.0),
                      neuron_type=None, tau=0.01, seed=1, g=G):
    neuron_type = neuron_type if neuron_type is not None else nengo.LIF()
    net = nengo.Network(label="Cascade NEF", seed=seed)
    with net:
        plant = nengo.Node(CascadePlantNode(dt, s, x0), size_in=1, size_out=4,
                           label="plant[p,v,a,rate]")
        ref = nengo.Node(ref_fn, label="p_ref")

        # --- outer (position) loop ---
        e_p = nengo.Ensemble(200, 1, radius=3.0, neuron_type=neuron_type, label="e_pos")
        de_p = nengo.Ensemble(200, 1, radius=2.0, neuron_type=neuron_type, label="de_pos")
        u_pos = nengo.Ensemble(300, 1, radius=12.0, neuron_type=neuron_type, label="u_pos")
        nengo.Connection(ref, e_p, transform=1.0, synapse=tau)
        nengo.Connection(plant[0], e_p, transform=-1.0, synapse=tau)
        nengo.Connection(plant[1], de_p, transform=-1.0, synapse=tau)
        nengo.Connection(e_p, u_pos, transform=gains.Kp_p, synapse=tau)
        nengo.Connection(de_p, u_pos, transform=gains.Kd_p, synapse=tau)

        # --- virtual control command: a_des = atan2(s*u_pos, g)  (nonlinear node) ---
        a_des = nengo.Node(lambda t, x: float(np.clip(np.arctan2(s * x[0], g),
                                                      -TILT_MAX, TILT_MAX)),
                           size_in=1, label="a_des")
        nengo.Connection(u_pos, a_des, synapse=tau)

        # --- inner (angle) loop ---
        e_a = nengo.Ensemble(200, 1, radius=1.0, neuron_type=neuron_type, label="e_ang")
        de_a = nengo.Ensemble(200, 1, radius=4.0, neuron_type=neuron_type, label="de_ang")
        u_tau = nengo.Ensemble(400, 1, radius=50.0, neuron_type=neuron_type, label="tau")
        nengo.Connection(a_des, e_a, transform=1.0, synapse=tau)
        nengo.Connection(plant[2], e_a, transform=-1.0, synapse=tau)
        nengo.Connection(plant[3], de_a, transform=-1.0, synapse=tau)
        nengo.Connection(e_a, u_tau, transform=gains.Kp_a, synapse=tau)
        nengo.Connection(de_a, u_tau, transform=gains.Kd_a, synapse=tau)
        nengo.Connection(u_tau, plant, synapse=tau)

        net.p_state = nengo.Probe(plant, synapse=None)
        net.p_u = nengo.Probe(u_tau, synapse=0.01)
        net.p_ref = nengo.Probe(ref, synapse=None)
        net.p_ades = nengo.Probe(a_des, synapse=0.01)
    return net
