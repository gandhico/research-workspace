"""Quaternion attitude tracking: PID, residual, self-tuning, and dual controllers.

Plant, missions, gains, torque limits, allocation and collective thrust are the
ACC 2027 canonical ones (gra_control, imported read-only).

  v0  pid         quaternion PID, k_i = 0.05 k_q, conditional integration
      pid_res     pid + CMG-PES bounded residual (beta 0.5)
      st_pid      pid with CMG-PES target-scheduled gains (beta_g 0.5)
      dual        st_pid + residual
  v1  st_pid_f    st_pid, p/i targets retreat to nominal while saturated
      dual_f      st_pid_f + residual
      stn         faithful CMG STN-PID-PES (Olivares et al. 2026): unbounded MIT-rule gains
      stn_b       bounded STN: projection [0.5, 1.5], leak, conditional adaptation
      dual_stn_b  stn_b + residual

Held-out missions (declared in docs/PLAN.md before v1 results): hard45b, hardstep_b.

Run:  python run_dual.py --platform x2 --mission full3 --controller dual_stn_b --output <dir>
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
from gra_control.math3d import euler_to_quat, quat_angle, quat_conj, quat_error, reference_quat  # noqa: E402
from gra_control.platforms.drone import SPECS, _free_joint, _mixer, torque_limits  # noqa: E402
from dual_controller import (IDGainCorrector, IDGCConfig, PIDBase, SelfTuner, STNConfig, STNSelfTuner,  # noqa: E402
                             TunerConfig)

CONTROLLERS = ("pid", "pid_res", "st_pid", "dual", "st_pid_f", "dual_f", "stn", "stn_b", "dual_stn_b",
               "stn_b_ks", "dual_stn_b_ks", "st_pid_v2", "dual_v2", "stn_ks_v2", "dual_stn_ks_v2",
               "stn_dx_v3", "dual_stn_dx_v3", "pid_body", "pid_res_body", "idgc_v4", "dual_idgc_v4")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
HELDOUT = ("hard45b", "hardstep_b", "hard45c", "hardstep_c")
PLATFORM_SCALE = {"x2": 1.0, "cf2-rotor": 1.5}
ALLOCATIONS = ("clip", "tpa", "tpa_r", "apa")
RESIDUAL = {"pid_res", "dual", "dual_f", "dual_stn_b", "dual_stn_b_ks", "dual_v2", "dual_stn_ks_v2", "dual_stn_dx_v3",
            "pid_res_body", "dual_idgc_v4"}
BODY_GAINS = {"pid_body", "pid_res_body"}          # v4: gains from body-frame diag(J) instead of j_tune
IDGC = {"idgc_v4", "dual_idgc_v4"}                 # v4: identification-based gain correction
# value: (freeze_on_sat, v2_gating)
TARGET_TUNER = {"st_pid": (False, False), "dual": (False, False), "st_pid_f": (True, False),
                "dual_f": (True, False), "st_pid_v2": (False, True), "dual_v2": (False, True)}
# value: (bounded, known_sign, v2_gating, dither_id). *_ks = post-smoke ablation, Yhat = +1 (PLAN v1 addendum)
STN_TUNER = {"stn": (False, False, False, False), "stn_b": (True, False, False, False),
             "dual_stn_b": (True, False, False, False), "stn_b_ks": (True, True, False, False),
             "dual_stn_b_ks": (True, True, False, False), "stn_ks_v2": (True, True, True, False),
             "dual_stn_ks_v2": (True, True, True, False), "stn_dx_v3": (True, False, True, True),
             "dual_stn_dx_v3": (True, False, True, True)}


def tpa_allocate(B_inv: np.ndarray, T: float, tau: np.ndarray, lo: np.ndarray, hi: np.ndarray):
    """Thrust-priority allocation (ARCHITECTURE_MATH §7.1): keep collective, scale torque by alpha in [0, 1]."""
    c = B_inv[:, 0]
    pos = c > 1e-12
    if np.any(pos):
        T = min(T, float(np.min(hi[pos] / c[pos])))
    T = max(T, 0.0)
    f_T = c * T
    f_tau = B_inv[:, 1:] @ tau
    alpha = 1.0
    for i in range(len(f_T)):
        if f_tau[i] > 1e-15:
            alpha = min(alpha, (hi[i] - f_T[i]) / f_tau[i])
        elif f_tau[i] < -1e-15:
            alpha = min(alpha, (f_T[i] - lo[i]) / (-f_tau[i]))
    alpha = float(np.clip(alpha, 0.0, 1.0))
    return np.clip(f_T + alpha * f_tau, lo, hi), alpha, T


def tpa_r_allocate(B_inv, T, tau, lo, hi, reserve: float = 0.25):
    """Thrust priority with a torque reserve: collective capped at (1 - reserve) T_max (PLAN v3 addendum)."""
    c = B_inv[:, 0]
    pos = c > 1e-12
    if np.any(pos):
        T = min(T, (1.0 - reserve) * float(np.min(hi[pos] / c[pos])))
    return tpa_allocate(B_inv, T, tau, lo, hi)


def _collective_interval(c, f_tau, lo, hi):
    pos = c > 1e-12
    t_lo = float(np.max((lo[pos] - f_tau[pos]) / c[pos]))
    t_hi = float(np.min((hi[pos] - f_tau[pos]) / c[pos]))
    return t_lo, t_hi


def apa_allocate(B_inv, T, tau, lo, hi):
    """Attitude priority: keep torque, move collective to the closest feasible value; scale torque only if needed."""
    c = B_inv[:, 0]
    f_tau = B_inv[:, 1:] @ tau
    t_lo, t_hi = _collective_interval(c, f_tau, lo, hi)
    alpha = 1.0
    if t_lo > t_hi:                                   # no collective realizes tau: largest feasible alpha
        a_lo, a_hi = 0.0, 1.0
        for _ in range(40):
            a = 0.5 * (a_lo + a_hi)
            l, h = _collective_interval(c, a * f_tau, lo, hi)
            if l <= h:
                a_lo = a
            else:
                a_hi = a
        alpha = a_lo
        t_lo, t_hi = _collective_interval(c, alpha * f_tau, lo, hi)
    T_new = float(np.clip(T, t_lo, t_hi))
    return np.clip(c * T_new + alpha * f_tau, lo, hi), alpha, T_new


def heldout_euler(t: float, mission: str) -> np.ndarray:
    if mission == "hard45b":
        return np.array([
            0.50 * np.sin(0.85 * t + 0.3) + 0.18 * np.sin(1.95 * t),
            0.40 * np.sin(1.05 * t + 1.0) + 0.20 * np.sin(1.55 * t + 0.7),
            0.60 * np.sin(0.65 * t + 2.0) + 0.22 * np.sin(1.25 * t),
        ])
    if mission == "hardstep_b":
        if t < 1.0:
            return np.zeros(3)
        rows = [[-0.60, 0.50, -0.45], [0.70, -0.40, 0.80], [-0.55, -0.55, -0.60], [0.65, 0.45, -0.30]]
        return np.array(rows[int((t - 1.0) // 2.5) % 4])
    if mission == "hard45c":                                        # v3 held-out (PLAN v3)
        return np.array([
            0.45 * np.sin(0.70 * t + 1.2) + 0.22 * np.sin(2.30 * t + 0.5),
            0.52 * np.sin(0.90 * t) + 0.16 * np.sin(1.85 * t + 1.3),
            0.58 * np.sin(0.60 * t + 0.4) + 0.20 * np.sin(1.45 * t + 2.2),
        ])
    if mission == "hardstep_c":
        if t < 1.5:
            return np.zeros(3)
        rows = [[0.55, 0.60, -0.50], [-0.75, -0.30, 0.65], [0.40, -0.65, -0.85], [-0.50, 0.55, 0.35]]
        return np.array(rows[int((t - 1.5) // 3.0) % 4])
    raise ValueError(mission)


def ref_quat(t: float, mission: str, duration: float) -> np.ndarray:
    if mission in HELDOUT:
        return euler_to_quat(*heldout_euler(t, mission))
    return reference_quat(t, mission, duration)


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def run(platform: str, mission: str, controller: str, output: Path, duration: float = 45.0,
        dt: float = 5e-4, beta: float = 0.5, learning_rate: float = 8e-4, k_error: float = 8.0,
        ki_factor: float = 0.05, tuner: TunerConfig | None = None, stn_cfg: STNConfig | None = None,
        log_every: int = 20, allocation: str = "clip") -> dict:
    if allocation not in ALLOCATIONS:
        raise ValueError(allocation)
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
    j_gain = inertia
    if controller in BODY_GAINS:
        R_i = np.zeros(9)
        mujoco.mju_quat2Mat(R_i, model.body_iquat[body_id])
        R_i = R_i.reshape(3, 3)
        j_gain = np.diag(R_i @ np.diag(inertia) @ R_i.T).copy()
    kq = 2.0 * j_gain * wn * wn
    kw = 2.0 * 0.95 * wn * j_gain
    ki0 = ki_factor * kq

    data.qpos[qa:qa + 3] = [0.0, 0.0, 1.0]
    data.qpos[qa + 3:qa + 7] = [1.0, 0.0, 0.0, 0.0]
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0
    mujoco.mj_forward(model, data)
    act_ids, _, B_inv, ctrl_range = _mixer(model)
    ctrl_range[:, 1] *= PLATFORM_SCALE[platform]
    model.actuator_ctrlrange[act_ids, 1] = ctrl_range[:, 1]

    pid = PIDBase(limits)
    residual = (CMGResidualAugmentor(3, limits, "online_pes", True, beta, learning_rate=learning_rate)
                if controller in RESIDUAL else None)
    st = None
    tcfg = None
    if controller in TARGET_TUNER:
        tcfg = tuner or TunerConfig()
        freeze, v2 = TARGET_TUNER[controller]
        if freeze or v2:
            tcfg = TunerConfig(**{**tcfg.__dict__, "freeze_on_sat": freeze, "v2_gating": v2})
        st = SelfTuner(tcfg)
    stn = None
    scfg = None
    if controller in STN_TUNER:
        bounded, known_sign, v2, dither_id = STN_TUNER[controller]
        scfg = STNConfig(**{**(stn_cfg or STNConfig()).__dict__, "bounded": bounded, "known_sign": known_sign,
                            "v2_gating": v2, "dither_id": dither_id})
        stn = STNSelfTuner(scfg, limits, inertia=inertia)
    idgc = IDGainCorrector(IDGCConfig(), limits, inertia) if controller in IDGC else None
    alphas, s_hats = [], []

    n_steps = int(round(duration / dt))
    qerr, sat, res_norm, mults, yhats = [], [], [], [], []
    rows = []
    step = 0
    prev_axis_sat = np.zeros(3, dtype=bool)
    u_prev = np.zeros(3)
    headroom_prev = 1.0
    z_min = float(data.qpos[qa + 2])
    diverged = False
    while data.time < duration:
        t = float(data.time)
        q_meas = quat_conj(np.asarray(data.qpos[qa + 3:qa + 7], dtype=float))
        omega = np.asarray(data.qvel[va + 3:va + 6], dtype=float).copy()
        qref = ref_quat(t, mission, duration)
        qe, eq = quat_error(qref, q_meas)

        if st is not None:
            freeze, v2 = TARGET_TUNER[controller]
            if v2:
                mp, mi, md = st.step(eq, omega, dt, headroom=headroom_prev)
            elif freeze:
                mp, mi, md = st.step(eq, omega, dt, saturated=prev_axis_sat)
            else:
                mp, mi, md = st.step(eq, omega, dt)
        elif stn is not None:
            if STN_TUNER[controller][3]:
                mp, mi, md = stn.step(eq, omega, pid.xi.copy(), u_prev, prev_axis_sat, dt, headroom=headroom_prev,
                                      t_now=t)
            elif STN_TUNER[controller][2]:
                mp, mi, md = stn.step(eq, omega, pid.xi.copy(), u_prev, prev_axis_sat, dt, headroom=headroom_prev)
            else:
                mp, mi, md = stn.step(eq, omega, pid.xi.copy(), u_prev, prev_axis_sat, dt)
        elif idgc is not None:
            mp = mi = md = idgc.step(omega, t, dt, headroom=headroom_prev)
        else:
            mp = mi = md = np.ones(3)
        tau0 = pid.command(eq, omega, kq * mp, ki0 * mi, kw * md, dt)
        cmd_sat = ~pid.last_free
        if residual is not None:
            target = np.clip(-k_error * eq, -1.0, 1.0)
            out = residual.step(tau0, dt, target)
            tau, res = out.command, out.residual
        else:
            tau, res = tau0, np.zeros(3)
        if stn is not None and scfg.dither_id:
            tau = np.clip(tau + stn.dither(t), -limits, limits)
        if idgc is not None:
            tau = np.clip(tau + idgc.dither(t), -limits, limits)

        R = np.asarray(data.xmat[body_id], dtype=float).reshape(3, 3)
        z, vz = float(data.qpos[qa + 2]), float(data.qvel[va + 2])
        tilt = max(float(R[2, 2]), 0.35)
        collective = float(np.clip(mass * (gravity + 6.0 * (1.0 - z) - 4.0 * vz) / tilt,
                                   0.0, 2.5 * mass * max(gravity, 1.0)))
        data.ctrl[:] = 0.0
        if allocation in ("tpa", "tpa_r", "apa"):
            fn = {"tpa": tpa_allocate, "tpa_r": tpa_r_allocate, "apa": apa_allocate}[allocation]
            motors, alpha, _ = fn(B_inv, collective, tau, ctrl_range[:, 0], ctrl_range[:, 1])
            alphas.append(alpha)
        else:
            motors = np.clip(B_inv @ np.r_[collective, tau], ctrl_range[:, 0], ctrl_range[:, 1])
            alpha = 1.0
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
        if allocation != "clip":
            prev_axis_sat = cmd_sat | saturated | (alpha < 1.0 - 1e-12)
        else:
            prev_axis_sat = cmd_sat | saturated
        if stn is not None and scfg.dither_id:
            s_hats.append(stn.last_s_hat.copy())
        if idgc is not None:
            s_hats.append(idgc.last_s_hat.copy())
        u_prev = np.asarray(tau, dtype=float).copy()
        span = np.maximum(ctrl_range[:, 1] - ctrl_range[:, 0], 1e-12)
        headroom_prev = float(np.clip(np.min(np.minimum(motors - ctrl_range[:, 0], ctrl_range[:, 1] - motors)
                                             / (0.5 * span)), 0.0, 1.0))
        z_min = min(z_min, float(data.qpos[qa + 2]))

        qerr.append(quat_angle(qe))
        sat.append(saturated)
        res_norm.append(float(np.linalg.norm(res)))
        mults.append(np.concatenate([mp, mi, md]))
        if stn is not None:
            yhats.append(stn.last_yhat.copy())
        if step % log_every == 0:
            row = {"t": t, "qerr": qerr[-1], "saturated": int(saturated), "z": z}
            for k, v in zip("xyz", eq):
                row[f"eq_{k}"] = float(v)
            for k, v in zip("xyz", tau0):
                row[f"tau0_{k}"] = float(v)
            for k, v in zip("xyz", res):
                row[f"res_{k}"] = float(v)
            for g, block in (("p", mp), ("i", mi), ("d", md)):
                for k, v in zip("xyz", block):
                    row[f"m{g}_{k}"] = float(v)
            if st is not None:
                row["WS_fro"] = float(np.linalg.norm(st.W))
                row["aS_mean"] = float(np.mean(st.last_activity))
            if stn is not None:
                for k, v in zip("xyz", stn.last_yhat):
                    row[f"yhat_{k}"] = float(v)
            if residual is not None:
                row["WR_fro"] = float(np.linalg.norm(residual.W))
            rows.append(row)
        step += 1

    if diverged:                       # non-finite state: charge pi rad and saturation to the rest
        qerr += [float(np.pi)] * (n_steps - len(qerr))
        sat += [True] * (n_steps - len(sat))
    output.mkdir(parents=True, exist_ok=True)
    with (output / "trace.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    qerr = np.asarray(qerr)
    mults = np.asarray(mults)
    summary = {
        "platform": platform, "mission": mission, "controller": controller,
        "duration_s": duration, "dt_s": dt, "steps": step, "diverged": diverged, "z_min_m": z_min,
        "allocation": allocation,
        "alpha_mean": float(np.mean(alphas)) if alphas else None,
        "alpha_min": float(np.min(alphas)) if alphas else None,
        "torque_scaled_fraction": float(np.mean(np.asarray(alphas) < 1.0 - 1e-12)) if alphas else None,
        "s_hat_mean": np.mean(s_hats, axis=0).tolist() if s_hats else None,
        "beta": beta, "learning_rate": learning_rate, "k_error": k_error, "ki_factor": ki_factor,
        "tuner": tcfg.__dict__ if tcfg is not None else None,
        "stn": scfg.__dict__ if scfg is not None else None,
        "gain_inertia": j_gain.tolist(),
        "idgc": idgc.cfg.__dict__ if idgc is not None else None,
        "multiplier_final": mults[-1].tolist(),
        "idgc_held_fraction": (idgc.held_steps / max(step, 1)).tolist() if idgc is not None else None,
        "qerr_mean_rad": float(qerr.mean()), "qerr_rmse_rad": float(np.sqrt(np.mean(qerr ** 2))),
        "qerr_max_rad": float(qerr.max()), "saturation_fraction": float(np.mean(sat)),
        "residual_rms_Nm": float(np.sqrt(np.mean(np.square(res_norm)))) if res_norm else None,
        "torque_limits_Nm": limits.tolist(),
        "multiplier_mean": mults.mean(axis=0).tolist(),
        "multiplier_min": mults.min(axis=0).tolist(),
        "multiplier_max": mults.max(axis=0).tolist(),
        "integral_frozen_fraction": (pid.frozen_steps / max(step, 1)).tolist(),
        "WS_final_fro": float(np.linalg.norm(st.W)) if st is not None else None,
        "WR_final_fro": float(np.linalg.norm(residual.W)) if residual is not None else None,
        "yhat_mean": np.mean(yhats, axis=0).tolist() if yhats else None,
        "yhat_negative_fraction": float(np.mean(np.asarray(yhats) < 0)) if yhats else None,
        "stn_valid_fraction": (stn.valid_steps / max(step, 1)).tolist() if stn is not None else None,
        "stn_blocked_fraction": (stn.blocked_steps / max(step, 1)).tolist() if stn is not None else None,
        "wall_s": time.perf_counter() - started,
        "hashes": {
            "run_dual.py": sha(HERE / "run_dual.py"),
            "dual_controller.py": sha(HERE / "dual_controller.py"),
            "gra_control/gate.py": sha(ACC / "src/gra_control/gate.py"),
            "gra_control/platforms/drone.py": sha(ACC / "src/gra_control/platforms/drone.py"),
            "gra_control/math3d.py": sha(ACC / "src/gra_control/math3d.py"),
            "model": sha(spec.model),
        },
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--platform", choices=tuple(PLATFORM_SCALE), required=True)
    ap.add_argument("--mission", choices=MISSIONS + HELDOUT, required=True)
    ap.add_argument("--controller", choices=CONTROLLERS, required=True)
    ap.add_argument("--duration", type=float, default=45.0)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--allocation", choices=ALLOCATIONS, default="clip")
    a = ap.parse_args()
    s = run(a.platform, a.mission, a.controller, a.output, duration=a.duration, allocation=a.allocation)
    print(json.dumps({k: s[k] for k in ("platform", "mission", "controller", "qerr_mean_rad",
                                          "saturation_fraction", "diverged", "multiplier_mean",
                                          "yhat_mean", "wall_s")}, indent=1))


if __name__ == "__main__":
    main()
