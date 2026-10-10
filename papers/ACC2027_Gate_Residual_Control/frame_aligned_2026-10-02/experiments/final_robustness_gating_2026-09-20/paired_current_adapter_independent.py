"""Independent, from-scratch reimplementation of the "static paired-current" non-neural basis (TECHNICAL_METHOD.md
section 6: a_k = clip[0,1](I_k / (I_b + I_g))), written without reading or importing family_basis_adapter.py, as a true
independent cross-check -- not a reuse of their code. Direct hand-computed PES update, no Nengo, no feature-scale
normalization issue possible by construction (this basis never had the bug; this file exists only to verify the
reported numbers with code nobody at either end wrote twice from the same source).
"""
from __future__ import annotations

import numpy as np


class PairedCurrentPESIndependent:
    family = "paired-current"

    def __init__(self, limits: np.ndarray, dt: float, beta: float, learning_rate: float, seed: int,
                 current_bias: float = 0.75, current_gain: float = 1.25, leak: float = 1e-6):
        del dt, seed
        self.limits = np.asarray(limits, dtype=float)
        self.beta = float(beta)
        self.eta = float(learning_rate)
        self.leak = float(leak)
        self.Ib, self.Ig = float(current_bias), float(current_gain)
        self.W = np.c_[np.eye(3), -np.eye(3)]          # W0 = [I3, -I3], same convention as the paper's own eq. (23)
        self._a = np.zeros(6)
        self._decoded_raw = np.zeros(3)
        self._decoded_clipped = np.zeros(3)
        self._pes_error = np.zeros(3)

    def step(self, baseline: np.ndarray, target: np.ndarray):
        u0 = np.clip(np.asarray(baseline, float), -self.limits, self.limits)
        n = np.divide(u0, self.limits, out=np.zeros(3), where=self.limits > 1e-12)
        I = np.r_[self.Ib + self.Ig * np.maximum(n, 0.0), self.Ib + self.Ig * np.maximum(-n, 0.0)]
        self._a = np.clip(I / (self.Ib + self.Ig), 0.0, 1.0)          # a_k = clip[0,1](I_k / (I_b+I_g))
        y_star = np.clip(np.asarray(target, float), -1.0, 1.0)
        self._decoded_raw = self.W @ self._a
        self._decoded_clipped = np.clip(self._decoded_raw, -1.0, 1.0)
        s = self._decoded_clipped
        self._pes_error = y_star - s
        self.W = self.W + self.eta * np.outer(self._pes_error, self._a) - self.leak * self.W
        np.clip(self.W, -6.0, 6.0, out=self.W)
        residual = self.beta * self.limits * s
        command = np.clip(u0 + residual, -self.limits, self.limits)
        return type("Out", (), {"command": command, "residual": command - u0})()

    def diagnostics(self):
        zeros = np.zeros(6)
        return dict(activity=self._a.copy(), weights=self.W.copy(), voltage=zeros.copy(), gate=zeros.copy(),
                    decoded_raw=self._decoded_raw.copy(), decoded_clipped=self._decoded_clipped.copy(),
                    pes_error=self._pes_error.copy(),
                    states={}, current=np.zeros(6), effective_threshold=zeros.copy(), gate_argument=zeros.copy(),
                    gate_target=zeros.copy(), conductance_gain=zeros.copy(), conductance=zeros.copy(),
                    membrane_lambda=zeros.copy(), membrane_drive=zeros.copy())

    @property
    def nengo_learning_rate(self):
        return None

    def close(self):
        pass
