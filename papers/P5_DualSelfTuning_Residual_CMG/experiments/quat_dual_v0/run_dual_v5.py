"""v5 campaign runner: self-tuning S generalized to LQR/backstepping/MPC/NMPC (docs/PLAN.md v5 declaration).

  {family}_base   classical AdvancedBaseline, apa allocation, no S, no R
  {family}_res    classical + CMG-PES residual R (beta 0.5)           -- "just the residual"
  {family}_st     classical + v2 gated self-tuner S (mp, md only)     -- "just self-tuning"
  {family}_dual   S + R

family in (lqr, backstepping, mpc, nmpc). Missions: the 5 standard ones only (see dual_controller_v5.py
docstring for why). Allocation is always apa (P5's own selected allocation since v3 -- SCREEN.md), so *_base
here is a fresh, apa-allocation reference, not a re-read of A5's clip-allocation numbers: G9 compares this
runner at mp=md=1 (S disabled) against a direct, unwrapped AdvancedBaseline+apa computation of the same
mission, not against A5 (different allocation, would never match).

Run:  python run_dual_v5.py --family lqr --platform x2 --mission hard45 --controller lqr_dual --output <dir>
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import mujoco
import numpy as np

ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ACC / "src"))
sys.path.insert(0, str(HERE))

from gra_control.gate import CMGResidualAugmentor  # noqa: E402
from gra_control.math3d import quat_angle, quat_conj, quat_error, reference_quat  # noqa: E402
from gra_control.platforms.drone import SPECS, _free_joint, _mixer, torque_limits  # noqa: E402
from dual_controller import SelfTuner, TunerConfig  # noqa: E402
from dual_controller_v5 import FAMILIES, TunedBaseline  # noqa: E402
from run_dual import apa_allocate  # noqa: E402  (unchanged reuse, v3-selected allocation)

MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
PLATFORM_SCALE = {"x2": 1.0, "cf2-rotor": 1.5}
ARMS = ("base", "res", "st", "dual")


def controller_id(family: str, arm: str) -> str:
    return f"{family}_{arm}"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def gate_multiplier(mult: np.ndarray, loaded_prev: np.ndarray) -> np.ndarray:
    """v6, docs/ARCHITECTURE_MATH.md sec.8: a gain INCREASE (mult>1) on an axis already at its torque box
    last step is set back to exactly 1 (the un-boosted nominal gain) -- it cannot produce more realized
    torque, only a larger settling-tail transient once the axis un-saturates (R's own documented Hardstep
    mechanism, ACC2027 Sec. VI-E). Decreases (mult<1, i.e. mult-1<0) always pass through unchanged: reducing
    commanded torque on a loaded axis is never harmful. Default (loaded_prev all False) is a no-op, so v5's
    original numbers are exactly reproduced when this gate is not used."""
    return np.where((mult > 1.0) & loaded_prev, 1.0, mult)


def run(platform: str, mission: str, family: str, arm: str, output: Path, duration: float = 45.0,
        dt: float = 5e-4, beta: float = 0.5, learning_rate: float = 8e-4, k_error: float = 8.0,
        tuner: TunerConfig | None = None, log_every: int = 20, sat_gate_axes: bool = False) -> dict:
    if family not in FAMILIES:
        raise ValueError(family)
    if arm not in ARMS:
        raise ValueError(arm)
    if mission not in MISSIONS:
        raise ValueError(f"v5 covers only the 5 standard missions, not {mission!r} (see dual_controller_v5.py)")
    started = time.perf_counter()
    spec = SPECS[platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    inertia = model.body_inertia[body_id].copy()
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    limits = torque_limits(platform, inertia, model, "model")
    wn = np.array([4.0, 4.0, 3.5])

    data.qpos[qa:qa + 3] = [0.0, 0.0, 1.0]
    data.qpos[qa + 3:qa + 7] = [1.0, 0.0, 0.0, 0.0]
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0
    mujoco.mj_forward(model, data)
    act_ids, _, B_inv, ctrl_range = _mixer(model)
    ctrl_range[:, 1] *= PLATFORM_SCALE[platform]
    model.actuator_ctrlrange[act_ids, 1] = ctrl_range[:, 1]

    tb = TunedBaseline(family, mission, duration, dt, inertia, limits, wn)
    residual = (CMGResidualAugmentor(3, limits, "online_pes", True, beta, learning_rate=learning_rate)
                if arm in ("res", "dual") else None)
    st = None
    tcfg = None
    if arm in ("st", "dual"):
        tcfg = tuner or TunerConfig(v2_gating=True)
        st = SelfTuner(tcfg)

    n_steps = int(round(duration / dt))
    qerr, sat, res_norm, mults = [], [], [], []
    rows = []
    step = 0
    headroom_prev = 1.0
    loaded_prev = np.zeros(3, dtype=bool)
    gate_blocked_steps = 0
    z_min = float(data.qpos[qa + 2])
    diverged = False
    while data.time < duration:
        t = float(data.time)
        q_meas = quat_conj(np.asarray(data.qpos[qa + 3:qa + 7], dtype=float))
        omega = np.asarray(data.qvel[va + 3:va + 6], dtype=float).copy()
        qref = reference_quat(t, mission, duration)
        qe, eq = quat_error(qref, q_meas)

        if st is not None:
            mp, _mi, md = st.step(eq, omega, dt, headroom=headroom_prev)
            if sat_gate_axes:
                mp_g, md_g = gate_multiplier(mp, loaded_prev), gate_multiplier(md, loaded_prev)
                gate_blocked_steps += int(np.any(mp_g != mp) or np.any(md_g != md))
                mp, md = mp_g, md_g
        else:
            mp = md = np.ones(3)
        tau0 = tb.torque(t, eq, omega, q_meas, mp, md)
        if sat_gate_axes:
            loaded_prev = np.abs(tau0) >= limits
        if residual is not None:
            target = np.clip(-k_error * eq, -1.0, 1.0)
            out = residual.step(tau0, dt, target)
            tau, res = out.command, out.residual
        else:
            tau, res = tau0, np.zeros(3)

        R = np.asarray(data.xmat[body_id], dtype=float).reshape(3, 3)  # noqa: F841 (parity with run_dual.py)
        z, vz = float(data.qpos[qa + 2]), float(data.qvel[va + 2])
        tilt = max(float(np.asarray(data.xmat[body_id]).reshape(3, 3)[2, 2]), 0.35)
        collective = float(np.clip(mass * (gravity + 6.0 * (1.0 - z) - 4.0 * vz) / tilt,
                                   0.0, 2.5 * mass * max(gravity, 1.0)))
        data.ctrl[:] = 0.0
        motors, alpha, _ = apa_allocate(B_inv, collective, tau, ctrl_range[:, 0], ctrl_range[:, 1])
        if not np.all(np.isfinite(motors)):
            diverged = True
            break
        data.ctrl[act_ids] = motors
        saturated = bool(np.any(np.isclose(motors, ctrl_range[:, 0], atol=1e-7)) or
                         np.any(np.isclose(motors, ctrl_range[:, 1], atol=1e-7)))
        mujoco.mj_step(model, data)
        if not np.all(np.isfinite(data.qpos)):
            diverged = True
            break
        span = np.maximum(ctrl_range[:, 1] - ctrl_range[:, 0], 1e-12)
        headroom_prev = float(np.clip(np.min(np.minimum(motors - ctrl_range[:, 0], ctrl_range[:, 1] - motors)
                                             / (0.5 * span)), 0.0, 1.0))
        z_min = min(z_min, float(data.qpos[qa + 2]))

        qerr.append(quat_angle(qe))
        sat.append(saturated)
        res_norm.append(float(np.linalg.norm(res)))
        mults.append(np.concatenate([mp, md]))
        if step % log_every == 0:
            row = {"t": t, "qerr": qerr[-1], "saturated": int(saturated), "z": z, "alpha": alpha}
            for k, v in zip("xyz", eq):
                row[f"eq_{k}"] = float(v)
            for k, v in zip("xyz", tau0):
                row[f"tau0_{k}"] = float(v)
            for k, v in zip("xyz", res):
                row[f"res_{k}"] = float(v)
            for g, block in (("p", mp), ("d", md)):
                for k, v in zip("xyz", block):
                    row[f"m{g}_{k}"] = float(v)
            rows.append(row)
        step += 1

    if diverged:
        qerr += [float(np.pi)] * (n_steps - len(qerr))
        sat += [True] * (n_steps - len(sat))
    output.mkdir(parents=True, exist_ok=True)
    if rows:
        with (output / "trace.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    qerr_arr = np.asarray(qerr)
    mults_arr = np.asarray(mults) if mults else np.zeros((1, 6))
    summary = {
        "platform": platform, "mission": mission, "family": family, "arm": arm,
        "controller": controller_id(family, arm), "allocation": "apa", "sat_gate_axes": sat_gate_axes,
        "gate_blocked_fraction": (gate_blocked_steps / max(step, 1)) if sat_gate_axes else None,
        "duration_s": duration, "dt_s": dt, "steps": step, "diverged": diverged, "z_min_m": z_min,
        "beta": beta, "learning_rate": learning_rate, "k_error": k_error,
        "tuner": tcfg.__dict__ if tcfg is not None else None,
        "qerr_mean_rad": float(qerr_arr.mean()), "qerr_rmse_rad": float(np.sqrt(np.mean(qerr_arr ** 2))),
        "qerr_max_rad": float(qerr_arr.max()), "saturation_fraction": float(np.mean(sat)) if sat else None,
        "residual_rms_Nm": float(np.sqrt(np.mean(np.square(res_norm)))) if res_norm else None,
        "torque_limits_Nm": limits.tolist(),
        "multiplier_mean": mults_arr.mean(axis=0).tolist(),
        "multiplier_min": mults_arr.min(axis=0).tolist(),
        "multiplier_max": mults_arr.max(axis=0).tolist(),
        "WS_final_fro": float(np.linalg.norm(st.W)) if st is not None else None,
        "WR_final_fro": float(np.linalg.norm(residual.W)) if residual is not None else None,
        "wall_s": time.perf_counter() - started,
        "hashes": {
            "run_dual_v5.py": sha(HERE / "run_dual_v5.py"),
            "dual_controller_v5.py": sha(HERE / "dual_controller_v5.py"),
            "dual_controller.py": sha(HERE / "dual_controller.py"),
            "run_dual.py": sha(HERE / "run_dual.py"),
            "run_mujoco_nef_baselines.py": sha(ACC / "experiments" / "nengo_nef_replication_2026-08-29" /
                                                "run_mujoco_nef_baselines.py"),
            "model": sha(spec.model),
        },
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--platform", choices=tuple(PLATFORM_SCALE), required=True)
    ap.add_argument("--mission", choices=MISSIONS, required=True)
    ap.add_argument("--family", choices=FAMILIES, required=True)
    ap.add_argument("--arm", choices=ARMS, required=True)
    ap.add_argument("--duration", type=float, default=45.0)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    s = run(a.platform, a.mission, a.family, a.arm, a.output, duration=a.duration)
    print(json.dumps({k: s[k] for k in ("platform", "mission", "controller", "qerr_mean_rad",
                                          "saturation_fraction", "diverged", "z_min_m", "wall_s")}, indent=1))


if __name__ == "__main__":
    main()
