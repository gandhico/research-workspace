"""Baseline-centred racing dual controller (X2/CF2 only).

This is a NEW racing-level dual architecture: bounded adaptation of the
inner body-rate gain plus bounded correction to the teacher's wrench.
It is not the ACC paper's quaternion-PD gain adaptation design. At zero
modulation the exact teacher rotor vector is used without reallocation.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
from scipy.optimize import lsq_linear
import mujoco

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "rl_cmg_2026_09_30"
sys.path.insert(0, str(PARENT))
from racing_env import RacingEnv  # noqa: E402


class DualEnv(RacingEnv):
    RESIDUAL_SCALE = np.array([0.06, 0.12, 0.12, 0.08])
    GAIN_SCALE = 0.20

    def __init__(self, vehicle="x2", scenario="nominal", policy_dt=0.02,
                 episode_s=12.0, seed=1):
        if vehicle not in ("x2", "cf2"):
            raise ValueError("benchmark is restricted to X2 and CF2")
        if scenario not in ("nominal", "gust"):
            raise ValueError(scenario)
        self.scenario = scenario
        self.gain_scale = np.ones(3)
        super().__init__(vehicle, policy_dt, episode_s, seed, observation="reference")

    def reset(self):
        obs = super().reset()
        self.gain_scale = np.ones(3)
        self.d.xfrc_applied[:] = 0.0
        return obs

    def _disturbance(self):
        self.d.xfrc_applied[:] = 0.0
        if self.scenario != "gust":
            return
        c = self.teacher
        t = float(self.d.time) - self.start_time
        R = self.d.xmat[c.bid].reshape(3, 3)
        force_world = (0.15 * c.mass * 9.81 *
                       np.array([np.sin(0.73 * t + 0.4),
                                 0.75 * np.sin(1.17 * t + 0.9),
                                 0.25 * np.sin(0.53 * t + 0.2)]))
        inertia_diag = np.diag(c.J)
        torque_body = (0.15 * 0.25 * inertia_diag * c.alpha_max *
                       np.array([np.sin(1.31 * t + 0.2),
                                 np.sin(1.73 * t + 1.1),
                                 0.5 * np.sin(2.11 * t + 0.7)]))
        self.d.xfrc_applied[c.bid, :3] = force_world
        self.d.xfrc_applied[c.bid, 3:] = R @ torque_body

    def step(self, action, teacher=False):
        self._disturbance()
        return super().step(action, teacher=teacher)

    def step_dual(self, latent, arm="dual"):
        """Policy latent in [-1,1]^7: [4 wrench residual, 3 gain modulation]."""
        z = np.clip(np.asarray(latent, dtype=float), -1.0, 1.0)
        if z.shape != (7,):
            raise ValueError("dual latent must be seven-dimensional")
        if arm not in ("baseline", "self", "residual", "dual"):
            raise ValueError(arm)
        residual = self.RESIDUAL_SCALE * z[:4] if arm in ("residual", "dual") else np.zeros(4)
        self.gain_scale = (1.0 + self.GAIN_SCALE * z[4:]
                           if arm in ("self", "dual") else np.ones(3))
        c = self.teacher
        before = len(self.judge.passes)
        crash_before = len(self.judge.crashes)
        saturated_count = 0
        rotor_last = np.zeros(len(c.act))
        wrench_delta_last = np.zeros(4)
        self._disturbance()
        for _ in range(self.substeps):
            c(self.d)
            rotor0 = self.d.ctrl[c.act].copy()
            rotor = rotor0.copy()
            if arm != "baseline" and np.any(z != 0):
                wrench0 = c.Bs @ rotor0
                _, _, _, w = c.state(self.d)
                gyroscopic = np.cross(w, c.J @ w)
                rate_error = np.linalg.solve(c.J, wrench0[1:] - gyroscopic) / self.rate_gain
                delta_thrust = 0.5 * self.tmax * residual[0]
                delta_rate = self.rate_max * residual[1:]
                delta_tau_res = c.J @ (self.rate_gain * delta_rate)
                delta_tau_gain = c.J @ (self.rate_gain * (self.gain_scale - 1.0) * rate_error)
                delta_wrench = np.r_[delta_thrust, delta_tau_res + delta_tau_gain]
                wrench_delta_last = delta_wrench.copy()
                requested = wrench0 + delta_wrench
                rotor = c.Bpinv @ requested
                if np.any(rotor < c.lo - 1e-9) or np.any(rotor > c.hi + 1e-9):
                    weights = np.array([1.0, 1.0, 1.0, 0.05])
                    rotor = lsq_linear(c.Bs * weights[:, None], requested * weights,
                                       bounds=(c.lo, c.hi), method="bvls").x
                self.d.ctrl[c.act] = rotor
            saturated_count += int(np.any(np.isclose(rotor, c.lo, atol=1e-8) |
                                          np.isclose(rotor, c.hi, atol=1e-8)))
            rotor_last = rotor.copy()
            mujoco.mj_step(self.m, self.d)
            self.judge.step(self.d)
        p, _, _, w = c.state(self.d)
        pr, _, _, _ = c.reference(float(self.d.time))
        new_dist = self._gate_distance()
        new_passes = [x for x in self.judge.passes[before:] if x["in_order"]]
        progress = self.prev_gate_distance - new_dist if not new_passes else 0.0
        position_error = float(np.linalg.norm(p - pr))
        base_reward = (2.0 * np.clip(progress, -1.0, 1.0)
                       + 12.0 * len(new_passes)
                       - 0.004 * min(25.0, position_error ** 2)
                       - 0.001 * np.linalg.norm(w) ** 2
                       - 0.003 * saturated_count / self.substeps)
        crashed = len(self.judge.crashes) > crash_before
        if crashed:
            base_reward -= 25.0
        self.prev_gate_distance = new_dist
        self.steps += 1
        invalid = not np.isfinite(self.d.qpos).all()
        timeout = self.steps * self.policy_dt >= self.episode_s
        completed = len([x for x in self.judge.passes if x["in_order"]]) >= 7
        outside = np.linalg.norm(p[:2]) > 30.0
        ground = p[2] < 0.15
        done = crashed or invalid or ground or outside or timeout or completed
        reason = ("collision" if crashed else "invalid_state" if invalid else
                  "ground" if ground else "outside" if outside else
                  "seven_gates" if completed else "time_limit" if timeout else "")
        # Common, predeclared reward; gate progression still comes from the
        # parent environment. A denser trajectory term distinguishes small
        # tracking effects while the baseline already passes the gates.
        reward = (base_reward - 0.5 * min(25.0, position_error ** 2)
                  - 0.01 * float(np.mean(z ** 2)))
        info = dict(time_s=float(self.d.time), gates_in_order=len([x for x in self.judge.passes if x["in_order"]]),
                    collisions=len(self.judge.crashes), position_error_m=position_error,
                    saturation_fraction=saturated_count / self.substeps,
                    rotor=rotor_last, position=p.copy(), termination_reason=reason,
                    residual_action=residual.copy(), gain_scale=self.gain_scale.copy(),
                    wrench_delta=wrench_delta_last,
                    disturbance_force_world=self.d.xfrc_applied[c.bid, :3].copy(),
                    disturbance_torque_world=self.d.xfrc_applied[c.bid, 3:].copy())
        return self.observe(), float(reward), bool(done), info
