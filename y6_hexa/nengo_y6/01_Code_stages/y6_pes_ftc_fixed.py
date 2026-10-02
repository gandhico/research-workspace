"""
y6_pes_ftc.py  —  Stage 7
===========================
Adds **PES online learning** to the NEF control allocation layer for
fault-tolerant control (FTC).

PES  (Prescribed Error Sensitivity):
  The learning rule modifies the decoders of the allocation ensemble
  ``e_cmd`` based on a scalar error signal. The error signal is derived
  from the attitude-tracking residual:
    e_learning = ||[phi_err, theta_err, psi_err]||  (smoothed L2 norm)
  A positive residual means the current allocation is producing insufficient
  moments, so PES pushes the decoded rotor thrusts to compensate.

Fault injection:
  A rotor fault is introduced at t = fault_t by setting alpha_i = 0 for
  rotor i.  The PES rule observes the increased tracking error and adapts
  the allocation weights online.

Architecture:
  The learning connection targets F_node (the decoded per-rotor thrusts).
  A separate error_node feeds the PES learning signal.

Warning: PES convergence depends on learning rate (learning_rate) and error
  scaling.  Tune these if the vehicle diverges after fault injection.

Run:
    python y6_pes_ftc.py
Nengo GUI:
    nengo y6_pes_ftc.py
"""

import numpy as np
import nengo
import y6_model as y6
from y6_model import Params, Gains
from y6_nengo import Y6Plant, default_ref
from y6_nef_attitude import _make_err_node
from y6_nef_position_fixed import _build_pos_loop
from y6_nef_allocation_stage6_fixed import _build_mixer_matrix, _omega_from_F
from y6_snn_integral import IntegralGains


# ---------------------------------------------------------------------------
# Fault scenario helper
# ---------------------------------------------------------------------------
def make_fault_alpha(fault_rotor=0, fault_t=6.0):
    """Returns alpha_fn that kills rotor `fault_rotor` at time `fault_t`."""
    def alpha_fn(t):
        alpha = np.ones(6)
        if t >= fault_t:
            alpha[fault_rotor] = 0.0
        return alpha
    return alpha_fn


# ---------------------------------------------------------------------------
# Network builder
# ---------------------------------------------------------------------------
def build_network(ref_fn=default_ref, x0=None, alpha_fn=None,
                  fault_rotor=0, fault_t=6.0,
                  learning_rate=1e-5,
                  n_cmd=600, tau_syn=0.01,
                  P=Params, G=Gains, Gi=IntegralGains):
    """
    Parameters
    ----------
    fault_rotor  : rotor index (0-5) that fails at fault_t
    fault_t      : time of fault injection [s]
    learning_rate: PES learning rate  (tune if unstable)
    """
    if alpha_fn is None:
        alpha_fn = make_fault_alpha(fault_rotor, fault_t)

    plant_obj = Y6Plant(x0=x0, alpha_fn=alpha_fn, P=P)
    A_mix     = _build_mixer_matrix(P)

    net = nengo.Network(label="Y6 Stage-7: NEF allocation + PES FTC")
    with net:
        plant = nengo.Node(plant_obj, size_in=6, size_out=12, label="plant")
        omega_node = nengo.Node(_omega_from_F, size_in=6, size_out=6,
                                label="F_to_omega")

        # --- NEF outer position loop ---
        outer_out = _build_pos_loop(net, plant, ref_fn, P=P, G=G)

        # --- SNN inner attitude loop (Stage 4 structure) ---
        axes = [
            dict(label="phi",   Kp=G.Kp_phi, Kd=G.Kd_phi, Ki=Gi.Ki_phi,
                 r_err=0.70, r_rate=3.0, r_int=0.30),
            dict(label="theta", Kp=G.Kp_the, Kd=G.Kd_the, Ki=Gi.Ki_the,
                 r_err=0.70, r_rate=3.0, r_int=0.30),
            dict(label="psi",   Kp=G.Kp_psi, Kd=G.Kd_psi, Ki=Gi.Ki_psi,
                 r_err=3.20, r_rate=2.0, r_int=1.00),
        ]
        n_att   = 500
        tau_att = 0.01
        rec_A   = 0.9998

        tau_xyz = nengo.Node(lambda t, x: x, size_in=3, size_out=3,
                             label="tau_xyz")
        att_err_all = nengo.Node(lambda t, x: x, size_in=3, size_out=3,
                                 label="att_err_all")

        net.ens_err  = []
        for i, ax in enumerate(axes):
            err_node = nengo.Node(_make_err_node(f"err_{ax['label']}"),
                                  size_in=2, size_out=1,
                                  label=f"err_{ax['label']}")
            nengo.Connection(outer_out[1 + i:2 + i], err_node[0:1], synapse=None)
            nengo.Connection(plant[6 + i:7 + i],     err_node[1:2], synapse=None)

            # pass-through for PES error signal
            nengo.Connection(err_node, att_err_all[i:i + 1], synapse=None)

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

            net.ens_err.append(e_err)

        # ----------------------------------------------------------------
        # NEF allocation ensemble (4-D command)
        # ----------------------------------------------------------------
        e_cmd = nengo.Ensemble(n_cmd, 4,
                               radius=35.2,
                               label="e_cmd")

        nengo.Connection(outer_out[0:1], e_cmd[0:1], synapse=tau_syn)
        nengo.Connection(tau_xyz,        e_cmd[1:4], synapse=tau_syn)

        # Fixed initial decoders (pre-trained to A_mix)
        F_node = nengo.Node(lambda t, x: x, size_in=6, size_out=6, label="F_cmd")

        for j in range(6):
            nengo.Connection(e_cmd, F_node[j:j + 1],
                             function=lambda x, row=A_mix[j]: np.dot(row, x),
                             synapse=tau_syn)

        # ----------------------------------------------------------------
        # PES learning connection
        # PES error: smoothed L2 norm of attitude errors, broadcast to 6 dims
        # ----------------------------------------------------------------
        def _pes_error(t, x):
            """x = [phi_err, theta_err, psi_err] -> 6-D error broadcast."""
            norm = float(np.sqrt(np.dot(x, x)))
            # Only drive adaptation after a short warm-up
            if t < 1.0:
                return np.zeros(6)
            return np.full(6, norm)

        pes_err_node = nengo.Node(_pes_error, size_in=3, size_out=6,
                                  label="pes_error")
        nengo.Connection(att_err_all, pes_err_node, synapse=0.05)

        # Learning connection: e_cmd -> F_node with PES
        learn_conn = nengo.Connection(
            e_cmd, F_node,
            function=lambda x: np.zeros(6),   # starts at zero (offset from fixed conn)
            learning_rule_type=nengo.PES(learning_rate=learning_rate),
            synapse=tau_syn,
        )
        nengo.Connection(pes_err_node, learn_conn.learning_rule, synapse=None)

        nengo.Connection(F_node,     omega_node, synapse=None)
        nengo.Connection(omega_node, plant,      synapse=None)

        # --- Probes ---
        net.p_state    = nengo.Probe(plant,       synapse=None)
        net.p_omega    = nengo.Probe(omega_node,  synapse=None)
        net.p_F        = nengo.Probe(F_node,      synapse=0.02)
        net.p_att_err  = nengo.Probe(att_err_all, synapse=0.05)
        net.p_pes_err  = nengo.Probe(pes_err_node, synapse=0.05)

    net.plant_obj   = plant_obj
    net.fault_rotor = fault_rotor
    net.fault_t     = fault_t
    return net


# ---------------------------------------------------------------------------
# Demo  (healthy hover -> step -> fault at t=6 -> PES adaptation)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    net = build_network(default_ref, fault_rotor=0, fault_t=6.0,
                        learning_rate=1e-5)
    with nengo.Simulator(net, dt=0.001, progress_bar=True) as sim:
        sim.run(18.0)

    t  = sim.trange()
    st = sim.data[net.p_state]
    import y6_model as y6m
    print("=== Stage 7: PES fault-tolerant control ===")
    print("Fault: rotor %d killed at t=%.1f s" % (net.fault_rotor, net.fault_t))
    print("final pos = (%.4f, %.4f, %.4f) m" % (st[-1, y6m.IX], st[-1, y6m.IY], st[-1, y6m.IZ]))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 2, figsize=(13, 9))

        for idx, lbl in zip([y6m.IX, y6m.IY, y6m.IZ], ["x", "y", "z"]):
            axes[0, 0].plot(t, st[:, idx], label=lbl)
        axes[0, 0].axvline(net.fault_t, color="r", ls="--", lw=0.8,
                           label=f"fault t={net.fault_t}s")
        axes[0, 0].set_title("Position (Stage 7: PES FTC)")
        axes[0, 0].set_xlabel("t [s]"); axes[0, 0].legend()

        axes[0, 1].plot(t, sim.data[net.p_omega])
        axes[0, 1].axvline(net.fault_t, color="r", ls="--", lw=0.8)
        axes[0, 1].set_title("Rotor speeds [rad/s]"); axes[0, 1].set_xlabel("t [s]")

        att_err_data = sim.data[net.p_att_err]
        for idx, lbl in zip(range(3), ["phi_err", "theta_err", "psi_err"]):
            axes[1, 0].plot(t, np.degrees(att_err_data[:, idx]), label=lbl)
        axes[1, 0].axvline(net.fault_t, color="r", ls="--", lw=0.8)
        axes[1, 0].set_title("Attitude errors [deg]")
        axes[1, 0].set_xlabel("t [s]"); axes[1, 0].legend()

        pes_data = sim.data[net.p_pes_err]
        axes[1, 1].plot(t, pes_data[:, 0], label="PES error signal")
        axes[1, 1].axvline(net.fault_t, color="r", ls="--", lw=0.8)
        axes[1, 1].set_title("PES learning error")
        axes[1, 1].set_xlabel("t [s]"); axes[1, 1].legend()

        plt.tight_layout()
        plt.savefig("y6_pes_ftc_demo.png", dpi=110)
        print("saved y6_pes_ftc_demo.png")
    except ImportError:
        pass
