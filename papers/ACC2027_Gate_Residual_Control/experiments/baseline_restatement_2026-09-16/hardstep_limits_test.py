"""Does the X2 Hardstep behaviour change when the torque limits use the true body inertia?

DEFECT UNDER TEST. `torque_limits(...)` builds l = inertia * (12,12,10) rad/s^2 from
`model.body_inertia`, i.e. the PRINCIPAL moments in MuJoCo's reported order (j_tune), not the
body-frame diagonal diag(J). On X2 those differ by (1.66, 1.44, 0.42), so the yaw channel is
allowed only 0.254 N m = 4.2 rad/s^2 of the intended 10 rad/s^2, while roll/pitch get 19.9/17.2.
CF2's principal axes are its body axes, so j_tune = diag(J) and CF2 is an untouched control.

PRE-REGISTERED PREDICTIONS (written before any run of this script):
  P1  With l from diag(J), X2 yaw authority rises 2.4x and the PD Hardstep mean error falls.
  P2  The X2 rho=3 CMG regression (+17.0% mean, +40.2% settling time, measured on the canonical
      limits) shrinks or disappears, because it is driven by saturation of the starved yaw axis.
  P3  CF2 is numerically unchanged, since j_tune == diag(J) there.
  Gate  (gains j_tune, limits j_tune, rho=1, PD) must reproduce the canonical Table II Hardstep
        mean error: X2 .454528 rad, CF2 .426182 rad.

The attitude loop below is copied from gra_control.platforms.drone.run_drone (canonical, unmodified
in the repository); only the gain/limit source and the bandwidth scale are parameterised.
"""
from __future__ import annotations

import argparse
import csv
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

OUT = ACC / "experiments" / "baseline_restatement_2026-09-16" / "hardstep_limits"
NU = np.array([12.0, 12.0, 10.0])
WN0 = np.array([4.0, 4.0, 3.5])


def inertias(model, body_id):
    j_tune = model.body_inertia[body_id].copy()
    R = np.zeros(9)
    mujoco.mju_quat2Mat(R, model.body_iquat[body_id])
    R = R.reshape(3, 3)
    return j_tune, np.diag(R @ np.diag(j_tune) @ R.T).copy()


def run(platform: str, controller: str, gains_src: str, limits_src: str, rho: float,
        duration: float = 45.0, dt: float = 5e-4, beta: float = 0.5, lr: float = 8e-4,
        k_error: float = 8.0) -> dict:
    spec = SPECS[platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    j_tune, j_body = inertias(model, body_id)
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    j_gain = j_tune if gains_src == "j_tune" else j_body
    j_lim = j_tune if limits_src == "j_tune" else j_body
    limits = np.maximum(j_lim * NU, 1e-6)
    wn = rho * WN0
    kq = 2.0 * j_gain * wn * wn
    kw = 2.0 * 0.95 * wn * j_gain

    augmentor = (CMGResidualAugmentor(3, limits, "online_pes", True, beta, learning_rate=lr)
                 if controller == "cmg" else None)
    data.qpos[qa:qa + 3] = [0.0, 0.0, 1.0]
    data.qpos[qa + 3:qa + 7] = [1.0, 0.0, 0.0, 0.0]
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)
    act_ids, _, B_inv, ctrl_range = _mixer(model)
    if platform == "cf2-rotor":                 # canonical CF2 uses the 1.5x rotor-authority design
        ctrl_range[:, 1] *= 1.5
        model.actuator_ctrlrange[act_ids, 1] = ctrl_range[:, 1]

    rows = []
    while data.time < duration:
        t = float(data.time)
        q_meas = quat_conj(np.asarray(data.qpos[qa + 3:qa + 7], dtype=float))
        omega = np.asarray(data.qvel[va + 3:va + 6], dtype=float).copy()
        qref = reference_quat(t, "hardstep", duration)
        qe, eq = quat_error(qref, q_meas)
        tau0 = np.clip(-kq * eq - kw * omega, -limits, limits)
        if augmentor is None:
            tau = tau0
        else:
            out = augmentor.step(tau0, dt, np.clip(-k_error * eq, -1.0, 1.0))
            tau = out.command
        R = np.asarray(data.xmat[body_id], dtype=float).reshape(3, 3)
        z, vz = float(data.qpos[qa + 2]), float(data.qvel[va + 2])
        tilt = max(float(R[2, 2]), 0.35)
        collective = float(np.clip(mass * (gravity + 6.0 * (1.0 - z) - 4.0 * vz) / tilt,
                                   0.0, 2.5 * mass * max(gravity, 1.0)))
        data.ctrl[:] = 0.0
        data.xfrc_applied[:] = 0.0
        motors = np.clip(B_inv @ np.r_[collective, tau], ctrl_range[:, 0], ctrl_range[:, 1])
        data.ctrl[act_ids] = motors
        saturated = bool(np.any(np.isclose(motors, ctrl_range[:, 0], atol=1e-7)) or
                         np.any(np.isclose(motors, ctrl_range[:, 1], atol=1e-7)))
        mujoco.mj_step(model, data)
        rows.append({"t": t, "qerr": quat_angle(qe), "z": z, "saturated": int(saturated),
                     "tau_x": tau[0], "tau_y": tau[1], "tau_z": tau[2]})

    t = np.array([r["t"] for r in rows])
    q = np.array([r["qerr"] for r in rows])
    tau = np.abs(np.array([[r["tau_x"], r["tau_y"], r["tau_z"]] for r in rows]))
    ts = []
    for k in range(22):
        t0 = 1.0 + 2.0 * k
        if t0 + 2.0 > t[-1]:
            break
        m = (t >= t0) & (t < t0 + 2.0)
        tt, qq = t[m] - t0, np.degrees(q[m])
        if qq.size == 0 or qq[0] < 5.0:
            continue
        below = np.where(qq < 5.0)[0]
        ts.append(tt[below[0]] if below.size else 2.0)
    phase = (t - 1.0) % 2.0
    late = (t > 1.0) & (phase > 1.5)
    tag = f"{platform}_{controller}_g-{gains_src}_l-{limits_src}_rho{rho:g}"
    d = OUT / tag
    d.mkdir(parents=True, exist_ok=True)
    with (d / "trace.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    s = {"platform": platform, "controller": controller, "gains": gains_src, "limits": limits_src,
         "rho": rho, "torque_limits_Nm": limits.tolist(),
         "accel_envelope_rad_s2": (limits / j_body).tolist(),
         "qerr_mean_rad": float(q.mean()), "qerr_mean_deg": float(np.degrees(q.mean())),
         "settled_deg": float(np.degrees(q[late].mean())), "t_settle_5deg_s": float(np.mean(ts)),
         "saturation_fraction": float(np.mean([r["saturated"] for r in rows])),
         "z_min_m": float(min(r["z"] for r in rows)),
         "tau_at_limit_frac": (tau >= 0.999 * limits).mean(axis=0).tolist()}
    (d / "summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    return s


def job(a):
    return run(*a)


CASES = ([("x2", c, g, l, r) for c in ("pd", "cmg") for g, l in
          (("j_tune", "j_tune"), ("j_tune", "diagJ"), ("diagJ", "diagJ")) for r in (1.0, 3.0)]
         + [("cf2-rotor", c, "j_tune", "j_tune", r) for c in ("pd", "cmg") for r in (1.0, 3.0)])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    print(f"{len(CASES)} runs", flush=True)
    res = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(job, c) for c in CASES]):
            s = f.result()
            res.append(s)
            print(f"done {s['platform']:10s} {s['controller']:4s} g={s['gains']:6s} l={s['limits']:6s} "
                  f"rho={s['rho']:g}: mean {s['qerr_mean_deg']:6.2f} deg, t_settle "
                  f"{s['t_settle_5deg_s']:.3f} s, sat {s['saturation_fraction']:.3f}", flush=True)
    (OUT / "all_summaries.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
