"""
Learned HyperLIF gate residual experiment (Paper 5 differentiator).

Goal
----
The fixed gate-state residual caps out at score ~0.266 on hard45 (7.4% over
classical 0.287) because the decode from the bounded gate r to a body torque is
FIXED pair-coding and the gate itself is nearly silent (activity ~1e-6). The
STN-PID-PES adaptive controller reaches ~0.048 (83%). The unifying insight from
Papers 2/3 is that ADAPTATION is the active ingredient, not the neuron. So here
we make the gate->torque decode LEARNABLE and test whether an online / imitation
learned HyperLIF gate can close the gap toward the STN-PES level.

This script is self-contained: it replicates the *exact* validated MuJoCo
attitude loop + thrust model + DirectNeuronTorqueController decode used by
mujoco_classical_vs_neural.py, but exposes the 6->3 decode matrix W as a
trainable parameter. Fixed W = pair-coding reproduces the 0.266 baseline.

Five training ideas (per the agreed sequence):
  1. online_pes    - online PES delta-rule on W (dW ~ -lr * error * activity)
  2. imitation     - behavioral cloning of the STN-PES correction (ridge fit W)
     imitation_pes - imitation bootstrap + online PES refinement
  3. eprop_anneal  - PES with an annealed eligibility trace (wide -> sharp)
  4. demand_mod    - demand-modulated residual gain (gate only under load)
  5. stn_mod       - STN-PES sensitivity multiplicatively modulates the gate

Run:
  python learned_gate_experiment.py --quad bitcraze_crazyflie_2 --mission hard45 \
      --sim-time 45 --dt 0.0005
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import mujoco

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

# The _stn benchmark module carries every helper we need (quaternion math,
# reference trajectories, model/thrust helpers) AND wires the STN controller
# path onto sys.path, so importing it also makes STNPIDAttitudeController usable.
import mujoco_classical_vs_neural_stn as B
from neuron_dynamics import make_direct_neuron
from benchmark_metrics import summarize_controller_run
from stn_pid_attitude_controller import STNPIDAttitudeController


# Fixed pair-coding decode: signed = activity[0:3] - activity[3:6].
# This W exactly reproduces DirectNeuronTorqueController and the 0.266 baseline.
W_PAIR = np.array(
    [
        [1.0, 0.0, 0.0, -1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, -1.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, -1.0],
    ],
    dtype=float,
)


@dataclass
class World:
    model: mujoco.MjModel
    data: mujoco.MjData
    body_id: int
    qpos_adr: int
    qvel_adr: int
    total_mass: float
    gravity: float
    kq: np.ndarray
    kw: np.ndarray
    tau_limit: np.ndarray


def build_world(quad: str, dt: float) -> World:
    xml_path = B.MODEL_XMLS[quad]
    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)
    model.opt.timestep = dt

    free_jid = B.find_freejoint(model)
    body_id = model.jnt_bodyid[free_jid]
    qpos_adr = model.jnt_qposadr[free_jid]
    qvel_adr = model.jnt_dofadr[free_jid]

    total_mass = float(np.sum(model.body_mass))
    gravity = float(abs(model.opt.gravity[2]))
    inertia = np.array(model.body_inertia[body_id], dtype=float)
    kq, kw, tau_limit = B.build_scaled_gains(inertia)

    return World(model, data, body_id, qpos_adr, qvel_adr,
                 total_mass, gravity, kq, kw, tau_limit)


def reset_world(w: World, z_ref: float) -> None:
    if w.model.nu > 0:
        w.data.ctrl[:] = 0.0
    w.data.qpos[w.qpos_adr:w.qpos_adr + 3] = np.array([0.0, 0.0, z_ref])
    w.data.qpos[w.qpos_adr + 3:w.qpos_adr + 7] = np.array([1.0, 0.0, 0.0, 0.0])
    w.data.qvel[w.qvel_adr:w.qvel_adr + 6] = 0.0
    w.data.xfrc_applied[:] = 0.0
    w.data.time = 0.0
    mujoco.mj_forward(w.model, w.data)


class LearnedGate:
    """HyperLIF gate residual with a learnable 6->3 decode W.

    Replicates DirectNeuronTorqueController.step exactly when W = W_PAIR,
    learn=False, demand_mod=False, stn_mod=False.
    """

    def __init__(self, w: World, dt: float, sim_time: float,
                 neuron_name: str = "hyperlif",
                 blend: float = 0.5, gate_gain: float = 1e5,
                 current_bias: float = 0.75, current_gain: float = 1.25,
                 W: np.ndarray | None = None,
                 learn: bool = False, lr: float = 5e-4, k_err: float = 8.0,
                 k_rate: float = 0.0, leak: float = 0.0, w_clip: float = 6.0,
                 elig: bool = False, anneal: bool = False,
                 demand_mod: bool = False, k_demand: float = 6.0, gmin: float = 0.05,
                 stn_mod: bool = False):
        self.w = w
        self.dt = dt
        self.sim_time = max(sim_time, 1e-9)
        self.blend = blend
        self.gate_gain = gate_gain
        self.current_bias = current_bias
        self.current_gain = current_gain
        self.taul = np.asarray(w.tau_limit, dtype=float)
        self.kq = np.asarray(w.kq, dtype=float)
        self.kw = np.asarray(w.kw, dtype=float)

        self.neuron_name = neuron_name
        self.neuron = make_direct_neuron(neuron_name, n=6,
                                         activity_mode="gate", scale="control")
        self.W = (W.copy() if W is not None else W_PAIR.copy())

        self.learn = learn
        self.lr = lr
        self.k_err = k_err
        self.k_rate = k_rate
        self.leak = leak
        self.w_clip = w_clip
        self.elig = elig
        self.anneal = anneal
        self.e_trace = np.zeros(6, dtype=float)

        self.demand_mod = demand_mod
        self.k_demand = k_demand
        self.gmin = gmin

        self.stn_mod = stn_mod
        self.stn = (STNPIDAttitudeController(mode="stn_pes",
                                             tau_limit=float(np.max(self.taul)))
                    if stn_mod else None)

        # diagnostics
        self.activity_sum = 0.0
        self.residual_sum = 0.0
        self.n_steps = 0

    def encode(self, axis_error, omega):
        tau_pd = -self.kq * axis_error - self.kw * omega
        tau_pd = np.clip(tau_pd, -self.taul, self.taul)
        tau_norm = np.divide(tau_pd, self.taul,
                             out=np.zeros_like(tau_pd),
                             where=np.abs(self.taul) > 1e-12)
        tau_norm = np.clip(tau_norm, -1.0, 1.0)
        currents = np.zeros(6, dtype=float)
        currents[0:3] = self.current_bias + self.current_gain * np.maximum(tau_norm, 0.0)
        currents[3:6] = self.current_bias + self.current_gain * np.maximum(-tau_norm, 0.0)
        return tau_pd, currents

    def _lr_now(self, t):
        if not self.anneal:
            return self.lr
        frac = np.clip(t / self.sim_time, 0.0, 1.0)
        # start high, decay to 1/5th
        return self.lr * (1.0 - 0.8 * frac)

    def _decay_now(self, t):
        # eligibility trace: wide (0.98) early -> sharp (0.5) late
        if not self.anneal:
            return 0.9
        frac = np.clip(t / self.sim_time, 0.0, 1.0)
        return 0.98 - 0.48 * frac

    def step(self, t, axis_error, omega, dt):
        tau_pd, currents = self.encode(axis_error, omega)
        res = self.neuron.step(currents, dt)
        activity = np.clip(res.activity * self.gate_gain, 0.0, 1.0)

        signed = np.clip(self.W @ activity, -1.0, 1.0)
        tau_neuron = signed * self.taul

        if self.stn_mod and self.stn is not None:
            _tau_stn, info = self.stn.step(error=axis_error, omega=omega,
                                           dt=dt, measure=axis_error)
            kp_rel = np.array([info.get("Kp_x", 0.03),
                               info.get("Kp_y", 0.03),
                               info.get("Kp_z", 0.03)], dtype=float) / 0.03
            gain_mult = np.clip(1.0 + 0.6 * (kp_rel - 1.0), 0.4, 2.5)
            tau_neuron = tau_neuron * gain_mult

        blend_eff = self.blend
        if self.demand_mod:
            demand = np.clip(self.k_demand * float(np.linalg.norm(axis_error)),
                             self.gmin, 1.0)
            blend_eff = self.blend * demand

        tau = (1.0 - blend_eff) * tau_pd + blend_eff * tau_neuron
        tau = np.clip(tau, -self.taul, self.taul)

        if self.learn:
            self._update(t, axis_error, omega, activity, signed)

        self.activity_sum += float(np.mean(activity))
        self.residual_sum += float(np.linalg.norm(blend_eff * (tau_neuron - tau_pd)))
        self.n_steps += 1
        return tau

    def _update(self, t, axis_error, omega, activity, signed):
        # PES delta-rule: drive the decoded residual toward a PD-style torque
        # that opposes attitude error AND angular rate.  The rate (damping) term
        # is essential on step commands: a pure -k_err*error target learns extra
        # proportional gain, which overshoots and flips the quad on sharp steps.
        target = np.clip(-self.k_err * axis_error - self.k_rate * omega, -1.0, 1.0)
        e_dec = target - signed
        if self.elig:
            decay = self._decay_now(t)
            self.e_trace = decay * self.e_trace + (1.0 - decay) * activity
            act_used = self.e_trace
        else:
            act_used = activity
        # PES step with a weight leak (L2 decay) that bounds W and prevents
        # wind-up on sharp / step commands, plus a hard clip.
        self.W += self._lr_now(t) * np.outer(e_dec, act_used) - self.leak * self.W
        self.W = np.clip(self.W, -self.w_clip, self.w_clip)


def run_episode(w: World, gate: "LearnedGate | None", mission: str,
                sim_time: float, dt: float, z_ref: float,
                classical_only: bool = False) -> dict:
    reset_world(w, z_ref)
    if gate is not None:
        gate.neuron.reset()
    rows = []
    while w.data.time < sim_time:
        t = float(w.data.time)
        w.data.xfrc_applied[:] = 0.0

        pos = np.array(w.data.qpos[w.qpos_adr:w.qpos_adr + 3], dtype=float)
        vel = np.array(w.data.qvel[w.qvel_adr:w.qvel_adr + 3], dtype=float)
        q_mj = B.q_normalize(np.array(w.data.qpos[w.qpos_adr + 3:w.qpos_adr + 7], dtype=float))
        omega = np.array(w.data.qvel[w.qvel_adr + 3:w.qvel_adr + 6], dtype=float)

        q_meas = B.mujoco_quat_to_paper_quat(q_mj)
        q_ref = B.reference_quat(t, mission, sim_time)
        eul_ref = B.reference_euler(t, mission, sim_time)

        q_err = B.q_mul(q_ref, B.q_conj(q_meas))
        if q_err[0] < 0.0:
            q_err = -q_err
        axis_error = q_err[1:4]

        if classical_only or gate is None:
            tau_body = np.clip(-w.kq * axis_error - w.kw * omega,
                               -w.tau_limit, w.tau_limit)
        else:
            tau_body = gate.step(t, axis_error, omega, dt)
        tau_body = np.clip(tau_body, -w.tau_limit, w.tau_limit)

        r_wb = w.data.xmat[w.body_id].reshape(3, 3)
        body_z_world = r_wb[:, 2]
        tilt_cos = max(0.35, body_z_world[2])
        collective = w.total_mass * (
            w.gravity + 6.0 * (z_ref - pos[2]) + 4.0 * (0.0 - vel[2])
        ) / tilt_cos
        collective = np.clip(collective, 0.0, 2.5 * w.total_mass * max(w.gravity, 1.0))
        force_world = collective * body_z_world
        a_xy = -1.5 * pos[:2] - 2.2 * vel[:2]
        force_world[:2] += w.total_mass * B.clip_norm(a_xy, 3.0)

        w.data.xfrc_applied[w.body_id, 0:3] = force_world
        w.data.xfrc_applied[w.body_id, 3:6] = r_wb @ tau_body

        mujoco.mj_step(w.model, w.data)

        eul_meas = B.quat_to_euler(q_meas)
        eul_err = B.wrap_to_pi(eul_meas - eul_ref)
        rows.append({
            "t": t,
            "phi_err": eul_err[0], "theta_err": eul_err[1], "psi_err": eul_err[2],
            "qerr_angle": B.quat_angle_error(q_err),
            "z": pos[2],
            "tau_x": tau_body[0], "tau_y": tau_body[1], "tau_z": tau_body[2],
            "event_count_step": 0.0, "activity_mean": 0.0, "activity_max": 0.0,
        })

    summ = summarize_controller_run(rows, w.tau_limit)
    if gate is not None and gate.n_steps > 0:
        summ["gate_activity_mean"] = gate.activity_sum / gate.n_steps
        summ["gate_residual_mean"] = gate.residual_sum / gate.n_steps
    return summ


def collect_imitation_data(w: World, mission: str, sim_time: float,
                           dt: float, z_ref: float, blend: float = 1.0,
                           neuron_name: str = "hyperlif"):
    """Run STN-PES; simultaneously drive a HyperLIF gate with the PD-encoded
    currents to record (activity, target_signed) pairs, where the target is
    the STN-PES correction torque normalized into decode units."""
    reset_world(w, z_ref)
    stn = STNPIDAttitudeController(mode="stn_pes", tau_limit=float(np.max(w.tau_limit)))
    neuron = make_direct_neuron(neuron_name, n=6, activity_mode="gate", scale="control")
    taul = np.asarray(w.tau_limit, dtype=float)
    bias, cgain, ggain = 0.75, 1.25, 1e5

    acts, targs, pdns = [], [], []
    stn_score_rows = []
    while w.data.time < sim_time:
        t = float(w.data.time)
        w.data.xfrc_applied[:] = 0.0
        pos = np.array(w.data.qpos[w.qpos_adr:w.qpos_adr + 3], dtype=float)
        vel = np.array(w.data.qvel[w.qvel_adr:w.qvel_adr + 3], dtype=float)
        q_mj = B.q_normalize(np.array(w.data.qpos[w.qpos_adr + 3:w.qpos_adr + 7], dtype=float))
        omega = np.array(w.data.qvel[w.qvel_adr + 3:w.qvel_adr + 6], dtype=float)
        q_meas = B.mujoco_quat_to_paper_quat(q_mj)
        q_ref = B.reference_quat(t, mission, sim_time)
        eul_ref = B.reference_euler(t, mission, sim_time)
        q_err = B.q_mul(q_ref, B.q_conj(q_meas))
        if q_err[0] < 0.0:
            q_err = -q_err
        axis_error = q_err[1:4]

        tau_pd = np.clip(-w.kq * axis_error - w.kw * omega, -taul, taul)
        tau_norm = np.clip(np.divide(tau_pd, taul, out=np.zeros_like(tau_pd),
                                     where=np.abs(taul) > 1e-12), -1.0, 1.0)
        currents = np.zeros(6)
        currents[0:3] = bias + cgain * np.maximum(tau_norm, 0.0)
        currents[3:6] = bias + cgain * np.maximum(-tau_norm, 0.0)
        activity = np.clip(neuron.step(currents, dt).activity * ggain, 0.0, 1.0)

        tau_stn, _info = stn.step(error=axis_error, omega=omega, dt=dt, measure=axis_error)
        tau_stn = np.clip(np.asarray(tau_stn, dtype=float), -taul, taul)
        correction = blend * (-0.05) * tau_stn          # the STN-PES residual
        target_signed = np.clip(correction / taul, -1.0, 1.0)

        acts.append(activity.copy())
        targs.append(target_signed.copy())
        pdns.append(tau_norm.copy())

        # STN-PES body torque, so we also score the teacher on this run
        tau_body = np.clip(tau_pd + correction, -taul, taul)
        r_wb = w.data.xmat[w.body_id].reshape(3, 3)
        body_z_world = r_wb[:, 2]
        tilt_cos = max(0.35, body_z_world[2])
        collective = w.total_mass * (w.gravity + 6.0 * (z_ref - pos[2]) + 4.0 * (-vel[2])) / tilt_cos
        collective = np.clip(collective, 0.0, 2.5 * w.total_mass * max(w.gravity, 1.0))
        force_world = collective * body_z_world
        a_xy = -1.5 * pos[:2] - 2.2 * vel[:2]
        force_world[:2] += w.total_mass * B.clip_norm(a_xy, 3.0)
        w.data.xfrc_applied[w.body_id, 0:3] = force_world
        w.data.xfrc_applied[w.body_id, 3:6] = r_wb @ tau_body
        mujoco.mj_step(w.model, w.data)

        eul_meas = B.quat_to_euler(q_meas)
        eul_err = B.wrap_to_pi(eul_meas - eul_ref)
        stn_score_rows.append({
            "t": t, "phi_err": eul_err[0], "theta_err": eul_err[1], "psi_err": eul_err[2],
            "qerr_angle": B.quat_angle_error(q_err), "z": pos[2],
            "tau_x": tau_body[0], "tau_y": tau_body[1], "tau_z": tau_body[2],
        })

    A = np.array(acts).T          # 6 x N  gate activity
    T = np.array(targs).T         # 3 x N  STN correction only (decode units)
    PDN = np.array(pdns).T        # 3 x N  normalized PD torque (tau_pd / tau_limit)
    stn_summ = summarize_controller_run(stn_score_rows, w.tau_limit)
    return A, T, PDN, stn_summ


def fit_decode(A: np.ndarray, T: np.ndarray, lam: float = 1e-3) -> np.ndarray:
    """Ridge-regress W (3x6) so that W @ A ~ T."""
    G = A @ A.T + lam * np.eye(A.shape[0])
    W = (T @ A.T) @ np.linalg.inv(G)
    return W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quad", default="bitcraze_crazyflie_2", choices=sorted(B.MODEL_XMLS))
    ap.add_argument("--mission", default="hard45")
    ap.add_argument("--sim-time", type=float, default=45.0)
    ap.add_argument("--dt", type=float, default=0.0005)
    ap.add_argument("--z-ref", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=8e-4)
    ap.add_argument("--k-err", type=float, default=8.0)
    ap.add_argument("--k-rate", type=float, default=0.0,
                    help="Damping weight in the PES target (-k_rate*omega); stabilizes step commands.")
    ap.add_argument("--leak", type=float, default=0.0,
                    help="L2 weight leak per step on the learned decode (bounds W; stabilizes step commands).")
    ap.add_argument("--out", default=str(THIS_DIR / "learned_gate_results.json"))
    ap.add_argument("--methods", default="all")
    ap.add_argument("--neuron", default="hyperlif",
                    choices=["hyperlif", "adaptive_hyperlif"],
                    help="Direct neuron used by the gate residual (control scale, gate mode).")
    args = ap.parse_args()

    w = build_world(args.quad, args.dt)
    common = dict(mission=args.mission, sim_time=args.sim_time, dt=args.dt, z_ref=args.z_ref)
    gkw = dict(dt=args.dt, sim_time=args.sim_time, neuron_name=args.neuron)

    results = {}

    def record(name, summ):
        results[name] = summ
        extra = ""
        if "gate_residual_mean" in summ:
            extra = f"  act={summ.get('gate_activity_mean',0):.3e}  resid_tau={summ.get('gate_residual_mean',0):.3e}"
        print(f"{name:22s} score={summ['score']:.6f}  qerr_mean={summ['qerr_mean']:.6f}"
              f"  qerr_max={summ['qerr_max']:.4f}  sat={summ['sat_fraction']:.3f}{extra}", flush=True)

    want = args.methods.split(",") if args.methods != "all" else None
    def run(name):
        return want is None or name in want

    print(f"=== Learned gate residual :: neuron={args.neuron} :: {args.quad} / "
          f"{args.mission} / {args.sim_time}s ===", flush=True)

    # --- references ---
    if run("classical"):
        record("classical", run_episode(w, None, classical_only=True, **common))
    if run("fixed_gate"):
        g = LearnedGate(w, **gkw, blend=0.5, W=W_PAIR.copy())
        record("fixed_gate", run_episode(w, g, **common))

    # --- imitation (idea 2): collect STN-PES + gate activity, fit W ---
    # The blend architecture is tau = (1-b) tau_pd + b tau_neuron.  To make the
    # final torque equal the teacher (tau_pd + correction) the neuron must supply
    # tau_neuron = tau_pd + correction/b  (NOT the correction alone -- that was the
    # bug that halved the PD backbone and diverged).  Target in decode units:
    #   target = PDN + T_corr / b   (b = eval blend = 0.5)
    W_imit = None
    B_IMIT = 0.5
    if run("imitation") or run("imitation_pes"):
        A, T_corr, PDN, stn_summ = collect_imitation_data(
            w, args.mission, args.sim_time, args.dt, args.z_ref, blend=1.0,
            neuron_name=args.neuron)
        record("stn_pes_teacher", stn_summ)
        T_target = np.clip(PDN + T_corr / B_IMIT, -1.0, 1.0)
        W_imit = fit_decode(A, T_target, lam=1e-3)
        print(f"  [imitation] fit W range [{W_imit.min():.3f},{W_imit.max():.3f}]  "
              f"train MSE={np.mean((W_imit@A - T_target)**2):.3e}", flush=True)
    if run("imitation") and W_imit is not None:
        g = LearnedGate(w, **gkw, blend=0.5, W=W_imit.copy())
        record("imitation", run_episode(w, g, **common))

    # --- online PES (idea 1) ---
    if run("online_pes"):
        g = LearnedGate(w, **gkw, blend=0.5, W=W_PAIR.copy(),
                        learn=True, lr=args.lr, k_err=args.k_err,
                        k_rate=args.k_rate, leak=args.leak)
        record("online_pes", run_episode(w, g, **common))

    # --- imitation bootstrap + online PES refine ---
    if run("imitation_pes") and W_imit is not None:
        g = LearnedGate(w, **gkw, blend=0.5, W=W_imit.copy(),
                        learn=True, lr=args.lr * 0.5, k_err=args.k_err)
        record("imitation_pes", run_episode(w, g, **common))

    # --- annealed eligibility e-prop (idea 3) ---
    if run("eprop_anneal"):
        g = LearnedGate(w, **gkw, blend=0.5, W=W_PAIR.copy(),
                        learn=True, lr=args.lr * 2.0, k_err=args.k_err,
                        k_rate=args.k_rate, leak=args.leak,
                        elig=True, anneal=True)
        record("eprop_anneal", run_episode(w, g, **common))

    # --- demand-modulated gain (idea 4) ---
    if run("demand_mod"):
        g = LearnedGate(w, **gkw, blend=0.7, W=W_PAIR.copy(), demand_mod=True)
        record("demand_mod", run_episode(w, g, **common))
    if run("demand_mod_imit") and W_imit is not None:
        g = LearnedGate(w, **gkw, blend=0.7, W=W_imit.copy(), demand_mod=True)
        record("demand_mod_imit", run_episode(w, g, **common))

    # --- STN-PES-modulated HyperLIF (idea 5) ---
    if run("stn_mod"):
        g = LearnedGate(w, **gkw, blend=0.5, W=W_PAIR.copy(), stn_mod=True)
        record("stn_mod", run_episode(w, g, **common))
    if run("stn_mod_imit") and W_imit is not None:
        g = LearnedGate(w, **gkw, blend=0.5, W=W_imit.copy(), stn_mod=True)
        record("stn_mod_imit", run_episode(w, g, **common))

    Path(args.out).write_text(json.dumps(results, indent=2))
    print(f"\nSaved: {args.out}", flush=True)

    # ranking
    ranked = sorted(results.items(), key=lambda kv: kv[1]["score"])
    print("\n=== RANKING (lower score = better) ===", flush=True)
    base = results.get("classical", {}).get("score", None)
    for name, s in ranked:
        impr = f"  ({100*(base-s['score'])/base:+.1f}% vs classical)" if base else ""
        print(f"  {name:22s} {s['score']:.6f}{impr}", flush=True)


if __name__ == "__main__":
    main()
