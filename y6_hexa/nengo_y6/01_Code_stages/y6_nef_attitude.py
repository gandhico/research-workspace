"""
y6_nef_attitude.py  —  Stage 2
================================
The inner attitude loop is replaced by three pairs of NEF ensembles (one pair
per axis: roll, pitch, yaw).  The outer position loop and control allocation
remain as plain Nengo ``Node`` objects so the NEF improvement is isolated and
easy to compare against the Stage-1 baseline.

Neuron type: ``nengo.RectifiedLinear()`` (rate-mode, no spikes yet).
Each axis uses two 1-D ensembles:
  * ``e_err_i``  — represents the scalar attitude error  (phi_des - phi, etc.)
  * ``e_rate_i`` — represents the scalar body rate        (p, q, r)
The tau output is formed by two linear decode connections:
  tau_i  =  Kp * e_err_i  +  (-Kd) * e_rate_i

Stage 3 (y6_snn_attitude.py) swaps the neuron type to LIF; everything else is
identical.

Run:
    python y6_nef_attitude.py
Nengo GUI:
    nengo y6_nef_attitude.py
"""

import numpy as np
import nengo
import y6_model as y6
from y6_model import Params, Gains
from y6_nengo import Y6Plant, default_ref


# ---------------------------------------------------------------------------
# Helpers: outer loop and allocator as thin Node callables
# ---------------------------------------------------------------------------
class _PosCtrl:
    def __init__(self, ref_fn, P=Params, G=Gains):
        self.ref_fn, self.P, self.G = ref_fn, P, G

    def __call__(self, t, state):
        T, phi_d, theta_d, psi_d = y6.position_controller(
            state, self.ref_fn(t), self.P, self.G)
        return np.array([T, phi_d, theta_d, psi_d])


def _allocator(t, x):
    """x = [T, tau_x, tau_y, tau_z]  ->  6 rotor speeds [rad/s]."""
    T, tx, ty, tz = x
    F_cmd = y6.allocate(T, tx, ty, tz)
    return y6.thrust_to_omega(F_cmd)


# ---------------------------------------------------------------------------
# Error-subtraction nodes (one per axis, avoids lambda-in-loop pitfall)
# ---------------------------------------------------------------------------
def _make_err_node(label):
    """Returns a Node callable: x=[des, actual] -> des - actual."""
    def _fn(t, x):
        return x[0] - x[1]
    _fn.__name__ = label
    return _fn


# ---------------------------------------------------------------------------
# Network builder
# ---------------------------------------------------------------------------
def build_network(ref_fn=default_ref, x0=None, alpha_fn=None,
                  n_neurons=300, tau_syn=0.005,
                  P=Params, G=Gains):
    """
    Parameters
    ----------
    ref_fn    : callable t -> (x_r, y_r, z_r, psi_r)
    x0        : initial 12-D state (default zeros = on ground)
    alpha_fn  : callable t -> (6,) fault params (default all-ones = healthy)
    n_neurons : neurons per 1-D ensemble  (300 is accurate for rate mode)
    tau_syn   : post-synaptic time constant for ensemble i/o  [s]
    """
    if nengo is None:
        raise RuntimeError("nengo is not installed.")

    plant_obj = Y6Plant(x0=x0, alpha_fn=alpha_fn, P=P)
    pos_ctrl_obj = _PosCtrl(ref_fn, P=P, G=G)

    # Per-axis gains and representation radii
    # radius = rough max magnitude of represented signal
    axes = [
        dict(label="phi",   Kp=G.Kp_phi, Kd=G.Kd_phi, r_err=0.70, r_rate=3.0),
        dict(label="theta", Kp=G.Kp_the, Kd=G.Kd_the, r_err=0.70, r_rate=3.0),
        dict(label="psi",   Kp=G.Kp_psi, Kd=G.Kd_psi, r_err=3.20, r_rate=2.0),
    ]

    net = nengo.Network(label="Y6 Stage-2: NEF attitude (rate)")
    with net:
        # ----------------------------------------------------------------
        # I/O nodes
        # ----------------------------------------------------------------
        plant = nengo.Node(plant_obj, size_in=6, size_out=12, label="plant")
        pos_ctrl = nengo.Node(pos_ctrl_obj, size_in=12, size_out=4,
                              label="pos_ctrl")
        allocator = nengo.Node(_allocator, size_in=4, size_out=6,
                               label="allocator")

        # Accumulation node: collects tau_x, tau_y, tau_z from the ensembles
        tau_xyz = nengo.Node(lambda t, x: x, size_in=3, size_out=3,
                             label="tau_xyz")

        # Plant state -> outer loop (low-pass to avoid derivative spikes)
        nengo.Connection(plant, pos_ctrl, synapse=0)

        # ----------------------------------------------------------------
        # NEF attitude block  (3 independent 1-D+1-D pairs)
        # ----------------------------------------------------------------
        net.ens_err  = []
        net.ens_rate = []

        for i, ax in enumerate(axes):
            # --- error subtraction node ---
            err_node = nengo.Node(_make_err_node(f"err_{ax['label']}"),
                                  size_in=2, size_out=1,
                                  label=f"err_{ax['label']}")

            # att_des[i] from outer loop output  (pos_ctrl dims 1,2,3)
            nengo.Connection(pos_ctrl[1 + i:2 + i], err_node[0:1],
                             synapse=None)
            # actual angle from plant state  (dims 6,7,8 = phi,theta,psi)
            nengo.Connection(plant[6 + i:7 + i], err_node[1:2],
                             synapse=None)

            # --- attitude-error ensemble ---
            e_err = nengo.Ensemble(n_neurons, 1,
                                   radius=ax['r_err'],
                                   neuron_type=nengo.RectifiedLinear(),
                                   label=f"e_err_{ax['label']}")
            nengo.Connection(err_node, e_err, synapse=tau_syn)

            # --- angular-rate ensemble ---
            e_rate = nengo.Ensemble(n_neurons, 1,
                                    radius=ax['r_rate'],
                                    neuron_type=nengo.RectifiedLinear(),
                                    label=f"e_rate_{ax['label']}")
            # plant dims 9,10,11 = p, q, r
            nengo.Connection(plant[9 + i:10 + i], e_rate, synapse=tau_syn)

            # --- linear decode -> tau_i ---
            nengo.Connection(e_err,  tau_xyz[i:i + 1],
                             transform=[[ax['Kp']]], synapse=tau_syn)
            nengo.Connection(e_rate, tau_xyz[i:i + 1],
                             transform=[[-ax['Kd']]], synapse=tau_syn)

            net.ens_err.append(e_err)
            net.ens_rate.append(e_rate)

        # ----------------------------------------------------------------
        # Allocator receives T (from pos_ctrl[0]) + tau_xyz
        # ----------------------------------------------------------------
        nengo.Connection(pos_ctrl[0:1], allocator[0:1], synapse=None)
        nengo.Connection(tau_xyz,       allocator[1:4], synapse=None)

        # Allocator drives plant
        nengo.Connection(allocator, plant, synapse=None)

        # ----------------------------------------------------------------
        # Probes
        # ----------------------------------------------------------------
        net.p_state    = nengo.Probe(plant,    synapse=None)
        net.p_omega    = nengo.Probe(allocator, synapse=None)
        net.p_att_des  = nengo.Probe(pos_ctrl[1:4], synapse=None)
        net.p_tau      = nengo.Probe(tau_xyz,  synapse=0.01)

    net.plant_obj = plant_obj
    return net


# ---------------------------------------------------------------------------
# Demo / standalone run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    net = build_network(default_ref)
    with nengo.Simulator(net, dt=0.01, progress_bar=True) as sim:
        sim.run(12.0)

    t  = sim.trange()
    st = sim.data[net.p_state]
    import y6_model as y6m
    print("=== Stage 2: NEF attitude (rate neurons) ===")
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
        axes[0].set_title("Position (Stage 2: NEF att)")
        axes[0].set_xlabel("t [s]"); axes[0].legend()

        axes[1].plot(t, sim.data[net.p_omega])
        axes[1].set_title("Rotor speeds [rad/s]")
        axes[1].set_xlabel("t [s]")

        tau_data = sim.data[net.p_tau]
        for idx, lbl in zip(range(3), ["tau_x", "tau_y", "tau_z"]):
            axes[2].plot(t, tau_data[:, idx], label=lbl)
        axes[2].set_title("Body moments [N·m]")
        axes[2].set_xlabel("t [s]"); axes[2].legend()

        plt.tight_layout()
        plt.savefig("y6_nef_attitude_demo.png", dpi=110)
        print("saved y6_nef_attitude_demo.png")
    except ImportError:
        pass
