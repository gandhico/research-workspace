"""
altitude_nef.py  —  NEF / Nengo altitude controller (Phase 2).

Neuromorphic equivalent of the classical PD + gravity feed-forward law.  The
SAME 1-DOF plant (``altitude_1dof``) is wrapped as a ``nengo.Node``, so the only
difference from the classical run is that the *feedback control law is computed
by populations of neurons*:

    e_z   ensemble  represents   z_ref - z              (altitude error)
    de_z  ensemble  represents   zdot_ref - zdot = -zdot (error rate)
    u_fb  ensemble  represents   Kp e_z + Kd de_z        (PD feedback thrust)

The constant gravity feed-forward  m g  is added downstream as a feedforward
Node (it is a known constant, not a computation), keeping the neural ensemble
``u_fb`` centred near zero for good decoding resolution.  Total command:

    u = m g + Kp e_z + Kd de_z

Two design notes vs. Victor's per-axis Nengo code (Quad1Z.py):
  * velocity ``zdot`` is read from the plant state (full-state feedback), which
    removes the noisy dual-synapse finite-difference differentiator;
  * everything else (Principle-3 readout, linear decoders for the PD gains) is
    the standard NEF construction.
"""
import numpy as np
import nengo

from src.models.altitude_1dof import AltitudePlantNode, step_reference


def build_network(P, G, dt, t_step=1.0, z_target=1.0, x0=(0.0, 0.0),
                  neuron_type=None, n_err=200, n_rate=200, n_u=400,
                  tau=0.01, seed=1):
    """Build the closed-loop altitude-control network.

    Parameters mirror the classical run so the comparison is apples-to-apples.
    ``neuron_type`` selects LIF (spiking) vs. RectifiedLinear (rate) etc.
    """
    neuron_type = neuron_type if neuron_type is not None else nengo.LIF()

    net = nengo.Network(label="Altitude NEF controller", seed=seed)
    with net:
        # --- plant (identical dynamics to the classical run) ---
        plant = nengo.Node(AltitudePlantNode(P, dt, x0),
                           size_in=1, size_out=2, label="plant[z,zdot]")

        # --- exogenous inputs ---
        ref = nengo.Node(lambda t: step_reference(t, t_step, z_target, x0[0]),
                         label="z_ref")
        grav = nengo.Node(P.u_hover, label="mg (grav FF)")

        # --- neural populations ---
        e_z = nengo.Ensemble(n_err, 1, radius=1.5,
                             neuron_type=neuron_type, label="e_z")
        de_z = nengo.Ensemble(n_rate, 1, radius=3.0,
                              neuron_type=neuron_type, label="de_z")
        u_fb = nengo.Ensemble(n_u, 1, radius=12.0,
                              neuron_type=neuron_type, label="u_fb (PD)")

        # summation / actuator node (passthrough: sums mg + PD feedback)
        u_cmd = nengo.Node(size_in=1, label="u_cmd")

        # error  e = z_ref - z
        nengo.Connection(ref, e_z, transform=1.0, synapse=tau)
        nengo.Connection(plant[0], e_z, transform=-1.0, synapse=tau)
        # error rate  de = zdot_ref - zdot = -zdot
        nengo.Connection(plant[1], de_z, transform=-1.0, synapse=tau)
        # PD feedback  u_fb = Kp e + Kd de
        nengo.Connection(e_z, u_fb, transform=G.Kp, synapse=tau)
        nengo.Connection(de_z, u_fb, transform=G.Kd, synapse=tau)
        # total command  u = mg + u_fb
        nengo.Connection(grav, u_cmd, transform=1.0, synapse=tau)
        nengo.Connection(u_fb, u_cmd, transform=1.0, synapse=tau)
        # close the loop
        nengo.Connection(u_cmd, plant, synapse=None)

        # probes (raw plant state; filtered command read-out)
        net.p_state = nengo.Probe(plant, synapse=None)
        net.p_u = nengo.Probe(u_cmd, synapse=0.01)
        net.p_ref = nengo.Probe(ref, synapse=None)
    return net
