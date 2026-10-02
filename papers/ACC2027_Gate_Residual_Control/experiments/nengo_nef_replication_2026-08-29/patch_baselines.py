"""Create run_mujoco_nef_baselines.py: the PID/feedforward runner plus five
model-based attitude baselines, each usable with or without the CMG residual.

Chain: run_mujoco_nef.py --(patch_pid.py)--> run_mujoco_nef_pid.py
                         --(this file)-----> run_mujoco_nef_baselines.py

  --baseline pd            existing PD / PID / PD+ff paths, unchanged
  --baseline lqr           LQR tracking law
  --baseline backstepping  computed-torque backstepping (aero2 form)
  --baseline smc           boundary-layer sliding mode (aero2 form)
  --baseline mpc           unconstrained finite-horizon first-move MPC (aero2 form)
  --baseline nmpc          grid-search NMPC with RK4 rigid-body prediction (aero2 form)

The formulations follow C:\\Research\\aero2\\aero2\\control\\ (Gandhi's own
Aero 2 implementations), carried from a 2-DOF voltage-input helicopter to a
3-axis torque-input rigid body. Two deliberate differences from aero2:

* Reference-rate feedforward. The aero2 laws damp absolute rate (backstepping
  -k2*theta_dot, SMC surface theta_dot + lambda*e, LQR x_ref with zero rates),
  the gap found in the attitude PD on 2026-09-10. Here every family uses the
  rate error w_e = omega - omega_d and the acceleration feedforward
  J*omega_d_dot + omega x J omega, with omega_d from reference_rate (mode
  --rate-ff, 'left-neg' is the verified one).
* Matched bandwidth. Every family takes its natural frequency from the PD's
  wn = [4, 4, 3.5] rad/s times --bw-scale, so none is more aggressive than the
  others by construction. What differs is structure, not tuning.

All families use the same small-angle error e = 2 e_q, the same torque box,
and the same torque interface into allocation, so the CMG residual attaches
to any of them unchanged.

Run:  python patch_baselines.py
"""
from __future__ import annotations

import io
import os
import py_compile
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "run_mujoco_nef_pid.py"
# BASELINES_DST lets a test copy be generated while a sweep is still reading
# the live runner; the default is the live runner.
DST = HERE / os.environ.get("BASELINES_DST", "run_mujoco_nef_baselines.py")

shutil.copyfile(SRC, DST)
s = io.open(DST, encoding="utf-8").read()
n = 0


def sub(old: str, new: str, tag: str) -> None:
    global s, n
    c = s.count(old)
    if c != 1:
        raise SystemExit(f"FAILED [{tag}]: found {c}, expected 1")
    s = s.replace(old, new, 1)
    n += 1
    print(f"  ok  {tag}")


s = "\n".join([
    "# Model-based-baseline variant (patch_baselines.py <- run_mujoco_nef_pid.py).",
    "# --baseline pd (default) reproduces run_mujoco_nef_pid.py exactly.",
    "",
]) + s

# ---------------------------------------------------------------------------
BASELINE_CLASS = r'''class AdvancedBaseline:
    """Model-based attitude baselines on the PD's torque interface.

    Shared by all families: e = 2 e_q (small-angle rotation vector), rate
    error w_e = omega - omega_d, acceleration feedforward omega_d_dot, the
    gyroscopic term omega x J omega, and the PD's torque box. Natural
    frequency wn = PD's wn * bw_scale for every family.
    """

    def __init__(self, args, inertia, limits, wn):
        self.a = args
        # The controller's model of the inertia. --model-inertia-scale 1 uses
        # MuJoCo's own inertia -- an exact model, the best case for
        # model-based control and the worst case for a learned residual.
        # Other values model a mis-identified vehicle: every use of J in the
        # control law (gains, feedforward, gyroscopic term, NMPC prediction)
        # sees the wrong value, as it would in practice.
        self.J = np.asarray(inertia, dtype=float) * float(args.model_inertia_scale)
        self.lim = np.asarray(limits, dtype=float)
        self.wn = np.asarray(wn, dtype=float) * float(args.bw_scale)
        self.zeta = 0.95                      # the PD's damping ratio
        self.mode = args.rate_ff
        self.model_ff = not args.no_model_ff
        rate = float(args.baseline_rate_hz)
        self.every = max(1, int(round(1.0 / (rate * args.dt)))) if rate > 0 else 1
        self.count = 0
        self.hold = None
        b = args.baseline
        if b == "lqr":
            # Per-axis double integrator x = [e, w_e], input = angular accel.
            # With Q = diag(q_e, 0), R = r the CARE has the closed form
            # K = [sqrt(q_e/r), sqrt(2 sqrt(q_e/r))]; choosing q_e/r = wn^4
            # gives K = [wn^2, sqrt(2) wn], i.e. zeta = 1/sqrt(2).
            self.k1, self.k2 = self.wn ** 2, np.sqrt(2.0) * self.wn
        elif b in ("backstepping", "nmpc"):
            # Computed-torque backstepping (aero2 form): desired accel
            # -k1 e - k2 w_e, then inverse dynamics. NMPC uses it as nominal.
            self.k1, self.k2 = self.wn ** 2, 2.0 * self.zeta * self.wn
        elif b == "smc":
            # s = w_e + lam e; accel = -lam w_e - eta sat(s/phi). Inside the
            # boundary layer this is a PD with k1 = lam eta/phi, k2 = lam +
            # eta/phi; lam = wn and eta/phi = wn make it critically damped at
            # wn, outside it a bounded reaching law of magnitude eta.
            self.lam = self.wn.copy()
            self.eta = float(args.smc_eta_frac) * self.lim / self.J
            self.phi = self.eta / self.wn
        elif b == "mpc":
            self.K0 = np.array([self._mpc_first_gain(i) for i in range(3)])
        if b == "nmpc":
            d = float(args.nmpc_offset_frac) * self.lim
            g = np.linspace(-1.0, 1.0, int(args.nmpc_grid))
            self.offsets = [np.array([i, j, k]) * d for i in g for j in g for k in g]
            self.qe_w = self.wn ** 4          # angle weight, as LQR's q_e/r = wn^4
            # rate-error weight; the metric scores angle only, so a heavy
            # weight here lets the optimiser trade angle for rate matching
            self.qw_w = float(args.nmpc_rate_weight) * self.wn ** 2
        self.n_updates = 0
        self.n_nonzero = 0
        self.pred = None
        self.pred_err = []
        self.hold_err = []
        self.q_prev = None

    # ---- MPC: aero2's unconstrained finite-horizon first-move gain ---------
    def _mpc_first_gain(self, i):
        T, N = float(self.a.mpc_dt), int(self.a.mpc_horizon)
        Ad = np.array([[1.0, T], [0.0, 1.0]])
        Bd = np.array([[0.5 * T * T], [T]])          # exact ZOH, accel input
        Q = np.diag([self.wn[i] ** 4, float(self.a.mpc_q_rate) * self.wn[i] ** 2])
        R = np.array([[1.0]])
        n, m = 2, 1
        Sx = np.zeros((N * n, n))
        Su = np.zeros((N * n, N * m))
        Ap = np.eye(n)
        for k in range(N):
            Ap = Ad @ Ap
            Sx[k * n:(k + 1) * n, :] = Ap
            for j in range(k + 1):
                Su[k * n:(k + 1) * n, j * m:(j + 1) * m] = (
                    np.linalg.matrix_power(Ad, k - j) @ Bd)
        Qb, Rb = np.kron(np.eye(N), Q), np.kron(np.eye(N), R)
        H = Su.T @ Qb @ Su + Rb
        F = Su.T @ Qb @ Sx
        return np.linalg.solve(H + 1e-9 * np.eye(N * m), F)[:m, :].ravel()

    # ---- references --------------------------------------------------------
    def _wd(self, t):
        if self.mode == "none":
            return np.zeros(3)
        return reference_rate(t, self.a.mission, self.a.duration, self.mode)

    def _wd_dot(self, t, h=1e-3):
        if self.mode == "none" or not self.model_ff:
            return np.zeros(3)
        t0 = max(t - h, 0.0)
        return (self._wd(t + h) - self._wd(t0)) / ((t + h) - t0)

    # ---- rigid-body prediction in MuJoCo's own convention -------------------
    def _deriv(self, q, w, tau):
        qd = 0.5 * quat_mul(q, np.array([0.0, w[0], w[1], w[2]]))
        wd = (tau - np.cross(w, self.J * w)) / self.J
        return qd, wd

    def _rk4(self, q, w, tau, h):
        k1q, k1w = self._deriv(q, w, tau)
        k2q, k2w = self._deriv(q + 0.5 * h * k1q, w + 0.5 * h * k1w, tau)
        k3q, k3w = self._deriv(q + 0.5 * h * k2q, w + 0.5 * h * k2w, tau)
        k4q, k4w = self._deriv(q + h * k3q, w + h * k3w, tau)
        q = q + (h / 6.0) * (k1q + 2 * k2q + 2 * k3q + k4q)
        w = w + (h / 6.0) * (k1w + 2 * k2w + 2 * k3w + k4w)
        return q / np.linalg.norm(q), w

    # ---- the control law ----------------------------------------------------
    def torque(self, t, eq, omega, q_meas):
        if self.hold is not None and self.count % self.every != 0:
            self.count += 1
            return self.hold
        self.count += 1
        # NMPC self-check: compare last update's one-period-ahead prediction
        # with where the attitude actually is now. A convention error in the
        # propagation shows up as prediction error of the size of the motion.
        if self.pred is not None:
            self.pred_err.append(quat_angle(quat_error(self.pred, q_meas)[0]))
            self.hold_err.append(quat_angle(quat_error(self.q_prev, q_meas)[0]))
        wd, wd_dot = self._wd(t), self._wd_dot(t)
        e, we = 2.0 * eq, omega - wd
        gyro = np.cross(omega, self.J * omega) if self.model_ff else np.zeros(3)
        b = self.a.baseline
        if b in ("lqr", "backstepping"):
            acc = wd_dot - self.k1 * e - self.k2 * we
        elif b == "smc":
            s_ = we + self.lam * e
            acc = wd_dot - self.lam * we - self.eta * np.clip(s_ / self.phi, -1.0, 1.0)
        elif b == "mpc":
            acc = wd_dot - (self.K0[:, 0] * e + self.K0[:, 1] * we)
        elif b == "nmpc":
            acc = wd_dot - self.k1 * e - self.k2 * we
        tau = np.clip(self.J * acc + gyro, -self.lim, self.lim)
        if b == "nmpc":
            tau = self._nmpc(t, q_meas, omega, tau)
        self.hold = tau
        return tau

    def _nmpc(self, t, q_meas, omega, tau_nom):
        a = self.a
        dtp, N = float(a.nmpc_dt), int(a.nmpc_horizon)
        # 'open' (aero2): each candidate holds one constant torque over the
        # whole horizon. Diagnosed 2026-09-10 as the wrong model of a loop
        # that re-plans every period -- it made tracking worse than its own
        # nominal law (0.209 vs 0.118 rad, X2 Full3, 3 s). 'policy': the
        # nominal law is re-evaluated on each predicted state and the
        # candidate adds a constant offset, so the prediction models the
        # closed loop that will actually run.
        tk = [t + k * dtp for k in range(N + 1)]
        qrs = [reference_quat(x, a.mission, a.duration) for x in tk]
        wrs = [self._wd(x) for x in tk]
        wds = [self._wd_dot(x) for x in tk]
        q0 = quat_conj(q_meas)                 # measured -> MuJoCo convention
        policy = a.nmpc_predict == "policy"
        best, best_cost, best_off = tau_nom, np.inf, None
        for off in self.offsets:
            first = np.clip(tau_nom + off, -self.lim, self.lim)
            tau_c = first
            q, w, cost = q0.copy(), omega.copy(), 0.0
            for k in range(N):
                if policy and k > 0:
                    _, ekp = quat_error(qrs[k], quat_conj(q))
                    acc = wds[k] - self.k1 * 2.0 * ekp - self.k2 * (w - wrs[k])
                    g_ = np.cross(w, self.J * w) if self.model_ff else 0.0
                    tau_c = np.clip(self.J * acc + g_ + off, -self.lim, self.lim)
                q, w = self._rk4(q, w, tau_c, dtp)
                _, ek = quat_error(qrs[k + 1], quat_conj(q))
                wek = w - wrs[k + 1]
                wt = float(a.nmpc_terminal) if k == N - 1 else 1.0
                cost += wt * (float(np.sum(self.qe_w * (2.0 * ek) ** 2))
                              + float(np.sum(self.qw_w * wek ** 2)))
                cost += float(np.sum((tau_c / self.J) ** 2))
            if cost < best_cost:
                best, best_cost, best_off = first, cost, off
        self.n_updates += 1
        self.n_nonzero += int(np.any(best_off != 0.0))
        period = self.every * a.dt
        qp, _ = self._rk4(q0.copy(), omega.copy(), best, period)
        self.pred = quat_conj(qp)
        self.q_prev = q_meas.copy()
        return best

    def stats(self):
        out = {"bw_scale": float(self.a.bw_scale), "wn": [float(v) for v in self.wn],
               "update_every_steps": self.every}
        if self.a.baseline == "nmpc":
            out.update({
                "nmpc_updates": self.n_updates,
                "nmpc_nonzero_offset_fraction": self.n_nonzero / max(self.n_updates, 1),
                "nmpc_pred_err_mean_deg": float(np.degrees(np.mean(self.pred_err)))
                if self.pred_err else None,
                "nmpc_hold_err_mean_deg": float(np.degrees(np.mean(self.hold_err)))
                if self.hold_err else None,
            })
        return out


def _build_augmentor(name, limits, dt, beta, learning_rate, seed):'''

sub("def _build_augmentor(name, limits, dt, beta, learning_rate, seed):",
    BASELINE_CLASS, "baseline-class")

sub("    rotor_sat_prev = False\n",
    "    rotor_sat_prev = False\n"
    "    adv = (AdvancedBaseline(args, inertia, limits, wn)\n"
    "           if args.baseline != 'pd' else None)\n",
    "construct")

sub("            if args.ki_factor == 0.0 and args.rate_ff == 'none':\n",
    "            if args.baseline != 'pd':\n"
    "                tau0 = adv.torque(t, eq, omega, q_meas)\n"
    "            elif args.ki_factor == 0.0 and args.rate_ff == 'none':\n",
    "dispatch")

sub('        "rate_ff": args.rate_ff,\n',
    '        "rate_ff": args.rate_ff,\n'
    '        "baseline_family": args.baseline,\n'
    '        "baseline_stats": adv.stats() if adv is not None else {},\n',
    "summary")

sub('                   help="Damp omega - omega_d instead of omega.")\n',
    '                   help="Damp omega - omega_d instead of omega.")\n'
    '    p.add_argument("--baseline", default="pd",\n'
    '                   choices=("pd", "lqr", "backstepping", "smc", "mpc", "nmpc"))\n'
    '    p.add_argument("--bw-scale", type=float, default=1.0,\n'
    '                   help="Natural frequency as a multiple of the PD\'s.")\n'
    '    p.add_argument("--baseline-rate-hz", type=float, default=0.0,\n'
    '                   help="Baseline update rate with zero-order hold; 0 = every step.")\n'
    '    p.add_argument("--no-model-ff", action="store_true",\n'
    '                   help="Drop J*omega_d_dot and omega x J omega (regression check).")\n'
    '    p.add_argument("--smc-eta-frac", type=float, default=0.5,\n'
    '                   help="Reaching accel as a fraction of max accel limits/J.")\n'
    '    p.add_argument("--mpc-dt", type=float, default=0.02)\n'
    '    p.add_argument("--mpc-horizon", type=int, default=120)\n'
    '    p.add_argument("--mpc-q-rate", type=float, default=0.0)\n'
    '    p.add_argument("--nmpc-dt", type=float, default=0.06)\n'
    '    p.add_argument("--nmpc-horizon", type=int, default=5)\n'
    '    p.add_argument("--nmpc-terminal", type=float, default=1.5)\n'
    '    p.add_argument("--nmpc-offset-frac", type=float, default=0.1,\n'
    '                   help="Grid offsets as a fraction of the torque limit.")\n'
    '    p.add_argument("--model-inertia-scale", type=float, default=1.0,\n'
    '                   help="Controller-model inertia as a multiple of the true one.")\n'
    '    p.add_argument("--nmpc-rate-weight", type=float, default=2.0,\n'
    '                   help="Rate-error cost weight, times wn^2.")\n'
    '    p.add_argument("--nmpc-grid", type=int, default=3,\n'
    '                   help="Offset levels per axis (odd; 3 = -d, 0, +d).")\n'
    '    p.add_argument("--nmpc-predict", choices=("open", "policy"), default="policy",\n'
    '                   help="open: constant torque over the horizon (aero2 form); "\n'
    '                        "policy: nominal law re-evaluated on the prediction.")\n',
    "cli")

io.open(DST, "w", encoding="utf-8").write(s)
py_compile.compile(str(DST), doraise=True)
print(f"\nwrote {DST.name} ({n} changes), compiles cleanly")
