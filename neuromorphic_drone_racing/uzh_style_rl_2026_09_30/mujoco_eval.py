"""Fly a frozen, exported policy in the full MuJoCo race world (sim-to-sim transfer test). No PyTorch import.

Uses rl_cmg_2026_09_30/racing_env.RacingEnv: same X2 model, thrust/body-rate interface, rotor allocation,
real MuJoCo contacts with gate frames and legs, and race.GateJudge. The observation and CMG features are rebuilt
exactly as in vec_race.py / train_ppo.py (CMG cells from cmg_cells.py, identical to the batched cells to 1e-15).
Usage: python mujoco_eval.py <run_dir> [--laps 2] [--viewer]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "rl_cmg_2026_09_30"))
sys.path.insert(0, str(HERE.parent))
from racing_env import RacingEnv  # noqa: E402
from cmg_cells import CMGPopulation, policy_preset  # noqa: E402
import track  # noqa: E402

GC = np.array([c for _, c, _ in track.GATES], float)
GN = np.array([track.gate_normal(y) for _, _, y in track.GATES])


def observe(env, prev_action):
    p, v, R, w = env.teacher.state(env.d)
    i = env.judge.next_gate
    j = (i + 1) % 7
    obs = np.r_[R.T @ v / 10.0, R.reshape(9), w / 10.0, R.T @ (GC[i] - p) / 15.0, R.T @ GN[i],
                R.T @ (GC[j] - p) / 15.0, R.T @ GN[j], prev_action]
    return np.clip(obs, -3, 3)


class HyperLIFNumpy:
    """P2 HyperLIF (HyperLIFNengo.step, P2 defaults), same equations as vec_race.HyperLIFBatch."""

    def __init__(self, n, tau_syn=0.02, scale_hz=75.0):
        self.v, self.r, self.rate = np.zeros(n), np.zeros(n), np.zeros(n)
        self.tau_syn, self.scale_hz = tau_syn, scale_hz

    def step(self, j, dt):
        v_prev = self.v
        x = np.clip(100.0 * (self.v - (1.0 - 0.2 * self.r)), -700, 700)
        target = 1.0 / (1.0 + np.exp(-x))
        self.r = np.clip(target + (self.r - target) * np.exp(-dt / 0.002), 0.0, 1.0)
        c = 100.0 * self.r ** 2
        lam = 1.0 / 0.02 + c
        decay = np.exp(-lam * dt)
        self.v = np.maximum(self.v * decay + (j / 0.02) / lam * (1.0 - decay), 0.0)
        ev = ((v_prev < 1.0) & (self.v >= 1.0)).astype(float)
        self.rate += -np.expm1(-dt / self.tau_syn) * (ev / dt - self.rate)


class Policy:
    def __init__(self, path):
        z = dict(np.load(path, allow_pickle=True))
        self.z, self.arm = z, str(z["arm"])
        mode = {"mlp": None, "cmg": "graded", "cmg_crossing": "crossing", "cmg_reset_gate": "reset_gate",
                "cmg_spike": "reset_spike", "hyperlif_spike": "hyperlif", "hyperlif_gate": "hyperlif",
                "cmg_acc": "acc"}[self.arm]
        self.hl = HyperLIFNumpy(32) if mode == "hyperlif" else None
        self.acc = None
        if mode == "acc":   # the ACC controller's own neuron bank
            sys.path.insert(0, r"C:\Research\papers\ACC2027_Gate_Residual_Control\src")
            from gra_control.gate import CMGConfig, CoupledMembraneGateBank
            self.acc = CoupledMembraneGateBank(32, True, CMGConfig())
        self.cmg = None if mode in (None, "hyperlif", "acc") else CMGPopulation(32, mode, policy_preset(mode))

    def features(self, obs):
        if self.hl is not None:
            j = 1.0 + 1.25 * 0.5 * (1.0 + np.tanh(self.z["enc"] @ obs + self.z["off"]))
            for _ in range(200):
                self.hl.step(j, 1e-4)
            return np.clip(self.hl.r, 0, 1) if self.arm == "hyperlif_gate" else np.clip(self.hl.rate / 75.0, 0, 1)
        if self.acc is not None:
            zz = np.tanh(self.z["enc"][:16] @ obs)
            j = np.r_[0.75 + 1.25 * np.maximum(zz, 0), 0.75 + 1.25 * np.maximum(-zz, 0)]
            for _ in range(40):
                r = self.acc.step(j, 0.0005)
            return np.clip(1e5 * r, 0, 1)
        if self.cmg is None:
            return np.zeros(32)
        j = np.clip(0.85 + self.z["off"] + 0.95 * np.tanh(self.z["enc"] @ obs), 0.05, 2.2)
        return self.cmg.advance(j, 0.02, 0.0005)

    def act(self, obs):
        z = self.z
        x = np.r_[obs, self.features(obs)]
        x = np.clip((x - z["norm_mean"]) / np.sqrt(z["norm_var"] + 1e-8), -5, 5)
        h = np.tanh(z["pi_0_weight"] @ x + z["pi_0_bias"])
        h = np.tanh(z["pi_2_weight"] @ h + z["pi_2_bias"])
        return np.tanh(z["pi_4_weight"] @ h + z["pi_4_bias"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--laps", type=int, default=1)
    ap.add_argument("--time-s", type=float, default=40.0)
    ap.add_argument("--viewer", action="store_true")
    a = ap.parse_args()
    pol = Policy(a.run / "policy_numpy.npz")
    env = RacingEnv("x2", policy_dt=0.02, episode_s=a.time_s, seed=1, observation="reference")
    env.reset()
    viewer = None
    if a.viewer:
        import mujoco.viewer
        viewer = mujoco.viewer.launch_passive(env.m, env.d)
    prev = np.zeros(4)
    log = {k: [] for k in ("t", "p", "action", "gates", "sat")}
    t0 = time.perf_counter()
    info = {}
    for _ in range(round(a.time_s / 0.02)):
        obs = observe(env, prev)
        act = pol.act(obs)
        _, _, done, info = env.step(act)
        prev = act
        log["t"].append(info["time_s"] - env.start_time); log["p"].append(info["position"])
        log["action"].append(act); log["gates"].append(info["gates_in_order"]); log["sat"].append(info["saturation_fraction"])
        if viewer is not None:
            viewer.sync()
            time.sleep(max(0.0, log["t"][-1] - (time.perf_counter() - t0)))
        if done:
            break
    gates = np.asarray(log["gates"])
    gate_times = [round(float(log["t"][int(np.argmax(gates >= g))]), 2) for g in range(1, int(gates[-1]) + 1)]
    res = dict(run=str(a.run), arm=pol.arm, gates_in_order=int(gates[-1]), collisions=int(info["collisions"]),
               termination=info["termination_reason"], lap_completed=bool(gates[-1] >= 7),
               lap_time_s=gate_times[6] if len(gate_times) >= 7 else None, gate_times_s=gate_times,
               mean_rotor_saturation=float(np.mean(log["sat"])),
               note="full MuJoCo race world, frozen policy, perfect state, no learning during the flight")
    (a.run / "mujoco_eval.json").write_text(json.dumps(res, indent=1))
    np.savez_compressed(a.run / "mujoco_flight.npz", **{k: np.asarray(v) for k, v in log.items()})
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
