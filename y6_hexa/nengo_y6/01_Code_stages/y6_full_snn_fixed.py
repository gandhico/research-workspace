"""
y6_full_snn.py  —  Stage 8
============================
**Full SNN controller** — every computational layer is implemented as a Nengo
spiking (LIF) ensemble.  The only remaining Nodes are:
  * ``plant``     : physics integration (not a controller, has to be a Node)
  * ``ref_node``  : external reference signal
  * ``yaw_trig``  : sin/cos(psi) pre-processor  (trig, stays as Node)
  * ``F_to_omega``: square-root inversion + saturation  (nonlinear, stays as Node)

All PD/integral attitude control, the yaw-mixed position loop, and the linear
allocation matrix are represented by LIF ensembles with appropriate decoders.

Network topology (all boxes are LIF ensembles unless noted):
  ref_node (Node)
       |
  e_pos_xy  [x_err, y_err, vx, vy]  -> acc_des [ax, ay]
  e_yaw_mix [ax, ay, cpsi, spsi]    -> [phi_des, theta_des]
  e_alt     [z_err, vz]             -> T
       |
  e_err_{phi,the,psi}  [att_error]
  e_rate_{phi,the,psi} [body_rate]
  e_int_{phi,the,psi}  [integrator] (recurrent)
       |  tau_xyz [tau_x, tau_y, tau_z]
  e_cmd [T, tau_x, tau_y, tau_z]   -> F_cmd (+ PES learning)
       |
  F_to_omega (Node: sqrt + clip)
       |
  plant (Node: RK4 EoM)

Run:
    python y6_full_snn.py
Nengo GUI:
    nengo y6_full_snn.py
"""

import numpy as np
import nengo
import y6_model as y6
from y6_model import Params, Gains
from y6_nengo import Y6Plant, default_ref
from y6_nef_attitude import _make_err_node
from y6_nef_position_fixed import _yaw_trig, _world_vel, _tilt_clip
from y6_nef_allocation_stage6_fixed import _build_mixer_matrix, _omega_from_F
from y6_snn_integral import IntegralGains


# ---------------------------------------------------------------------------
# Network builder
# ---------------------------------------------------------------------------
def build_network(ref_fn=default_ref, x0=None, alpha_fn=None,
                  # Neuron counts (reduce for speed, increase for accuracy)
                  n_pos_xy=600, n_yaw_mix=800, n_alt=300,
                  n_att=500, n_cmd=800,
                  tau_syn=0.01, recurrent_A=0.9998,
                  learning_rate=5e-6,
                  P=Params, G=Gains, Gi=IntegralGains):
    """Full SNN controller for the Y6 coaxial tricopter."""

    plant_obj = Y6Plant(x0=x0, alpha_fn=alpha_fn, P=P)
    A_mix     = _build_mixer_matrix(P)

    axes_att = [
        dict(label="phi",   Kp=G.Kp_phi, Kd=G.Kd_phi, Ki=Gi.Ki_phi,
             r_err=0.70, r_rate=3.0, r_int=0.30),
        dict(label="theta", Kp=G.Kp_the, Kd=G.Kd_the, Ki=Gi.Ki_the,
             r_err=0.70, r_rate=3.0, r_int=0.30),
        dict(label="psi",   Kp=G.Kp_psi, Kd=G.Kd_psi, Ki=Gi.Ki_psi,
             r_err=3.20, r_rate=2.0, r_int=1.00),
    ]

    net = nengo.Network(label="Y6 Stage-8: Full SNN controller")
    with net:
        # ----------------------------------------------------------------
        # I/O Nodes (physics / signals — not controller logic)
        # ----------------------------------------------------------------
        plant      = nengo.Node(plant_obj, size_in=6, size_out=12, label="plant")
        ref_node   = nengo.Node(lambda t: np.array(ref_fn(t)),
                                size_out=4, label="reference")
        yaw_trig   = nengo.Node(_yaw_trig, size_in=12, size_out=2, label="yaw_trig")
        wvel_node  = nengo.Node(_world_vel, size_in=6, size_out=3, label="world_vel")
        omega_node = nengo.Node(_omega_from_F, size_in=6, size_out=6,
                                label="F_to_omega")

        nengo.Connection(plant, yaw_trig, synapse=None)
        nengo.Connection(plant[y6.IPHI:y6.IPSI + 1], wvel_node[0:3], synapse=None)
        nengo.Connection(plant[y6.IU:y6.IW + 1],     wvel_node[3:6], synapse=None)

        # ----------------------------------------------------------------
        # Outer position loop  (all LIF)
        # ----------------------------------------------------------------

        # XY PD: [x_err, y_err, vx, vy] -> [ax_des, ay_des]
        xy_err_node = nengo.Node(lambda t, x: x[0:2] - x[2:4],
                                 size_in=4, size_out=2, label="xy_err")
        nengo.Connection(ref_node[0:2], xy_err_node[0:2], synapse=None)
        nengo.Connection(plant[y6.IX:y6.IY + 1], xy_err_node[2:4], synapse=None)

        e_pos_xy = nengo.Ensemble(n_pos_xy, 4,
                                  radius=7.1,
                                  neuron_type=nengo.LIF(),
                                  label="e_pos_xy")
        nengo.Connection(xy_err_node,  e_pos_xy[0:2], synapse=tau_syn)
        nengo.Connection(wvel_node[0:2], e_pos_xy[2:4], synapse=tau_syn)

        A_xy = np.array([
            [G.Kp_xy, 0,       -G.Kd_xy, 0      ],
            [0,       G.Kp_xy,  0,       -G.Kd_xy],
        ])
        acc_des = nengo.Node(lambda t, x: x, size_in=2, size_out=2,
                             label="acc_des")
        nengo.Connection(e_pos_xy, acc_des,
                         function=lambda x: A_xy @ x, synapse=tau_syn)

        # Yaw mixing: [ax_des, ay_des, cpsi, spsi] -> [phi_des, theta_des]
        e_yaw_mix = nengo.Ensemble(n_yaw_mix, 4,
                                   radius=4.5,
                                   neuron_type=nengo.LIF(),
                                   label="e_yaw_mix")
        nengo.Connection(acc_des,  e_yaw_mix[0:2], synapse=tau_syn)
        nengo.Connection(yaw_trig, e_yaw_mix[2:4], synapse=tau_syn)

        def _decode_att(x):
            ax, ay, cpsi, spsi = x
            return np.array([(ax * spsi - ay * cpsi) / P.g,   # phi_des
                             (ax * cpsi + ay * spsi) / P.g])  # theta_des

        att_des_raw = nengo.Node(lambda t, x: x, size_in=2, size_out=2,
                                 label="att_des_raw")
        nengo.Connection(e_yaw_mix, att_des_raw, function=_decode_att,
                         synapse=tau_syn)
        att_des_clip = nengo.Node(_tilt_clip, size_in=2, size_out=2,
                                  label="att_des_clip")
        nengo.Connection(att_des_raw, att_des_clip, synapse=None)

        # Altitude PD: [z_err, vz] -> T
        z_err_node = nengo.Node(lambda t, x: np.array([x[0] - x[1], x[2]]),
                                size_in=3, size_out=2, label="z_err")
        nengo.Connection(ref_node[2],  z_err_node[0:1], synapse=None)
        nengo.Connection(plant[y6.IZ], z_err_node[1:2], synapse=None)
        nengo.Connection(wvel_node[2], z_err_node[2:3], synapse=None)

        e_alt = nengo.Ensemble(n_alt, 2,
                               radius=6.5,
                               neuron_type=nengo.LIF(),
                               label="e_alt")
        nengo.Connection(z_err_node, e_alt, synapse=tau_syn)

        def _decode_thrust(x):
            z_err, vz = x
            T = (P.m * P.g + G.Kp_z * z_err - G.Kd_z * vz) / 0.9
            return np.clip(T, 0.0, G.T_max * P.m * P.g)

        T_node = nengo.Node(lambda t, x: x, size_in=1, size_out=1, label="T")
        nengo.Connection(e_alt, T_node, function=_decode_thrust, synapse=tau_syn)

        # ----------------------------------------------------------------
        # Inner attitude loop  (LIF + integrators)
        # ----------------------------------------------------------------
        tau_xyz     = nengo.Node(lambda t, x: x, size_in=3, size_out=3,
                                 label="tau_xyz")
        att_err_all = nengo.Node(lambda t, x: x, size_in=3, size_out=3,
                                 label="att_err_all")

        net.ens_att = []
        for i, ax in enumerate(axes_att):
            err_node = nengo.Node(_make_err_node(f"err_{ax['label']}"),
                                  size_in=2, size_out=1,
                                  label=f"err_{ax['label']}")
            # att_des: phi_des and theta_des from clip node, psi_des from ref
            if i < 2:
                nengo.Connection(att_des_clip[i:i + 1], err_node[0:1], synapse=None)
            else:
                nengo.Connection(ref_node[3], err_node[0:1], synapse=None)
            nengo.Connection(plant[6 + i:7 + i], err_node[1:2], synapse=None)
            nengo.Connection(err_node, att_err_all[i:i + 1], synapse=None)

            e_err = nengo.Ensemble(n_att, 1, radius=ax['r_err'],
                                   neuron_type=nengo.LIF(),
                                   label=f"e_err_{ax['label']}")
            nengo.Connection(err_node, e_err, synapse=tau_syn)

            e_rate = nengo.Ensemble(n_att, 1, radius=ax['r_rate'],
                                    neuron_type=nengo.LIF(),
                                    label=f"e_rate_{ax['label']}")
            nengo.Connection(plant[9 + i:10 + i], e_rate, synapse=tau_syn)

            e_int = nengo.Ensemble(n_att, 1, radius=ax['r_int'],
                                   neuron_type=nengo.LIF(),
                                   label=f"e_int_{ax['label']}")
            nengo.Connection(e_err, e_int,
                             transform=[[1.0 - recurrent_A]], synapse=tau_syn)
            nengo.Connection(e_int, e_int,
                             transform=[[recurrent_A]], synapse=tau_syn)

            nengo.Connection(e_err,  tau_xyz[i:i + 1],
                             transform=[[ax['Kp']]], synapse=tau_syn)
            nengo.Connection(e_rate, tau_xyz[i:i + 1],
                             transform=[[-ax['Kd']]], synapse=tau_syn)
            nengo.Connection(e_int,  tau_xyz[i:i + 1],
                             transform=[[ax['Ki']]], synapse=tau_syn)

            net.ens_att.append((e_err, e_rate, e_int))

        # ----------------------------------------------------------------
        # Neural control allocation  (LIF, 4-D)
        # ----------------------------------------------------------------
        e_cmd = nengo.Ensemble(n_cmd, 4,
                               radius=35.2,
                               neuron_type=nengo.LIF(),
                               label="e_cmd")
        nengo.Connection(T_node,  e_cmd[0:1], synapse=tau_syn)
        nengo.Connection(tau_xyz, e_cmd[1:4], synapse=tau_syn)

        F_node = nengo.Node(lambda t, x: x, size_in=6, size_out=6, label="F_cmd")
        for j in range(6):
            nengo.Connection(e_cmd, F_node[j:j + 1],
                             function=lambda x, row=A_mix[j]: np.dot(row, x),
                             synapse=tau_syn)

        # PES learning connection
        def _pes_error(t, x):
            if t < 2.0:
                return np.zeros(6)
            return np.full(6, float(np.sqrt(np.dot(x, x))))

        pes_err = nengo.Node(_pes_error, size_in=3, size_out=6, label="pes_error")
        nengo.Connection(att_err_all, pes_err, synapse=0.05)

        learn_conn = nengo.Connection(
            e_cmd, F_node,
            function=lambda x: np.zeros(6),
            learning_rule_type=nengo.PES(learning_rate=learning_rate),
            synapse=tau_syn,
        )
        nengo.Connection(pes_err, learn_conn.learning_rule, synapse=None)

        nengo.Connection(F_node,     omega_node, synapse=None)
        nengo.Connection(omega_node, plant,      synapse=None)

        # ----------------------------------------------------------------
        # Probes
        # ----------------------------------------------------------------
        net.p_state   = nengo.Probe(plant,       synapse=None)
        net.p_omega   = nengo.Probe(omega_node,  synapse=None)
        net.p_tau     = nengo.Probe(tau_xyz,     synapse=0.02)
        net.p_att_err = nengo.Probe(att_err_all, synapse=0.05)
        net.p_F       = nengo.Probe(F_node,      synapse=0.02)

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
    print("=== Stage 8: Full SNN controller ===")
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
        axes[0, 0].set_title("Position (Stage 8: Full SNN)")
        axes[0, 0].set_xlabel("t [s]"); axes[0, 0].legend()

        axes[0, 1].plot(t, sim.data[net.p_omega])
        axes[0, 1].set_title("Rotor speeds [rad/s]")
        axes[0, 1].set_xlabel("t [s]")

        tau_d = sim.data[net.p_tau]
        for idx, lbl in zip(range(3), ["tau_x", "tau_y", "tau_z"]):
            axes[1, 0].plot(t, tau_d[:, idx], label=lbl)
        axes[1, 0].set_title("Body moments [N·m]")
        axes[1, 0].set_xlabel("t [s]"); axes[1, 0].legend()

        att_err_d = sim.data[net.p_att_err]
        for idx, lbl in zip(range(3), ["phi_err", "theta_err", "psi_err"]):
            axes[1, 1].plot(t, np.degrees(att_err_d[:, idx]), label=lbl)
        axes[1, 1].set_title("Attitude errors [deg]")
        axes[1, 1].set_xlabel("t [s]"); axes[1, 1].legend()

        plt.tight_layout()
        plt.savefig("y6_full_snn_demo.png", dpi=110)
        print("saved y6_full_snn_demo.png")
    except ImportError:
        pass
