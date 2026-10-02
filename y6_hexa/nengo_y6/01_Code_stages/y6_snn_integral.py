"""
y6_snn_integral.py  —  Stage 4
================================
Extends Stage 3 with a **neural integrator** on each attitude axis.

Architecture per axis (e.g. roll):
  e_err_phi   : 1-D LIF, represents phi_err               (proportional)
  e_rate_phi  : 1-D LIF, represents p                     (derivative)
  e_int_phi   : 1-D LIF, recurrent, integrates phi_err    (integral)

  tau_x = Kp * phi_err  -  Kd * p  +  Ki * integral(phi_err)

The neural integrator is implemented as a recurrent ensemble:
  input -> e_int   (scaled by dt / tau_int)
  e_int -> e_int   (recurrent weight A = 1 — perfect integrator in the NEF)

In practice, use A slightly < 1 (e.g. 0.9998 at dt=0.001) to give a very slow
leak that prevents run-away accumulation.  This is equivalent to a leaky
integrator with time constant tau_int = -dt / ln(A).

Run:
    python y6_snn_integral.py
Nengo GUI:
    nengo y6_snn_integral.py
"""

import numpy as np
import nengo
import y6_model as y6
from y6_model import Params, Gains
from y6_nengo import Y6Plant, default_ref
from y6_nef_attitude import _PosCtrl, _allocator, _make_err_node


class IntegralGains:
    """Integral gains (small — integral action is a trim correction)."""
    Ki_phi = 0.08
    Ki_the = 0.08
    Ki_psi = 0.04


# ---------------------------------------------------------------------------
# Network builder
# ---------------------------------------------------------------------------
def build_network(ref_fn=default_ref, x0=None, alpha_fn=None,
                  n_neurons=500, tau_syn=0.01,
                  recurrent_A=0.9998,
                  P=Params, G=Gains, Gi=IntegralGains):
    """
    Parameters
    ----------
    recurrent_A : integrator recurrent weight  (<1 for leaky, =1 for perfect)
    """
    plant_obj    = Y6Plant(x0=x0, alpha_fn=alpha_fn, P=P)
    pos_ctrl_obj = _PosCtrl(ref_fn, P=P, G=G)

    axes = [
        dict(label="phi",   Kp=G.Kp_phi, Kd=G.Kd_phi, Ki=Gi.Ki_phi,
             r_err=0.70, r_rate=3.0, r_int=0.30),
        dict(label="theta", Kp=G.Kp_the, Kd=G.Kd_the, Ki=Gi.Ki_the,
             r_err=0.70, r_rate=3.0, r_int=0.30),
        dict(label="psi",   Kp=G.Kp_psi, Kd=G.Kd_psi, Ki=Gi.Ki_psi,
             r_err=3.20, r_rate=2.0, r_int=1.00),
    ]

    net = nengo.Network(label="Y6 Stage-4: SNN attitude + neural integrator")
    with net:
        plant     = nengo.Node(plant_obj,    size_in=6,  size_out=12, label="plant")
        pos_ctrl  = nengo.Node(pos_ctrl_obj, size_in=12, size_out=4,  label="pos_ctrl")
        allocator = nengo.Node(_allocator,   size_in=4,  size_out=6,  label="allocator")
        tau_xyz   = nengo.Node(lambda t, x: x, size_in=3, size_out=3, label="tau_xyz")

        nengo.Connection(plant, pos_ctrl, synapse=0)

        net.ens_err  = []
        net.ens_rate = []
        net.ens_int  = []

        for i, ax in enumerate(axes):
            # --- error subtraction ---
            err_node = nengo.Node(_make_err_node(f"err_{ax['label']}"),
                                  size_in=2, size_out=1,
                                  label=f"err_{ax['label']}")
            nengo.Connection(pos_ctrl[1 + i:2 + i], err_node[0:1], synapse=None)
            nengo.Connection(plant[6 + i:7 + i],    err_node[1:2], synapse=None)

            # --- PD ensembles (LIF) ---
            e_err = nengo.Ensemble(n_neurons, 1, radius=ax['r_err'],
                                   neuron_type=nengo.LIF(),
                                   label=f"e_err_{ax['label']}")
            nengo.Connection(err_node, e_err, synapse=tau_syn)

            e_rate = nengo.Ensemble(n_neurons, 1, radius=ax['r_rate'],
                                    neuron_type=nengo.LIF(),
                                    label=f"e_rate_{ax['label']}")
            nengo.Connection(plant[9 + i:10 + i], e_rate, synapse=tau_syn)

            # --- neural integrator (recurrent LIF ensemble) ---
            e_int = nengo.Ensemble(n_neurons, 1, radius=ax['r_int'],
                                   neuron_type=nengo.LIF(),
                                   label=f"e_int_{ax['label']}")
            # feed-in: error drives the integrator
            nengo.Connection(e_err, e_int,
                             transform=[[1.0 - recurrent_A]],
                             synapse=tau_syn)
            # recurrent self-connection (identity decode)
            nengo.Connection(e_int, e_int,
                             transform=[[recurrent_A]],
                             synapse=tau_syn)

            # --- decode to tau_i ---
            nengo.Connection(e_err,  tau_xyz[i:i + 1],
                             transform=[[ax['Kp']]], synapse=tau_syn)
            nengo.Connection(e_rate, tau_xyz[i:i + 1],
                             transform=[[-ax['Kd']]], synapse=tau_syn)
            nengo.Connection(e_int,  tau_xyz[i:i + 1],
                             transform=[[ax['Ki']]], synapse=tau_syn)

            net.ens_err.append(e_err)
            net.ens_rate.append(e_rate)
            net.ens_int.append(e_int)

        nengo.Connection(pos_ctrl[0:1], allocator[0:1], synapse=None)
        nengo.Connection(tau_xyz,       allocator[1:4], synapse=None)
        nengo.Connection(allocator,     plant,          synapse=None)

        # --- Probes ---
        net.p_state   = nengo.Probe(plant,     synapse=None)
        net.p_omega   = nengo.Probe(allocator, synapse=None)
        net.p_tau     = nengo.Probe(tau_xyz,   synapse=0.02)
        net.p_int_phi = nengo.Probe(net.ens_int[0], synapse=0.02)

    net.plant_obj = plant_obj
    return net


# ---------------------------------------------------------------------------
# Demo / standalone run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    net = build_network(default_ref)
    with nengo.Simulator(net, dt=0.001, progress_bar=True) as sim:
        sim.run(12.0)

    t  = sim.trange()
    st = sim.data[net.p_state]
    import y6_model as y6m
    print("=== Stage 4: SNN attitude + neural integrator ===")
    print("final pos = (%.4f, %.4f, %.4f) m   target (1, -0.5, 2.0)"
          % (st[-1, y6m.IX], st[-1, y6m.IY], st[-1, y6m.IZ]))
    print("rotor speed range = [%.1f, %.1f] rad/s"
          % (sim.data[net.p_omega].min(), sim.data[net.p_omega].max()))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(14, 4))

        for idx, lbl in zip([y6m.IX, y6m.IY, y6m.IZ], ["x", "y", "z"]):
            axes[0].plot(t, st[:, idx], label=lbl)
        axes[0].set_title("Position (Stage 4: SNN + integrator)")
        axes[0].set_xlabel("t [s]"); axes[0].legend()

        tau_data = sim.data[net.p_tau]
        for idx, lbl in zip(range(3), ["tau_x", "tau_y", "tau_z"]):
            axes[1].plot(t, tau_data[:, idx], label=lbl)
        axes[1].set_title("Body moments [N·m]")
        axes[1].set_xlabel("t [s]"); axes[1].legend()

        axes[2].plot(t, sim.data[net.p_int_phi], label="int(phi_err)")
        axes[2].set_title("Neural integrator state (roll)")
        axes[2].set_xlabel("t [s]"); axes[2].legend()

        plt.tight_layout()
        plt.savefig("y6_snn_integral_demo.png", dpi=110)
        print("saved y6_snn_integral_demo.png")
    except ImportError:
        pass
