"""Offline equation-to-code checks. Does not run MuJoCo or access hardware."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
HERE = Path(__file__).resolve().parent
GATE = ROOT / "src/gra_control/gate.py"
spec = importlib.util.spec_from_file_location("audited_gate", GATE)
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)

rng = np.random.default_rng(20260911)
errors = {name: 0.0 for name in ("gate", "membrane", "activity", "weights", "command", "residual")}
count = 0
clipping_steps = 0
for chi in (False, True):
    for gain in (1.0, 1e5):
        for beta in (0.0, 0.5, 1.0):
            p = gate.CMGConfig(gate_gain=gain)
            limits = np.array([0.11, 0.17, 0.07])
            aug = gate.CMGResidualAugmentor(3, limits, mode="online_pes",
                adaptive_conductance=chi, beta=beta, learning_rate=8e-4, leak=1e-6, cfg=p)
            # Both canonical and near-projection-bound initial conditions are checked.
            for segment in ("canonical", "projection_stress"):
                aug.reset()
                if segment == "projection_stress":
                    aug.W[:] = rng.choice([-1.0, 1.0], (3, 6)) * 5.99999
                    aug.units.r[:] = rng.uniform(0.1, 0.9, 6)
                for _ in range(256):
                    h = 0.0005
                    baseline = rng.uniform(-1.5, 1.5, 3) * limits
                    target = rng.uniform(-1.3, 1.3, 3)
                    v, r, W = aug.units.v.copy(), aug.units.r.copy(), aug.W.copy()
                    u0 = np.clip(baseline, -limits, limits)
                    normalized = u0 / limits
                    current = np.r_[p.current_bias + p.current_gain*np.maximum(normalized, 0),
                                    p.current_bias + p.current_gain*np.maximum(-normalized, 0)]
                    b = 1/(1+np.exp(-np.clip(p.alpha*(v-p.v_threshold+p.gamma*r), -60, 60)))
                    rp = np.clip(r + h/p.tau_r*(b-r), 0, 1)
                    c = (p.base_gain + int(chi)*p.gain_scaling*np.abs(current))*rp**2
                    lam = 1/p.tau + c
                    d = (p.v_rest+current)/p.tau + c*p.v_reset
                    vp = np.exp(-lam*h)*v + (1-np.exp(-lam*h))*d/lam
                    a = np.clip(gain*rp, 0, 1)
                    s = np.clip(W@a, -1, 1)
                    candidate = (1-aug.leak)*W + aug.learning_rate*np.outer(np.clip(target, -1, 1)-s, a)
                    Wnext = np.clip(candidate, -6, 6)
                    clipping_steps += int(np.any(candidate != Wnext))
                    u = np.clip(u0 + beta*limits*s, -limits, limits)
                    out = aug.step(baseline, h, target)
                    pairs = {"gate": (out.gate, rp), "membrane": (aug.units.v, vp),
                             "activity": (out.activity, a), "weights": (aug.W, Wnext),
                             "command": (out.command, u), "residual": (out.residual, u-u0)}
                    for name, (actual, expected) in pairs.items():
                        errors[name] = max(errors[name], float(np.max(np.abs(actual-expected))))
                        np.testing.assert_allclose(actual, expected, atol=5e-13, rtol=5e-13)
                    assert a.shape == (6,) and Wnext.shape == (3, 6) and u.shape == (3,)
                    assert np.all(np.abs(out.residual) <= beta*limits + 1e-14)
                    if beta == 0:
                        np.testing.assert_array_equal(out.command, u0)
                    count += 1

sources = [GATE, ROOT / "experiments/nengo_nef_replication_2026-08-29/run_mujoco_nef.py",
           ROOT / "experiments/nengo_nef_replication_2026-08-29/nengo_cmg.py"]
report = {
    "scope": "Independent arithmetic reconstruction of the direct CMG-PES step; no plant simulation or hardware",
    "steps_checked": count,
    "projection_exercised_steps": clipping_steps,
    "maximum_absolute_discrepancy": errors,
    "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
    "not_claimed": ["new mission performance", "backend weight-sequence equivalence", "closed-loop stability proof"],
}
assert clipping_steps > 0
output = HERE / "ARCHITECTURE_VALIDATION.json"
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
