"""Izhikevich-PES behind the interface `run_final_robustness.py` uses for the CMG augmentor (amendment A3).

Wraps the ARCHIVED `NengoNeuronFamilyAugmentor` (the object behind the paper's neuron-family rows) with the archived
calibration (`feature_calibration.json`: feature scale 42.6, native current scale 10, 5-ms low-pass feature).  Nothing about
the neuron, the PES rule, the decoder leak/clip or the paired-current encoding is changed; the wrapper only exposes the
diagnostic keys the runner logs (CMG-only quantities are reported as zeros; `voltage` is the Izhikevich membrane potential in mV
and `gate` is its recovery variable, the same mapping the archived runner uses).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from nengo_neuron_family import NengoNeuronFamilyAugmentor  # resolved through the runner's sys.path (upstream folder)

UPSTREAM = Path(__file__).resolve().parents[1] / "nengo_nef_replication_2026-08-29"
CMG_ONLY = ("effective_threshold", "gate_argument", "gate_target", "conductance_gain", "conductance",
            "membrane_lambda", "membrane_drive")


class IzhikevichPESAdapter:
    family = "izhikevich"

    def __init__(self, limits: np.ndarray, dt: float, beta: float, learning_rate: float, seed: int):
        calibration = json.loads((UPSTREAM / "feature_calibration.json").read_text(encoding="utf-8"))
        item = calibration["families"]["izhikevich"]
        self._a = NengoNeuronFamilyAugmentor(
            family="izhikevich", limits=limits, dt=dt, beta=beta, mode="pes", learning_rate=learning_rate,
            feature_tau=calibration["feature_tau_s"], feature_scale=item["feature_scale"],
            native_current_scale=item.get("native_current_scale", 1.0), seed=seed)
        self.nengo_learning_rate = self._a.nengo_learning_rate

    @property
    def W(self) -> np.ndarray:
        return self._a.W

    def step(self, baseline: np.ndarray, target: np.ndarray):
        return self._a.step(baseline, target)

    def diagnostics(self) -> dict:
        d = self._a.diagnostics()
        states = d["states"]
        zeros = np.zeros(6)
        out = dict(d)
        out["voltage"] = np.asarray(states.get("voltage", zeros)).copy()
        out["gate"] = np.asarray(states.get("adaptation", states.get("recovery", states.get("refractory_time", zeros)))).copy()
        for name in CMG_ONLY:
            out[name] = zeros.copy()
        return out

    def close(self) -> None:
        self._a.close()
