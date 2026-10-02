"""Conductance-vs-gate residual comparison on the MuJoCo quad (Crazyflie 2, body-torque).

Self-contained: reuses this project's quad infrastructure + neuron models, but computes the
residual readout inline so NOTHING in the existing controllers/neurons is modified. Tests whether
reading the effective conductance G_eff=(G_base+beta|I|)*r^2 (where beta+demand appear directly)
beats the gate-state readout r — and whether Adaptive then beats plain HyperLIF (it can't in the
gate readout, by construction). Headless (no viewer/dashboard).

Run with the python that has mujoco:
    <global-python> v2_clean/runners/compare_conductance_residual.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT / "src"))

import mujoco  # noqa: E402

from quad.models import load_drone  # noqa: E402
from quad.reference import reference_quat  # noqa: E402
from quad.math_utils import quat_angle_error, quat_conj, quat_mul, quat_normalize  # noqa: E402
from quad.bridge import get_state, compute_hover_force, apply_body_torque  # noqa: E402
from controllers.neuron_dynamics import make_direct_neuron  # noqa: E402

QUAD = "bitcraze_crazyflie_2"
MISSION = "hard45"
SIM_TIME = 20.0
DT = 5e-4
Z_REF = 1.0
BLEND = 0.50
GATE_GAIN = 1.0e5      # gate readout: binary (the team's best setting)
COND_SCALE = 120.0     # conductance normalization (~ G_base)
HYBRID_W = 0.5
BIAS, IGAIN = 0.75, 1.25


def _conductance(neuron, r, currents):
    if hasattr(neuron, "reset_gain"):                       # HyperLIF
        return neuron.reset_gain * r**2
    return (neuron.base_gain + neuron.gain_scaling * np.abs(currents)) * r**2  # Adaptive


def run_config(neuron_name, readout):
    params = load_drone(QUAD)
    model = mujoco.MjModel.from_xml_path(str(params.xml_path))
    data = mujoco.MjData(model)
    model.opt.timestep = DT
    pa = params.qpos_adr
    data.qpos[pa:pa + 3] = [0.0, 0.0, Z_REF]
    data.qpos[pa + 3:pa + 7] = [1.0, 0.0, 0.0, 0.0]
    data.qvel[:] = 0.0
    if model.nu > 0:
        data.ctrl[:] = params.hover_cmd_vector()
    mujoco.mj_forward(model, data)

    neuron = None if readout == "pd" else make_direct_neuron(neuron_name, n=6, activity_mode="gate", scale="control")
    kq, kw, tau_limit = params.kq, params.kw, params.tau_limit
    qerrs, acts = [], []
    while data.time < SIM_TIME:
        t = float(data.time)
        data.xfrc_applied[:] = 0.0
        state = get_state(model, data, params)
        q_ref = reference_quat(t, MISSION, SIM_TIME)

        q_err = quat_normalize(quat_mul(quat_normalize(q_ref), quat_conj(quat_normalize(state.q))))
        e_q = q_err[1:].copy()
        if q_err[0] < 0.0:
            e_q = -e_q
        tau_pd = np.clip(-kq * e_q - kw * np.asarray(state.omega), -tau_limit, tau_limit)

        if readout == "pd":
            tau = tau_pd
            acts.append(0.0)
        else:
            tn = np.clip(np.divide(tau_pd, tau_limit, out=np.zeros_like(tau_pd), where=np.abs(tau_limit) > 1e-12), -1, 1)
            currents = np.concatenate([BIAS + IGAIN * np.maximum(tn, 0.0), BIAS + IGAIN * np.maximum(-tn, 0.0)])
            res = neuron.step(currents, DT)
            r = res.gate
            gate_s = np.clip(GATE_GAIN * (r[0:3] - r[3:6]), -1, 1)
            G = _conductance(neuron, r, currents)
            cond_s = np.clip((G[0:3] - G[3:6]) / COND_SCALE, -1, 1)
            if readout == "gate":
                signed = gate_s
            elif readout == "conductance":
                signed = cond_s
            else:  # hybrid
                signed = np.clip((1 - HYBRID_W) * gate_s + HYBRID_W * cond_s, -1, 1)
            tau = np.clip((1 - BLEND) * tau_pd + BLEND * signed * tau_limit, -tau_limit, tau_limit)
            acts.append(float(np.mean(np.abs(signed))))

        apply_body_torque(data, params, tau, compute_hover_force(state, params, z_ref=Z_REF))
        mujoco.mj_step(model, data)
        qerrs.append(quat_angle_error(q_err))
        if not np.isfinite(data.qpos).all():
            return float("nan"), float("nan")
    return float(np.mean(qerrs)), float(np.mean(acts))


def main():
    print(f"{QUAD} | {MISSION} | {SIM_TIME}s | blend={BLEND} | gate_gain={GATE_GAIN:g}\n")
    pd_q, _ = run_config("hyperlif", "pd")
    print(f"PD baseline qerr_mean = {pd_q:.4f} rad\n")
    print(f"{'readout':14s} {'neuron':18s} {'qerr_mean':>10s} {'vs PD %':>9s} {'activity':>9s}")
    for readout in ["gate", "conductance", "hybrid"]:
        for neuron in ["hyperlif", "adaptive_hyperlif"]:
            q, act = run_config(neuron, readout)
            imp = (pd_q - q) / pd_q * 100.0 if np.isfinite(q) else float("nan")
            print(f"{readout:14s} {neuron:18s} {q:10.4f} {imp:9.2f} {act:9.3f}")
        print()


if __name__ == "__main__":
    main()
