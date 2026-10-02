"""NeuromorphicIdentifier — HyperLIF reservoir one-step predictor (identification).

A fully-Python **reservoir-computing** baseline: a fixed random-input Adaptive
HyperLIF reservoir provides gate-state features; a ridge-regression readout
predicts y(k). Exposes the same fit / one-step / free-run / fit_metric surface as
`identification.arx`, so it is scored on the IDENTICAL splits (docs/09 Table II).

This is a *first* neuromorphic identifier. The strong learning machinery
(gate-eligibility e-prop, APEX V11) is Julia and is future work (docs/10) — so this
reservoir is expected to trail ARX, which is reported honestly. No fabrication.
"""
from __future__ import annotations

import numpy as np

from aero2.config import hyperlif as cfg
from aero2.control.neuromorphic.neuron import make_direct_neuron
from aero2.identification import arx


class NeuromorphicIdentifier:
    def __init__(self, na=1, nb=3, nk=1, output="y", inputs=None, readout="hybrid",
                 reservoir_size=cfg.ID_RESERVOIR_SIZE, neuron_name=cfg.ID_RESERVOIR_NEURON,
                 input_gain=cfg.ID_INPUT_GAIN, input_bias=cfg.ID_INPUT_BIAS,
                 ridge=cfg.ID_RIDGE, seed=cfg.ID_SEED):
        self.na, self.nb, self.nk = na, nb, nk
        self.output, self.inputs = output, inputs
        # "reservoir": gate features only;  "hybrid": gate features + linear lag features
        # (the linear lags carry the prediction; the gates are currently auxiliary — docs/10).
        self.readout = readout
        self.N = int(reservoir_size)
        self.neuron_name = neuron_name
        self.input_gain, self.input_bias = float(input_gain), float(input_bias)
        self.ridge, self.seed = float(ridge), int(seed)
        self.W_in = self.W_out = None
        self.ts = None
        self._mu = self._sd = None

    # --- internal ---------------------------------------------------------
    def _lag_vector(self, y, u_dict, i, keys):
        f = [y[i - j] for j in range(1, self.na + 1)]
        for key in keys:
            f.extend(u_dict[key][i - self.nk - j] for j in range(self.nb))
        return np.asarray(f, dtype=float)

    def _reservoir_states(self, feats_norm, dt):
        neuron = make_direct_neuron(self.neuron_name, n=self.N, activity_mode="gate", scale="control")
        neuron.reset()
        R = np.zeros((len(feats_norm), self.N))
        for k, f in enumerate(feats_norm):
            currents = self.input_bias + self.input_gain * np.tanh(self.W_in @ f)
            R[k] = neuron.step(currents, dt).gate
        return R

    # --- fit / predict ----------------------------------------------------
    def fit(self, t, y, u_dict, demean=True, start_time=3.0, downsample_factor=1):
        if self.inputs is None:
            self.inputs = list(u_dict)
        y, u_dict, ts, _, _ = arx.prepare(t, y, u_dict, start_time, demean, downsample_factor)
        self.ts = ts
        keys = self.inputs
        start = max(self.na, self.nk + self.nb - 1)

        feats = np.array([self._lag_vector(y, u_dict, i, keys) for i in range(start, len(y))])
        targets = y[start:]
        self._mu, self._sd = feats.mean(0), feats.std(0) + 1e-9
        feats_n = (feats - self._mu) / self._sd

        rng = np.random.default_rng(self.seed)
        self.W_in = rng.normal(0.0, 1.0 / np.sqrt(feats_n.shape[1]), size=(self.N, feats_n.shape[1]))
        R = self._reservoir_states(feats_n, ts)

        blocks = [R, feats_n] if self.readout == "hybrid" else [R]
        Phi = np.hstack(blocks + [np.ones((len(R), 1))])
        A = Phi.T @ Phi + self.ridge * np.eye(Phi.shape[1])
        self.W_out = np.linalg.solve(A, Phi.T @ targets)
        return self

    def _run(self, y, u_dict, free_run):
        keys = self.inputs
        start = max(self.na, self.nk + self.nb - 1)
        neuron = make_direct_neuron(self.neuron_name, n=self.N, activity_mode="gate", scale="control")
        neuron.reset()
        ywork = np.asarray(y, dtype=float).copy()
        out = np.full(len(y), np.nan)
        for i in range(start, len(ywork)):
            src = ywork if free_run else y
            f = self._lag_vector(src, u_dict, i, keys)
            fn = (f - self._mu) / self._sd
            currents = self.input_bias + self.input_gain * np.tanh(self.W_in @ fn)
            r = neuron.step(currents, self.ts).gate
            feat = np.hstack([r, fn, 1.0]) if self.readout == "hybrid" else np.hstack([r, 1.0])
            yhat = float(feat @ self.W_out)
            out[i] = yhat
            if free_run:
                ywork[i] = yhat
        return out

    def predict_onestep(self, y, u_dict):
        return self._run(y, u_dict, free_run=False)

    def simulate_freerun(self, y, u_dict):
        return self._run(y, u_dict, free_run=True)

    def validate(self, y, u_dict) -> dict:
        return {
            "onestep_fit": arx.fit_metric(y, self.predict_onestep(y, u_dict)),
            "freerun_fit": arx.fit_metric(y, self.simulate_freerun(y, u_dict)),
        }


__all__ = ["NeuromorphicIdentifier"]
