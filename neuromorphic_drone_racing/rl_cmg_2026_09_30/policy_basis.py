"""Fixed observation-to-CMG current mapping shared by simulation workers."""
from __future__ import annotations

import numpy as np
from cmg_cells import CMGPopulation, policy_preset

OBS_DIM = 26
N_UNITS = 32


class Basis:
    def __init__(self, mode: str, seed: int, policy_dt: float):
        self.mode, self.n, self.policy_dt = mode, N_UNITS, policy_dt
        self.neural_dt = 0.0005
        rng = np.random.default_rng(seed + 8001)
        self.encoder = rng.normal(size=(self.n, OBS_DIM)) / np.sqrt(OBS_DIM)
        self.offset = rng.uniform(-0.30, 0.30, self.n)
        self.cell = None if mode == "mlp" else CMGPopulation(self.n, mode, policy_preset(mode))

    def reset(self):
        if self.cell is not None:
            self.cell.reset()

    def encode(self, obs: np.ndarray):
        if self.cell is None:
            return np.r_[obs, np.zeros(self.n)].astype(np.float32), np.zeros(self.n)
        current = np.clip(0.85 + self.offset + 0.95 * np.tanh(self.encoder @ obs), 0.05, 2.2)
        feature = self.cell.advance(current, self.policy_dt, self.neural_dt)
        return np.r_[obs, feature].astype(np.float32), current

    def metadata(self):
        return dict(mode=self.mode, n=self.n, policy_dt=self.policy_dt,
                    neural_dt=self.neural_dt, encoder=self.encoder.tolist(),
                    offset=self.offset.tolist(),
                    cmg_params=None if self.cell is None else self.cell.p.asdict())
