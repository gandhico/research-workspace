"""Why the residual degrades Hardstep at rho=3, and whether a saturation-aware gate fixes it.

MECHANISM UNDER TEST. The applied command is u = sat_l(u0 + beta*l*s) with s a LAGGED image of the
teaching target (latched PES = first-order filter, pole .9952, tau .104 s, corner 9.6 rad/s).
When the baseline is NOT saturated the residual shifts the command either way. When |u0_i| = l_i the
interaction becomes one-sided:
    same sign as u0  -> u0 + beta*l*s clips back to l_i, no effect;
    opposite sign    -> the command drops to l_i(1 - beta), i.e. up to beta of the axis authority is
                        subtracted exactly when the loop needs all of it.
A step slew at rho=3 saturates the baseline and reverses sign within ~0.1 s (a 12 rad/s loop has a
0.52 s period, so the 0.104 s decoder lag is ~72 deg of phase), so the lagged residual opposes a
saturated baseline during braking. At rho=1 the loop is slower than the decoder and rarely saturates.

FIX UNDER TEST (`cmg_gate`): do not let the residual oppose a saturated axis,
    s_i <- 0  if |u0_i| >= l_i and sign(s_i) != sign(u0_i).
This keeps |u - u0| <= beta*l and exact baseline recovery at beta = 0.

PRE-REGISTERED PREDICTIONS (written before running):
  P1  Hardstep rho=3: the gate removes most of the regression (X2 settling .83 -> <= .65 s).
  P2  rho=1, all missions: |change| < 2%, since the baseline is saturated < 2% of samples there.
  P3  Smooth missions at rho=3: little change, they do not saturate.
  P4  Diagnostic: in the canonical rho=3 Hardstep run, opposing-while-saturated occupies a
      materially larger share of samples than at rho=1.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import mujoco
import numpy as np

ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
sys.path.insert(0, str(ACC / "src"))
from gra_control.gate import CMGResidualAugmentor  # noqa: E402
from gra_control.math3d import quat_angle, quat_conj, quat_error, reference_quat  # noqa: E402
from gra_control.platforms.drone import SPECS, _free_joint, _mixer  # noqa: E402

OUT = ACC / "experiments" / "baseline_restatement_2026-09-16" / "hardstep_fix"
NU = np.array([12.0, 12.0, 10.0])
WN0 = np.array([4.0, 4.0, 3.5])
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")


def run(platform: str, mission: str, controller: str, rho: float, beta: float,
        duration: float = 45.0, dt: float = 5e-4, lr: float = 8e-4, k_error: float = 8.0) -> dict:
    spec = SPECS[platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    j = model.body_inertia[body_id].copy()
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    limits = np.maximum(j * NU, 1e-6)
    wn = rho * WN0
    kq, kw = 2.0 * j * wn * wn, 2.0 * 0.95 * wn * j
    aug = (CMGResidualAugmentor(3, limits, "online_pes", True, beta, learning_rate=lr)
           if controller != "pd" else None)

    data.qpos[qa:qa + 3] = [0.0, 0.0, 1.0]
    data.qpos[qa + 3:qa + 7] = [1.0, 0.0, 0.0, 0.0]
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)
    act_ids, _, B_inv, ctrl_range = _mixer(model)
    if platform == "cf2-rotor":
        ctrl_range[:, 1] *= 1.5
        model.actuator_ctrlrange[act_ids, 1] = ctrl_range[:, 1]

    t_log, q_log, sat_log = [], [], []
    n_base_sat = np.zeros(3)
    n_oppose = np.zeros(3)
    lost = np.zeros(3)
    steps = 0
    while data.time < duration:
        t = float(data.time)
        q_meas = quat_conj(np.asarray(data.qpos[qa + 3:qa + 7], dtype=float))
        omega = np.asarray(data.qvel[va + 3:va + 6], dtype=float).copy()
        qe, eq = quat_error(reference_quat(t, mission, duration), q_meas)
        u_un = -kq * eq - kw * omega
        tau0 = np.clip(u_un, -limits, limits)
        base_sat = np.abs(tau0) >= limits * (1 - 1e-9)
        if aug is None:
            tau = tau0
        else:
            out = aug.step(tau0, dt, np.clip(-k_error * eq, -1.0, 1.0))
            res = out.residual.copy()
            opposing = base_sat & (np.sign(res) != np.sign(tau0)) & (res != 0.0)
            n_base_sat += base_sat
            n_oppose += opposing
            lost += np.where(opposing, np.abs(res), 0.0)
            if controller == "cmg_gate":
                res = np.where(opposing, 0.0, res)
            tau = np.clip(tau0 + res, -limits, limits)
        R = np.asarray(data.xmat[body_id], dtype=float).reshape(3, 3)
        z, vz = float(data.qpos[qa + 2]), float(data.qvel[va + 2])
        collective = float(np.clip(mass * (gravity + 6.0 * (1.0 - z) - 4.0 * vz)
                                   / max(float(R[2, 2]), 0.35), 0.0, 2.5 * mass * max(gravity, 1.0)))
        data.ctrl[:] = 0.0
        data.xfrc_applied[:] = 0.0
        motors = np.clip(B_inv @ np.r_[collective, tau], ctrl_range[:, 0], ctrl_range[:, 1])
        data.ctrl[act_ids] = motors
        sat_log.append(bool(np.any(np.isclose(motors, ctrl_range[:, 1], atol=1e-7)) or
                            np.any(np.isclose(motors, ctrl_range[:, 0], atol=1e-7))))
        mujoco.mj_step(model, data)
        t_log.append(t)
        q_log.append(quat_angle(qe))
        steps += 1

    t_arr, q_arr = np.array(t_log), np.array(q_log)
    ts = []
    if mission == "hardstep":
        for k in range(22):
            t0 = 1.0 + 2.0 * k
            if t0 + 2.0 > t_arr[-1]:
                break
            m = (t_arr >= t0) & (t_arr < t0 + 2.0)
            tt, qq = t_arr[m] - t0, np.degrees(q_arr[m])
            if qq.size == 0 or qq[0] < 5.0:
                continue
            below = np.where(qq < 5.0)[0]
            ts.append(tt[below[0]] if below.size else 2.0)
    settled = None
    if mission == "hardstep":
        phase = (t_arr - 1.0) % 2.0
        late = (t_arr > 1.0) & (phase > 1.5)
        settled = float(np.degrees(q_arr[late].mean()))
    s = {"platform": platform, "mission": mission, "controller": controller, "rho": rho, "beta": beta,
         "qerr_mean_rad": float(q_arr.mean()), "qerr_mean_deg": float(np.degrees(q_arr.mean())),
         "t_settle_5deg_s": float(np.mean(ts)) if ts else None, "settled_deg": settled,
         "rotor_sat_fraction": float(np.mean(sat_log)),
         "baseline_sat_fraction": (n_base_sat / steps).tolist(),
         "opposing_fraction": (n_oppose / steps).tolist(),
         "opposing_share_of_sat": (n_oppose / np.maximum(n_base_sat, 1)).tolist(),
         "mean_torque_removed_frac_of_limit": (lost / steps / limits).tolist()}
    d = OUT / f"{platform}_{mission}_{controller}_rho{rho:g}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    return s


BETA = {"x2": 0.5, "cf2-rotor": 0.5}          # canonical Table II authority on both platforms
CASES = [(p, m, c, r, BETA[p]) for p in ("x2", "cf2-rotor") for m in MISSIONS
         for c in ("pd", "cmg", "cmg_gate") for r in (1.0, 3.0)]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    print(f"{len(CASES)} runs", flush=True)
    res = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(run, *c) for c in CASES]):
            s = f.result()
            res.append(s)
            ts = f"{s['t_settle_5deg_s']:.3f}" if s["t_settle_5deg_s"] else "   -- "
            print(f"{s['platform']:10s} {s['mission']:9s} {s['controller']:8s} rho={s['rho']:g}: "
                  f"{s['qerr_mean_deg']:7.3f} deg  t_settle {ts}  rotor_sat "
                  f"{s['rotor_sat_fraction']:.3f}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "all.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
