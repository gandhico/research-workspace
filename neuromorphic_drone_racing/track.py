"""
track.py  --  race-track geometry and per-vehicle reference trajectories.

Track: 7 square gates in a 30 x 30 x 8 m volume with a Split-S (two gates stacked
vertically, passed in opposite directions), i.e. the *format* of the Swift track
(Kaufmann et al., Nature 2023: "seven square gates arranged in a volume of 30 x 30 x 8 m,
forming a lap of 75 m", with a Split-S).  The gate POSES below are our own approximation;
the real ones are in racing_data.zip/3_quadrotor_racing_code/quadrotor_racing/params/track.yaml
(Zenodo 10.5281/zenodo.7955278) and can be dropped in with load_track_yaml().

Gate = square opening GATE_INNER x GATE_INNER, frame width GATE_BORDER, passed along its
normal n = (cos yaw, sin yaw, 0).

Reference: C2 quintic-Hermite racing line through the gate centres (straight, curvature-free
crossing of every gate), then a speed profile limited by curvature, curvature rate (lateral
jerk), tangential acceleration and -- per vehicle -- its thrust-to-weight ratio.
"""
import numpy as np

GATE_INNER = 1.5      # m, square opening (passes the Omnicopter's 0.87 x 0.96 m frontal area)
GATE_BORDER = 0.20    # m, frame bar width
GATE_DEPTH = 0.10     # m, frame thickness along the normal
PASS_LEAD = 1.2       # m, straight segment before/after each gate centre

# name, centre (x, y, z) [m], yaw of the passing direction [deg]
GATES = [
    ("G1",        (-8.0, -10.0, 2.0),    0.0),
    ("G2",        ( 6.0, -10.0, 3.0),    0.0),
    ("G3",        (12.0,  -2.0, 3.5),   90.0),
    ("G4 SplitS-top",    ( 6.0,   6.0, 5.4),  180.0),
    ("G5 SplitS-bottom", ( 6.0,   6.0, 1.8),    0.0),
    ("G6",        (12.0,  10.5, 2.5),   90.0),
    ("G7",        (-4.0,  10.5, 3.0),  180.0),
]
START = np.array([-12.0, -10.0, 0.0])   # podium
# shaping points that are not gates (keep the path clear of frames and the ground)
EXTRA = {                       # inserted AFTER the gate with this index
    3: [(2.8, 6.0, 3.6)],       # Split-S: continue -x below/behind the top gate, loop down
    4: [(9.5, 7.2, 2.1)],       # exit of the Split-S, swing towards G6
    6: [(-11.0, 6.0, 2.8), (-12.0, -4.0, 2.2)],   # west U-turn back to G1
}


def gate_normal(yaw_deg):
    a = np.radians(yaw_deg)
    return np.array([np.cos(a), np.sin(a), 0.0])


def control_points():
    pts, tags = [], []
    for i, (name, c, yaw) in enumerate(GATES):
        c, n = np.array(c), gate_normal(yaw)
        pts += [c - PASS_LEAD*n, c, c + PASS_LEAD*n]
        tags += [None, i, None]
        for e in EXTRA.get(i, []):
            pts.append(np.array(e)); tags.append(None)
    return np.array(pts), tags


class RaceLine:
    """C2 racing line: quintic Hermite segments gate-centre -> gate-centre.

    At every gate: position = gate centre, tangent = gate normal * TANGENT_GAIN*|chord|,
    second derivative = 0  ->  each gate is crossed through its centre, flying straight
    (curvature 0 there), and curvature is continuous everywhere (finite jerk at any speed).
    The Split-S needs no helper points: G4 (heading -x) -> G5 (heading +x) is a loop.
    """
    TANGENT_GAIN = 1.1
    SEG_GAIN = {3: 2.2}        # G4 -> G5 (Split-S): a roomier descending loop

    def __init__(self):
        C = [np.array(c, float) for _, c, _ in GATES]
        N = [gate_normal(y) for _, _, y in GATES]
        n = len(C)
        self.segs = []
        for i in range(n):
            j = (i + 1) % n
            L = np.linalg.norm(C[j] - C[i])
            k = self.SEG_GAIN.get(i, self.TANGENT_GAIN)
            self.segs.append((C[i], C[j], k*L*N[i], k*L*N[j]))
        # arc-length table
        uu = np.linspace(0, n, 40000*n//7 + 1)
        d1 = self._eval(uu, 1)
        sp = np.linalg.norm(d1, axis=1)
        s = np.concatenate([[0], np.cumsum(0.5*(sp[1:] + sp[:-1])*np.diff(uu))])
        self.length = float(s[-1])
        self._s, self._u = s, uu
        self.gate_s = [float(np.interp(k, uu, s)) for k in range(n)]
        self.tags = list(range(n))

    @staticmethod
    def _basis(u, der):
        """quintic Hermite basis (p0, p1, v0, v1; a0 = a1 = 0) and derivatives"""
        if der == 0:
            return (1 - 10*u**3 + 15*u**4 - 6*u**5, 10*u**3 - 15*u**4 + 6*u**5,
                    u - 6*u**3 + 8*u**4 - 3*u**5, -4*u**3 + 7*u**4 - 3*u**5)
        if der == 1:
            return (-30*u**2 + 60*u**3 - 30*u**4, 30*u**2 - 60*u**3 + 30*u**4,
                    1 - 18*u**2 + 32*u**3 - 15*u**4, -12*u**2 + 28*u**3 - 15*u**4)
        return (-60*u + 180*u**2 - 120*u**3, 60*u - 180*u**2 + 120*u**3,
                -36*u + 96*u**2 - 60*u**3, -24*u + 84*u**2 - 60*u**3)

    def _eval(self, ug, der):
        ug = np.atleast_1d(ug)
        k = np.minimum(np.floor(ug).astype(int), len(self.segs) - 1)
        u = ug - k
        out = np.zeros((len(ug), 3))
        for i, (p0, p1, v0, v1) in enumerate(self.segs):
            m = k == i
            if m.any():
                b = self._basis(u[m], der)
                out[m] = np.outer(b[0], p0) + np.outer(b[1], p1) + np.outer(b[2], v0) + np.outer(b[3], v1)
        return out

    def geom(self, s):
        """position, unit tangent, curvature vector (d2p/ds2) at arc length s (periodic)."""
        s = np.atleast_1d(s)
        u = np.interp(np.mod(s, self.length), self._s, self._u)
        d1, d2 = self._eval(u, 1), self._eval(u, 2)
        sp = np.linalg.norm(d1, axis=-1, keepdims=True)
        T = d1/sp
        K = (d2 - np.sum(d2*T, axis=-1, keepdims=True)*T)/sp**2
        return self._eval(u, 0), T, K


def speed_profile(line, s, v_max, a_lat, a_tan, j_lat=None, v0=0.0, v1=0.0):
    """Forward/backward pass on an (unrolled) arc-length grid s:
    v <= min(v_max, sqrt(a_lat/kappa), (j_lat/|dK/ds|)^(1/3)), |dv/dt| <= a_tan,
    v(start) = v0, v(end) = v1.  The jerk bound keeps the lateral-acceleration rate
    (v^3 dK/ds, from curvature changing along the spline) within the tilt bandwidth."""
    _, _, K = line.geom(s)
    kap = np.linalg.norm(K, axis=1)
    v = np.minimum(v_max, np.sqrt(a_lat/np.maximum(kap, 1e-6)))
    if j_lat is not None:
        dK = np.linalg.norm(np.gradient(K, s, axis=0), axis=1)
        v = np.minimum(v, np.cbrt(j_lat/np.maximum(dK, 1e-9)))
    v[0], v[-1] = min(v[0], v0), min(v[-1], v1)
    ds = np.diff(s)
    for i in range(1, len(s)):
        v[i] = min(v[i], np.sqrt(v[i-1]**2 + 2*a_tan*ds[i-1]))
    for i in range(len(s) - 2, -1, -1):
        v[i] = min(v[i], np.sqrt(v[i+1]**2 + 2*a_tan*ds[i]))
    return v


def jerk_limit(v, n):
    """Moving minimum then moving average over n samples: the result never exceeds v
    (each output is a mean of window-minima that all contain the sample) and its
    acceleration is continuous -> no tilt steps in the reference (bang-bang removed)."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    vm = minimum_filter1d(v, size=n, mode="nearest")
    return np.minimum(uniform_filter1d(vm, size=n, mode="nearest"), v)


class Trajectory:
    """Standing-start race for ONE vehicle, feasible for its thrust-to-weight ratio.

    Arc length is unrolled over the laps: start line RUN_UP m before G1 (v = 0), `laps` full
    laps, finish = crossing G1 again, then brake to a stop FINISH_BRAKE m later.
    """
    G = 9.81
    RUN_UP, FINISH_BRAKE, DS = 8.0, 6.0, 0.05
    JERK_WINDOW = 3.0          # m of arc length for the min+average jerk filter
    JERK_BW = 2.0              # 1/s: lateral jerk bound = JERK_BW * available acceleration
                               # (race.py passes jerk_bw = omega_att/5 from each vehicle's gains)

    def __init__(self, line, tw_ratio, laps=2, v_cap=12.0, margin=0.75, t0=0.0, jerk_bw=None):
        self.line, self.laps, self.t0 = line, laps, t0
        jerk_bw = self.JERK_BW if jerk_bw is None else jerk_bw
        g1 = line.gate_s[0]
        self.s0 = g1 - self.RUN_UP
        self.s_finish = g1 + laps*line.length
        s = np.arange(self.s0, self.s_finish + self.FINISH_BRAKE, self.DS)
        tw = margin*tw_ratio                                  # keep 25 % for attitude control
        a_avail = self.G*np.sqrt(max(tw**2 - 1.0, 0.05))      # horizontal accel. at level altitude
        v_nom = speed_profile(line, s, v_cap, 0.8*a_avail, 0.6*a_avail, j_lat=jerk_bw*a_avail)
        v_raw = v_nom
        v_nom = jerk_limit(v_nom, int(self.JERK_WINDOW/self.DS))
        # the min-filter pins v~0 over the first/last window: restore a gentle launch/brake
        # ramp at 30 % of the tangential limit (a small, bounded tilt step at the start)
        ramp = np.sqrt(2*0.3*0.6*a_avail*np.minimum(s - s[0], s[-1] - s))
        v_nom = np.maximum(v_nom, np.minimum(v_raw, ramp))
        v_nom[0] = 0.0
        v_nom[1:] = np.maximum(v_nom[1:], 1e-3)
        # uniform speed scaling until |a + g e_z| <= tw * g everywhere (climbs, Split-S)
        for scale in np.linspace(1.0, 0.2, 81):
            v = v_nom*scale
            t = self._time_of(s, v)
            if self._max_thrust_ratio(s, t, v) <= tw:
                break
        self.s_grid, self.v_grid, self.t_grid = s, v, t
        self.t_race = float(np.interp(self.s_finish, s, t))      # start line -> finish line
        self.lap_time = self.t_race/laps                          # mean lap incl. the standing start
        self.t_end = t0 + t[-1]
        self.tw_used = self._max_thrust_ratio(s, t, v)
        self.dvdt = np.gradient(v, t)

    @staticmethod
    def _time_of(s, v):
        ds = np.diff(s)
        return np.concatenate([[0], np.cumsum(2*ds/np.maximum(v[1:] + v[:-1], 1e-6))])

    def _max_thrust_ratio(self, s, t, v):
        _, T, K = self.line.geom(s)
        dvdt = np.gradient(v, t)
        a = T*dvdt[:, None] + K*(v**2)[:, None]
        return np.max(np.linalg.norm(a + np.array([0, 0, self.G]), axis=1))/self.G

    def s_at(self, t):
        return float(np.interp(t - self.t0, self.t_grid, self.s_grid))

    def ref(self, t):
        """pos, vel, acc at time t (before t0: at the start line, after the end: stopped)."""
        tl = t - self.t0
        s = float(np.interp(tl, self.t_grid, self.s_grid))
        v = float(np.interp(tl, self.t_grid, self.v_grid)) if 0 <= tl <= self.t_grid[-1] else 0.0
        a = float(np.interp(tl, self.t_grid, self.dvdt)) if 0 <= tl <= self.t_grid[-1] else 0.0
        p, T, K = self.line.geom(np.array([s]))
        return p[0], T[0]*v, T[0]*a + K[0]*v*v

    def yaw_ref(self, t):
        """Heading = passing direction of the next gate, blended from the previous gate
        (keeps the forward camera on the gate sequence, incl. through the Split-S)."""
        s = self.s_at(t)
        L, gs = self.line.length, np.array(self.line.gate_s)
        allg = np.concatenate([gs + k*L for k in range(-1, self.laps + 2)])
        k = int(np.searchsorted(allg, s))
        s_prev, s_next = allg[k - 1], allg[k]
        i_prev, i_next = (k - 1) % len(gs), k % len(gs)
        w = np.clip((s - s_prev)/(s_next - s_prev), 0, 1)
        w = 0.5 - 0.5*np.cos(np.pi*w)
        y0, y1 = np.radians(GATES[i_prev][2]), np.radians(GATES[i_next][2])
        dy = (y1 - y0 + np.pi) % (2*np.pi) - np.pi
        return y0 + w*dy


def load_track_yaml(path):
    """Replace GATES with the real Swift track (params/track.yaml) once available."""
    raise NotImplementedError("pending: download of racing_data.zip (Zenodo 7955278) not yet approved")


if __name__ == "__main__":
    L = RaceLine()
    print(f"lap length {L.length:.1f} m, gates at s = {np.round(L.gate_s, 1)}")
    for name, tw in [("CF2", 1.32), ("Y6", 2.40), ("X2", 4.0), ("Omni", 1.88)]:
        tr = Trajectory(L, tw)
        print(f"{name:5s} T/W {tw:4.2f}: 2-lap race {tr.t_race:5.1f} s, v_max {tr.v_grid.max():4.1f} m/s, "
              f"peak thrust/weight used {tr.tw_used:4.2f}")
