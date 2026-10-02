"""Does the vehicle actually touch the ground on step missions? Count MuJoCo contacts.

Replays the canonical PID (identical to ACC 2027 PID(0.05) and to run_dual.py 'pid')
with contact logging, and reports min body height, the first contact time, the
fraction of steps with any contact, and the lowest geom point above the floor.
Also reads the ACC 2027 matched-campaign classical and CMG-PES traces (z column) for X2/CF2 Hardstep.
"""
from __future__ import annotations

import csv
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


def replay(platform, mission, duration=45.0, dt=5e-4):
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
    zmin, first_contact, contact_steps, steps, lowest = 9.0, None, 0, 0, 9.0
    while data.time < duration:
        t = float(data.time)
        q = quat_conj(np.asarray(data.qpos[qa + 3:qa + 7])); w = np.asarray(data.qvel[va + 3:va + 6]).copy()
        _, eq = quat_error(ref_quat(t, mission, duration), q)
        tau = pid.command(eq, w, kq, 0.05 * kq, kw, dt)
        R = np.asarray(data.xmat[body_id]).reshape(3, 3)
        z, vz = float(data.qpos[qa + 2]), float(data.qvel[va + 2])
        T = float(np.clip(mass * (g + 6 * (1 - z) - 4 * vz) / max(R[2, 2], 0.35), 0, 2.5 * mass * max(g, 1)))
        data.ctrl[:] = 0; data.ctrl[act] = np.clip(B_inv @ np.r_[T, tau], cr[:, 0], cr[:, 1])
        mujoco.mj_step(model, data)
        zmin = min(zmin, float(data.qpos[qa + 2]))
        if data.ncon > 0:
            contact_steps += 1
            if first_contact is None:
                first_contact = float(data.time)
        # lowest point of any geom belonging to the vehicle (AABB of geom centre minus bounding radius)
        vgeoms = [i for i in range(model.ngeom) if model.geom_bodyid[i] != 0]
        lowest = min(lowest, min(float(data.geom_xpos[i, 2] - model.geom_rbound[i]) for i in vgeoms))
        steps += 1
    return zmin, first_contact, contact_steps / steps, lowest


for platform in ("x2", "cf2-rotor"):
    for mission in ("hardstep", "hardstep_b"):
        zmin, fc, frac, low = replay(platform, mission)
        print(f"{platform:9s} {mission:10s} PID: z_min={zmin:.3f} m, lowest geom bound={low:.3f} m, "
              f"first contact={'none' if fc is None else f'{fc:.2f} s'}, contact fraction={frac:.4f}")

for platform in ("x2", "cf2-rotor"):
    for ctrl in ("classical", "nengo-nef-pes"):
        p = ACC / "experiments/nengo_nef_replication_2026-08-29/results/neuron_family_matched_45s" / platform / "hardstep" / ctrl / "trace.csv"
        with p.open(encoding="utf-8") as f:
            r = csv.DictReader(f)
            zs = [float(row["z"]) for row in r] if "z" in (r.fieldnames or []) else []
        print(f"ACC 2027 matched trace {platform}/hardstep/{ctrl}: "
              f"{'no z column' if not zs else f'z_min={min(zs):.3f} m'}")
