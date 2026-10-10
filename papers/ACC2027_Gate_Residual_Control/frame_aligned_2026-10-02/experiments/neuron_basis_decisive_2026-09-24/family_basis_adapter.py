"""Adapters for the decisive neuron-family and no-neuron PES comparison.

Every adapter exposes the interface used by the final rho=3 MuJoCo runner:
six paired activities, a 3x6 decoder initialized as [I,-I], the same clipped
PES target/error, decoder leak/projection, residual scale beta, and outer
torque saturation.  Only the mapping from paired current to activity changes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from nengo_neuron_family import NengoNeuronFamilyAugmentor


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
UPSTREAM = REPO / "experiments" / "nengo_nef_replication_2026-08-29"
CALIBRATION = json.loads(
    (UPSTREAM / "feature_calibration.json").read_text(encoding="utf-8")
)
CMG_ONLY = (
    "effective_threshold",
    "gate_argument",
    "gate_target",
    "conductance_gain",
    "conductance",
    "membrane_lambda",
    "membrane_drive",
)


def _state_or_zeros(states: dict, *names: str) -> np.ndarray:
    for name in names:
        if name in states:
            return np.asarray(states[name], dtype=float).copy()
    return np.zeros(6, dtype=float)


class FamilyPESAdapter:
    """Conventional Nengo neuron family behind the common residual interface."""

    def __init__(
        self,
        family: str,
        limits: np.ndarray,
        dt: float,
        beta: float,
        learning_rate: float,
        seed: int,
        *,
        current_bias: float | None = None,
        current_gain: float | None = None,
        feature_tau: float | None = None,
        feature_scale: float | None = None,
        native_current_scale: float | None = None,
        learning_normalization: str = "exact",
    ):
        if family not in ("lif", "alif", "lifrate", "izhikevich"):
            raise ValueError(f"Unsupported conventional family: {family}")
        calibrated = CALIBRATION["families"][family]
        self.family = family
        self.feature_scale = float(
            calibrated["feature_scale"] if feature_scale is None else feature_scale
        )
        self.native_current_scale = float(
            calibrated.get("native_current_scale", 1.0)
            if native_current_scale is None
            else native_current_scale
        )
        self.feature_tau = float(
            CALIBRATION["feature_tau_s"] if feature_tau is None else feature_tau
        )
        self.current_bias = 0.75 if current_bias is None else float(current_bias)
        self.current_gain = 1.25 if current_gain is None else float(current_gain)
        if learning_normalization not in ("exact", "archived"):
            raise ValueError("learning_normalization must be exact or archived")
        self.learning_normalization = learning_normalization
        # If p=S*a is the filtered native feature and Theta=W/S is the
        # physical Nengo connection weight, SimPES gives
        #   Delta W = S Delta Theta
        #           = eta_N dt S^2/N (target-y) a^T.
        # Therefore equal normalized direct learning requires
        # eta_N=eta*N/(dt*S^2).  The archived adapter used only one S in the
        # denominator and consequently implemented Delta W=eta*S*e*a^T.
        upstream_learning_rate = (
            learning_rate / self.feature_scale
            if learning_normalization == "exact"
            else learning_rate
        )
        self._a = NengoNeuronFamilyAugmentor(
            family=family,
            limits=limits,
            dt=dt,
            beta=beta,
            mode="pes",
            learning_rate=upstream_learning_rate,
            feature_tau=self.feature_tau,
            feature_scale=self.feature_scale,
            native_current_scale=self.native_current_scale,
            seed=seed,
            current_bias=self.current_bias,
            current_gain=self.current_gain,
        )
        self.nengo_learning_rate = self._a.nengo_learning_rate

    @property
    def W(self) -> np.ndarray:
        return self._a.W

    def step(self, baseline: np.ndarray, target: np.ndarray):
        return self._a.step(baseline, target)

    def diagnostics(self) -> dict:
        d = self._a.diagnostics()
        states = d["states"]
        zeros = np.zeros(6, dtype=float)
        out = dict(d)
        out["voltage"] = _state_or_zeros(states, "voltage")
        # This field is deliberately named generically in the saved schema.
        # It is adaptation for ALIF, recovery for Izhikevich, refractory time
        # for LIF/LIFRate, and is not interpreted as a CMG gate.
        out["gate"] = _state_or_zeros(
            states, "adaptation", "recovery", "refractory_time"
        )
        for name in CMG_ONLY:
            out[name] = zeros.copy()
        return out

    def close(self) -> None:
        self._a.close()


@dataclass
class _BasisOutput:
    command: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    activity: np.ndarray
    raw_output: np.ndarray


class NoNeuronPESAdapter:
    """Analytic six-feature basis with the same decoder and PES recursion.

    ``constant-one`` isolates the persistent-basis mechanism: after the first
    sample all six features equal one.  ``paired-current`` removes temporal
    neuron dynamics while retaining the exact paired current encoder, scaled
    to [0,1] by its maximum current ``current_bias + current_gain``.
    """

    family = "no-neuron"

    def __init__(
        self,
        basis: str,
        limits: np.ndarray,
        dt: float,
        beta: float,
        learning_rate: float,
        seed: int,
        *,
        current_bias: float = 0.75,
        current_gain: float = 1.25,
        leak: float = 1e-6,
    ):
        del seed
        if basis not in ("constant-one", "paired-current"):
            raise ValueError(f"Unsupported non-neural basis: {basis}")
        self.basis = basis
        self.limits = np.asarray(limits, dtype=float)
        self.dt = float(dt)
        self.beta = float(beta)
        self.learning_rate = float(learning_rate)
        self.leak = float(leak)
        self.current_bias = float(current_bias)
        self.current_gain = float(current_gain)
        self._weights = np.c_[np.eye(3), -np.eye(3)].astype(float)
        self._current = np.zeros(6, dtype=float)
        self._activity = np.zeros(6, dtype=float)
        self._decoded_raw = np.zeros(3, dtype=float)
        self._decoded_clipped = np.zeros(3, dtype=float)
        self._target = np.zeros(3, dtype=float)
        self._pes_error = np.zeros(3, dtype=float)
        self._weight_delta = np.zeros((3, 6), dtype=float)
        # Compatibility metadata only; no Nengo learning operator is used.
        self.nengo_learning_rate = None

    @property
    def W(self) -> np.ndarray:
        return self._weights.copy()

    def _features(self, baseline: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        normalized = np.divide(
            baseline,
            self.limits,
            out=np.zeros(3, dtype=float),
            where=self.limits > 1e-12,
        )
        current = np.r_[
            self.current_bias + self.current_gain * np.maximum(normalized, 0.0),
            self.current_bias + self.current_gain * np.maximum(-normalized, 0.0),
        ]
        if self.basis == "constant-one":
            activity = np.ones(6, dtype=float)
        else:
            current_max = max(self.current_bias + self.current_gain, 1e-12)
            activity = np.clip(current / current_max, 0.0, 1.0)
        return current, activity

    def step(self, baseline: np.ndarray, target: np.ndarray) -> _BasisOutput:
        u0 = np.clip(np.asarray(baseline, dtype=float), -self.limits, self.limits)
        self._current[:], self._activity[:] = self._features(u0)
        self._target[:] = np.clip(np.asarray(target, dtype=float), -1.0, 1.0)

        weights_before = self._weights.copy()
        self._decoded_raw[:] = weights_before @ self._activity
        self._decoded_clipped[:] = np.clip(self._decoded_raw, -1.0, 1.0)
        self._pes_error[:] = self._decoded_clipped - self._target
        self._weights[:] = (
            weights_before
            + self.learning_rate
            * np.outer(self._target - self._decoded_clipped, self._activity)
            - self.leak * weights_before
        )
        np.clip(self._weights, -6.0, 6.0, out=self._weights)
        self._weight_delta[:] = self._weights - weights_before

        requested = self.beta * self.limits * self._decoded_clipped
        command = np.clip(u0 + requested, -self.limits, self.limits)
        return _BasisOutput(
            command=command.copy(),
            baseline=u0.copy(),
            residual=(command - u0).copy(),
            activity=self._activity.copy(),
            raw_output=self._activity.copy(),
        )

    def diagnostics(self) -> dict:
        zeros = np.zeros(6, dtype=float)
        out = {
            "current": self._current.copy(),
            "native_current": self._current.copy(),
            "raw_output": self._activity.copy(),
            "activity": self._activity.copy(),
            "states": {},
            "voltage": zeros.copy(),
            "gate": zeros.copy(),
            "decoded_raw": self._decoded_raw.copy(),
            "decoded_clipped": self._decoded_clipped.copy(),
            "target": self._target.copy(),
            "pes_error": self._pes_error.copy(),
            "weights": self._weights.copy(),
            "weight_delta": self._weight_delta.copy(),
        }
        for name in CMG_ONLY:
            out[name] = zeros.copy()
        return out

    def close(self) -> None:
        return None
