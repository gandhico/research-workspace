"""Full-rigid-body racing RL environment on the existing MuJoCo track.

Stage-1 observation intentionally includes the existing planned reference as
well as the next two gates. This is *trajectory-conditioned* vehicle control,
not a Swift-equivalent vision-only, time-optimal gate policy. The policy
commands collective thrust + body rates; the vehicle-specific mixer handles
rotors. The teacher is used only for common imitation initialization/anchor.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import mujoco
from scipy.optimize import lsq_linear

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(PROJECT))
import build_scene  # noqa: E402
import track  # noqa: E402
from controller import VehicleController  # noqa: E402
from race import GateJudge, VEHICLE_CFG  # noqa: E402


class RacingEnv:
    OBS_DIM = 26
    ACT_DIM = 4

    def __init__(self, vehicle: str = "x2", policy_dt: float = 0.02,
                 episode_s: float = 8.0, seed: int = 1,
                 observation: str = "reference"):
        if vehicle not in ("x2", "cf2", "y6"):
            raise ValueError("stage-1 4-command interface supports x2/cf2/y6; omni needs 6D wrench policy")
        if observation not in ("reference", "gate_only"):
            raise ValueError("observation must be reference or gate_only")
        self.vehicle, self.policy_dt, self.episode_s = vehicle, policy_dt, episode_s
        self.observation = observation
        self.seed = seed
        (HERE / "results").mkdir(exist_ok=True)
        _, self.m = build_scene.build(out=HERE / "results" / f"race_world_{vehicle}.xml",
                                      fleet=(vehicle,))
        self.d = mujoco.MjData(self.m)
        self.plant_dt = float(self.m.opt.timestep)
        self.substeps = round(policy_dt / self.plant_dt)
        if not np.isclose(self.substeps * self.plant_dt, policy_dt):
            raise ValueError("policy_dt must be an integer number of MuJoCo steps")
        line = track.RaceLine()
        root = build_scene.FLEET[vehicle][1]
        cfg = VEHICLE_CFG[vehicle]
        probe = VehicleController(self.m, vehicle, root, track.Trajectory(line, 2.0),
                                  auth_frac=cfg["auth_frac"])
        traj = track.Trajectory(line, probe.tw, laps=1, margin=cfg["margin"],
                                jerk_bw=np.sqrt(probe.kR) / 5.0)
        self.teacher = VehicleController(self.m, vehicle, root, traj,
                                         t_takeoff=3.0, t_start=7.0,
                                         auth_frac=cfg["auth_frac"])
        self.traj = traj
        self.gate_centres = np.asarray([x[1] for x in track.GATES], dtype=float)
        self.tmax = self.teacher.mass * 9.81 * self.teacher.tw
        self.rate_max = np.array([6.0, 6.0, 3.0])
        self.rate_gain = np.array([self.teacher.kW, self.teacher.kW, self.teacher.kW_yaw])
        self._prepare_start()
        self.reset()

    def _prepare_start(self):
        mujoco.mj_resetData(self.m, self.d)
        mujoco.mj_forward(self.m, self.d)
        self.teacher.p_start = None
        for _ in range(round(self.teacher.t_start / self.plant_dt)):
            self.teacher(self.d)
            mujoco.mj_step(self.m, self.d)
        self.start_qpos = self.d.qpos.copy()
        self.start_qvel = self.d.qvel.copy()
        self.start_act = self.d.act.copy()
        self.start_time = float(self.d.time)
        self.start_position = self.teacher.p_start.copy()

    def reset(self) -> np.ndarray:
        mujoco.mj_resetData(self.m, self.d)
        self.d.qpos[:] = self.start_qpos
        self.d.qvel[:] = self.start_qvel
        self.d.act[:] = self.start_act
        self.d.time = self.start_time
        self.d.ctrl[:] = 0.0
        mujoco.mj_forward(self.m, self.d)
        self.teacher.p_start = self.start_position.copy()
        self.teacher.log = dict(t=[], p=[], p_ref=[], u=[], sat=[])
        self.judge = GateJudge(self.m, self.vehicle, self.teacher.bid)
        self.judge.step(self.d)
        self.prev_action = np.zeros(4)
        self.prev_gate_distance = self._gate_distance()
        self.steps = 0
        return self.observe()

    def _gate_distance(self) -> float:
        p = self.teacher.state(self.d)[0]
        return float(np.linalg.norm(self.gate_centres[self.judge.next_gate] - p))

    def observe(self) -> np.ndarray:
        p, v, R, w = self.teacher.state(self.d)
        pr, vr, ar, yaw = self.teacher.reference(float(self.d.time))
        i = self.judge.next_gate
        body = R.T
        obs = np.r_[body @ (self.gate_centres[i] - p) / 15.0,
                    body @ (self.gate_centres[(i + 1) % 7] - p) / 15.0,
                    body @ v / 10.0,
                    body @ np.array([0.0, 0.0, 1.0]),
                    w / 10.0,
                    body @ (pr - p) / 5.0,
                    body @ (vr - v) / 10.0,
                    body @ ar / 10.0,
                    np.sin(yaw), np.cos(yaw)]
        if self.observation == "gate_only":
            # State and next-two-gate vectors remain; no planned path, speed,
            # acceleration or desired yaw is shown to the policy.
            obs[15:] = 0.0
        assert obs.shape == (self.OBS_DIM,)
        return np.clip(obs, -3.0, 3.0).astype(np.float32)

    def teacher_action(self) -> np.ndarray:
        """Geometric teacher projected to the common thrust/body-rate interface."""
        self.teacher(self.d)
        u = self.d.ctrl[self.teacher.act]
        wrench = self.teacher.Bs @ u
        _, _, _, w = self.teacher.state(self.d)
        alpha = np.linalg.solve(self.teacher.J, wrench[1:] - np.cross(w, self.teacher.J @ w))
        desired_rate = w + alpha / self.rate_gain
        action = np.r_[2.0 * wrench[0] / self.tmax - 1.0,
                       desired_rate / self.rate_max]
        return np.clip(action, -1.0, 1.0).astype(np.float32)

    def _apply_policy(self, action: np.ndarray):
        c = self.teacher
        _, _, _, w = c.state(self.d)
        thrust = 0.5 * (float(action[0]) + 1.0) * self.tmax
        desired_rate = action[1:] * self.rate_max
        tau = c.J @ (self.rate_gain * (desired_rate - w)) + np.cross(w, c.J @ w)
        wrench = np.r_[thrust, tau]
        u = c.Bpinv @ wrench
        saturated = np.any(u < c.lo - 1e-9) or np.any(u > c.hi + 1e-9)
        if saturated:
            weights = np.array([1.0, 1.0, 1.0, 0.05])
            u = lsq_linear(c.Bs * weights[:, None], wrench * weights,
                           bounds=(c.lo, c.hi), method="bvls").x
        self.d.ctrl[:] = 0.0
        self.d.ctrl[c.act] = u
        return bool(saturated), u.copy()

    def step(self, action: np.ndarray, teacher: bool = False):
        action = np.clip(np.asarray(action, dtype=float), -1.0, 1.0)
        if action.shape != (4,):
            raise ValueError("action must have four components [thrust, body rates]")
        before = len(self.judge.passes)
        crash_before = len(self.judge.crashes)
        saturation = 0
        rotor_last = np.zeros(len(self.teacher.act))
        for _ in range(self.substeps):
            if teacher:
                self.teacher(self.d)
                rotor_last = self.d.ctrl[self.teacher.act].copy()
                saturation += int(np.any(np.isclose(rotor_last, self.teacher.lo, atol=1e-8) |
                                         np.isclose(rotor_last, self.teacher.hi, atol=1e-8)))
            else:
                sat, rotor_last = self._apply_policy(action)
                saturation += int(sat)
            mujoco.mj_step(self.m, self.d)
            self.judge.step(self.d)
        p, v, R, w = self.teacher.state(self.d)
        pr, _, _, _ = self.teacher.reference(float(self.d.time))
        new_dist = self._gate_distance()
        new_passes = [x for x in self.judge.passes[before:] if x["in_order"]]
        progress = self.prev_gate_distance - new_dist if not new_passes else 0.0
        # Development reward: gate progress + a declared trajectory anchor.
        # It is not a time-optimal, gate-only Swift reward.
        reward = (2.0 * np.clip(progress, -1.0, 1.0)
                  + 12.0 * len(new_passes)
                  - 0.004 * min(25.0, np.linalg.norm(p - pr) ** 2)
                  - 0.001 * np.linalg.norm(w) ** 2
                  - 0.002 * np.linalg.norm(action - self.prev_action) ** 2
                  - 0.003 * saturation / self.substeps)
        crashed = len(self.judge.crashes) > crash_before
        if crashed:
            reward -= 25.0
        self.prev_action = action.copy()
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
        info = dict(time_s=float(self.d.time), gates_in_order=len([x for x in self.judge.passes if x["in_order"]]),
                    collisions=len(self.judge.crashes), position_error_m=float(np.linalg.norm(p - pr)),
                    saturation_fraction=saturation / self.substeps,
                    rotor=rotor_last, position=p.copy(), action=action.copy(),
                    termination_reason=reason)
        return self.observe(), float(reward), bool(done), info
