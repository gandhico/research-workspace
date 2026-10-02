"""6-DOF pilot (docs/PLAN.md: 6-DOF pilot declaration + addendum). Exploratory.

ACC 2027 tuned cascade (position PD + flatness feedforward -> thrust vector -> q_des -> quaternion PD with
omega_des feedforward -> clipped rotor allocation). Only the inner attitude loop changes:

  cas          classical, expression-identical to run_6dof_cascade_ff.run (gate G8)
  cas_res      + 3-channel CMG-PES attitude residual (beta, lr from FF6 selection)
  cas_dual_v2  + gated v2 target-scheduled tuner on (k_q, k_w) + residual
  cas_idgc_v4  + v4 gain correction, quadrature lock-in (predicted closed-loop biased at these bandwidths)
  cas_idgc_kc  + gain correction, known-controller complex lock-in: J = (w Im(1/H) + k)/w^2

ACC helpers are imported read-only; nothing in the ACC repository is modified.
Run:  python pilot_6dof.py [--workers 4] [--compile-only]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import mujoco
import numpy as np

ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
SIX = ACC / "experiments" / "six_dof_expansion_2026-08-31"
HERE = Path(__file__).resolve().parent
P5 = HERE.parents[1]
QUAT = P5 / "experiments" / "quat_dual_v0"
OUT = P5 / "results" / "six_dof_pilot_2026-09-12"
for pth in (ACC / "src", SIX, QUAT):
    sys.path.insert(0, str(pth))

from gra_control.gate import CMGResidualAugmentor  # noqa: E402
from gra_control.math3d import quat_angle, quat_conj, quat_error  # noqa: E402
from gra_control.platforms.drone import SPECS, _free_joint, _mixer, torque_limits  # noqa: E402
from run_6dof_cascade_ff import MIN_THRUST_FRACTION, position_rates, thrust_vector_to_attitude  # noqa: E402
from run_6dof_wrench import MASS_FORCE_LIMIT_SCALE, position_reference  # noqa: E402
from dual_controller import IDGainCorrector, IDGCConfig, SelfTuner, TunerConfig  # noqa: E402

TUNED = {  # FF6_FINDINGS_2026-09-10 selections
    "x2": dict(wn_att=(20.0, 20.0, 17.5), wn_pos=(2.0, 2.0, 2.4), beta=0.05, lr=8e-4,
               acc_dir=SIX / "results/ff6_2026-09-10/x2_tune/a20_20_17.5_p2_2_2.4"),
    "cf2-rotor": dict(wn_att=(24.0, 24.0, 20.4), wn_pos=(2.25, 2.25, 2.7), beta=0.008, lr=2e-4,
                      acc_dir=SIX / "results/ff6_2026-09-10/cf2_tune/a24_24_20.4_p2.25_2.25_2.7"),
}
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("hover3d", "waypoint_step", "circle_xy", "full6_stress")
CONTROLLERS = ("cas", "cas_res", "cas_dual_v2", "cas_idgc_v4", "cas_idgc_kc")
RESIDUAL = {"cas_res", "cas_dual_v2"}


class KnownControllerIDGC(IDGainCorrector):
    """Indirect closed-loop identification: complex lock-in response H(jw) and the known PD gains."""

    def __init__(self, cfg, limits, inertia):
        super().__init__(cfg, limits, inertia)
        self.zs = np.zeros(3)
        self.last_kw_check = np.zeros(3)

    def step(self, omega, t, dt, headroom=1.0, kq=None, kw=None):
        c = self.cfg
        self.zs += (dt / c.tau_demod) * (omega * np.sin(self.w * t) - self.zs)
        self.z += (dt / c.tau_demod) * (omega * np.cos(self.w * t) - self.z)
        H = 2.0 * (self.zs + 1j * self.z) / (c.dither_amp * self.limits)
        inv = np.divide(1.0, H, out=np.zeros(3, dtype=complex), where=np.abs(H) > 1e-12)
        J_hat = (self.w * inv.imag + 0.5 * self.m * kq) / self.w ** 2
        s_hat = np.divide(self.inertia, J_hat, out=np.zeros(3), where=J_hat > 0.0)
        self.last_s_hat = s_hat
        self.last_kw_check = inv.real / (self.m * kw)
        if t >= c.warmup_s:
            ok = s_hat > 0.0
            target = np.clip(np.divide(1.0, s_hat, out=np.ones(3), where=ok), c.m_lo, c.m_hi)
            dm = np.where(ok, (dt / c.tau_id) * (target - self.m), 0.0)
            dm = np.where(dm > 0.0, float(headroom) * dm, dm)
            self.m = np.clip(self.m + dm, c.m_lo, c.m_hi)
            self.held_steps += (~ok).astype(int)
        return self.m.copy()


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def run(platform: str, mission: str, controller: str, output: Path, duration: float = 15.0, dt: float = 5e-4,
        k_error_att: float = 8.0) -> dict:
    started = time.perf_counter()
    cfg = TUNED[platform]
    spec = SPECS[platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    inertia = model.body_inertia[body_id].copy()
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    act_ids, _, B_inv, ctrl_range = _mixer(model)

    wn = np.asarray(cfg["wn_att"], dtype=float)
    kq = 2.0*inertia*wn*wn
    kw = 2.0*0.95*wn*inertia
    tau_limits = 1.0*torque_limits(platform, inertia, model, "model")
    force_limits = 1.0*np.array([MASS_FORCE_LIMIT_SCALE*mass*gravity]*2+[1.8*mass*gravity])
    wn_pos = np.asarray(cfg["wn_pos"], dtype=float)
    kp_pos = mass*wn_pos*wn_pos
    kd_pos = mass*2.0*0.75*wn_pos
    ki_pos = np.zeros(3)
    ki_att = np.zeros(3)
    min_thrust = MIN_THRUST_FRACTION*mass*gravity
    pos_integral_limit = np.divide(0.3*force_limits, ki_pos, out=np.full(3, np.inf), where=ki_pos > 1e-12)
    att_integral_limit = np.divide(0.3*tau_limits, ki_att, out=np.full(3, np.inf), where=ki_att > 1e-12)

    residual = (CMGResidualAugmentor(3, tau_limits, "online_pes", True, cfg["beta"], learning_rate=cfg["lr"])
                if controller in RESIDUAL else None)
    tuner = SelfTuner(TunerConfig(v2_gating=True)) if controller == "cas_dual_v2" else None
    idgc = None
    if controller == "cas_idgc_v4":
        idgc = IDGainCorrector(IDGCConfig(), tau_limits, inertia)
    elif controller == "cas_idgc_kc":
        idgc = KnownControllerIDGC(IDGCConfig(), tau_limits, inertia)

    data.qpos[qa:qa+3] = position_reference(0.0, mission, duration)
    data.qpos[qa+3:qa+7] = quat_conj(np.array([1.0, 0.0, 0.0, 0.0]))
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)

    pos_errs, qerrs, sats, res_norms, mults, s_hats, kw_checks = [], [], [], [], [], [], []
    trace = []
    q_des_prev = np.array([1.0, 0.0, 0.0, 0.0])
    pos_integral = np.zeros(3)
    att_integral = np.zeros(3)
    headroom_prev = 1.0
    z_min = float(data.qpos[qa+2])
    step = 0
    while data.time < duration:
        t = float(data.time)
        p = np.asarray(data.qpos[qa:qa+3], dtype=float)
        v = np.asarray(data.qvel[va:va+3], dtype=float)
        q_meas = quat_conj(np.asarray(data.qpos[qa+3:qa+7], dtype=float))
        omega = np.asarray(data.qvel[va+3:va+6], dtype=float)

        p_ref = position_reference(t, mission, duration)
        pos_integral = np.clip(pos_integral+(p-p_ref)*dt, -pos_integral_limit, pos_integral_limit)
        v_ref, a_ref = position_rates(t, mission, duration)
        F0 = np.clip(mass*(gravity*np.array([0, 0, 1])+a_ref)-kp_pos*(p-p_ref)
                     -kd_pos*(v-v_ref)-ki_pos*pos_integral,
                     -force_limits, force_limits)
        F_cmd = F0
        tau_att_residual = np.zeros(3)

        yaw_des = 0.0
        q_des, thrust_mag = thrust_vector_to_attitude(F_cmd, yaw_des, min_thrust)
        q_des = quat_conj(q_des)
        _, dq_vec = quat_error(q_des, q_des_prev)
        omega_des = 2.0*dq_vec/dt
        q_des_prev = q_des
        qe, eq = quat_error(q_des, q_meas)
        att_integral = np.clip(att_integral+eq*dt, -att_integral_limit, att_integral_limit)

        mp = mi = md = np.ones(3)
        if tuner is not None:
            mp, mi, md = tuner.step(eq, omega-omega_des, dt, headroom=headroom_prev)
        elif controller == "cas_idgc_kc":
            mp = mi = md = idgc.step(omega, t, dt, headroom=headroom_prev, kq=kq, kw=kw)
        elif idgc is not None:
            mp = mi = md = idgc.step(omega, t, dt, headroom=headroom_prev)

        if controller == "cas":
            tau0 = np.clip(-kq*eq-kw*(omega-omega_des)-ki_att*att_integral, -tau_limits, tau_limits)
            tau = np.clip(tau0+tau_att_residual, -tau_limits, tau_limits)
            res = tau_att_residual
        else:
            tau0 = np.clip(-kq*mp*eq-kw*md*(omega-omega_des)-ki_att*mi*att_integral, -tau_limits, tau_limits)
            if residual is not None:
                out = residual.step(tau0, dt, np.clip(-k_error_att*eq, -1.0, 1.0))
                tau, res = out.command, out.residual
            else:
                tau, res = tau0, np.zeros(3)
            if idgc is not None:
                tau = np.clip(tau+idgc.dither(t), -tau_limits, tau_limits)

        motors = B_inv@np.r_[thrust_mag, tau]
        motors = np.clip(motors, ctrl_range[:, 0], ctrl_range[:, 1])
        data.ctrl[:] = 0.0
        data.ctrl[act_ids] = motors
        data.xfrc_applied[:] = 0.0
        mujoco.mj_step(model, data)

        saturated = bool(np.any(np.isclose(motors, ctrl_range[:, 0], atol=1e-7)) or
                         np.any(np.isclose(motors, ctrl_range[:, 1], atol=1e-7)))
        span = np.maximum(ctrl_range[:, 1]-ctrl_range[:, 0], 1e-12)
        headroom_prev = float(np.clip(np.min(np.minimum(motors-ctrl_range[:, 0], ctrl_range[:, 1]-motors)
                                             / (0.5*span)), 0.0, 1.0))
        z_min = min(z_min, float(data.qpos[qa+2]))
        pos_errs.append(float(np.linalg.norm(p-p_ref)))
        qerrs.append(quat_angle(qe))
        sats.append(saturated)
        res_norms.append(float(np.linalg.norm(res)))
        mults.append(np.concatenate([mp, md]))
        if idgc is not None:
            s_hats.append(idgc.last_s_hat.copy())
            if controller == "cas_idgc_kc":
                kw_checks.append(idgc.last_kw_check.copy())
        if step % 20 == 0:
            row = {"t": t, "pos_err": pos_errs[-1], "qerr": qerrs[-1], "x": p[0], "y": p[1], "z": p[2],
                   "x_ref": p_ref[0], "y_ref": p_ref[1], "z_ref": p_ref[2], "saturated": int(saturated),
                   "headroom": headroom_prev}
            for k_, val in zip("xyz", tau):
                row[f"tau_{k_}"] = float(val)
            for k_, val in zip("xyz", res):
                row[f"res_{k_}"] = float(val)
            for k_, val in zip("xyz", mp):
                row[f"mp_{k_}"] = float(val)
            for k_, val in zip("xyz", md):
                row[f"md_{k_}"] = float(val)
            if idgc is not None:
                for k_, val in zip("xyz", idgc.last_s_hat):
                    row[f"s_hat_{k_}"] = float(val)
            trace.append(row)
        step += 1

    output.mkdir(parents=True, exist_ok=True)
    with (output/"trace.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(trace[0]))
        w.writeheader()
        w.writerows(trace)
    pos_err = np.array(pos_errs)
    qerr = np.array(qerrs)
    mults = np.asarray(mults)
    tail = int(round(5.0/dt))
    summary = {
        "platform": platform, "mission": mission, "controller": controller, "duration": duration, "dt": dt,
        "wn_att": list(cfg["wn_att"]), "wn_pos": list(cfg["wn_pos"]),
        "beta": cfg["beta"] if residual is not None else None, "learning_rate": cfg["lr"] if residual is not None else None,
        "pos_err_mean_m": float(pos_err.mean()), "pos_err_max_m": float(pos_err.max()),
        "qerr_mean_rad": float(qerr.mean()), "qerr_max_rad": float(qerr.max()),
        "z_min_m": z_min, "saturation_fraction": float(np.mean(sats)),
        "residual_rms_Nm": float(np.sqrt(np.mean(np.square(res_norms)))),
        "torque_limits_Nm": tau_limits.tolist(),
        "mp_final": mults[-1, 0:3].tolist(), "md_final": mults[-1, 3:6].tolist(),
        "mp_min": mults[:, 0:3].min(axis=0).tolist(), "mp_max": mults[:, 0:3].max(axis=0).tolist(),
        "s_hat_last5s_mean": np.mean(s_hats[-tail:], axis=0).tolist() if s_hats else None,
        "kw_check_last5s_mean": np.mean(kw_checks[-tail:], axis=0).tolist() if kw_checks else None,
        "idgc": idgc.cfg.__dict__ if idgc is not None else None,
        "wall_s": time.perf_counter()-started,
        "hashes": {"pilot_6dof.py": sha(HERE/"pilot_6dof.py"), "dual_controller.py": sha(QUAT/"dual_controller.py"),
                   "run_6dof_cascade_ff.py": sha(SIX/"run_6dof_cascade_ff.py"),
                   "run_6dof_wrench.py": sha(SIX/"run_6dof_wrench.py"),
                   "gra_control/gate.py": sha(ACC/"src/gra_control/gate.py"),
                   "gra_control/math3d.py": sha(ACC/"src/gra_control/math3d.py"),
                   "gra_control/platforms/drone.py": sha(ACC/"src/gra_control/platforms/drone.py"),
                   "model": sha(spec.model)},
    }
    (output/"summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def job(args):
    p, m, c = args
    s = run(p, m, c, OUT/p/m/c)
    return p, m, c, s["pos_err_mean_m"], s["qerr_mean_rad"], s["z_min_m"], s["wall_s"]


def load(d: Path) -> dict:
    return json.loads((d/"summary.json").read_text(encoding="utf-8"))


def compile_report():
    S = {(p, m, c): load(OUT/p/m/c) for p in PLATFORMS for m in MISSIONS for c in CONTROLLERS}
    L = ["# 6-DOF pilot: dual / gain-correcting inner attitude loops on the ACC 2027 tuned cascade", "",
         "Generated by `experiments/six_dof_pilot/pilot_6dof.py`. Exploratory (PLAN 6-DOF pilot declaration + addendum).",
         "15 s, dt 0.5 ms, noise-free, deterministic, clipped allocation, position feedforward on.",
         "Cells: mean position error [mm] / mean attitude error [deg] (ratio of position error to `cas`).", "", "## Gate G8", ""]
    ok = True
    for p in PLATFORMS:
        for m in MISSIONS:
            a = load(TUNED[p]["acc_dir"]/m)
            s = S[(p, m, "cas")]
            same = a["pos_err_mean_m"] == s["pos_err_mean_m"] and a["qerr_mean_rad"] == s["qerr_mean_rad"]
            ok &= same
            L.append(f"- {p}/{m}: ACC {a['pos_err_mean_m']:.10f} m vs P5 {s['pos_err_mean_m']:.10f} m -> "
                     f"{'bit-identical' if same else 'DIFFERENT'}")
    L.append(f"\n**G8: {'PASS' if ok else 'FAIL'}**\n")
    for p in PLATFORMS:
        L += [f"## {p}", "", "| controller | " + " | ".join(MISSIONS) + " | geo pos ratio (moving 3) | z_min min [m] | sat max |",
              "|---|" + "---|" * (len(MISSIONS) + 3)]
        for c in CONTROLLERS:
            cells = []
            for m in MISSIONS:
                s, b = S[(p, m, c)], S[(p, m, "cas")]
                r = f"{s['pos_err_mean_m'] / b['pos_err_mean_m']:.2f}" if b["pos_err_mean_m"] > 0 else "n/a"
                cells.append(f"{1e3*s['pos_err_mean_m']:.3f} / {math.degrees(s['qerr_mean_rad']):.3f} ({r})")
            g = math.exp(sum(math.log(S[(p, m, c)]["pos_err_mean_m"] / S[(p, m, "cas")]["pos_err_mean_m"])
                             for m in MISSIONS[1:]) / 3)
            zmin = min(S[(p, m, c)]["z_min_m"] for m in MISSIONS)
            smax = max(S[(p, m, c)]["saturation_fraction"] for m in MISSIONS)
            L.append(f"| {c} | " + " | ".join(cells) + f" | {g:.3f} | {zmin:.3f} | {smax:.3f} |")
        L.append("")
    L += ["## Gain correction: identified ratio and final multipliers", "",
          "| platform | mission | controller | s_hat last 5 s (x,y,z) | m final (x,y,z) | kw check Re(1/H)/(m k_w) |",
          "|---|---|---|---|---|---|"]
    for p in PLATFORMS:
        for m in MISSIONS:
            for c in ("cas_idgc_v4", "cas_idgc_kc"):
                s = S[(p, m, c)]
                kc = ", ".join(f"{v:.2f}" for v in s["kw_check_last5s_mean"]) if s["kw_check_last5s_mean"] else "-"
                L.append(f"| {p} | {m} | {c} | {', '.join(f'{v:.2f}' for v in s['s_hat_last5s_mean'])} | "
                         f"{', '.join(f'{v:.2f}' for v in s['mp_final'])} | {kc} |")
    L.append("\nModel targets m = J/j_tune: X2 (0.60, 0.70, 2.38); CF2 (1, 1, 1). "
             "Predicted quadrature-only targets: X2 (1.42, 1.11, 2.41); CF2 (1.61, 1.37, 1.18).")
    L += ["", "## Dual v2 multipliers (cas_dual_v2)", "", "| platform | mission | m_p final | m_d final | m_p range |", "|---|---|---|---|---|"]
    for p in PLATFORMS:
        for m in MISSIONS:
            s = S[(p, m, "cas_dual_v2")]
            L.append(f"| {p} | {m} | {', '.join(f'{v:.2f}' for v in s['mp_final'])} | "
                     f"{', '.join(f'{v:.2f}' for v in s['md_final'])} | "
                     f"{', '.join(f'{a:.2f}-{b:.2f}' for a, b in zip(s['mp_min'], s['mp_max']))} |")
    rows = [{"platform": p, "mission": m, "controller": c, **{k: S[(p, m, c)][k] for k in
            ("pos_err_mean_m", "pos_err_max_m", "qerr_mean_rad", "z_min_m", "saturation_fraction", "residual_rms_Nm")}}
            for p in PLATFORMS for m in MISSIONS for c in CONTROLLERS]
    with (OUT/"summary_6dof_pilot.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (OUT/"REPORT_6dof_pilot.md").write_text("\n".join(L)+"\n", encoding="utf-8")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--compile-only", action="store_true")
    a = ap.parse_args()
    if not a.compile_only:
        todo = [(p, m, c) for p in PLATFORMS for m in MISSIONS for c in CONTROLLERS
                if not (OUT/p/m/c/"summary.json").exists()]
        todo.sort(key=lambda x: x[2] != "cas")
        print(f"{len(todo)} jobs, workers={a.workers}", flush=True)
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            for f in as_completed([ex.submit(job, t) for t in todo]):
                p, m, c, pe, qe, zm, wall = f.result()
                print(f"done {p}/{m}/{c}: pos {1e3*pe:.3f} mm, att {math.degrees(qe):.3f} deg, z_min {zm:.2f} ({wall:.0f} s)",
                      flush=True)
    compile_report()


if __name__ == "__main__":
    main()
