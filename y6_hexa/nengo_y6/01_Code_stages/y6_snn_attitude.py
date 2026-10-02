"""
y6_snn_attitude.py  —  Stage 3
================================
Identical wiring to Stage 2 (y6_nef_attitude.py) but neuron type is
``nengo.LIF()`` — integrate-and-fire spikes.

Design differences from Stage 2:
  * ``neuron_type = nengo.LIF()``      instead of RectifiedLinear
  * More neurons (500 per ensemble)    to compensate for spike noise
  * Output synapse on ensemble->tau    connections is 0.01 s (vs 0.005 s)
    to low-pass the spike train and recover a smooth moment command

Run:
    python y6_snn_attitude.py
Nengo GUI:
    nengo y6_snn_attitude.py
"""

import numpy as np
import nengo
import y6_model as y6
from y6_model import Params, Gains
from y6_nengo import Y6Plant, default_ref
from y6_nef_attitude import _PosCtrl, _allocator, _make_err_node


# ---------------------------------------------------------------------------
# Network builder  (same structure as Stage 2, LIF neurons)
# ---------------------------------------------------------------------------
def build_network(ref_fn=default_ref, x0=None, alpha_fn=None,
                  n_neurons=500, tau_syn=0.01,
                  P=Params, G=Gains):
    """
    Parameters
    ----------
    n_neurons : neurons per 1-D ensemble  (500 recommended for LIF accuracy)
    tau_syn   : post-synaptic time constant for spike smoothing  [s]
    """
    plant_obj    = Y6Plant(x0=x0, alpha_fn=alpha_fn, P=P)
    pos_ctrl_obj = _PosCtrl(ref_fn, P=P, G=G)

    axes = [
        dict(label="phi",   Kp=G.Kp_phi, Kd=G.Kd_phi, r_err=0.70, r_rate=3.0),
        dict(label="theta", Kp=G.Kp_the, Kd=G.Kd_the, r_err=0.70, r_rate=3.0),
        dict(label="psi",   Kp=G.Kp_psi, Kd=G.Kd_psi, r_err=3.20, r_rate=2.0),
    ]

    net = nengo.Network(label="Y6 Stage-3: SNN attitude (LIF)")
    with net:
        plant     = nengo.Node(plant_obj, size_in=6, size_out=12, label="plant")
        pos_ctrl  = nengo.Node(pos_ctrl_obj, size_in=12, size_out=4,
                               label="pos_ctrl")
        allocator = nengo.Node(_allocator, size_in=4, size_out=6,
                               label="allocator")
        tau_xyz   = nengo.Node(lambda t, x: x, size_in=3, size_out=3,
                               label="tau_xyz")

        nengo.Connection(plant, pos_ctrl, synapse=0)

        net.ens_err  = []
        net.ens_rate = []

        for i, ax in enumerate(axes):
            err_node = nengo.Node(_make_err_node(f"err_{ax['label']}"),
                                  size_in=2, size_out=1,
                                  label=f"err_{ax['label']}")
            nengo.Connection(pos_ctrl[1 + i:2 + i], err_node[0:1], synapse=None)
            nengo.Connection(plant[6 + i:7 + i],    err_node[1:2], synapse=None)

            e_err = nengo.Ensemble(n_neurons, 1,
                                   radius=ax['r_err'],
                                   neuron_type=nengo.LIF(),
                                   label=f"e_err_{ax['label']}")
            nengo.Connection(err_node, e_err, synapse=tau_syn)

            e_rate = nengo.Ensemble(n_neurons, 1,
                                    radius=ax['r_rate'],
                                    neuron_type=nengo.LIF(),
                                    label=f"e_rate_{ax['label']}")
            nengo.Connection(plant[9 + i:10 + i], e_rate, synapse=tau_syn)

            nengo.Connection(e_err,  tau_xyz[i:i + 1],
                             transform=[[ax['Kp']]], synapse=tau_syn)
            nengo.Connection(e_rate, tau_xyz[i:i + 1],
                             transform=[[-ax['Kd']]], synapse=tau_syn)

            net.ens_err.append(e_err)
            net.ens_rate.append(e_rate)

        nengo.Connection(pos_ctrl[0:1], allocator[0:1], synapse=None)
        nengo.Connection(tau_xyz,       allocator[1:4], synapse=None)
        nengo.Connection(allocator,     plant,          synapse=None)

        # --- Probes ---
        net.p_state   = nengo.Probe(plant,    synapse=None)
        net.p_omega   = nengo.Probe(allocator, synapse=None)
        net.p_att_des = nengo.Probe(pos_ctrl[1:4], synapse=None)
        net.p_tau     = nengo.Probe(tau_xyz,  synapse=0.02)
        # Spike rasters for the first roll-error ensemble
        net.p_spikes_err0  = nengo.Probe(net.ens_err[0].neurons,  synapse=None)
        net.p_spikes_rate0 = nengo.Probe(net.ens_rate[0].neurons, synapse=None)

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
    print("=== Stage 3: SNN attitude (LIF) ===")
    print("final pos = (%.4f, %.4f, %.4f) m   target (1, -0.5, 2.0)"
          % (st[-1, y6m.IX], st[-1, y6m.IY], st[-1, y6m.IZ]))
    print("rotor speed range = [%.1f, %.1f] rad/s"
          % (sim.data[net.p_omega].min(), sim.data[net.p_omega].max()))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 2, figsize=(13, 9))

        for idx, lbl in zip([y6m.IX, y6m.IY, y6m.IZ], ["x", "y", "z"]):
            axes[0, 0].plot(t, st[:, idx], label=lbl)
        axes[0, 0].set_title("Position (Stage 3: SNN att)")
        axes[0, 0].set_xlabel("t [s]"); axes[0, 0].legend()

        axes[0, 1].plot(t, sim.data[net.p_omega])
        axes[0, 1].set_title("Rotor speeds [rad/s]"); axes[0, 1].set_xlabel("t [s]")

        tau_data = sim.data[net.p_tau]
        for idx, lbl in zip(range(3), ["tau_x", "tau_y", "tau_z"]):
            axes[1, 0].plot(t, tau_data[:, idx], label=lbl)
        axes[1, 0].set_title("Body moments [N·m]")
        axes[1, 0].set_xlabel("t [s]"); axes[1, 0].legend()

        # spike raster for roll-error ensemble (first 50 neurons)
        spk = sim.data[net.p_spikes_err0][:, :50]
        spike_times = np.where(spk > 0)
        axes[1, 1].scatter(t[spike_times[0]], spike_times[1],
                           s=0.4, c="k", alpha=0.5)
        axes[1, 1].set_title("Spike raster: e_err_phi (50 neurons)")
        axes[1, 1].set_xlabel("t [s]"); axes[1, 1].set_ylabel("neuron #")

        plt.tight_layout()
        plt.savefig("y6_snn_attitude_demo.png", dpi=110)
        print("saved y6_snn_attitude_demo.png")
    except ImportError:
        pass
