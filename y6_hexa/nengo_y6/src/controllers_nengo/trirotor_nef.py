"""
trirotor_nef.py  —  full NEF/Nengo controller for the coaxial Y6 trirotor (Phase 5).

Same neuromorphic recipe as the quad (Phase 4) PLUS the new piece: a **neural control
allocator**.  The six PD commands are each one neuron population; the geometric
inversions (world velocity, tilt set-points, thrust) are Nodes; and the 6x4 mixer is
realised as a 4-D ensemble ``e_cmd`` representing [T, tau_x, tau_y, tau_z] from which
six linear decoders read the six rotor-thrust demands.  (Pattern from
01_Code/y6_nef_allocation.py.)

The 4 virtual commands live on very different scales (T ~ 14 N vs tau ~ 1 N*m), so
``e_cmd`` represents the *normalised* command and the mixer scale is folded into the
decoders — this keeps a single scalar-radius ensemble well-conditioned.
"""
import numpy as np
import nengo

from src.models.coaxial_trirotor import (TrirotorPlantNode, TrirotorParams, R_EB,
                                         IX, IY, IZ, IU, IV, IW, IPHI, ITHE, IPSI, IP, IQ, IR)
from src.allocation.y6_allocation import build_mixer_matrix, thrust_to_omega


def _pd(net, sources, radius, neuron_type, tau, label, n=300):
    """One population representing a weighted sum (a PD command).

    sources = list of (signal_slice, gain); the ensemble represents sum(gain*signal).
    """
    with net:
        ens = nengo.Ensemble(n, 1, radius=radius, neuron_type=neuron_type, label=label)
        for sig, gain in sources:
            nengo.Connection(sig, ens, transform=gain, synapse=tau)
    return ens


def _integrator(net, err_sources, radius, neuron_type, tau, label, leak=0.9995, n=200):
    """NEF leaky integrator: v = integral of sum(gain*signal) dt (canonical NEF form,
    recurrent transform ~1 with synapse tau, input transform tau).  The leak (<1) and
    the ensemble radius bound drift / windup.  Used for outer-loop integral action.
    """
    with net:
        I = nengo.Ensemble(n, 1, radius=radius, neuron_type=neuron_type, label=label)
        nengo.Connection(I, I, transform=leak, synapse=tau)
        for sig, g in err_sources:
            nengo.Connection(sig, I, transform=g, synapse=tau)
    return I


def build_network(dt, gains, ref_fn, x0=None, neuron_type=None, tau=0.01,
                  seed=1, n_cmd=800, integral_gains=None,
                  P: TrirotorParams = TrirotorParams()):
    G = gains
    neuron_type = neuron_type if neuron_type is not None else nengo.LIF()
    A = build_mixer_matrix(P)
    scale = np.array([35.0, 2.5, 2.5, 1.2])     # normalisation of [T, tx, ty, tz]

    net = nengo.Network(label="Y6 trirotor NEF", seed=seed)
    with net:
        plant = nengo.Node(TrirotorPlantNode(dt, x0, P=P), size_in=6, size_out=12,
                           label="trirotor plant")
        refs = nengo.Node(lambda t: ref_fn(t), size_out=4, label="ref[x,y,z,psi]")

        # world-frame velocity (nonlinear): [phi,theta,psi,u,v,w] -> [vx,vy,vz]
        wvel = nengo.Node(lambda t, s: R_EB(s[0], s[1], s[2]) @ s[3:6],
                          size_in=6, size_out=3, label="world_vel")
        nengo.Connection(plant[[IPHI, ITHE, IPSI, IU, IV, IW]], wvel, synapse=tau)

    # ---- outer position PD (neural) -> ax_des, ay_des, u_fb_z ----
    ax = _pd(net, [(refs[0], G.Kp_xy), (plant[IX], -G.Kp_xy), (wvel[0], -G.Kd_xy)],
             radius=7.0, neuron_type=neuron_type, tau=tau, label="ax_des")
    ay = _pd(net, [(refs[1], G.Kp_xy), (plant[IY], -G.Kp_xy), (wvel[1], -G.Kd_xy)],
             radius=7.0, neuron_type=neuron_type, tau=tau, label="ay_des")
    ufbz = _pd(net, [(refs[2], G.Kp_z), (plant[IZ], -G.Kp_z), (wvel[2], -G.Kd_z)],
               radius=15.0, neuron_type=neuron_type, tau=tau, label="u_fb_z")

    with net:
        # tilt set-points (nonlinear, psi-dependent): [ax,ay,psi] -> [theta*,phi*]
        def _attdes(t, v):
            ax_, ay_, psi = v
            cps, sps = np.cos(psi), np.sin(psi)
            th = np.clip((ax_ * cps + ay_ * sps) / P.g, -G.tilt_max, G.tilt_max)
            ph = np.clip((ax_ * sps - ay_ * cps) / P.g, -G.tilt_max, G.tilt_max)
            return [th, ph]
        att_des = nengo.Node(_attdes, size_in=3, size_out=2, label="theta*,phi*")
        nengo.Connection(ax, att_des[0], synapse=tau)
        nengo.Connection(ay, att_des[1], synapse=tau)
        nengo.Connection(plant[IPSI], att_des[2], synapse=tau)

        # thrust (nonlinear): [u_fb_z, phi, theta] -> T
        def _thrust(t, v):
            ufb, phi, theta = v
            T = (P.m * P.g + ufb) / max(np.cos(phi) * np.cos(theta), 0.5)
            return float(np.clip(T, 0.0, G.T_to_w * P.m * P.g))
        Tnode = nengo.Node(_thrust, size_in=3, size_out=1, label="T")
        nengo.Connection(ufbz, Tnode[0], synapse=tau)
        nengo.Connection(plant[IPHI], Tnode[1], synapse=tau)
        nengo.Connection(plant[ITHE], Tnode[2], synapse=tau)

    # ---- inner attitude PD (neural) -> tau_x, tau_y, tau_z ----
    tx = _pd(net, [(att_des[1], G.Kp_phi), (plant[IPHI], -G.Kp_phi), (plant[IP], -G.Kd_phi)],
             radius=2.5, neuron_type=neuron_type, tau=tau, label="tau_x")
    ty = _pd(net, [(att_des[0], G.Kp_the), (plant[ITHE], -G.Kp_the), (plant[IQ], -G.Kd_the)],
             radius=2.5, neuron_type=neuron_type, tau=tau, label="tau_y")
    tz = _pd(net, [(refs[3], G.Kp_psi), (plant[IPSI], -G.Kp_psi), (plant[IR], -G.Kd_psi)],
             radius=1.2, neuron_type=neuron_type, tau=tau, label="tau_z")

    # ---- optional outer-loop INTEGRAL action (Phase 5a): reject decode bias ----
    if integral_gains is not None:
        Ig = integral_gains
        Ix = _integrator(net, [(refs[0], tau), (plant[IX], -tau)], 4.0, neuron_type, tau, "I_x")
        Iy = _integrator(net, [(refs[1], tau), (plant[IY], -tau)], 4.0, neuron_type, tau, "I_y")
        Iz = _integrator(net, [(refs[2], tau), (plant[IZ], -tau)], 4.0, neuron_type, tau, "I_z")
        Ipsi = _integrator(net, [(refs[3], tau), (plant[IPSI], -tau)], 2.0, neuron_type, tau, "I_psi")
        with net:
            nengo.Connection(Ix, ax, transform=Ig.Ki_xy, synapse=tau)
            nengo.Connection(Iy, ay, transform=Ig.Ki_xy, synapse=tau)
            nengo.Connection(Iz, ufbz, transform=Ig.Ki_z, synapse=tau)
            nengo.Connection(Ipsi, tz, transform=Ig.Ki_psi, synapse=tau)

    with net:
        # ---- NEURAL ALLOCATION: 4-D ensemble (normalised) -> 6 rotor thrusts ----
        e_cmd = nengo.Ensemble(n_cmd, 4, radius=1.8, neuron_type=neuron_type, label="e_cmd")
        nengo.Connection(Tnode, e_cmd[0], transform=1.0 / scale[0], synapse=tau)
        nengo.Connection(tx, e_cmd[1], transform=1.0 / scale[1], synapse=tau)
        nengo.Connection(ty, e_cmd[2], transform=1.0 / scale[2], synapse=tau)
        nengo.Connection(tz, e_cmd[3], transform=1.0 / scale[3], synapse=tau)

        F_node = nengo.Node(size_in=6, label="F_cmd")     # six rotor thrusts
        for j in range(6):
            w = A[j] * scale                               # fold normalisation into decoder
            nengo.Connection(e_cmd, F_node[j],
                             function=lambda x, w=w: float(np.dot(w, x)), synapse=tau)

        # F -> omega (nonlinear) -> plant
        omega_node = nengo.Node(lambda t, F: thrust_to_omega(F, P), size_in=6, size_out=6,
                                label="F_to_omega")
        nengo.Connection(F_node, omega_node, synapse=None)
        nengo.Connection(omega_node, plant, synapse=None)

        net.p_state = nengo.Probe(plant, synapse=None)
        net.p_omega = nengo.Probe(omega_node, synapse=0.01)
        net.p_F = nengo.Probe(F_node, synapse=0.01)
        net.p_ref = nengo.Probe(refs, synapse=None)
    return net
