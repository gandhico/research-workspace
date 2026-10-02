"""
y6_nef_position.py  —  Stage 5
================================
The **outer position loop** is replaced by NEF ensembles while the inner
attitude loop reuses the Stage-4 SNN+integrator block.

Design choices
--------------
The position controller has a nonlinear yaw-compensation step:
  theta* = (ax_des * cos(psi) + ay_des * sin(psi)) / g
  phi*   = (ax_des * sin(psi) - ay_des * cos(psi)) / g

Encoding cos(psi) and sin(psi) in a high-D ensemble directly would require a
large 3-D (ax, ay, psi) ensemble.  Instead we factor the computation:
  1. A 4-D ensemble ``e_pos_xy`` represents [x_err, y_err, xdot, ydot] and
     decodes [ax_des, ay_des]  (linear PD in world frame).
  2. A pre-processing Node computes cos(psi)/sin(psi) from the plant state.
  3. A 3-D ensemble ``e_yaw_mix`` represents [ax_des, cos(psi), sin(psi)] and
     decodes the yaw-mixed [theta_des, phi_des] via a bilinear function.
  4. A 2-D ensemble ``e_alt`` represents [z_err, zdot] and decodes T (linear).

This keeps each ensemble's dimensionality small while capturing the nonlinear
yaw-mixing faithfully.

Run:
    python y6_nef_position.py
Nengo GUI:
    nengo y6_nef_position.py
"""

import numpy as np
import nengo
import y6_model as y6
from y6_model import Params, Gains
from y6_nengo import Y6Plant, default_ref
from y6_nef_attitude import _allocator, _make_err_node
from y6_snn_integral import build_network as _build_att_int_net, IntegralGains


# ---------------------------------------------------------------------------
# Helper callables
# ---------------------------------------------------------------------------
def _yaw_trig(t, state):
    """Extract (cos(psi), sin(psi)) from the 12-D plant state."""
    psi = state[y6.IPSI]
    return np.array([np.cos(psi), np.sin(psi)])


def _world_vel(t, x):
    """Convert body-frame velocity to world frame.
    x = [phi, theta, psi, u, v, w]  ->  [vx, vy, vz]
    """
    phi, theta, psi = x[0], x[1], x[2]
    uvw = x[3:6]
    return y6.R_EB(phi, theta, psi) @ uvw


def _tilt_clip(t, x):
    """Clip theta_des, phi_des to tilt_max and apply sign convention."""
    lim = Gains.tilt_max
    return np.clip(x, -lim, lim)


# ---------------------------------------------------------------------------
# NEF outer-loop builder  (returns sub-network, not the full network)
# ---------------------------------------------------------------------------
def _build_pos_loop(net, plant, ref_fn,
                    n_xy=400, n_alt=200, n_yaw_mix=500,
                    tau_syn=0.01, P=Params, G=Gains):
    """
    Builds the NEF position loop inside ``net`` and returns a 4-D Node whose
    output is [T, phi_des, theta_des, psi_des].
    """
    with net:
        # --- reference Node ---
        ref_node = nengo.Node(lambda t: np.array(ref_fn(t)),
                              size_out=4, label="reference")

        # --- world-frame velocity pre-processor ---
        wvel = nengo.Node(_world_vel, size_in=6, size_out=3, label="world_vel")
        nengo.Connection(plant[y6.IPHI:y6.IPSI + 1], wvel[0:3], synapse=None)
        nengo.Connection(plant[y6.IU:y6.IW + 1],     wvel[3:6], synapse=None)

        # --- yaw trig pre-processor (cos psi, sin psi) ---
        yaw_trig = nengo.Node(_yaw_trig, size_in=12, size_out=2, label="yaw_trig")
        nengo.Connection(plant, yaw_trig, synapse=None)

        # ----------------------------------------------------------------
        # XY position: 4-D ensemble [x_err, y_err, vx, vy]
        # decodes [ax_des, ay_des]
        # ----------------------------------------------------------------
        e_pos_xy = nengo.Ensemble(n_xy, 4,
                                  radius=np.array([3.0, 3.0, 4.0, 4.0]),
                                  label="e_pos_xy")

        # feed position errors
        xy_err = nengo.Node(lambda t, x: x[0:2] - x[2:4],
                            size_in=4, size_out=2, label="xy_err")
        nengo.Connection(ref_node[0:2], xy_err[0:2], synapse=None)
        nengo.Connection(plant[y6.IX:y6.IY + 1], xy_err[2:4], synapse=None)

        nengo.Connection(xy_err, e_pos_xy[0:2], synapse=tau_syn)
        nengo.Connection(wvel[0:2], e_pos_xy[2:4], synapse=tau_syn)

        # linear decode: [ax_des, ay_des] = [Kp*(x_err) - Kd*(vx), ...]
        A_xy = np.array([
            [G.Kp_xy, 0,        -G.Kd_xy, 0       ],   # ax_des
            [0,       G.Kp_xy,  0,        -G.Kd_xy],    # ay_des
        ])
        acc_des = nengo.Node(lambda t, x: x, size_in=2, size_out=2,
                             label="acc_des")
        nengo.Connection(e_pos_xy, acc_des, function=lambda x: A_xy @ x,
                         synapse=tau_syn)

        # ----------------------------------------------------------------
        # Yaw mixing: 3-D ensemble [ax_des, ay_des, combined with trig]
        # We use two 3-D ensembles: one for theta_des, one for phi_des
        # input = [a_des_component, cos_psi_or_sin_psi, other_trig]
        # function = a1*trig1 + a2*trig2  (bilinear -> needs 3-D repr.)
        # ----------------------------------------------------------------
        # theta_des = (ax_des*cpsi + ay_des*spsi) / g
        # phi_des   = (ax_des*spsi - ay_des*cpsi) / g
        # We represent [ax_des, ay_des, cpsi, spsi] in a 4-D ensemble
        e_yaw_mix = nengo.Ensemble(n_yaw_mix, 4,
                                   radius=np.array([3.0, 3.0, 1.0, 1.0]),
                                   label="e_yaw_mix")
        nengo.Connection(acc_des,    e_yaw_mix[0:2], synapse=tau_syn)
        nengo.Connection(yaw_trig,   e_yaw_mix[2:4], synapse=tau_syn)

        att_des_raw = nengo.Node(lambda t, x: x, size_in=2, size_out=2,
                                 label="att_des_raw")

        def _decode_att(x):
            ax, ay, cpsi, spsi = x
            g = P.g
            theta_d = (ax * cpsi + ay * spsi) / g
            phi_d   = (ax * spsi - ay * cpsi) / g
            return np.array([phi_d, theta_d])

        nengo.Connection(e_yaw_mix, att_des_raw, function=_decode_att,
                         synapse=tau_syn)

        att_des_clip = nengo.Node(_tilt_clip, size_in=2, size_out=2,
                                  label="att_des_clip")
        nengo.Connection(att_des_raw, att_des_clip, synapse=None)

        # ----------------------------------------------------------------
        # Altitude: 2-D ensemble [z_err, vz]  -> T
        # ----------------------------------------------------------------
        e_alt = nengo.Ensemble(n_alt, 2,
                               radius=np.array([5.0, 4.0]),
                               label="e_alt")
        z_err_node = nengo.Node(lambda t, x: np.array([x[0] - x[1], x[2]]),
                                size_in=3, size_out=2, label="z_err")
        nengo.Connection(ref_node[2],   z_err_node[0:1], synapse=None)
        nengo.Connection(plant[y6.IZ],  z_err_node[1:2], synapse=None)
        nengo.Connection(wvel[2],       z_err_node[2:3], synapse=None)
        nengo.Connection(z_err_node, e_alt, synapse=tau_syn)

        # tilt-compensated thrust output
        thrust_node = nengo.Node(lambda t, x: x, size_in=1, size_out=1,
                                 label="T_raw")

        def _decode_thrust(x):
            z_err, vz = x
            phi   = 0.0    # approx: inner loop corrects attitude
            theta = 0.0
            T = (P.m * P.g + G.Kp_z * z_err - G.Kd_z * vz) / max(
                np.cos(phi) * np.cos(theta), 0.5)
            return np.clip(T, 0.0, G.T_max * P.m * P.g)

        nengo.Connection(e_alt, thrust_node, function=_decode_thrust,
                         synapse=tau_syn)

        # ----------------------------------------------------------------
        # Combine outer-loop outputs: [T, phi_des, theta_des, psi_des]
        # ----------------------------------------------------------------
        outer_out = nengo.Node(lambda t, x: x, size_in=4, size_out=4,
                               label="outer_out")
        nengo.Connection(thrust_node,       outer_out[0:1], synapse=None)
        nengo.Connection(att_des_clip[0:1], outer_out[1:2], synapse=None)  # phi_des
        nengo.Connection(att_des_clip[1:2], outer_out[2:3], synapse=None)  # theta_des
        nengo.Connection(ref_node[3],       outer_out[3:4], synapse=None)  # psi_des pass-through

    return outer_out


# ---------------------------------------------------------------------------
# Full network builder
# ---------------------------------------------------------------------------
def build_network(ref_fn=default_ref, x0=None, alpha_fn=None,
                  P=Params, G=Gains, Gi=IntegralGains):
    plant_obj = Y6Plant(x0=x0, alpha_fn=alpha_fn, P=P)

    net = nengo.Network(label="Y6 Stage-5: NEF position + SNN attitude")
    with net:
        plant     = nengo.Node(plant_obj, size_in=6, size_out=12, label="plant")
        allocator = nengo.Node(_allocator, size_in=4, size_out=6, label="allocator")

        # --- NEF outer loop ---
        outer_out = _build_pos_loop(net, plant, ref_fn, P=P, G=G)

        # --- SNN inner attitude loop (Stage 4 block) ---
        axes = [
            dict(label="phi",   Kp=G.Kp_phi, Kd=G.Kd_phi, Ki=Gi.Ki_phi,
                 r_err=0.70, r_rate=3.0, r_int=0.30),
            dict(label="theta", Kp=G.Kp_the, Kd=G.Kd_the, Ki=Gi.Ki_the,
                 r_err=0.70, r_rate=3.0, r_int=0.30),
            dict(label="psi",   Kp=G.Kp_psi, Kd=G.Kd_psi, Ki=Gi.Ki_psi,
                 r_err=3.20, r_rate=2.0, r_int=1.00),
        ]
        n_neurons = 500
        tau_syn   = 0.01
        recurrent_A = 0.9998

        tau_xyz = nengo.Node(lambda t, x: x, size_in=3, size_out=3,
                             label="tau_xyz")

        for i, ax in enumerate(axes):
            err_node = nengo.Node(_make_err_node(f"err_{ax['label']}"),
                                  size_in=2, size_out=1,
                                  label=f"err_{ax['label']}")
            # att_des from NEF outer loop (dims 1,2,3 = phi_des,theta_des,psi_des)
            nengo.Connection(outer_out[1 + i:2 + i], err_node[0:1], synapse=None)
            nengo.Connection(plant[6 + i:7 + i],     err_node[1:2], synapse=None)

            e_err = nengo.Ensemble(n_neurons, 1, radius=ax['r_err'],
                                   neuron_type=nengo.LIF(),
                                   label=f"e_err_{ax['label']}")
            nengo.Connection(err_node, e_err, synapse=tau_syn)

            e_rate = nengo.Ensemble(n_neurons, 1, radius=ax['r_rate'],
                                    neuron_type=nengo.LIF(),
                                    label=f"e_rate_{ax['label']}")
            nengo.Connection(plant[9 + i:10 + i], e_rate, synapse=tau_syn)

            e_int = nengo.Ensemble(n_neurons, 1, radius=ax['r_int'],
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

        nengo.Connection(outer_out[0:1], allocator[0:1], synapse=None)
        nengo.Connection(tau_xyz,        allocator[1:4], synapse=None)
        nengo.Connection(allocator,      plant,          synapse=None)

        net.p_state  = nengo.Probe(plant,     synapse=None)
        net.p_omega  = nengo.Probe(allocator, synapse=None)
        net.p_tau    = nengo.Probe(tau_xyz,   synapse=0.02)
        net.p_outer  = nengo.Probe(outer_out, synapse=0.02)

    net.plant_obj = plant_obj
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
    print("=== Stage 5: NEF position + SNN attitude ===")
    print("final pos = (%.4f, %.4f, %.4f) m   target (1, -0.5, 2.0)"
          % (st[-1, y6m.IX], st[-1, y6m.IY], st[-1, y6m.IZ]))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        for idx, lbl in zip([y6m.IX, y6m.IY, y6m.IZ], ["x", "y", "z"]):
            axes[0].plot(t, st[:, idx], label=lbl)
        axes[0].set_title("Position (Stage 5: NEF pos + SNN att)")
        axes[0].set_xlabel("t [s]"); axes[0].legend()
        axes[1].plot(t, sim.data[net.p_omega])
        axes[1].set_title("Rotor speeds [rad/s]"); axes[1].set_xlabel("t [s]")
        plt.tight_layout()
        plt.savefig("y6_nef_position_demo.png", dpi=110)
        print("saved y6_nef_position_demo.png")
    except ImportError:
        pass
