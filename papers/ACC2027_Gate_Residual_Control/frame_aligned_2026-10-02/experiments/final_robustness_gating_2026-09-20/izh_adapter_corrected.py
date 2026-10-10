"""Izhikevich-PES with the corrected Nengo PES learning-rate normalization (2026-09-24 correction).

Same as izh_adapter.py (kept, superseded, not edited -- it produced the currently-published A3 numbers) except for one
change: the archived NengoNeuronFamilyAugmentor computes its internal Nengo rate as eta*N/(dt*S), one power of S short of
what its own network wiring requires (verified independently below and in NOTE_LEARNING_RATE_CORRECTION_2026-09-24.md).
The fix pre-divides the requested rate by the feature scale before construction, exactly mirroring
experiments/neuron_basis_decisive_2026-09-24/family_basis_adapter.py's `learning_normalization="exact"` path, so that the
archived class's own S-division then lands on eta*N/(dt*S^2).

Verification (independent of that campaign): Nengo's SimPES (installed 4.1.0, builder/learning_rules.py) applies
delta = -(kappa*dt/N) * error (x) pre_filtered, where pre_filtered is the connection's raw pre-synaptic signal. In
nengo_neuron_family.py the PES-learned connection's pre is the raw (unnormalized) filtered neuron output p = S*a (confirmed
by reading its network wiring, lines 111-145: the S-divided node is a separate diagnostic tap, not the learned connection's
input), and the connection's transform Theta is initialized to W0/S with the class's own W property returning S*Theta.
Substituting: Delta_W = S*Delta_Theta = S*(kappa*dt/N)*error*p^T = (kappa*dt*S^2/N)*error*a^T. Matching Delta_W =
eta*error*a^T requires kappa = eta*N/(dt*S^2). The archived kappa = eta*N/(dt*S); dividing the requested eta by S before
it reaches that formula corrects it exactly.
"""
from __future__ import annotations

from izh_adapter import IzhikevichPESAdapter as _Original, UPSTREAM, CMG_ONLY  # noqa: F401  (re-export, same diagnostics map)
import json

import numpy as np

from nengo_neuron_family import NengoNeuronFamilyAugmentor


class IzhikevichPESAdapterCorrected(_Original):
    family = "izhikevich"

    def __init__(self, limits: np.ndarray, dt: float, beta: float, learning_rate: float, seed: int):
        calibration = json.loads((UPSTREAM / "feature_calibration.json").read_text(encoding="utf-8"))
        item = calibration["families"]["izhikevich"]
        feature_scale = item["feature_scale"]
        self._a = NengoNeuronFamilyAugmentor(
            family="izhikevich", limits=limits, dt=dt, beta=beta, mode="pes",
            learning_rate=learning_rate / feature_scale,          # <-- the one-line correction
            feature_tau=calibration["feature_tau_s"], feature_scale=feature_scale,
            native_current_scale=item.get("native_current_scale", 1.0), seed=seed)
        self.nengo_learning_rate = self._a.nengo_learning_rate
        self.requested_direct_rate = learning_rate
