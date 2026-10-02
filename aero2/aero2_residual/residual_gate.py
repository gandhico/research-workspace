"""Aero2 2-DOF gate-state residual (HyperLIF / Adaptive HyperLIF).

Direct port of the hardware-validated Qube gate (ServoPendulum project): a demand-driven
leaky membrane + HyperLIF gate + Eq.7 conductance readout + low-pass events, extended to
2 DOF (pitch + yaw). Pure computation — this module NEVER touches the hardware. The runner
decides whether/where to apply the (bounded) candidate.

Validated Qube behavior reproduced here:
  low demand  -> gate ~ 0, candidate ~ 0   (dormant)
  perturbation-> demand rises, gate opens, candidate activates
  recovery    -> gate releases (GAMMA = 0, no latch), candidate returns to 0
"""
from __future__ import annotations

import csv
import math
from collections import deque
from pathlib import Path
from typing import Any


def str2bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "t", "yes", "y", "on")


def _sigmoid(x: float) -> float:
    if x <= -60.0:
        return 0.0
    if x >= 60.0:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


class Aero2GateResidual:
    """Demand score + gate neuron + bounded pitch/yaw residual candidates for Aero2."""

    # Fixed internal neuron parameters (control-rate, seconds) — identical to the Qube build.
    TAU = 0.05          # membrane low-pass (~50 ms)
    TAU_R = 0.02        # gate time constant (~20 ms)
    TAU_EVENT = 0.10    # event low-pass (~100 ms)
    ALPHA = 8.0         # gate sigmoid slope
    GAMMA = 0.0         # hysteresis latch disabled (clean release)
    V_THRESH = 1.0      # gate sigmoid center
    G_BASE = 20.0       # base conductance (Eq.5/Eq.7)
    DRIVE_GAIN = 2.5    # demand[0,1] -> membrane drive

    # Demand normalization references (fixed so the equilibrium mission, ref=0, still normalizes).
    E_PITCH_REF_RAD = math.radians(15.0)
    E_YAW_REF_RAD = math.radians(30.0)
    RATE_REF = 3.0      # rad/s

    def __init__(self, neuron: str, sample_time_s: float, residual_threshold: float,
                 residual_demand_threshold: float, residual_max_voltage: float) -> None:
        self.neuron = neuron
        self.beta = 5.0 if neuron == "adaptive_hyperlif" else 0.0  # only HyperLIF->Adaptive diff
        self.dt = float(sample_time_s)
        self.residual_threshold = float(residual_threshold)
        self.residual_demand_threshold = float(residual_demand_threshold)
        self.vmax = float(residual_max_voltage)
        self.v = 0.0
        self.r = 0.0
        self.event_filt = 0.0
        self._decay_r = math.exp(-self.dt / self.TAU_R)
        self._decay_v = math.exp(-self.dt / self.TAU)
        self._decay_event = math.exp(-self.dt / self.TAU_EVENT)

    # ---- demand -------------------------------------------------------------
    def demand_scores(self, pitch_err, pitch_rate, yaw_err, yaw_rate, u_pitch, u_yaw, vlim):
        sat = min(1.0, max(abs(u_pitch), abs(u_yaw)) / max(abs(vlim), 1e-6))
        pd = (0.5 * abs(pitch_err) / self.E_PITCH_REF_RAD
              + 0.3 * abs(pitch_rate) / self.RATE_REF + 0.2 * sat)
        yd = (0.5 * abs(yaw_err) / self.E_YAW_REF_RAD
              + 0.3 * abs(yaw_rate) / self.RATE_REF + 0.2 * sat)
        pd = min(1.0, max(0.0, pd))
        yd = min(1.0, max(0.0, yd))
        combined = min(1.0, max(0.0, max(pd, yd)))
        return pd, yd, combined, sat

    # ---- gate neuron (advances one tick) -----------------------------------
    def step_gate(self, combined_demand: float) -> dict[str, float]:
        drive = self.DRIVE_GAIN * combined_demand
        prev_r = self.r
        self.v = self.v * self._decay_v + drive * (1.0 - self._decay_v)
        theta_eff = self.V_THRESH - self.GAMMA * self.r
        r_tgt = _sigmoid(self.ALPHA * (self.v - theta_eff))
        self.r = min(1.0, max(0.0, self.r * self._decay_r + r_tgt * (1.0 - self._decay_r)))
        gate = self.r
        conductance = (self.G_BASE + self.beta * abs(drive)) * (gate ** 2)
        event = 1.0 if (prev_r < self.residual_threshold <= gate) else 0.0
        self.event_filt = self._decay_event * self.event_filt + (1.0 - self._decay_event) * event
        active = 1.0 if (gate >= self.residual_threshold
                         and combined_demand >= self.residual_demand_threshold) else 0.0
        return {"gate_state": gate, "conductance_state": conductance,
                "event_activity": self.event_filt, "residual_active_flag": active}

    # ---- corrective directions (toward reference) --------------------------
    def correctives(self, pitch_err, yaw_err):
        cp = math.tanh((3.0 / self.E_PITCH_REF_RAD) * pitch_err)  # in [-1, 1]
        cy = math.tanh((3.0 / self.E_YAW_REF_RAD) * yaw_err)
        return cp, cy

    def candidates(self, gate_state, combined_demand, pitch_err, yaw_err):
        """Bounded gated candidate per virtual channel: |cand| <= residual_max_voltage."""
        cp, cy = self.correctives(pitch_err, yaw_err)
        pitch_cand = self.vmax * cp * gate_state * combined_demand
        yaw_cand = self.vmax * cy * gate_state * combined_demand
        return pitch_cand, yaw_cand, cp, cy


class ShuffleSource:
    """Time-misaligned gate/demand source for the shuffled_gate timing control.

    Loads gate_state (+ combined_demand_score) from a prior shadow/gate CSV and samples it
    at (elapsed + offset) wrapped — same gate statistics, broken alignment with the CURRENT
    perturbations. If no source is given the runner uses an in-run delayed deque instead.
    """

    def __init__(self, path: Path, offset_s: float) -> None:
        with Path(path).open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows or "gate_state" not in rows[0]:
            raise SystemExit(f"[shuffle-source] {path} lacks a 'gate_state' column.")

        def grab(name, default=0.0):
            return [float(r.get(name) or default) for r in rows]

        self.gate = grab("gate_state")
        dkey = "combined_demand_score" if "combined_demand_score" in rows[0] else "gate_state"
        self.demand = grab(dkey)
        t = grab("t") if "t" in rows[0] else grab("time_s")
        self.n = len(self.gate)
        if self.n > 1:
            diffs = [t[i + 1] - t[i] for i in range(self.n - 1)]
            diffs = [d for d in diffs if d > 0]
            self.dt = sorted(diffs)[len(diffs) // 2] if diffs else 0.002
        else:
            self.dt = 0.002
        self.offset = float(offset_s)

    def sample(self, elapsed: float) -> tuple[float, float]:
        idx = int(round((elapsed + self.offset) / self.dt)) % self.n
        return float(self.gate[idx]), float(self.demand[idx])


def make_inrun_shuffle_buffer(offset_s: float, sample_rate: float) -> deque:
    return deque(maxlen=max(1, int(round(offset_s * sample_rate))))
