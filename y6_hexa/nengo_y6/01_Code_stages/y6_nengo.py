"""
y6_nengo.py
===========
Nengo model of the Co-Axial Y6 Tricopter.

STEP 2 (this file): the plant and the cascaded controller are both plain Nengo
``Node`` objects that call the validated equations in ``y6_model.py``. This is
the math reference / oracle.

STEP 3 (next): the attitude inner loop Node will be replaced by an NEF network
(spiking ``nengo.Ensemble`` populations). The wiring below is arranged so that
swap is local -- only ``make_attitude_block`` changes.

Run:  python3 y6_nengo.py
Requires: nengo  (pip install nengo)
"""
import numpy as np
import y6_model as y6
from y6_model import Params, Gains

try:
    import nengo
except ImportError:
    nengo = None


# ---------------------------------------------------------------------------
# Plant as a stateful Node:  input = 6 rotor speeds, output = 12 states
# ---------------------------------------------------------------------------
class Y6Plant:
    """Integrates the rigid-body EoM with RK4 using the simulator's own dt."""
    def __init__(self, x0=None, alpha_fn=None, P=Params):
        self.state = np.zeros(12) if x0 is None else np.array(x0, float)
        self.alpha_fn = alpha_fn or (lambda t: np.ones(6))
        self.P = P
        self.t_prev = 0.0

    def __call__(self, t, omega):
        dt = t - self.t_prev
        self.t_prev = t
        if dt > 0:
            self.state = y6.rk4_step(self.state, omega, self.alpha_fn(t),
                                     dt, self.P)
        return self.state


# ---------------------------------------------------------------------------
# Baseline (math) controller as a Node: input = 12 states, output = 6 speeds
# ---------------------------------------------------------------------------
class BaselineController:
    def __init__(self, ref_fn, P=Params, G=Gains):
        self.ref_fn, self.P, self.G = ref_fn, P, G

    def __call__(self, t, state):
        omega, _ = y6.baseline_control(state, self.ref_fn(t), self.P, self.G)
        return omega


# ---------------------------------------------------------------------------
# Network builder
# ---------------------------------------------------------------------------
def build_network(ref_fn, x0=None, alpha_fn=None, P=Params, G=Gains):
    """Closed-loop Y6 model. Node<->Node feedback uses synapse=None, which gives
    a clean one-timestep delay and breaks the algebraic loop."""
    if nengo is None:
        raise RuntimeError("nengo is not installed in this environment.")

    plant_obj = Y6Plant(x0=x0, alpha_fn=alpha_fn, P=P)
    ctrl_obj  = BaselineController(ref_fn, P=P, G=G)

    net = nengo.Network(label="Y6 coaxial tricopter (baseline)")
    with net:
        plant = nengo.Node(plant_obj, size_in=6,  size_out=12, label="plant")
        ctrl  = nengo.Node(ctrl_obj,  size_in=12, size_out=6,  label="controller")

        nengo.Connection(ctrl, plant, synapse=None)     # omega -> plant
        nengo.Connection(plant, ctrl, synapse=0)      # state -> controller

        net.p_state = nengo.Probe(plant, synapse=None)
        net.p_omega = nengo.Probe(ctrl,  synapse=None)
    net.plant_obj = plant_obj
    return net


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def default_ref(t):
    """Hover at 1.5 m, then step to (1, -0.5, 2.0) with 20 deg yaw at t=2 s."""
    if t < 2.0:
        return (0.0, 0.0, 1.5, 0.0)
    return (1.0, -0.5, 2.0, np.radians(20.0))


if __name__ == "__main__":
    if nengo is None:
        print("Nengo not available here. Install with `pip install nengo` and "
              "run this file in your environment.")
        raise SystemExit(0)

    net = build_network(default_ref)
    with nengo.Simulator(net, dt=0.01, progress_bar=False) as sim:
        sim.run(12.0)

    t = sim.trange()
    st = sim.data[net.p_state]
    print("final pos = (%.4f, %.4f, %.4f) m   target (1, -0.5, 2.0)"
          % (st[-1, y6.IX], st[-1, y6.IY], st[-1, y6.IZ]))
    print("rotor speed range = [%.1f, %.1f] rad/s"
          % (sim.data[net.p_omega].min(), sim.data[net.p_omega].max()))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        for i, lbl in zip([y6.IX, y6.IY, y6.IZ], ["x", "y", "z"]):
            ax[0].plot(t, st[:, i], label=lbl)
        ax[0].set_title("Position (Nengo)"); ax[0].set_xlabel("t [s]"); ax[0].legend()
        ax[1].plot(t, sim.data[net.p_omega])
        ax[1].set_title("Rotor speeds"); ax[1].set_xlabel("t [s]")
        ax[1].set_ylabel("omega [rad/s]")
        plt.tight_layout(); plt.savefig("y6_nengo_demo.png", dpi=110)
        print("saved y6_nengo_demo.png")
    except ImportError:
        pass
