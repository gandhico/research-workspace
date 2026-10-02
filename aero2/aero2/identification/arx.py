"""Code-exact ARX / DARX least-squares identification (Ref 3, Eqs. 31-33).

Faithful to `M3_aero2_ls_arx_common.py`:
    rows  phi(k) = [1, y(k-1)..y(k-na), u(k-nk)..u(k-nk-nb+1) per input]
    Y = Phi beta,  beta_hat = np.linalg.lstsq(Phi, Y, rcond=None)
    fit% = 100 * (1 - ||y - yhat|| / ||y - mean(y)||)         (NRMSE-style)
Discrete convention (DARX): A(z^-1) y(k) = B(z^-1) u(k) + c,
    A(z^-1) = 1 - a1 z^-1 - a2 z^-2 - ...
Preprocessing: drop t < start_time (3 s), demean, optional downsample.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class ArxModel:
    output: str
    inputs: list
    na: int
    nb: int
    nk: int
    theta: np.ndarray
    ts: float
    downsample: int = 1
    y_mean: float = 0.0
    u_mean: dict = field(default_factory=dict)
    rank: int = 0
    cond: float = float("nan")

    # --- DARX coefficient views ------------------------------------------
    @property
    def c(self) -> float:
        return float(self.theta[0])

    @property
    def a(self) -> np.ndarray:
        """[a1..ana] (so A(z^-1) = 1 - a1 z^-1 - ...)."""
        return np.asarray(self.theta[1:1 + self.na], dtype=float)

    def b(self, input_name: str) -> np.ndarray:
        i = self.inputs.index(input_name)
        start = 1 + self.na + i * self.nb
        return np.asarray(self.theta[start:start + self.nb], dtype=float)

    @property
    def denominator_z_minus_1(self) -> list:
        return [1.0] + [-ai for ai in self.a]


# --- preprocessing ---------------------------------------------------------
def downsample(arr, factor: int) -> np.ndarray:
    return np.asarray(arr, dtype=float)[:: max(1, int(factor))]


def prepare(t, y, u_dict, start_time: float = 3.0, demean: bool = True, downsample_factor: int = 1):
    """Drop t<start_time, demean, downsample. Returns (y, u_dict, ts, means)."""
    t = np.asarray(t, dtype=float)
    mask = t >= start_time
    if not np.any(mask):
        mask = np.ones_like(t, dtype=bool)
    y = np.asarray(y, dtype=float)[mask]
    u_dict = {k: np.asarray(v, dtype=float)[mask] for k, v in u_dict.items()}
    tt = t[mask]

    if downsample_factor > 1:
        y = downsample(y, downsample_factor)
        u_dict = {k: downsample(v, downsample_factor) for k, v in u_dict.items()}
        tt = downsample(tt, downsample_factor)

    ts = float(np.mean(np.diff(tt))) if len(tt) > 1 else float("nan")
    y_mean = float(np.mean(y)) if demean else 0.0
    u_mean = {k: (float(np.mean(v)) if demean else 0.0) for k, v in u_dict.items()}
    y = y - y_mean
    u_dict = {k: v - u_mean[k] for k, v in u_dict.items()}
    return y, u_dict, ts, y_mean, u_mean


# --- regressor / fit -------------------------------------------------------
def build_regressor(y, u_dict, na: int, nb: int, nk: int = 1):
    keys = list(u_dict)
    start = max(na, nk + nb - 1)
    N = len(y)
    Z, Y = [], []
    for i in range(start, N):
        row = [1.0]
        for j in range(1, na + 1):
            row.append(y[i - j])
        for key in keys:
            for j in range(nb):
                row.append(u_dict[key][i - nk - j])
        Z.append(row)
        Y.append(y[i])
    return np.asarray(Z, dtype=float), np.asarray(Y, dtype=float), start


def estimate_ls(Z, Y):
    theta, _res, rank, _sv = np.linalg.lstsq(Z, Y, rcond=None)
    cond = float(np.linalg.cond(Z.T @ Z))
    return theta, int(rank), cond


def fit_arx(y, u_dict, na: int, nb: int, nk: int = 1, output: str = "y",
            ts: float = float("nan")) -> ArxModel:
    Z, Y, _ = build_regressor(y, u_dict, na, nb, nk)
    theta, rank, cond = estimate_ls(Z, Y)
    return ArxModel(output=output, inputs=list(u_dict), na=na, nb=nb, nk=nk,
                    theta=theta, ts=ts, rank=rank, cond=cond)


# --- prediction / simulation ----------------------------------------------
def one_step_predict(model: ArxModel, y, u_dict) -> np.ndarray:
    """Y_hat using MEASURED past outputs (regression prediction)."""
    Z, _Y, start = build_regressor(y, u_dict, model.na, model.nb, model.nk)
    yhat = Z @ model.theta
    out = np.full(len(y), np.nan)
    out[start:] = yhat
    return out


def free_run_simulate(model: ArxModel, y, u_dict) -> np.ndarray:
    """Recursive simulation using the model's OWN past outputs."""
    na, nb, nk, th = model.na, model.nb, model.nk, model.theta
    keys = model.inputs
    start = max(na, nk + nb - 1)
    y_sim = np.asarray(y, dtype=float).copy()
    for i in range(start, len(y_sim)):
        val = th[0]
        p = 1
        for j in range(1, na + 1):
            val += th[p] * y_sim[i - j]; p += 1
        for key in keys:
            for j in range(nb):
                val += th[p] * u_dict[key][i - nk - j]; p += 1
        y_sim[i] = val
    return y_sim


def fit_metric(y_true, y_pred) -> float:
    """Ref-3 fit %: 100*(1 - ||e|| / ||y - mean(y)||) over valid samples."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    m = np.isfinite(y_pred)
    yt, yp = y_true[m], y_pred[m]
    denom = np.linalg.norm(yt - np.mean(yt))
    if denom <= 0:
        return float("nan")
    return float(100.0 * (1.0 - np.linalg.norm(yp - yt) / denom))


__all__ = [
    "ArxModel", "downsample", "prepare", "build_regressor", "estimate_ls",
    "fit_arx", "one_step_predict", "free_run_simulate", "fit_metric",
]
