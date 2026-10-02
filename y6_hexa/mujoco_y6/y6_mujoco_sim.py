"""
y6_mujoco_sim.py  --  Coaxial Y6 tri-rotor flying a wind-turbine inspection mission in MuJoCo.

The controllers are NOT re-written here: they are imported unchanged from the Nengo
project (nengo_y6/src, copied from the ComRob-2026 working tree on the backup drive):

  classical : src/controllers_classical/trirotor_pd.baseline_control
              (outer position PD -> tilt set-points, inner attitude PD, 6x4 Czyba mixer)
  nef_lif   : src/controllers_nengo/trirotor_nef.build_network
              (6 PD laws in LIF populations + 4-D NEF allocator e_cmd, n_cmd = 3000)

Only the PLANT changes: the RK4 Newton-Euler node is swapped for a MuJoCo rigid body
(y6_turbine_scene.xml) whose rotor sites reproduce the same force/moment map.

Mission reference = min-jerk waypoints; heading = "look at the hub".  Velocity and
acceleration feed-forward enter through reference shaping,
    x_cmd = x_ref + (Kd/Kp) v_ref + a_ref/Kp
which turns the paper's  Kp(x_cmd - x) - Kd v  into  Kp e + Kd de/dt + a_ref
without touching either controller.

Usage (hyperlif env):
    python y6_mujoco_sim.py --ctrl classical            # ~10 s
    python y6_mujoco_sim.py --ctrl nef_lif              # ~2-3 min (spiking)
    python y6_mujoco_sim.py --ctrl classical --wind 4   # 4 m/s turbine-site wind + gusts
    python y6_mujoco_sim.py --validate                  # MuJoCo plant vs Nengo RK4 plant
Outputs -> results/<ctrl>[_wind<W>].npz
"""
import sys, pathlib, time, argparse
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nengo_y6"))

import numpy as np
import mujoco

from src.models.coaxial_trirotor import (TrirotorParams, rk4_step,
                                         IX, IY, IZ, IU, IV, IW, IPHI, ITHE, IPSI, IP, IQ, IR)
from src.controllers_classical.trirotor_pd import TrirotorGains, baseline_control

P, G = TrirotorParams(), TrirotorGains()
XML = HERE / "y6_turbine_scene.xml"
RESULTS = HERE / "results"
DT = 0.001
HUB = np.array([12.0, 0.0, 8.0])        # turbine hub (rotor disc at x ~ 11.3, R = 3.7 m)
Z0 = 0.13                               # spawn height (legs just clear of the pad)

# --------------------------------------------------------------------------------------
# Mission: (time [s], x, y, z).  Straight segments are min-jerk; blades are never crossed.
# --------------------------------------------------------------------------------------
WAYPOINTS = np.array([
    [0.0,  0.0,  0.0, Z0],     # on the pad
    [2.0,  0.0,  0.0, Z0],     # spin-up
    [6.0,  0.0,  0.0, 3.0],    # take-off
    [14.0, 6.0,  0.0, 8.0],    # hub stand-off, 5.3 m upwind of the rotor disc
    [18.0, 6.0,  0.0, 8.0],    # hold: FPV camera on the hub
    [23.0, 6.0, -3.0, 6.0],    # blade sweep (low / right)
    [30.0, 6.0,  3.0, 10.0],   # blade sweep (high / left)
    [34.0, 6.0,  0.0, 8.0],    # back to hub
    [42.0, 10.0, -7.0, 8.0],   # side view of nacelle (outside the rotor disc)
    [46.0, 10.0, -7.0, 8.0],   # hold
    [56.0, 0.0,  0.0, 3.0],    # return
    [61.0, 0.0,  0.0, Z0 + 0.05],  # land
    [64.0, 0.0,  0.0, Z0 + 0.05],
])
T_END = WAYPOINTS[-1, 0]


def _minjerk(s):
    """position, velocity, acceleration shape of a min-jerk segment, s in [0,1]."""
    return (10*s**3 - 15*s**4 + 6*s**5,
            30*s**2 - 60*s**3 + 30*s**4,
            60*s - 180*s**2 + 120*s**3)


def mission_ref(t):
    """Returns pos (3,), vel (3,), acc (3,), yaw [rad], yaw_rate."""
    t = min(max(t, 0.0), T_END)
    k = np.searchsorted(WAYPOINTS[:, 0], t, side="right") - 1
    k = min(k, len(WAYPOINTS) - 2)
    t0, t1 = WAYPOINTS[k, 0], WAYPOINTS[k + 1, 0]
    p0, p1 = WAYPOINTS[k, 1:], WAYPOINTS[k + 1, 1:]
    T = t1 - t0
    s = (t - t0) / T
    a, b, c = _minjerk(s)
    pos, vel, acc = p0 + (p1 - p0)*a, (p1 - p0)*b/T, (p1 - p0)*c/T**2
    # heading: look at the hub (horizontal), analytic rate from the reference motion
    dx, dy = HUB[0] - pos[0], HUB[1] - pos[1]
    yaw = np.arctan2(dy, dx)
    yaw_rate = (dx*(-vel[1]) - dy*(-vel[0])) / (dx*dx + dy*dy)
    return pos, vel, acc, yaw, yaw_rate


def shaped_ref(t, integ=np.zeros(3)):
    """Reference fed to the (unchanged) controllers: position + feed-forward folded in.
    `integ` = optional outer-loop integral term (m/s^2 per axis), see OuterIntegral."""
    pos, vel, acc, yaw, yaw_rate = mission_ref(t)
    x = pos[0] + (G.Kd_xy/G.Kp_xy)*vel[0] + (acc[0] + integ[0])/G.Kp_xy
    y = pos[1] + (G.Kd_xy/G.Kp_xy)*vel[1] + (acc[1] + integ[1])/G.Kp_xy
    z = pos[2] + (G.Kd_z/G.Kp_z)*vel[2] + (acc[2] + integ[2])/G.Kp_z
    psi = yaw + (G.Kd_psi/G.Kp_psi)*yaw_rate
    return (x, y, z, psi)


class OuterIntegral:
    """Optional outer-loop integral action  a_I = Ki * int(p_ref - p) dt  (PD -> PID),
    injected through the reference so both controllers stay untouched.  Gains =
    TrirotorIntegralGains from the Nengo project (Ki_xy 0.5, Ki_z 2.0); clamp = anti-windup.
    NOTE: computed in a plain Python node (not neurons) -- a neural integrator / PES
    version is the next step (Phase 5a showed NEF integrators inject their own bias)."""
    def __init__(self, plant, Ki=(0.5, 0.5, 2.0), clamp=3.0, t_on=2.0):
        self.plant, self.Ki, self.clamp, self.t_on = plant, np.array(Ki), clamp, t_on
        self.I, self.t_last = np.zeros(3), 0.0

    def __call__(self, t):
        if t > self.t_last:
            if t >= self.t_on:
                e = mission_ref(t)[0] - self.plant.d.qpos[0:3]
                self.I = np.clip(self.I + self.Ki*e*(t - self.t_last), -self.clamp, self.clamp)
            self.t_last = t
        return shaped_ref(t, self.I)


# --------------------------------------------------------------------------------------
# Wind at the turbine site (optional): mean + two gust harmonics + low-pass turbulence,
# acting through a linear-drag body force  F = c_d (w - v).
# --------------------------------------------------------------------------------------
class Wind:
    def __init__(self, mean=0.0, c_d=0.35, seed=0):
        self.mean, self.c_d = mean, c_d
        self.rng = np.random.default_rng(seed)
        self.turb = np.zeros(3)

    def __call__(self, t, dt):
        if self.mean == 0.0:
            return np.zeros(3)
        a = dt / 1.5                                            # 1.5 s turbulence corr. time
        self.turb += a*(-self.turb) + np.sqrt(2*a)*0.15*self.mean*self.rng.standard_normal(3)*np.array([1, 1, 0.3])
        gust = self.mean*np.array([0.25*np.sin(0.5*t) + 0.15*np.sin(1.3*t + 1.0), 0.15*np.sin(0.7*t), 0.0])
        return np.array([self.mean, 0.0, 0.0]) + gust + self.turb


# --------------------------------------------------------------------------------------
# MuJoCo plant with the Nengo plant's interface: omega(6) in -> 12-state out
# --------------------------------------------------------------------------------------
class Y6MuJoCoPlant:
    def __init__(self, wind=0.0, turbine_speed=0.8, log_every=1):
        self.m = mujoco.MjModel.from_xml_path(str(XML))
        self.m.opt.timestep = DT
        self.d = mujoco.MjData(self.m)
        self.bid = self.m.body("y6").id
        self.wind_mean, self.turbine_speed = wind, turbine_speed
        self.reset()

    def reset(self):
        """Back to the pad (also used when Nengo GUI presses reset)."""
        m, d = self.m, self.d
        mujoco.mj_resetData(m, d)
        d.ctrl[m.actuator("shaft_speed").id] = self.turbine_speed
        d.qvel[m.joint("shaft").dofadr[0]] = self.turbine_speed
        mujoco.mj_forward(m, d)
        self.wind = Wind(self.wind_mean)
        self._R = np.zeros(9)
        self._psi_prev, self._psi_turns = 0.0, 0
        self.log = dict(t=[], state=[], omega=[], qpos=[], wind=[])

    def state12(self):
        d = self.d
        mujoco.mju_quat2Mat(self._R, d.qpos[3:7])
        R = self._R.reshape(3, 3)
        phi = np.arctan2(R[2, 1], R[2, 2])
        theta = -np.arcsin(np.clip(R[2, 0], -1.0, 1.0))
        psi_w = np.arctan2(R[1, 0], R[0, 0])
        # continuous (unwrapped) yaw so the linear yaw PD / NEF ensemble never sees a 2pi jump
        dpsi = psi_w - self._psi_prev
        if dpsi > np.pi:
            self._psi_turns -= 1
        elif dpsi < -np.pi:
            self._psi_turns += 1
        self._psi_prev = psi_w
        psi = psi_w + 2*np.pi*self._psi_turns
        s = np.zeros(12)
        s[IX:IZ + 1] = d.qpos[0:3]
        s[IU:IW + 1] = R.T @ d.qvel[0:3]            # world -> body velocity
        s[IPHI], s[ITHE], s[IPSI] = phi, theta, psi
        s[IP:IR + 1] = d.qvel[3:6]                  # free-joint angular velocity is body-frame
        return s

    def step(self, omega):
        d = self.d
        omega = np.clip(np.asarray(omega, float), 0.0, P.omega_max)
        d.ctrl[:6] = P.KF*omega**2                  # rotor thrust F_i = KF Omega_i^2
        w = self.wind(d.time, DT)
        d.xfrc_applied[self.bid, :3] = self.wind.c_d*(w - d.qvel[0:3]) if self.wind.mean else 0.0
        mujoco.mj_step(self.m, d)
        s = self.state12()
        L = self.log
        L["t"].append(d.time); L["state"].append(s); L["omega"].append(omega)
        L["qpos"].append(d.qpos.copy()); L["wind"].append(w)
        return s

    # Nengo Node callable: (t, omega) -> state
    def __call__(self, t, omega):
        return self.step(omega)


# --------------------------------------------------------------------------------------
def run_classical(plant, ref=shaped_ref):
    s = plant.state12()
    n = int(round(T_END/DT))
    for k in range(n):
        omega, _ = baseline_control(s, ref(k*DT), P, G)
        s = plant.step(omega)


def run_nef(plant, neuron_type, n_cmd=3000, seed=1, ref=shaped_ref):
    import nengo
    import src.controllers_nengo.trirotor_nef as tnef
    # swap the RK4 plant node for MuJoCo -- the network itself is built unchanged
    tnef.TrirotorPlantNode = lambda dt, x0=None, P=P: plant
    net = tnef.build_network(DT, G, ref, neuron_type=neuron_type, seed=seed, n_cmd=n_cmd)
    with nengo.Simulator(net, dt=DT, progress_bar=False) as sim:
        sim.run(T_END)


def save(plant, tag, extra=None):
    RESULTS.mkdir(exist_ok=True)
    L = {k: np.asarray(v) for k, v in plant.log.items()}
    t = L["t"]
    R = np.array([mission_ref(tt)[0] for tt in t])
    Y = np.array([mission_ref(tt)[3] for tt in t])
    out = dict(**L, ref_pos=R, ref_yaw=Y, hub=HUB, waypoints=WAYPOINTS)
    if extra:
        out.update(extra)
    np.savez_compressed(RESULTS/f"{tag}.npz", **out)
    e = L["state"][:, IX:IZ + 1] - R
    fly = (t > 6.0) & (t < 56.0)
    rmse = np.sqrt(np.mean(e[fly]**2, axis=0))
    yaw_rmse = np.degrees(np.sqrt(np.mean((L["state"][fly, IPSI] - Y[fly])**2)))
    tilt = np.degrees(np.max(np.hypot(L["state"][:, IPHI], L["state"][:, ITHE])))
    print(f"[{tag}] RMSE (6-56 s) x/y/z = {rmse[0]*100:.1f}/{rmse[1]*100:.1f}/{rmse[2]*100:.1f} cm, "
          f"yaw {yaw_rmse:.2f} deg, max tilt {tilt:.1f} deg, "
          f"omega range [{L['omega'][t > 3].min():.0f}, {L['omega'][t > 3].max():.0f}] rad/s, "
          f"final pos {np.round(L['state'][-1, :3], 3)}")
    return rmse


def validate():
    """Same classical controller, same reference: MuJoCo plant vs Nengo-project RK4 plant."""
    plant = Y6MuJoCoPlant(wind=0.0)
    s_rk = plant.state12().copy()
    n = int(round(T_END/DT))
    S_rk = np.zeros((n, 12))
    for k in range(n):
        omega, _ = baseline_control(s_rk, shaped_ref(k*DT), P, G)
        s_rk = rk4_step(s_rk, omega, np.ones(6), DT, P)
        S_rk[k] = s_rk
    run_classical(plant)
    S_mj = np.asarray(plant.log["state"])
    d = S_mj[:, :3] - S_rk[:, :3]
    t = np.asarray(plant.log["t"])
    np.savez_compressed(RESULTS/"validate_mj_vs_rk4.npz", t=t, S_mj=S_mj, S_rk=S_rk)
    print(f"[validate] MuJoCo vs RK4 plant, classical ctrl: max |dpos| = {np.abs(d).max()*1000:.2f} mm, "
          f"RMS = {np.sqrt(np.mean(d**2))*1000:.3f} mm, max |dyaw| = "
          f"{np.degrees(np.abs(S_mj[:, IPSI]-S_rk[:, IPSI]).max()):.4f} deg")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctrl", choices=["classical", "nef_lif", "nef_rate"], default="classical")
    ap.add_argument("--wind", type=float, default=0.0, help="mean wind speed at the site [m/s]")
    ap.add_argument("--n_cmd", type=int, default=3000)
    ap.add_argument("--integral", action="store_true", help="add outer-loop integral (PD -> PID)")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    RESULTS.mkdir(exist_ok=True)
    if a.validate:
        validate(); sys.exit()
    tag = a.ctrl + (f"_wind{a.wind:g}" if a.wind else "") + ("_int" if a.integral else "")
    plant = Y6MuJoCoPlant(wind=a.wind)
    ref = OuterIntegral(plant) if a.integral else shaped_ref
    t0 = time.time()
    if a.ctrl == "classical":
        run_classical(plant, ref)
    else:
        import nengo
        run_nef(plant, nengo.LIF() if a.ctrl == "nef_lif" else nengo.RectifiedLinear(),
                n_cmd=a.n_cmd, ref=ref)
    wall = time.time() - t0
    print(f"[{tag}] simulated {T_END:.0f} s in {wall:.1f} s wall")
    save(plant, tag, extra=dict(wall=wall))
