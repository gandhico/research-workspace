"""Contact detail for X2 step missions: which geoms touch, when, how many steps, penetration.

Controllers: the ACC 2027 paper baseline PD (k_i = 0) and PID (k_i = 0.05 k_q).
"""
from __future__ import annotations

import sys
from pathlib import Path

import mujoco
import numpy as np

ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ACC / "src"))
sys.path.insert(0, str(HERE))
from gra_control.math3d import quat_conj, quat_error  # noqa: E402
from gra_control.platforms.drone import SPECS, _free_joint, _mixer, torque_limits  # noqa: E402
from dual_controller import PIDBase  # noqa: E402
from run_dual import PLATFORM_SCALE, ref_quat  # noqa: E402


def name(model, i):
    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i) or f"geom{i}"


def replay(platform, mission, ki_factor, duration=45.0, dt=5e-4):
    spec = SPECS[platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    inertia = model.body_inertia[body_id].copy()
    mass, g = float(np.sum(model.body_mass)), abs(float(model.opt.gravity[2]))
    limits = torque_limits(platform, inertia, model, "model")
    wn = np.array([4.0, 4.0, 3.5]); kq = 2 * inertia * wn * wn; kw = 2 * 0.95 * wn * inertia
    data.qpos[qa:qa + 3] = [0, 0, 1]; data.qpos[qa + 3:qa + 7] = [1, 0, 0, 0]
    mujoco.mj_forward(model, data)
    act, _, B_inv, cr = _mixer(model); cr[:, 1] *= PLATFORM_SCALE[platform]; model.actuator_ctrlrange[act, 1] = cr[:, 1]
    pid = PIDBase(limits)
    events, pairs, steps_with_contact, max_pen = [], set(), 0, 0.0
    while data.time < duration:
        t = float(data.time)
        q = quat_conj(np.asarray(data.qpos[qa + 3:qa + 7])); w = np.asarray(data.qvel[va + 3:va + 6]).copy()
        _, eq = quat_error(ref_quat(t, mission, duration), q)
        if ki_factor == 0.0:
            tau = np.clip(-kq * eq - kw * w, -limits, limits)       # byte-identical canonical PD
        else:
            tau = pid.command(eq, w, kq, ki_factor * kq, kw, dt)
        R = np.asarray(data.xmat[body_id]).reshape(3, 3)
        z, vz = float(data.qpos[qa + 2]), float(data.qvel[va + 2])
        T = float(np.clip(mass * (g + 6 * (1 - z) - 4 * vz) / max(R[2, 2], 0.35), 0, 2.5 * mass * max(g, 1)))
        data.ctrl[:] = 0; data.ctrl[act] = np.clip(B_inv @ np.r_[T, tau], cr[:, 0], cr[:, 1])
        mujoco.mj_step(model, data)
        if data.ncon > 0:
            steps_with_contact += 1
            for k in range(data.ncon):
                c = data.contact[k]
                pairs.add((name(model, c.geom1), name(model, c.geom2)))
                max_pen = max(max_pen, -float(c.dist))
            if not events or t - events[-1][1] > 0.05:
                events.append([t, t, float(data.qpos[qa + 2])])
            else:
                events[-1][1] = t
    return steps_with_contact, pairs, max_pen, events


for mission in ("hardstep", "hardstep_b"):
    for ki in (0.0, 0.05):
        n, pairs, pen, ev = replay("x2", mission, ki)
        label = "PD (paper baseline)" if ki == 0 else "PID k_i=0.05"
        print(f"\nx2 {mission} {label}: {n} contact steps ({n * 0.5:.1f} ms total), max penetration {pen * 1000:.2f} mm")
        print(f"  geom pairs: {sorted(pairs)}")
        print(f"  episodes (start-end s, z at start): {[(round(a, 3), round(b, 3), round(z, 3)) for a, b, z in ev]}")
