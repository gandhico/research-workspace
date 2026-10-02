"""LIFRate-PES, corrected Nengo PES normalization, threshold-aware operating point (current_bias=1.03, current_gain=0.97,
feature_tau=5ms -- the setting independently confirmed as the argmin of the pre-declared development-grid criterion in
neuron_basis_decisive_2026-09-24). Mirrors izh_adapter_corrected.py's correction exactly (same archived class, same
one-line eta -> eta/S fix); used only as an independent cross-check re-run, not part of the sealed pipeline.
"""
from __future__ import annotations

import json

import numpy as np

from izh_adapter import UPSTREAM, CMG_ONLY
from nengo_neuron_family import NengoNeuronFamilyAugmentor


class LIFRatePESAdapterCorrected:
    family = "lifrate"

    def __init__(self, limits: np.ndarray, dt: float, beta: float, learning_rate: float, seed: int):
        calibration = json.loads((UPSTREAM / "feature_calibration.json").read_text(encoding="utf-8"))
        item = calibration["families"]["lifrate"]
        feature_scale = item["feature_scale"]
        self._a = NengoNeuronFamilyAugmentor(
            family="lifrate", limits=limits, dt=dt, beta=beta, mode="pes",
            learning_rate=learning_rate / feature_scale,           # the correction
            feature_tau=0.005, feature_scale=feature_scale,
            native_current_scale=item.get("native_current_scale", 1.0), seed=seed,
            current_bias=1.03, current_gain=0.97)                  # the selected, verified-argmin operating point
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
