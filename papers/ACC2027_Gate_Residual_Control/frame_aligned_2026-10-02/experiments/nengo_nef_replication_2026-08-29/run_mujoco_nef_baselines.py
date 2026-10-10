# Model-based-baseline variant (patch_baselines.py <- run_mujoco_nef_pid.py).
# --baseline pd (default) reproduces run_mujoco_nef_pid.py exactly.
# PID / rate-feedforward variant of run_mujoco_nef.py (patch_pid.py).
# Defaults reproduce the canonical PD runner exactly.
"""Matched MuJoCo runner for classical, direct-CMG/PES, and Nengo-NEF/PES.

The plant, quaternion PD baseline, actuator allocation, limits, references, and
disturbances are copied from the paper's canonical ``run_drone`` implementation.
Only the residual-controller backend is varied.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import mujoco
import nengo
import numpy as np


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gra_control.gate import CMGResidualAugmentor  # noqa: E402
from gra_control.math3d import (  # noqa: E402
    euler_to_quat,
    quat_angle,
    quat_conj,
    quat_error,
    quat_mul,
    reference_euler,
    reference_quat,
)
from gra_control.platforms.drone import (  # noqa: E402
    SPECS,
    _free_joint,
    _mixer,
    _name_id,
    torque_limits,
)
from gra_control.provenance import manifest, write_json  # noqa: E402
from nengo_cmg import NengoCMGPESAugmentor  # noqa: E402
from nengo_neuron_family import NengoNeuronFamilyAugmentor  # noqa: E402


FAMILY_CONTROLLERS = tuple(
    f"nengo-{family}-{mode}"
    for family in ("cmg", "lif", "alif", "izhikevich", "lifrate")
    for mode in ("fixed", "pes")
)
CONTROLLERS = ("classical", "direct-online-pes", "nengo-nef-pes") + FAMILY_CONTROLLERS
MISSIONS = ("hover", "roll", "full3", "hard45", "hardstep", "yaw360")
NEURAL_SIGNALS = (
    "t",
    "plant_step",
    "baseline_tau",
    "target",
    "current",
    "voltage",
    "gate",
    "activity",
    "effective_threshold",
    "gate_argument",
    "gate_target",
    "conductance_gain",
    "conductance",
    "membrane_lambda",
    "membrane_drive",
    "decoded_raw",
    "decoded_clipped",
    "pes_error",
    "weights",
    "weight_delta",
    "residual_torque",
    "native_current",
    "raw_output",
    "state_voltage",
    "state_gate",
    "state_refractory_time",
    "state_adaptation",
    "state_recovery",
)


def reference_rate(t, mission, duration, mode, h=1e-4):
    """Reference angular rate from a central difference of reference_quat.

    'left'  uses vec(q(t+h) q(t-h)^-1); 'right' uses vec(q(t-h)^-1 q(t+h));
    the '-neg' variants flip the sign. Which one matches this codebase's
    passive convention is decided empirically by select_rate_ff.py.
    """
    t0 = max(t - h, 0.0)
    qa = reference_quat(t0, mission, duration)
    qb = reference_quat(t + h, mission, duration)
    base = mode.replace("-neg", "")
    if base == "left":
        dq = quat_mul(qb, quat_conj(qa))
    else:
        dq = quat_mul(quat_conj(qa), qb)
    if dq[0] < 0.0:
        dq = -dq
    w = 2.0 * dq[1:] / ((t + h) - t0)
    return -w if mode.endswith("-neg") else w


def _rotT(q):
    """R(q)^T for R(q) v = vec(q (x) [0, v] (x) q*): carries the desired-frame rate into the body frame (P-(8))."""
    w, x, y, z = np.asarray(q, dtype=float) / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]).T


class AdvancedBaseline:
    """Model-based attitude baselines on the PD's torque interface.

    Shared by all families: e = 2 e_q (small-angle rotation vector), rate
    error w_e = omega - omega_d, acceleration feedforward omega_d_dot, the
    gyroscopic term omega x J omega, and the PD's torque box. Natural
    frequency wn = PD's wn * bw_scale for every family.
    """

    def __init__(self, args, inertia, limits, wn):
        self.a = args
        self.J = np.asarray(inertia, dtype=float)
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
        qe_fa, _ = quat_error(reference_quat(t, self.a.mission, self.a.duration), q_meas)   # FRAME-ALIGNED
        e, we = 2.0 * eq, omega - _rotT(qe_fa) @ wd
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
                    qep, ekp = quat_error(qrs[k], quat_conj(q))
                    acc = wds[k] - self.k1 * 2.0 * ekp - self.k2 * (w - _rotT(qep) @ wrs[k])   # FRAME-ALIGNED
                    g_ = np.cross(w, self.J * w) if self.model_ff else 0.0
                    tau_c = np.clip(self.J * acc + g_ + off, -self.lim, self.lim)
                q, w = self._rk4(q, w, tau_c, dtp)
                qek, ek = quat_error(qrs[k + 1], quat_conj(q))
                wek = w - _rotT(qek) @ wrs[k + 1]   # FRAME-ALIGNED
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


def _build_augmentor(name, limits, dt, beta, learning_rate, seed):
    if name == "classical":
        return None
    if name == "direct-online-pes":
        return CMGResidualAugmentor(
            3,
            limits,
            mode="online_pes",
            adaptive_conductance=True,
            beta=beta,
            learning_rate=learning_rate,
        )
    if name == "nengo-nef-pes":
        return NengoCMGPESAugmentor(
            3,
            limits,
            dt=dt,
            beta=beta,
            learning_rate=learning_rate,
            adaptive_conductance=True,
            seed=seed,
        )
    if name in FAMILY_CONTROLLERS:
        _, family, mode = name.split("-", 2)
        calibration_path = Path(__file__).with_name("feature_calibration.json")
        calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
        item = calibration["families"][family]
        return NengoNeuronFamilyAugmentor(
            family=family,
            limits=limits,
            dt=dt,
            beta=beta,
            mode=mode,
            learning_rate=learning_rate,
            feature_tau=calibration["feature_tau_s"],
            feature_scale=item["feature_scale"],
            native_current_scale=item.get("native_current_scale", 1.0),
            seed=seed,
        )
    raise ValueError(name)


def _neuron_state(augmentor, current, target):
    if augmentor is None:
        z6 = np.zeros(6)
        return z6, z6, z6, np.zeros((3, 6)), np.zeros(3)
    if isinstance(augmentor, NengoCMGPESAugmentor):
        return augmentor.v, augmentor.r, augmentor.activity, augmentor.W, augmentor.pes_error
    if isinstance(augmentor, NengoNeuronFamilyAugmentor):
        diagnostic = augmentor.diagnostics()
        states = diagnostic["states"]
        voltage = states.get("voltage", np.zeros(6))
        secondary = states.get(
            "adaptation",
            states.get("recovery", states.get("refractory_time", np.zeros(6))),
        )
        return voltage, secondary, diagnostic["activity"], diagnostic["weights"], diagnostic["pes_error"]
    activity = np.clip(augmentor.cfg.gate_gain * augmentor.units.r, 0.0, 1.0)
    decoded = np.clip(augmentor.W @ activity, -1.0, 1.0)
    return (
        augmentor.units.v.copy(),
        augmentor.units.r.copy(),
        activity,
        augmentor.W.copy(),
        (decoded - target).copy(),
    )


def run(args) -> dict:
    spec = SPECS[args.platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = args.dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    inertia = model.body_inertia[body_id].copy()
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    limits = torque_limits(args.platform, inertia, model, args.torque_policy)
    wn = np.array([4.0, 4.0, 3.5])
    kq = 2.0 * inertia * wn * wn
    kw = 2.0 * 0.95 * wn * inertia
    # Integral action, scaled per axis by kq so one factor is fair to both
    # airframes. ki_factor = 0 makes the integral term identically zero.
    ki = args.ki_factor * kq
    eq_integral = np.zeros(3)
    integral_frozen_steps = np.zeros(3, dtype=int)
    rotor_sat_prev = False
    adv = (AdvancedBaseline(args, inertia, limits, wn)
           if args.baseline != 'pd' else None)
    augmentor = _build_augmentor(
        args.controller,
        limits,
        args.dt,
        args.beta,
        args.learning_rate,
        args.seed,
    )

    data.qpos[qa : qa + 3] = [0.0, 0.0, 1.0]
    initial_rad = np.deg2rad(args.initial_angle_deg)
    q_initial_body = euler_to_quat(initial_rad, -0.7 * initial_rad, 0.5 * initial_rad)
    data.qpos[qa + 3 : qa + 7] = quat_conj(q_initial_body)
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0
    mujoco.mj_forward(model, data)

    if spec.interface == "rotor4":
        act_ids, _, B_inv, ctrl_range = _mixer(model)
        if args.actuator_scale <= 0:
            raise ValueError("actuator_scale must be positive")
        ctrl_range[:, 1] *= args.actuator_scale
        model.actuator_ctrlrange[act_ids, 1] = ctrl_range[:, 1]
        gears = None
    else:
        names = ["body_thrust", "x_moment", "y_moment", "z_moment"]
        act_ids = np.array(
            [_name_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in names]
        )
        ctrl_range = model.actuator_ctrlrange[act_ids].copy()
        gears = np.abs(
            np.array(
                [
                    model.actuator_gear[act_ids[1], 3],
                    model.actuator_gear[act_ids[2], 4],
                    model.actuator_gear[act_ids[3], 5],
                ]
            )
        )

    rows = []
    neural_log = {name: [] for name in NEURAL_SIGNALS}
    metric_qerr = []
    metric_tau_norm = []
    metric_residual_norm = []
    metric_saturation = []
    metric_z = []
    step_index = 0
    rng = np.random.default_rng(args.seed)
    try:
        while data.time < args.duration:
            t = float(data.time)
            q_meas = quat_conj(np.asarray(data.qpos[qa + 3 : qa + 7], dtype=float))
            omega = np.asarray(data.qvel[va + 3 : va + 6], dtype=float).copy()
            if args.attitude_noise_std > 0:
                dq = euler_to_quat(*rng.normal(0.0, args.attitude_noise_std, size=3))
                q_meas = quat_mul(dq, q_meas)
            if args.rate_noise_std > 0:
                omega += rng.normal(0.0, args.rate_noise_std, size=3)

            ref_euler = reference_euler(t, args.mission, args.duration)
            qref = reference_quat(t, args.mission, args.duration)
            qe, eq = quat_error(qref, q_meas)
            if args.baseline != 'pd':
                tau0 = adv.torque(t, eq, omega, q_meas)
            elif args.ki_factor == 0.0 and args.rate_ff == 'none':
                # Canonical PD, byte-identical expression.
                tau0 = np.clip(-kq * eq - kw * omega, -limits, limits)
            else:
                if args.rate_ff == 'none':
                    omega_d = np.zeros(3)
                else:
                    omega_d = reference_rate(t, args.mission, args.duration,
                                             args.rate_ff)
                tau0_unsat = -kq * eq - kw * (omega - _rotT(qe) @ omega_d) - ki * eq_integral   # FRAME-ALIGNED
                tau0 = np.clip(tau0_unsat, -limits, limits)
                if args.ki_factor > 0.0:
                    # Conditional-integration anti-windup.
                    free = np.isclose(tau0, tau0_unsat, rtol=0.0, atol=1e-12)
                    if args.antiwindup == 'rotor' and rotor_sat_prev:
                        free = np.zeros(3, dtype=bool)
                    eq_integral += np.where(free, eq, 0.0) * args.dt
                    integral_frozen_steps += (~free).astype(int)
            target = np.clip(-args.k_error * eq - args.k_rate * omega, -1.0, 1.0)
            normalized = np.divide(
                tau0, limits, out=np.zeros_like(tau0), where=limits > 1e-12
            )
            current = np.concatenate(
                [
                    0.75 + 1.25 * np.maximum(normalized, 0.0),
                    0.75 + 1.25 * np.maximum(-normalized, 0.0),
                ]
            )

            if augmentor is None:
                tau = tau0.copy()
                residual = np.zeros(3)
            elif isinstance(augmentor, (NengoCMGPESAugmentor, NengoNeuronFamilyAugmentor)):
                weights_before = augmentor.W
                out = augmentor.step(tau0, target)
                tau, residual = out.command, out.residual
                diagnostics = augmentor.diagnostics()
                if args.save_neural_archive:
                    neural_log["t"].append(t + args.dt)
                    neural_log["plant_step"].append(step_index)
                    neural_log["baseline_tau"].append(tau0.copy())
                    neural_log["target"].append(target.copy())
                    for name in ("current", "activity", "decoded_raw", "decoded_clipped", "pes_error", "weights"):
                        neural_log[name].append(diagnostics[name].copy())
                    if isinstance(augmentor, NengoCMGPESAugmentor):
                        for name in (
                            "voltage", "gate", "effective_threshold", "gate_argument",
                            "gate_target", "conductance_gain", "conductance",
                            "membrane_lambda", "membrane_drive",
                        ):
                            neural_log[name].append(diagnostics[name].copy())
                    else:
                        neural_log["native_current"].append(diagnostics["native_current"].copy())
                        neural_log["raw_output"].append(diagnostics["raw_output"].copy())
                        if augmentor.family == "cmg":
                            for name in (
                                "voltage", "gate", "effective_threshold", "gate_argument",
                                "gate_target", "conductance_gain", "conductance",
                                "membrane_lambda", "membrane_drive",
                            ):
                                neural_log[name].append(diagnostics[name].copy())
                        for state_name, values in diagnostics["states"].items():
                            key = f"state_{state_name}"
                            if key in neural_log:
                                neural_log[key].append(values.copy())
                    neural_log["weight_delta"].append(
                        diagnostics["weights"] - weights_before
                    )
                    neural_log["residual_torque"].append(residual.copy())
            else:
                out = augmentor.step(tau0, args.dt, target)
                tau, residual = out.command, out.residual

            voltage, gate, activity, weights, pes_error = _neuron_state(
                augmentor, current, target
            )

            R = np.asarray(data.xmat[body_id], dtype=float).reshape(3, 3)
            z, vz = float(data.qpos[qa + 2]), float(data.qvel[va + 2])
            tilt = max(float(R[2, 2]), 0.35)
            collective = mass * (gravity + 6.0 * (1.0 - z) - 4.0 * vz) / tilt
            collective = float(
                np.clip(collective, 0.0, 2.5 * mass * max(gravity, 1.0))
            )

            data.ctrl[:] = 0.0
            data.xfrc_applied[:] = 0.0
            if args.disturbance_torque > 0:
                disturbance_body = args.disturbance_torque * np.array(
                    [
                        np.sin(1.31 * t + 0.2),
                        0.8 * np.sin(1.73 * t + 1.1),
                        0.6 * np.sin(2.17 * t + 2.0),
                    ]
                )
                data.xfrc_applied[body_id, 3:6] = R @ disturbance_body

            if spec.interface == "rotor4":
                actuator_command = B_inv @ np.r_[collective, tau]
                actuator_command = np.clip(
                    actuator_command, ctrl_range[:, 0], ctrl_range[:, 1]
                )
                data.ctrl[act_ids] = actuator_command
                saturated = bool(
                    np.any(
                        np.isclose(
                            actuator_command, ctrl_range[:, 0], atol=1e-7
                        )
                    )
                    or np.any(
                        np.isclose(
                            actuator_command, ctrl_range[:, 1], atol=1e-7
                        )
                    )
                )
            else:
                actuator_command = np.r_[collective, -tau / np.maximum(gears, 1e-15)]
                actuator_command = np.clip(
                    actuator_command, ctrl_range[:, 0], ctrl_range[:, 1]
                )
                data.ctrl[act_ids] = actuator_command
                saturated = bool(
                    np.any(
                        np.isclose(
                            actuator_command[1:], ctrl_range[1:, 0], atol=1e-7
                        )
                    )
                    or np.any(
                        np.isclose(
                            actuator_command[1:], ctrl_range[1:, 1], atol=1e-7
                        )
                    )
                )

            rotor_sat_prev = saturated
            qerr_value = quat_angle(qe)
            metric_qerr.append(qerr_value)
            metric_tau_norm.append(float(np.linalg.norm(tau)))
            metric_residual_norm.append(float(np.linalg.norm(residual)))
            metric_saturation.append(int(saturated))
            metric_z.append(z)

            row = {
                "t": t,
                "qerr": qerr_value,
                "qe_w": qe[0],
                "qe_x": eq[0],
                "qe_y": eq[1],
                "qe_z": eq[2],
                "ref_roll": ref_euler[0],
                "ref_pitch": ref_euler[1],
                "ref_yaw": ref_euler[2],
                "omega_x": omega[0],
                "omega_y": omega[1],
                "omega_z": omega[2],
                "tau0_x": tau0[0],
                "tau0_y": tau0[1],
                "tau0_z": tau0[2],
                "tau_x": tau[0],
                "tau_y": tau[1],
                "tau_z": tau[2],
                "residual_x": residual[0],
                "residual_y": residual[1],
                "residual_z": residual[2],
                "target_x": target[0],
                "target_y": target[1],
                "target_z": target[2],
                "pes_error_x": pes_error[0],
                "pes_error_y": pes_error[1],
                "pes_error_z": pes_error[2],
                "z": z,
                "saturated": int(saturated),
            }
            if step_index % args.log_every == 0:
                for i in range(6):
                    row[f"current_{i}"] = current[i]
                    row[f"voltage_{i}"] = voltage[i]
                    row[f"gate_{i}"] = gate[i]
                    row[f"activity_{i}"] = activity[i]
                for i, value in enumerate(weights.ravel()):
                    row[f"decoder_w_{i}"] = value
                if isinstance(augmentor, NengoCMGPESAugmentor):
                    for i in range(6):
                        row[f"gate_target_{i}"] = diagnostics["gate_target"][i]
                        row[f"effective_threshold_{i}"] = diagnostics["effective_threshold"][i]
                        row[f"gate_argument_{i}"] = diagnostics["gate_argument"][i]
                        row[f"conductance_gain_{i}"] = diagnostics["conductance_gain"][i]
                        row[f"conductance_{i}"] = diagnostics["conductance"][i]
                        row[f"membrane_lambda_{i}"] = diagnostics["membrane_lambda"][i]
                        row[f"membrane_drive_{i}"] = diagnostics["membrane_drive"][i]
                    for i, axis in enumerate(("x", "y", "z")):
                        row[f"decoder_raw_{axis}"] = diagnostics["decoded_raw"][i]
                        row[f"decoder_clipped_{axis}"] = diagnostics["decoded_clipped"][i]
                        row[f"decoder_update_norm_{axis}"] = np.linalg.norm(
                            diagnostics["weights"][i] - weights_before[i]
                        )
                elif isinstance(augmentor, NengoNeuronFamilyAugmentor):
                    row["neuron_family"] = augmentor.family
                    row["decoder_mode"] = augmentor.mode
                    for i in range(6):
                        row[f"raw_neuron_output_{i}"] = diagnostics["raw_output"][i]
                        row[f"native_current_{i}"] = diagnostics["native_current"][i]
                    for state_name, values in diagnostics["states"].items():
                        for i, value in enumerate(values):
                            row[f"state_{state_name}_{i}"] = value
                    for i, axis in enumerate(("x", "y", "z")):
                        row[f"decoder_raw_{axis}"] = diagnostics["decoded_raw"][i]
                        row[f"decoder_clipped_{axis}"] = diagnostics["decoded_clipped"][i]
                        row[f"decoder_update_norm_{axis}"] = np.linalg.norm(
                            diagnostics["weight_delta"][i]
                        )
                for i, value in enumerate(actuator_command):
                    row[f"actuator_{i}"] = value
                rows.append(row)
            step_index += 1
            mujoco.mj_step(model, data)
    finally:
        if isinstance(augmentor, (NengoCMGPESAugmentor, NengoNeuronFamilyAugmentor)):
            augmentor.close()

    args.output.mkdir(parents=True, exist_ok=True)
    csv_path = args.output / "trace.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    neural_path = None
    neural_schema_path = None
    if neural_log["t"]:
        neural_path = args.output / "neural_trace_full_rate.npz"
        neural_arrays = {
            name: np.asarray(values) for name, values in neural_log.items() if values
        }
        np.savez_compressed(neural_path, **neural_arrays)
        neural_schema_path = args.output / "neural_trace_schema.json"
        neural_schema = {
            "schema": 1,
            "format": "NumPy compressed archive",
            "sample_rate_hz": 1.0 / args.dt,
            "sample_period_s": args.dt,
            "axis_order": ["x/roll", "y/pitch", "z/yaw"],
            "unit_order": ["+x", "+y", "+z", "-x", "-y", "-z"],
            "weight_shape_per_sample": [3, 6],
            "signals": {
                name: {
                    "shape": list(value.shape),
                    "dtype": str(value.dtype),
                }
                for name, value in neural_arrays.items()
            },
            "semantics": {
                "decoded_raw": "unbounded W @ activity",
                "decoded_clipped": "clip(W @ activity,-1,1), used by PES and residual",
                "weight_delta": "change in all 18 decoder weights during this Nengo step",
                "pes_error": "decoded_clipped - target",
            },
            "controller": args.controller,
        }
        if args.controller == "nengo-nef-pes" or args.controller.startswith("nengo-cmg-"):
            neural_schema["semantics"].update({
                "gate_target": "sigmoid(alpha*(voltage-effective_threshold))",
                "conductance": "conductance_gain * gate^2",
            })
        if args.controller in FAMILY_CONTROLLERS:
            _, family, mode = args.controller.split("-", 2)
            calibration = json.loads(
                Path(__file__).with_name("feature_calibration.json").read_text(encoding="utf-8")
            )
            item = calibration["families"][family]
            neural_schema.update({
                "neuron_family": family,
                "decoder_mode": mode,
                "natural_observable": item["observable"],
                "feature_scale": item["feature_scale"],
                "native_current_scale": item.get("native_current_scale", 1.0),
                "available_neuron_states": [
                    name.removeprefix("state_")
                    for name in neural_arrays
                    if name.startswith("state_")
                ],
            })
        neural_schema_path.write_text(
            json.dumps(neural_schema, indent=2) + "\n", encoding="utf-8"
        )

    qerr = np.asarray(metric_qerr, dtype=float)
    family_meta = None
    if args.controller in FAMILY_CONTROLLERS:
        _, family_name, decoder_mode = args.controller.split("-", 2)
        calibration = json.loads(
            Path(__file__).with_name("feature_calibration.json").read_text(encoding="utf-8")
        )
        family_meta = {
            "neuron_family": family_name,
            "decoder_mode": decoder_mode,
            **calibration["families"][family_name],
        }
    pes_scale = 1.0 if family_meta is None else family_meta["feature_scale"]
    summary = {
        "experiment": "nengo_nef_replication_2026-08-29",
        "platform": args.platform,
        "model_interface": spec.interface,
        "controller": args.controller,
        "controller_backend": (
            "none"
            if augmentor is None
            else "nengo-4.1.0-built-in-PES"
            if args.controller == "nengo-nef-pes" or args.controller.endswith("-pes")
            else "nengo-4.1.0-fixed-decoder"
            if args.controller.startswith("nengo-")
            else "canonical-numpy-reference"
        ),
        "mission": args.mission,
        "duration": args.duration,
        "dt": args.dt,
        "beta": args.beta,
        "learning_rate_direct_equivalent": args.learning_rate,
        "nengo_pes_learning_rate": (
            args.learning_rate * 6 / (args.dt * pes_scale)
            if args.controller == "nengo-nef-pes" or args.controller.endswith("-pes")
            else None
        ),
        "neuron_family_metadata": family_meta,
        "decoder_leak_per_step": 1e-6 if (
            args.controller == "nengo-nef-pes" or args.controller.endswith("-pes")
        ) else 0.0,
        "decoder_weight_bound": 6.0 if augmentor is not None else 0.0,
        "k_error": args.k_error,
        "k_rate": args.k_rate,
        "actuator_scale": args.actuator_scale,
        "initial_angle_deg": args.initial_angle_deg,
        "disturbance_torque_Nm": args.disturbance_torque,
        "attitude_noise_std_rad": args.attitude_noise_std,
        "rate_noise_std_rad_s": args.rate_noise_std,
        "seed": args.seed,
        "ki_factor": args.ki_factor,
        "ki": [float(v) for v in ki],
        "antiwindup": args.antiwindup,
        "rate_ff": args.rate_ff,
        "baseline_family": args.baseline,
        "baseline_stats": adv.stats() if adv is not None else {},
        "baseline": ("PD" if args.ki_factor == 0.0 else "PID")
                    + ("" if args.rate_ff == "none" else "+ff"),
        "integral_final": [float(v) for v in eq_integral],
        "integral_frozen_fraction": [
            float(v) / max(step_index, 1) for v in integral_frozen_steps
        ],
        "torque_policy": args.torque_policy,
        "torque_limits_Nm": limits.tolist(),
        "qerr_mean_rad": float(np.mean(qerr)),
        "qerr_max_rad": float(np.max(qerr)),
        "qerr_rmse_rad": float(np.sqrt(np.mean(qerr**2))),
        "tau_mean_Nm": float(np.mean(metric_tau_norm)),
        "residual_mean_Nm": float(np.mean(metric_residual_norm)),
        "saturation_fraction": float(np.mean(metric_saturation)),
        "z_std_m": float(np.std(metric_z)),
        "n_steps": step_index,
        "logged_steps": len(rows),
        "log_every": args.log_every,
        "logged_dt": args.dt * args.log_every,
        "nengo_version": nengo.__version__,
        "trace": str(csv_path),
        "neural_trace_full_rate": None if neural_path is None else str(neural_path),
        "neural_trace_schema": None if neural_schema_path is None else str(neural_schema_path),
    }
    args_for_manifest = vars(args).copy()
    args_for_manifest["output"] = str(args.output)
    prov = manifest(
        REPO,
        args.platform,
        args.controller,
        spec.model,
        args_for_manifest,
    )
    prov["derived"] = {
        "body_inertia_kgm2": inertia.tolist(),
        "torque_limits_Nm": limits.tolist(),
        "kq_Nm": kq.tolist(),
        "kw_Nm_s": kw.tolist(),
    }
    write_json(args.output / "summary.json", summary)
    write_json(args.output / "manifest.json", prov)
    return summary


def make_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform", choices=("cf2", "cf2-rotor", "x2"), required=True)
    p.add_argument("--controller", choices=CONTROLLERS, required=True)
    p.add_argument("--mission", choices=MISSIONS, default="hard45")
    p.add_argument("--duration", type=float, default=45.0)
    p.add_argument("--dt", type=float, default=5e-4)
    p.add_argument("--beta", type=float, default=0.5)
    p.add_argument("--learning-rate", type=float, default=8e-4)
    p.add_argument("--k-error", type=float, default=8.0)
    p.add_argument("--k-rate", type=float, default=0.0)
    p.add_argument(
        "--torque-policy",
        choices=("model", "inertia", "legacy-learned"),
        default="model",
    )
    p.add_argument("--actuator-scale", type=float, default=1.0)
    p.add_argument("--initial-angle-deg", type=float, default=0.0)
    p.add_argument("--disturbance-torque", type=float, default=0.0)
    p.add_argument("--attitude-noise-std", type=float, default=0.0)
    p.add_argument("--rate-noise-std", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--ki-factor", type=float, default=0.0,
                   help="Integral gain as a multiple of kq, per axis. 0 = PD.")
    p.add_argument("--antiwindup", choices=("torque", "rotor"),
                   default="torque",
                   help="Freeze integration on torque-box clip only, or also "
                        "while any rotor was at its bound last step.")
    p.add_argument("--rate-ff",
                   choices=("none", "left", "right", "left-neg", "right-neg"),
                   default="none",
                   help="Damp omega - omega_d instead of omega.")
    p.add_argument("--baseline", default="pd",
                   choices=("pd", "lqr", "backstepping", "smc", "mpc", "nmpc"))
    p.add_argument("--bw-scale", type=float, default=1.0,
                   help="Natural frequency as a multiple of the PD's.")
    p.add_argument("--baseline-rate-hz", type=float, default=0.0,
                   help="Baseline update rate with zero-order hold; 0 = every step.")
    p.add_argument("--no-model-ff", action="store_true",
                   help="Drop J*omega_d_dot and omega x J omega (regression check).")
    p.add_argument("--smc-eta-frac", type=float, default=0.5,
                   help="Reaching accel as a fraction of max accel limits/J.")
    p.add_argument("--mpc-dt", type=float, default=0.02)
    p.add_argument("--mpc-horizon", type=int, default=120)
    p.add_argument("--mpc-q-rate", type=float, default=0.0)
    p.add_argument("--nmpc-dt", type=float, default=0.06)
    p.add_argument("--nmpc-horizon", type=int, default=5)
    p.add_argument("--nmpc-terminal", type=float, default=1.5)
    p.add_argument("--nmpc-offset-frac", type=float, default=0.1,
                   help="Grid offsets as a fraction of the torque limit.")
    p.add_argument("--nmpc-rate-weight", type=float, default=2.0,
                   help="Rate-error cost weight, times wn^2.")
    p.add_argument("--nmpc-grid", type=int, default=3,
                   help="Offset levels per axis (odd; 3 = -d, 0, +d).")
    p.add_argument("--nmpc-predict", choices=("open", "policy"), default="policy",
                   help="open: constant torque over the horizon (aero2 form); "
                        "policy: nominal law re-evaluated on the prediction.")
    p.add_argument(
        "--log-every",
        type=int,
        default=1,
        help="Write every Nth control step; metrics always use every step.",
    )
    p.add_argument(
        "--no-neural-archive",
        dest="save_neural_archive",
        action="store_false",
        help="Disable the default full-rate Nengo state/decoder archive.",
    )
    p.set_defaults(save_neural_archive=True)
    p.add_argument("--output", type=Path, required=True)
    return p


if __name__ == "__main__":
    parsed = make_parser().parse_args()
    if parsed.log_every < 1:
        raise SystemExit("--log-every must be >= 1")
    result = run(parsed)
    print(json.dumps(result, indent=2))
