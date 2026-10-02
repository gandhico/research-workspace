"""
gui_exp01_altitude_nef.py  —  Nengo GUI model for the Phase-2 NEF altitude controller.

Open it interactively with:

    ..\..\.venv\Scripts\nengo.exe gui_exp01_altitude_nef.py
    (or:  python -m nengo_gui gui_exp01_altitude_nef.py)

The companion ``gui_exp01_altitude_nef.py.cfg`` pre-arranges the live displays
(altitude z vs reference, thrust u, and the neural error / PD signals) so the GUI
opens straight onto the benchmark scenario (a 1 m altitude step at t = 1 s).

This file is intentionally **self-contained** (no ``src`` package imports) so the
Nengo GUI's re-exec-on-edit is robust.  The equations mirror, exactly,
``src/models/altitude_1dof.py`` and ``src/controllers_nengo/altitude_nef.py`` — the
benchmark in ``experiments/exp01_altitude_1dof`` remains the source of truth.
"""
import numpy as np
import nengo

# --- plant / controller constants (mirror AltitudeParams + AltitudeGains) ---
M, G_ACC = 0.9, 9.81              # kg, m/s^2
U_HOVER = M * G_ACC               # N   gravity feed-forward
U_MAX = 2.5 * U_HOVER             # N   actuator ceiling
KP, KD = 8.0, 4.0                 # PD gains  (omega_n~3 rad/s, zeta~0.75)
DT = 0.001                        # s   GUI simulator step
TAU = 0.01                        # s   synapse
T_STEP, Z_TARGET = 1.0, 1.0       # step reference: 0 -> 1 m at t = 1 s


class _AltitudePlant:
    """Stateful 1-DOF altitude plant as a Nengo Node:  u [N] -> [z, zdot].

    One RK4 step per call (ZOH on u) with actuator clipping — identical dynamics
    to src/models/altitude_1dof.py.
    """

    def __init__(self, dt):
        self.dt = dt
        self.s = np.array([0.0, 0.0])

    def _deriv(self, s, u):
        return np.array([s[1], u / M - G_ACC])

    def __call__(self, t, u):
        uc = float(np.clip(u[0], 0.0, U_MAX))
        dt = self.dt
        k1 = self._deriv(self.s, uc)
        k2 = self._deriv(self.s + 0.5 * dt * k1, uc)
        k3 = self._deriv(self.s + 0.5 * dt * k2, uc)
        k4 = self._deriv(self.s + dt * k3, uc)
        self.s = self.s + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        return self.s


def _ref(t):
    return Z_TARGET if t >= T_STEP else 0.0


# Nengo GUI requires a top-level variable named ``model``.
model = nengo.Network(label="Exp01 - NEF altitude (1-DOF)")
with model:
    # --- plant + exogenous inputs ---
    plant = nengo.Node(_AltitudePlant(DT), size_in=1, size_out=2,
                       label="plant [z, zdot]")
    z_ref = nengo.Node(_ref, label="z_ref")
    mg = nengo.Node(U_HOVER, label="mg (grav FF)")

    # --- neural populations (the controller) ---
    e_z = nengo.Ensemble(200, 1, radius=1.5, label="e_z (error)")
    de_z = nengo.Ensemble(200, 1, radius=3.0, label="de_z (rate)")
    u_fb = nengo.Ensemble(400, 1, radius=12.0, label="u_fb (PD)")

    # --- summation / actuator + a monitor for the live z-vs-ref plot ---
    u_cmd = nengo.Node(size_in=1, label="u_cmd [N]")
    track = nengo.Node(size_in=2, label="z vs z_ref")

    # error  e = z_ref - z
    nengo.Connection(z_ref, e_z, transform=1.0, synapse=TAU)
    nengo.Connection(plant[0], e_z, transform=-1.0, synapse=TAU)
    # error rate  de = -zdot
    nengo.Connection(plant[1], de_z, transform=-1.0, synapse=TAU)
    # PD feedback  u_fb = Kp e + Kd de
    nengo.Connection(e_z, u_fb, transform=KP, synapse=TAU)
    nengo.Connection(de_z, u_fb, transform=KD, synapse=TAU)
    # total command  u = mg + u_fb  -> plant
    nengo.Connection(mg, u_cmd, transform=1.0, synapse=TAU)
    nengo.Connection(u_fb, u_cmd, transform=1.0, synapse=TAU)
    nengo.Connection(u_cmd, plant, synapse=None)

    # monitor wiring (altitude and its reference, for one combined plot)
    nengo.Connection(plant[0], track[0], synapse=0.01)
    nengo.Connection(z_ref, track[1], synapse=0.01)
