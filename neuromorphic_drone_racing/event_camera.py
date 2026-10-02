"""
event_camera.py  --  DVS (dynamic vision sensor) emulator for MuJoCo cameras.

MuJoCo has no event sensor, but it renders any camera off-screen (mujoco.Renderer).  An
event camera reports, per pixel and asynchronously, when log-intensity has changed by a
contrast threshold C since that pixel's last event:

    L(x,y,t) = log(I(x,y,t) + eps)
    event e_k = (x, y, t_k, p_k)  when  |L(x,y,t_k) - L_ref(x,y)| >= C_p,  p_k = sign,
    then L_ref <- L_ref + p_k C_p                                   (Gallego et al., TPAMI 2022)

Emulation (the ESIM / v2e recipe: Rebecq et al. CoRL 2018; Hu et al. CVPRW 2021):
  * render grayscale frames at a high rate (default 1 kHz of simulated time, i.e. far above
    video rate: events get sub-millisecond timestamps by interpolation, not by frame time);
  * between two frames, L is interpolated linearly per pixel and every threshold crossing
    becomes one event with its interpolated timestamp;
  * sensor non-idealities (all optional, defaults loosely follow the v2e "clean" preset):
      - per-pixel threshold mismatch  C ~ N(C0, sigma_C)            (fixed-pattern)
      - refractory period t_ref: a pixel cannot fire twice within t_ref
      - background-activity (leak/shot) noise: Poisson rate per pixel
      - optional intensity-dependent pixel bandwidth (1st-order low-pass on L; darker = slower)

Output: structured numpy array with fields t [us, int64], x, y [uint16], p [int8, +1/-1].
Geometry defaults to the iniVation DAVIS346 (346 x 260).  Limitations: no motion blur in
the source frames, linear-in-time log-intensity between frames, no pixel latency jitter.
"""
import numpy as np
import mujoco

EVENT_DTYPE = np.dtype([("t", "<i8"), ("x", "<u2"), ("y", "<u2"), ("p", "i1")])


class DVS:
    def __init__(self, width=346, height=260, C=0.25, sigma_C=0.03, t_ref=1e-4,
                 noise_rate=0.1, eps=1e-3, bandwidth_hz=None, seed=0):
        self.W, self.H = width, height
        self.rng = np.random.default_rng(seed)
        self.Cp = np.clip(self.rng.normal(C, sigma_C, (height, width)), 0.05, None)   # ON thresholds
        self.Cn = np.clip(self.rng.normal(C, sigma_C, (height, width)), 0.05, None)   # OFF thresholds
        self.t_ref, self.noise_rate, self.eps, self.bw = t_ref, noise_rate, eps, bandwidth_hz
        self.L_ref = None          # log level at each pixel's last event
        self.L_prev = None         # log level at the previous frame
        self.t_prev = None
        self.t_last = np.full((height, width), -np.inf)   # last event time per pixel (refractory)
        self.n_events = 0

    def log_intensity(self, gray):
        return np.log(gray.astype(np.float64) + self.eps)

    def reset(self, gray, t):
        L = self.log_intensity(gray)
        self.L_ref, self.L_prev, self.t_prev = L.copy(), L.copy(), t

    def step(self, gray, t):
        """Feed the frame at simulated time t [s] (gray in [0,1]); return events in (t_prev, t]."""
        if self.L_prev is None:
            self.reset(gray, t)
            return np.zeros(0, EVENT_DTYPE)
        L_new = self.log_intensity(gray)
        dt = t - self.t_prev
        if self.bw is not None:        # finite photoreceptor bandwidth (brighter = faster)
            fc = self.bw*np.clip(np.exp(L_new)/0.5, 0.05, 1.0)
            a = 1 - np.exp(-2*np.pi*fc*dt)
            L_new = self.L_prev + a*(L_new - self.L_prev)
        L0, dL = self.L_prev, L_new - self.L_prev
        out = []
        # ON crossings: levels L_ref + k*Cp above, OFF: L_ref - k*Cn below
        for pol, Cth in ((1, self.Cp), (-1, self.Cn)):
            diff = pol*(L_new - self.L_ref)
            n = np.floor(diff/Cth).astype(np.int64)
            n[n < 0] = 0
            if n.max() == 0:
                continue
            ys, xs = np.nonzero(n)
            nk = n[ys, xs]
            kmax = int(nk.max())
            base = self.L_ref[ys, xs]
            d = dL[ys, xs]
            l0 = L0[ys, xs]
            c = Cth[ys, xs]
            for k in range(1, kmax + 1):
                m = nk >= k
                level = base[m] + pol*k*c[m]
                with np.errstate(divide="ignore", invalid="ignore"):
                    frac = np.where(np.abs(d[m]) > 1e-12, (level - l0[m])/d[m], 1.0)
                tk = self.t_prev + np.clip(frac, 0, 1)*dt
                out.append((tk, xs[m], ys[m], np.full(m.sum(), pol, np.int8)))
            self.L_ref[ys, xs] = base + pol*nk*c
        ev = self._assemble(out)
        # refractory period: drop events closer than t_ref to the same pixel's previous event
        # (vectorised; compares with the previous *generated* event of that pixel, which is
        # exact when a pixel fires at most once per t_ref, the usual case at 1 kHz frames)
        if len(ev) and self.t_ref > 0:
            pid = ev["y"].astype(np.int64)*self.W + ev["x"]
            order = np.lexsort((ev["t"], pid))
            ev, pid = ev[order], pid[order]
            tsec = ev["t"]*1e-6
            prev = np.empty(len(ev))
            same = np.r_[False, pid[1:] == pid[:-1]]
            prev[same] = tsec[:-1][same[1:]]
            first = ~same
            prev[first] = self.t_last.ravel()[pid[first]]
            keep = (tsec - prev) >= self.t_ref
            ev, pid, tsec = ev[keep], pid[keep], tsec[keep]
            last_idx = np.r_[pid[1:] != pid[:-1], True] if len(pid) else np.zeros(0, bool)
            self.t_last.ravel()[pid[last_idx]] = tsec[last_idx]
            ev = ev[np.argsort(ev["t"], kind="stable")]
        # background activity: Poisson, uniform in space/time, random polarity
        if self.noise_rate > 0:
            k = self.rng.poisson(self.noise_rate*self.W*self.H*dt)
            if k:
                nz = np.zeros(k, EVENT_DTYPE)
                nz["t"] = ((self.t_prev + self.rng.random(k)*dt)*1e6).astype(np.int64)
                nz["x"] = self.rng.integers(0, self.W, k); nz["y"] = self.rng.integers(0, self.H, k)
                nz["p"] = self.rng.choice(np.array([-1, 1], np.int8), k)
                ev = np.concatenate([ev, nz])
                ev = ev[np.argsort(ev["t"], kind="stable")]
        self.L_prev, self.t_prev = L_new, t
        self.n_events += len(ev)
        return ev

    @staticmethod
    def _assemble(parts):
        if not parts:
            return np.zeros(0, EVENT_DTYPE)
        tk = np.concatenate([p[0] for p in parts])
        ev = np.zeros(len(tk), EVENT_DTYPE)
        ev["t"] = (tk*1e6).astype(np.int64)
        ev["x"] = np.concatenate([p[1] for p in parts])
        ev["y"] = np.concatenate([p[2] for p in parts])
        ev["p"] = np.concatenate([p[3] for p in parts])
        return ev


class MujocoEventCamera:
    """Renders a named MuJoCo camera to grayscale and feeds a DVS."""
    def __init__(self, m, cam_name, width=346, height=260, **dvs_kw):
        self.m, self.cam = m, cam_name
        self.r = mujoco.Renderer(m, height, width)
        self.dvs = DVS(width, height, **dvs_kw)

    def gray(self, d):
        self.r.update_scene(d, camera=self.cam)
        rgb = self.r.render().astype(np.float32)/255.0
        return 0.299*rgb[..., 0] + 0.587*rgb[..., 1] + 0.114*rgb[..., 2]     # ITU-R BT.601 luma

    def step(self, d):
        g = self.gray(d)
        return self.dvs.step(g, d.time), g


def event_frame(ev, W, H, t0_us, t1_us):
    """Accumulate events in [t0, t1) into an RGB image: ON = red, OFF = blue, none = white."""
    img = np.full((H, W, 3), 255, np.uint8)
    sel = (ev["t"] >= t0_us) & (ev["t"] < t1_us)
    e = ev[sel]
    on, off = e["p"] > 0, e["p"] < 0
    img[e["y"][off], e["x"][off]] = (30, 60, 220)
    img[e["y"][on], e["x"][on]] = (220, 40, 40)
    return img
