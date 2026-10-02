"""Strengthened conductance/hybrid residual comparison: X2 (rotor) + CF2, with the origin variant
and a hybrid-weight sweep. Self-contained (no edits to existing controllers/neurons).

    <global-python> v2_clean/runners/compare_conductance_residual_v2.py
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
from quad.bridge import get_state, compute_hover_force, apply_body_torque, apply_rotor_commands  # noqa: E402
from rotor.mixer import wrench_to_motors, hover_wrench  # noqa: E402
from controllers.neuron_dynamics import AdaptiveHyperLIFDirect, NeuronStepResult, make_direct_neuron  # noqa: E402

SIM_TIME = 15.0
DT = 5e-4
Z_REF = 1.0
BLEND = 0.50
GATE_GAIN = 1.0e5
COND_SCALE = 120.0
BIAS, IGAIN = 0.75, 1.25


class OriginAdaptiveHyperLIF(AdaptiveHyperLIFDirect):
    """Adaptive HyperLIF + gate-coupled origin: v_reset_eff = v_reset - delta_reset*r (the novel knob)."""

    def __init__(self, *a, delta_reset=0.5, **k):
        super().__init__(*a, **k)
        self.delta_reset = delta_reset

    def step(self, current, dt):
        current = np.asarray(current, dtype=float)
        v_prev = self.v.copy()
        eff_thresh = self.v_thresh - self.gamma * self.r
        target_r = self._sig(self.alpha * (self.v - eff_thresh))
        self.r[:] = target_r + (self.r - target_r) * np.exp(-dt / self.tau_r)
        conductance = (self.base_gain + self.gain_scaling * np.abs(current)) * self.r ** 2
        v_reset_eff = self.v_reset - self.delta_reset * self.r
        lam = (1.0 / self.tau) + conductance
        drive = (self.v_rest / self.tau) + (current / self.tau) + conductance * v_reset_eff
        decay = np.exp(-lam * dt)
        self.v[:] = np.where(lam > 1e-12, self.v * decay + (drive / lam) * (1.0 - decay), self.v + dt * drive)
        events = ((v_prev < self.event_threshold) & (self.v >= self.event_threshold)).astype(float)
        act = np.clip(self.r, 0.0, 1.0)
        return NeuronStepResult(activity=act, events=events, voltage=self.v.copy(), gate=self.r.copy())


def get_neuron(name):
    if name == "origin":
        return OriginAdaptiveHyperLIF(n=6, activity_mode="gate", tau=0.05, tau_r=0.005,
                                      base_gain=120.0, gain_scaling=30.0, gamma=2.0,
                                      event_threshold=0.5, delta_reset=0.5)
    return make_direct_neuron(name, n=6, activity_mode="gate", scale="control")


def _cond(neuron, r, currents):
    if hasattr(neuron, "reset_gain"):
        return neuron.reset_gain * r**2
    return (neuron.base_gain + neuron.gain_scaling * np.abs(currents)) * r**2


def run_config(quad, neuron_name, readout, hybrid_w=0.5):
    params = load_drone(quad)
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
    rotor = params.actuator_mode == "rotor4"

    neuron = None if readout == "pd" else get_neuron(neuron_name)
    kq, kw, tl = params.kq, params.kw, params.tau_limit
    qerrs = []
    while data.time < SIM_TIME:
        t = float(data.time)
        data.xfrc_applied[:] = 0.0
        state = get_state(model, data, params)
        q_ref = reference_quat(t, "hard45", SIM_TIME)
        q_err = quat_normalize(quat_mul(quat_normalize(q_ref), quat_conj(quat_normalize(state.q))))
        e_q = q_err[1:].copy()
        if q_err[0] < 0.0:
            e_q = -e_q
        tau_pd = np.clip(-kq * e_q - kw * np.asarray(state.omega), -tl, tl)

        if readout == "pd":
            tau = tau_pd
        else:
            tn = np.clip(np.divide(tau_pd, tl, out=np.zeros_like(tau_pd), where=np.abs(tl) > 1e-12), -1, 1)
            cur = np.concatenate([BIAS + IGAIN * np.maximum(tn, 0.0), BIAS + IGAIN * np.maximum(-tn, 0.0)])
            res = neuron.step(cur, DT)
            r = res.gate
            gate_s = np.clip(GATE_GAIN * (r[0:3] - r[3:6]), -1, 1)
            G = _cond(neuron, r, cur)
            cond_s = np.clip((G[0:3] - G[3:6]) / COND_SCALE, -1, 1)
            signed = gate_s if readout == "gate" else (cond_s if readout == "conductance"
                     else np.clip((1 - hybrid_w) * gate_s + hybrid_w * cond_s, -1, 1))
            tau = np.clip((1 - BLEND) * tau_pd + BLEND * signed * tl, -tl, tl)

        if rotor:
            T = hover_wrench(params, state.pos, state.vel, state.R_wb, Z_REF)
            apply_rotor_commands(model, data, params, wrench_to_motors(T, tau, params, clip=True))
        else:
            apply_body_torque(data, params, tau, compute_hover_force(state, params, z_ref=Z_REF))
        mujoco.mj_step(model, data)
        qerrs.append(quat_angle_error(q_err))
        if not np.isfinite(data.qpos).all():
            return float("nan")
    return float(np.mean(qerrs))


def main():
    for quad in ["skydio_x2", "bitcraze_crazyflie_2"]:
        print(f"\n===== {quad} | hard45 | {SIM_TIME}s | blend={BLEND} =====")
        pd_q = run_config(quad, "hyperlif", "pd")
        gate_q = run_config(quad, "adaptive_hyperlif", "gate")  # gate: HyperLIF==Adaptive
        print(f"PD baseline = {pd_q:.4f} | gate residual (their design) = {gate_q:.4f} "
              f"({(pd_q-gate_q)/pd_q*100:+.2f}% vs PD)")
        print(f"{'readout':12s} {'neuron':10s} {'hw':>4s} {'qerr':>9s} {'vs PD %':>9s} {'vs gate %':>10s}")
        for hw in [0.5, 0.8]:
            for neuron in ["hyperlif", "adaptive_hyperlif", "origin"]:
                q = run_config(quad, neuron, "hybrid", hybrid_w=hw)
                vpd = (pd_q - q) / pd_q * 100.0
                vg = (gate_q - q) / gate_q * 100.0
                print(f"{'hybrid':12s} {neuron:10s} {hw:>4.1f} {q:9.4f} {vpd:9.2f} {vg:10.2f}")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
