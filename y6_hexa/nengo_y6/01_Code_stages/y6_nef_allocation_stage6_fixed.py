"""
y6_nef_allocation.py  —  Stage 6
==================================
The **control allocation** layer (mixer) is implemented as an NEF ensemble.

The allocation is a purely linear map:
    F = A_mix * [T, tau_x, tau_y, tau_z]

where A_mix is the 6×4 mixer matrix derived in y6_model.allocate().

NEF realisation:
  * One 4-D ensemble ``e_cmd`` represents [T, tau_x, tau_y, tau_z].
  * Six linear decode connections produce F_1..F_6 simultaneously.
  * A follow-up Node applies the nonlinear inversion F -> omega (square-root +
    saturation) — this nonlinearity is retained as a Node for now; Stage 8 will
    absorb it.

The inner attitude loop (Stage 4) and outer position loop (Stage 5) are reused
here so the only new component is the neural allocation ensemble.

Run:
    python y6_nef_allocation.py
Nengo GUI:
    nengo y6_nef_allocation.py
"""

import numpy as np
import nengo
import y6_model as y6
from y6_model import Params, Gains
from y6_nengo import Y6Plant, default_ref
from y6_nef_attitude import _make_err_node
from y6_nef_position_fixed import _build_pos_loop
from y6_snn_integral import IntegralGains


# ---------------------------------------------------------------------------
# Build the 6×4 mixer matrix  (same math as y6_model.allocate)
# ---------------------------------------------------------------------------
def _build_mixer_matrix(P=Params):
    k1   = 1.0 / (P.l1 + P.l3)
    kpsi = P.KF / (6.0 * P.Ktau)
    # Rows: F1..F6,  Cols: T, tau_x, tau_y, tau_z
    A = np.array([
        [ 0.5*P.l1*k1/2, -1.0/(4*P.l2), -k1/4,  kpsi],  # F1 back-right top
        [ 0.5*P.l1*k1/2, -1.0/(4*P.l2), -k1/4, -kpsi],  # F2 back-right bot
        [ 0.5*(1 - P.l1*k1),  0,          k1/2,  kpsi],  # F3 front top
        [ 0.5*(1 - P.l1*k1),  0,          k1/2, -kpsi],  # F4 front bot
        [ 0.5*P.l1*k1/2,  1.0/(4*P.l2), -k1/4,  kpsi],  # F5 back-left top
        [ 0.5*P.l1*k1/2,  1.0/(4*P.l2), -k1/4, -kpsi],  # F6 back-left bot
    ])
    return A


def _omega_from_F(t, F_cmd):
    """Node: F (6,) -> omega (6,) via square-root inversion + clip."""
    return y6.thrust_to_omega(F_cmd)


# ---------------------------------------------------------------------------
# Full network builder
# ---------------------------------------------------------------------------
def build_network(ref_fn=default_ref, x0=None, alpha_fn=None,
                  n_cmd=600, tau_syn=0.01,
                  P=Params, G=Gains, Gi=IntegralGains):
    """
    Parameters
    ----------
    n_cmd   : neurons in the 4-D allocation ensemble  (600 recommended)
    """
    plant_obj = Y6Plant(x0=x0, alpha_fn=alpha_fn, P=P)
    A_mix     = _build_mixer_matrix(P)

    net = nengo.Network(label="Y6 Stage-6: NEF allocation")
    with net:
        plant = nengo.Node(plant_obj, size_in=6, size_out=12, label="plant")
        omega_node = nengo.Node(_omega_from_F, size_in=6, size_out=6,
                                label="F_to_omega")

        # --- NEF outer position loop (Stage 5) ---
        outer_out = _build_pos_loop(net, plant, ref_fn, P=P, G=G)

        # --- SNN inner attitude loop (Stage 4) ---
        axes = [
            dict(label="phi",   Kp=G.Kp_phi, Kd=G.Kd_phi, Ki=Gi.Ki_phi,
                 r_err=0.70, r_rate=3.0, r_int=0.30),
            dict(label="theta", Kp=G.Kp_the, Kd=G.Kd_the, Ki=Gi.Ki_the,
                 r_err=0.70, r_rate=3.0, r_int=0.30),
            dict(label="psi",   Kp=G.Kp_psi, Kd=G.Kd_psi, Ki=Gi.Ki_psi,
                 r_err=3.20, r_rate=2.0, r_int=1.00),
        ]
        n_att     = 500
        tau_att   = 0.01
        rec_A     = 0.9998

        tau_xyz = nengo.Node(lambda t, x: x, size_in=3, size_out=3,
                             label="tau_xyz")

        for i, ax in enumerate(axes):
            err_node = nengo.Node(_make_err_node(f"err_{ax['label']}"),
                                  size_in=2, size_out=1,
                                  label=f"err_{ax['label']}")
            nengo.Connection(outer_out[1 + i:2 + i], err_node[0:1], synapse=None)
            nengo.Connection(plant[6 + i:7 + i],     err_node[1:2], synapse=None)

            e_err = nengo.Ensemble(n_att, 1, radius=ax['r_err'],
                                   neuron_type=nengo.LIF(),
                                   label=f"e_err_{ax['label']}")
            nengo.Connection(err_node, e_err, synapse=tau_att)

            e_rate = nengo.Ensemble(n_att, 1, radius=ax['r_rate'],
                                    neuron_type=nengo.LIF(),
                                    label=f"e_rate_{ax['label']}")
            nengo.Connection(plant[9 + i:10 + i], e_rate, synapse=tau_att)

            e_int = nengo.Ensemble(n_att, 1, radius=ax['r_int'],
                                   neuron_type=nengo.LIF(),
                                   label=f"e_int_{ax['label']}")
            nengo.Connection(e_err, e_int,
                             transform=[[1.0 - rec_A]], synapse=tau_att)
            nengo.Connection(e_int, e_int,
                             transform=[[rec_A]], synapse=tau_att)

            nengo.Connection(e_err,  tau_xyz[i:i + 1],
                             transform=[[ax['Kp']]], synapse=tau_att)
            nengo.Connection(e_rate, tau_xyz[i:i + 1],
                             transform=[[-ax['Kd']]], synapse=tau_att)
            nengo.Connection(e_int,  tau_xyz[i:i + 1],
                             transform=[[ax['Ki']]], synapse=tau_att)

        # ----------------------------------------------------------------
        # NEF allocation: 4-D ensemble [T, tau_x, tau_y, tau_z]
        # ----------------------------------------------------------------
        e_cmd = nengo.Ensemble(n_cmd, 4,
                               radius=35.2,
                               label="e_cmd")

        nengo.Connection(outer_out[0:1], e_cmd[0:1], synapse=tau_syn)
        nengo.Connection(tau_xyz,        e_cmd[1:4], synapse=tau_syn)

        # Six linear decode connections (one per rotor thrust)
        F_node = nengo.Node(lambda t, x: x, size_in=6, size_out=6, label="F_cmd")
        for j in range(6):
            nengo.Connection(e_cmd, F_node[j:j + 1],
                             function=lambda x, row=A_mix[j]: np.dot(row, x),
                             synapse=tau_syn)

        # F -> omega (nonlinear Node)
        nengo.Connection(F_node,    omega_node, synapse=None)
        nengo.Connection(omega_node, plant,      synapse=None)

        # --- Probes ---
        net.p_state  = nengo.Probe(plant,      synapse=None)
        net.p_omega  = nengo.Probe(omega_node, synapse=None)
        net.p_F      = nengo.Probe(F_node,     synapse=0.02)
        net.p_tau    = nengo.Probe(tau_xyz,    synapse=0.02)

    net.plant_obj = plant_obj
    net.A_mix     = A_mix
    return net


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    net = build_network(default_ref)
    with nengo.Simulator(net, dt=0.001, progress_bar=True) as sim:
        sim.run(12.0)

    t  = sim.trange()
    st = sim.data[net.p_state]
    import y6_model as y6m
    print("=== Stage 6: NEF control allocation ===")
    print("final pos = (%.4f, %.4f, %.4f) m   target (1, -0.5, 2.0)"
          % (st[-1, y6m.IX], st[-1, y6m.IY], st[-1, y6m.IZ]))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        for idx, lbl in zip([y6m.IX, y6m.IY, y6m.IZ], ["x", "y", "z"]):
            axes[0].plot(t, st[:, idx], label=lbl)
        axes[0].set_title("Position (Stage 6: NEF allocation)")
        axes[0].set_xlabel("t [s]"); axes[0].legend()
        axes[1].plot(t, sim.data[net.p_omega])
        axes[1].set_title("Rotor speeds [rad/s]"); axes[1].set_xlabel("t [s]")
        plt.tight_layout()
        plt.savefig("y6_nef_allocation_demo.png", dpi=110)
        print("saved y6_nef_allocation_demo.png")
    except ImportError:
        pass
