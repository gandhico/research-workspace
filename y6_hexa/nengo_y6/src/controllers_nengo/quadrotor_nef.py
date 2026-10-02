"""
quadrotor_nef.py  —  full NEF/Nengo quadrotor controller (Phase 4, the full system).

Neuromorphic version of quadrotor_pd.py: the six PD control laws (altitude, yaw,
x, y, pitch, roll) are each computed by neuron populations, while the three
*nonlinear inversions* stay in Nodes (exactly the maps Victor inverts analytically):

    u       = (u_fb_z + m g) / (cos theta cos phi)
    theta_d = atan2( u_x , g )                     (x outer -> pitch set-point)
    phi_d   = atan2( -u_y cos theta , g )          (y outer -> roll  set-point)

Each PD channel uses the Phase-2/3 recipe: an error ensemble + a rate ensemble feed
a command ensemble whose input connections carry the gains (so the population
represents the scaled command, well inside its radius).
"""
import numpy as np
import nengo

from src.models.quadrotor import QuadPlantNode, QuadParams, x_ref, x_ref_dot, y_ref, y_ref_dot, z_ref

P = QuadParams()


def _pd_channel(net, ref_err_sources, rate_sources, kp, kv, r_e, r_de, r_cmd,
                neuron_type, tau, label, n=200, n_cmd=300):
    """Build one PD channel: returns the command ensemble decoding kp*e + kv*de.

    ref_err_sources / rate_sources are lists of (signal, transform) feeding the
    error and rate ensembles respectively.
    """
    with net:
        e = nengo.Ensemble(n, 1, radius=r_e, neuron_type=neuron_type, label=f"e_{label}")
        de = nengo.Ensemble(n, 1, radius=r_de, neuron_type=neuron_type, label=f"de_{label}")
        cmd = nengo.Ensemble(n_cmd, 1, radius=r_cmd, neuron_type=neuron_type, label=f"cmd_{label}")
        for sig, tr in ref_err_sources:
            nengo.Connection(sig, e, transform=tr, synapse=tau)
        for sig, tr in rate_sources:
            nengo.Connection(sig, de, transform=tr, synapse=tau)
        nengo.Connection(e, cmd, transform=kp, synapse=tau)
        nengo.Connection(de, cmd, transform=kv, synapse=tau)
    return cmd


def build_network(dt, gains, neuron_type=None, tau=0.01, seed=1, x0=None):
    K = gains
    neuron_type = neuron_type if neuron_type is not None else nengo.LIF()
    net = nengo.Network(label="Full quad NEF", seed=seed)
    with net:
        plant = nengo.Node(QuadPlantNode(dt, x0), size_in=4, size_out=12, label="quad plant")
        # references
        xd = nengo.Node(x_ref, label="x_d"); dxd = nengo.Node(x_ref_dot, label="dx_d")
        yd = nengo.Node(y_ref, label="y_d"); dyd = nengo.Node(y_ref_dot, label="dy_d")
        zd = nengo.Node(z_ref, label="z_d")
        # plant state indices: x0 dx1 y2 dy3 z4 dz5 psi6 dpsi7 theta8 dtheta9 phi10 dphi11

    # ---- altitude: u_fb_z = kp_z(z_d-z) + kv_z(-dz) ----
    ufbz = _pd_channel(net, [(zd, 1.0), (plant[4], -1.0)], [(plant[5], -1.0)],
                       K.kp_z, K.kv_z, 0.5, 0.5, 15.0, neuron_type, tau, "z")
    # ---- yaw: tau_psi = kp_psi(0-psi) + kv_psi(-dpsi) ----
    tpsi = _pd_channel(net, [(plant[6], -1.0)], [(plant[7], -1.0)],
                       K.kp_psi, K.kv_psi, 0.4, 0.5, 8.0, neuron_type, tau, "psi")
    # ---- x outer: u_x = kp_x(x_d-x) + kv_x(dx_d-dx) ----
    ux = _pd_channel(net, [(xd, 1.0), (plant[0], -1.0)], [(dxd, 1.0), (plant[1], -1.0)],
                     K.kp_x, K.kv_x, 0.4, 0.4, 2.5, neuron_type, tau, "x")
    # ---- y outer: u_y = kp_y(y_d-y) + kv_y(dy_d-dy) ----
    uy = _pd_channel(net, [(yd, 1.0), (plant[2], -1.0)], [(dyd, 1.0), (plant[3], -1.0)],
                     K.kp_y, K.kv_y, 0.4, 0.4, 4.0, neuron_type, tau, "y")

    with net:
        # nonlinear inversions (Nodes)
        u_node = nengo.Node(lambda t, v: (v[0] + P.m * P.g) / (np.cos(v[1]) * np.cos(v[2])),
                            size_in=3, label="u = (u_fb+mg)/cos cos")
        nengo.Connection(ufbz, u_node[0], synapse=tau)
        nengo.Connection(plant[8], u_node[1], synapse=tau)
        nengo.Connection(plant[10], u_node[2], synapse=tau)

        theta_d = nengo.Node(lambda t, v: float(np.arctan2(v[0], P.g)), size_in=1, label="theta_d")
        nengo.Connection(ux, theta_d, synapse=tau)

        phi_d = nengo.Node(lambda t, v: float(np.arctan2(-v[0] * np.cos(v[1]), P.g)),
                           size_in=2, label="phi_d")
        nengo.Connection(uy, phi_d[0], synapse=tau)
        nengo.Connection(plant[8], phi_d[1], synapse=tau)

    # ---- pitch inner: tau_theta = kp_theta(theta_d-theta) + kv_theta(-dtheta) ----
    tth = _pd_channel(net, [(theta_d, 1.0), (plant[8], -1.0)], [(plant[9], -1.0)],
                      K.kp_theta, K.kv_theta, 0.4, 1.0, 40.0, neuron_type, tau, "theta")
    # ---- roll inner: tau_phi = kp_phi(phi_d-phi) + kv_phi(-dphi) ----
    tph = _pd_channel(net, [(phi_d, 1.0), (plant[10], -1.0)], [(plant[11], -1.0)],
                      K.kp_phi, K.kv_phi, 0.4, 1.0, 30.0, neuron_type, tau, "phi")

    with net:
        # assemble plant input [u, tau_psi, tau_theta, tau_phi]
        uvec = nengo.Node(size_in=4, label="[u,tau_psi,tau_theta,tau_phi]")
        nengo.Connection(u_node, uvec[0], synapse=tau)
        nengo.Connection(tpsi, uvec[1], synapse=tau)
        nengo.Connection(tth, uvec[2], synapse=tau)
        nengo.Connection(tph, uvec[3], synapse=tau)
        nengo.Connection(uvec, plant, synapse=None)

        net.p_state = nengo.Probe(plant, synapse=None)
        net.p_u = nengo.Probe(uvec, synapse=0.01)
    return net
