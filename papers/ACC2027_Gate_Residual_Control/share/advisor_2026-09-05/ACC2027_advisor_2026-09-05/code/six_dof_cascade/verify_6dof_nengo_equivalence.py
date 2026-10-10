"""Verify NengoCMGPESAugmentor(channels=6) matches the frozen NumPy
CMGResidualAugmentor(channels=6) to high precision, before trusting any
6-DOF Nengo cascade result -- same rigor as the existing 3-channel
verify_archived_equivalence.py, extended to 6 channels/12 units.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"nengo_nef_replication_2026-08-29"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"src"))
from nengo_cmg import NengoCMGPESAugmentor  # noqa: E402
from gra_control.gate import CMGResidualAugmentor  # noqa: E402

CHANNELS = 6
DT = 0.0005
STEPS = 2000
rng = np.random.default_rng(0)

limits = np.array([8.0, 8.0, 12.0, 0.05, 0.05, 0.04])
numpy_aug = CMGResidualAugmentor(CHANNELS, limits, "online_pes", True, beta=0.5, learning_rate=8e-4)
nengo_aug = NengoCMGPESAugmentor(CHANNELS, limits, DT, beta=0.5, learning_rate=8e-4)

max_command_err, max_activity_err, max_gate_err = 0.0, 0.0, 0.0
for i in range(STEPS):
    t = i*DT
    baseline = limits*0.4*np.sin(np.array([1.1, 1.7, 0.9, 2.3, 1.4, 2.0])*t+rng.normal(0, 0.01, 6))
    target = np.clip(0.6*np.sin(np.array([0.7, 1.3, 1.9, 0.5, 2.1, 1.6])*t), -1, 1)

    out_np = numpy_aug.step(baseline, DT, target)
    out_nengo = nengo_aug.step(baseline, target)

    max_command_err = max(max_command_err, np.max(np.abs(out_np.command-out_nengo.command)))
    max_activity_err = max(max_activity_err, np.max(np.abs(out_np.activity-out_nengo.activity)))
    max_gate_err = max(max_gate_err, np.max(np.abs(out_np.gate-out_nengo.gate)))

print(f"steps={STEPS}  channels={CHANNELS}  units={2*CHANNELS}")
print(f"max |command_np - command_nengo| = {max_command_err:.3e}  (limits scale ~{np.max(limits):.2f})")
print(f"max |activity_np - activity_nengo| = {max_activity_err:.3e}")
print(f"max |gate_np - gate_nengo| = {max_gate_err:.3e}")
rel = max_command_err/np.max(limits)
print(f"relative command error = {rel:.3e}  ({'PASS' if rel < 1e-4 else 'FAIL'} vs 1e-4 threshold)")
nengo_aug.close()
