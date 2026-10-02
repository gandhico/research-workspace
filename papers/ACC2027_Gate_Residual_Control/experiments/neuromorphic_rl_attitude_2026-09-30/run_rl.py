"""Matched MuJoCo attitude testbed for online TD actor-critic residuals.

This is an exploratory RL experiment, separate from the paper's PES results.
The CMG cell is the exact Nengo NeuronType.step implementation, called directly
at the plant clock. The learned actor/critic live outside Nengo; no claim of a
Nengo RL graph, spiking CMG, or hardware energy reduction is made.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import mujoco
import nengo
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
UPSTREAM = ROOT / "experiments" / "nengo_nef_replication_2026-08-29"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(UPSTREAM))

from gra_control.math3d import (  # noqa: E402
    quat_angle, quat_conj, quat_error, reference_quat,
)
from gra_control.platforms.drone import (  # noqa: E402
    SPECS, _free_joint, _mixer, torque_limits,
)
from nengo_cmg import CoupledMembraneGate  # noqa: E402
from run_mujoco_nef_baselines import AdvancedBaseline  # noqa: E402


MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
FAMILIES = ("cmg", "lif", "alif", "lifrate", "izhikevich", "paired-current", "constant")
CALIBRATION = json.loads((UPSTREAM / "feature_calibration.json").read_text())
TUNING = {
    "lif": (0.97, 1.03, 0.020),
    "alif": (0.97, 1.03, 0.020),
    "lifrate": (1.03, 0.97, 0.005),
    "izhikevich": (0.25, 1.75, 0.020),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ActivityBasis:
    """Six signed features, using the same neuron cells as the PES campaign."""

    def __init__(self, family: str, dt: float):
        self.family = family
        self.dt = dt
        self.bias, self.gain, self.tau_f = TUNING.get(family, (0.75, 1.25, 0.005))
        self.native_scale = float(CALIBRATION["families"].get(family, {}).get("native_current_scale", 1.0))
        self.feature_scale = float(CALIBRATION["families"].get(family, {}).get("feature_scale", 1.0))
        self.neuron = {
            "cmg": lambda: CoupledMembraneGate(adaptive=True),
            "lif": nengo.LIF,
            "alif": nengo.AdaptiveLIF,
            "lifrate": nengo.LIFRate,
            "izhikevich": nengo.Izhikevich,
        }.get(family, lambda: None)()
        self.raw = np.zeros(6)
        self.filtered = np.zeros(6)
        self.voltage = np.zeros(6)
        self.gate = np.zeros(6)
        self.refractory = np.zeros(6)
        self.adaptation = np.zeros(6)
        self.recovery = np.zeros(6)
        if family == "izhikevich":
            self.voltage[:] = -65.0

    def step(self, normalized_torque: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        n = np.clip(np.asarray(normalized_torque), -1.0, 1.0)
        current = self.bias + self.gain * np.r_[np.maximum(n, 0), np.maximum(-n, 0)]
        if self.family == "constant":
            return np.ones(6), current
        if self.family == "paired-current":
            return np.clip(current / (self.bias + self.gain), 0, 1), current
        drive = self.native_scale * current
        if self.family == "cmg":
            self.neuron.step(self.dt, drive, self.raw, self.voltage, self.gate)
            return np.clip(self.raw.copy(), 0, 1), current
        if self.family == "lifrate":
            self.neuron.step(self.dt, drive, self.raw)
        elif self.family == "lif":
            self.neuron.step(self.dt, drive, self.raw, self.voltage, self.refractory)
        elif self.family == "alif":
            self.neuron.step(self.dt, drive, self.raw, self.voltage, self.refractory, self.adaptation)
        elif self.family == "izhikevich":
            self.neuron.step(self.dt, drive, self.raw, self.voltage, self.recovery)
        self.filtered += -np.expm1(-self.dt / self.tau_f) * (self.raw - self.filtered)
        return np.clip(self.filtered / self.feature_scale, 0, 1), current


class TDLearner:
    """Linear Gaussian actor and linear TD(lambda) critic with local traces."""

    def __init__(self, seed: int, sigma: float = 0.08, actor_lr: float = 2e-5,
                 critic_lr: float = 1e-3, gamma: float = 0.98, lam: float = 0.90):
        self.rng = np.random.default_rng(seed)
        self.sigma = sigma
        self.actor_lr = actor_lr
        self.critic_lr = critic_lr
        self.gamma = gamma
        self.lam = lam
        self.actor = np.zeros((3, 16))
        self.critic = np.zeros(16)
        self.trace_actor = np.zeros_like(self.actor)
        self.trace_critic = np.zeros_like(self.critic)
        self.prev_phi = None
        self.prev_score = None

    def reset_traces(self):
        self.trace_actor.fill(0)
        self.trace_critic.fill(0)
        self.prev_phi = None
        self.prev_score = None

    def act(self, phi: np.ndarray, train: bool) -> tuple[np.ndarray, np.ndarray]:
        mean = np.tanh(self.actor @ phi)
        latent = mean + self.rng.normal(0, self.sigma, 3) if train else mean.copy()
        if train:
            score = np.outer((latent - mean) / (self.sigma ** 2) * (1 - mean ** 2), phi)
            self.prev_phi = phi.copy()
            self.prev_score = score
        return np.clip(latent, -1, 1), mean

    def learn(self, reward: float, next_phi: np.ndarray | None):
        if self.prev_phi is None:
            return 0.0
        current = float(self.critic @ self.prev_phi)
        bootstrap = float(self.critic @ next_phi) if next_phi is not None else 0.0
        td = float(np.clip(reward + self.gamma * bootstrap - current, -25, 25))
        self.trace_critic = np.clip(self.gamma * self.lam * self.trace_critic + self.prev_phi, -20, 20)
        self.trace_actor = np.clip(self.gamma * self.lam * self.trace_actor + self.prev_score, -100, 100)
        self.critic += np.clip(self.critic_lr * td * self.trace_critic, -0.02, 0.02)
        self.actor += np.clip(self.actor_lr * td * self.trace_actor, -0.002, 0.002)
        self.actor = np.clip(self.actor, -3, 3)
        return td


def make_phi(activity: np.ndarray, eq: np.ndarray, omega_error: np.ndarray,
             normalized_torque: np.ndarray) -> np.ndarray:
    return np.r_[1.0, activity - 0.5,
                 np.clip(eq / 0.1, -2, 2),
                 np.clip(omega_error, -2, 2),
                 np.clip(normalized_torque, -1, 1)]


def rollout(args, learner: TDLearner | None, family: str, mission: str,
            duration: float, seed: int, train: bool, output: Path | None):
    spec = SPECS[args.platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = args.dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    inertia = model.body_inertia[body_id].copy()
    limits = torque_limits(args.platform, inertia, model, "model")
    act_ids, mixer, mixer_inv, ctrl_range = _mixer(model)
    actuator_scale = 1.5 if args.platform == "cf2-rotor" else 1.0
    ctrl_range[:, 1] *= actuator_scale
    model.actuator_ctrlrange[act_ids, 1] = ctrl_range[:, 1]
    data.qpos[qa:qa + 3] = [0, 0, 1]
    data.qpos[qa + 3:qa + 7] = [1, 0, 0, 0]
    data.qvel[:] = 0
    data.ctrl[:] = 0
    mujoco.mj_forward(model, data)
    baseline_args = argparse.Namespace(
        baseline="backstepping", bw_scale=3.0, rate_ff="left-neg",
        no_model_ff=True, baseline_rate_hz=0.0, dt=args.dt,
        mission=mission, duration=duration,
    )
    baseline = AdvancedBaseline(baseline_args, inertia, limits, np.array([4.0, 4.0, 3.5]))
    basis = ActivityBasis(family, args.dt) if learner is not None else None
    if learner is not None:
        learner.reset_traces()
    decision_every = max(1, int(round(args.policy_dt / args.dt)))
    held_action = np.zeros(3)
    held_mean = np.zeros(3)
    reward_sum = 0.0
    error_sum = 0.0
    error_max = 0.0
    saturation_sum = 0
    gate_sum = 0
    effort_sum = 0.0
    reward_interval = 0.0
    interval_steps = 0
    rows = []
    full = {name: [] for name in ("t", "activity", "current", "voltage", "gate", "raw_neuron",
                                    "qerr_rad", "tau0", "raw_residual", "gated_residual",
                                    "tau_command", "tau_realized", "rotor_saturated", "output_gate")}
    step = 0
    while data.time < duration:
        t = float(data.time)
        q = quat_conj(np.asarray(data.qpos[qa + 3:qa + 7]).copy())
        omega = np.asarray(data.qvel[va + 3:va + 6]).copy()
        q_ref = reference_quat(t, mission, duration)
        qe, eq = quat_error(q_ref, q)
        theta = quat_angle(qe)
        tau0 = baseline.torque(t, eq, omega, q)
        normalized_torque = tau0 / limits
        if basis is not None:
            activity, current = basis.step(normalized_torque)
        else:
            activity, current = np.zeros(6), np.zeros(6)
        # Policy state uses the same measured variables as the paper baseline.
        omega_d = baseline._wd(t)
        phi = make_phi(activity, eq, omega - omega_d, normalized_torque)
        if step % decision_every == 0 and learner is not None:
            if train and interval_steps:
                learner.learn(reward_interval / interval_steps, phi)
            held_action, held_mean = learner.act(phi, train)
            reward_interval = 0.0
            interval_steps = 0
        # Optional uncertainty/error envelope is a new RL design choice. Keep
        # it zero for a direct bounded-interface comparison with the paper.
        envelope = (min(theta / args.error_envelope_rad, 1.0)
                    if args.error_envelope_rad > 0 else 1.0)
        raw_residual = args.beta * limits * envelope * held_action
        loaded = np.abs(tau0) >= limits - 1e-12
        output_gate = ~(loaded & (raw_residual * tau0 < 0))
        gated_residual = output_gate * raw_residual
        tau_command = np.clip(tau0 + gated_residual, -limits, limits)
        rotation = np.asarray(data.xmat[body_id]).reshape(3, 3)
        z = float(data.qpos[qa + 2])
        vz = float(data.qvel[va + 2])
        collective = mass * (gravity + 6 * (1 - z) - 4 * vz) / max(rotation[2, 2], 0.35)
        collective = float(np.clip(collective, 0, 2.5 * mass * max(gravity, 1)))
        rotor_requested = mixer_inv @ np.r_[collective, tau_command]
        rotor = np.clip(rotor_requested, ctrl_range[:, 0], ctrl_range[:, 1])
        rotor_sat = np.isclose(rotor, ctrl_range[:, 0], atol=1e-7) | np.isclose(rotor, ctrl_range[:, 1], atol=1e-7)
        realized = (mixer @ rotor)[1:]
        data.ctrl[:] = 0
        data.ctrl[act_ids] = rotor
        if args.disturbance_frac > 0:
            disturbance = args.disturbance_frac * limits * np.array([
                np.sin(1.31 * t + 0.2), 0.8 * np.sin(1.73 * t + 1.1),
                0.6 * np.sin(2.17 * t + 2.0),
            ])
            data.xfrc_applied[body_id, 3:6] = rotation @ disturbance
        reward = (-min(25.0, 1000.0 * theta ** 2)
                  - args.action_penalty * float(np.mean(held_action ** 2))
                  - 0.05 * float(np.any(rotor_sat)))
        reward_interval += reward
        interval_steps += 1
        error_sum += theta
        error_max = max(error_max, theta)
        saturation_sum += int(np.any(rotor_sat))
        gate_sum += int(np.any(~output_gate))
        effort_sum += float(np.mean((gated_residual / limits) ** 2))
        if output is not None:
            for name, value in (
                ("t", t), ("activity", activity), ("current", current),
                ("voltage", basis.voltage if basis else np.zeros(6)),
                ("gate", basis.gate if basis else np.zeros(6)),
                ("raw_neuron", basis.raw if basis else np.zeros(6)),
                ("qerr_rad", theta), ("tau0", tau0),
                ("raw_residual", raw_residual), ("gated_residual", gated_residual),
                ("tau_command", tau_command), ("tau_realized", realized),
                ("rotor_saturated", rotor_sat), ("output_gate", output_gate),
            ):
                full[name].append(np.asarray(value).copy())
            if step % decision_every == 0:
                rows.append({
                    "t": t, "qerr_rad": theta, "qerr_deg": np.degrees(theta),
                    "reward": reward, "action_x": held_action[0],
                    "action_y": held_action[1], "action_z": held_action[2],
                    "mean_x": held_mean[0], "mean_y": held_mean[1], "mean_z": held_mean[2],
                    "activity_mean": float(np.mean(activity)),
                    "rotor_saturated": int(np.any(rotor_sat)),
                    "gate_blocked": int(np.any(~output_gate)),
                })
        mujoco.mj_step(model, data)
        step += 1
    if train and learner is not None and interval_steps:
        learner.learn(reward_interval / interval_steps, None)
    steps = step
    summary = {
        "platform": args.platform, "mission": mission, "family": family,
        "train": train, "seed": seed, "duration_s": duration, "dt_s": args.dt,
        "policy_dt_s": decision_every * args.dt, "beta": args.beta,
        "error_envelope_rad": args.error_envelope_rad,
        "action_penalty": args.action_penalty,
        "disturbance_frac_limits": args.disturbance_frac,
        "qerr_true_mean_rad": error_sum / steps,
        "qerr_true_mean_deg": float(np.degrees(error_sum / steps)),
        "qerr_true_max_deg": float(np.degrees(error_max)),
        "rotor_saturation_fraction": saturation_sum / steps,
        "output_gate_fraction": gate_sum / steps,
        "realized_residual_normalized_rms": float(np.sqrt(effort_sum / steps)),
        "model_sha256": sha256(spec.model),
    }
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        with (output / "policy_trace.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        np.savez_compressed(output / "full_rate_trace.npz", **{k: np.asarray(v) for k, v in full.items()})
        (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform", choices=("x2", "cf2-rotor"), required=True)
    p.add_argument("--family", choices=FAMILIES, required=True)
    p.add_argument("--mode", choices=("baseline", "train-eval", "eval"), default="train-eval")
    p.add_argument("--train-episodes", type=int, default=12)
    p.add_argument("--train-duration", type=float, default=15.0)
    p.add_argument("--eval-duration", type=float, default=45.0)
    p.add_argument("--eval-missions", nargs="+", choices=MISSIONS, default=list(MISSIONS))
    p.add_argument("--dt", type=float, default=0.0005)
    p.add_argument("--policy-dt", type=float, default=0.020)
    p.add_argument("--beta", type=float, default=None)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--disturbance-frac", type=float, default=0.0)
    p.add_argument("--error-envelope-rad", type=float, default=0.0)
    p.add_argument("--action-penalty", type=float, default=0.03)
    p.add_argument("--checkpoint", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.beta = (0.5 if args.platform == "x2" else 0.2) if args.beta is None else args.beta
    if args.mode != "baseline" and not (0 < args.beta <= 1):
        p.error("RL beta must be in (0,1]")
    if args.dt <= 0 or args.policy_dt < args.dt or args.train_episodes < 0:
        p.error("invalid clock or episode count")
    if args.error_envelope_rad < 0 or args.action_penalty < 0:
        p.error("error envelope and action penalty must be nonnegative")
    args.output.mkdir(parents=True, exist_ok=True)
    learner = None if args.mode == "baseline" else TDLearner(args.seed)
    if args.mode == "eval":
        if args.checkpoint is None:
            p.error("--eval requires --checkpoint")
        with np.load(args.checkpoint) as archive:
            if str(archive["family"]) != args.family or str(archive["platform"]) != args.platform:
                p.error("checkpoint platform/family mismatch")
            learner.actor[:] = archive["actor"]
            learner.critic[:] = archive["critic"]
    train_rows = []
    if args.mode == "train-eval":
        # Fixed development split; all five 45-s evaluations are subsequent.
        for episode in range(args.train_episodes):
            mission = ("full3", "hard45")[episode % 2]
            row = rollout(args, learner, args.family, mission,
                          args.train_duration, args.seed + episode, True, None)
            row["episode"] = episode
            train_rows.append(row)
            print(f"train {episode + 1}/{args.train_episodes} {mission}: {row['qerr_true_mean_deg']:.3f} deg", flush=True)
        np.savez_compressed(args.output / "policy.npz", actor=learner.actor,
                            critic=learner.critic, family=args.family, platform=args.platform)
        (args.output / "training.json").write_text(json.dumps(train_rows, indent=2), encoding="utf-8")
    eval_rows = []
    for mission in args.eval_missions:
        out = args.output / "eval" / mission
        row = rollout(args, learner, args.family, mission, args.eval_duration,
                      args.seed + 10000, False, out)
        eval_rows.append(row)
        print(f"eval {mission}: {row['qerr_true_mean_deg']:.4f} deg", flush=True)
    source = {"runner": sha256(Path(__file__)), "cmg_neuron": sha256(UPSTREAM / "nengo_cmg.py"),
              "baseline": sha256(UPSTREAM / "run_mujoco_nef_baselines.py"),
              "math3d": sha256(ROOT / "src" / "gra_control" / "math3d.py")}
    manifest = {"status": "exploratory", "algorithm": "online linear Gaussian TD(lambda) actor-critic",
                "learning_signal": "TD reward prediction error, not PES teacher error",
                "development_missions": ["full3", "hard45"],
                "held_out_missions": ["roll", "hardstep", "yaw360"],
                "family_settings": TUNING.get(args.family, (0.75, 1.25, 0.005)),
                "args": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                "versions": {"mujoco": mujoco.__version__, "nengo": nengo.__version__,
                             "numpy": np.__version__},
                "source_sha256": source, "eval": eval_rows}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
