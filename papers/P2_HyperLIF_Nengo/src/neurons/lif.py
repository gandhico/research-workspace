"""Minimal baseline LIF neuron.

The LIF model here is intentionally small. It is included as a reference
baseline for figures and decoding comparisons, not as a replacement for
Nengo's production LIF implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LIFParams:
    """Parameters for the hard-reset LIF baseline."""

    tau: float = 0.02
    tau_ref: float = 0.002
    v_rest: float = 0.0
    v_thresh: float = 1.0
    v_reset: float = 0.0
    amplitude: float = 1.0
    min_voltage: float = 0.0


def _lif_voltage_update(v: float, current: float, dt: float, p: LIFParams) -> float:
    """Exact subthreshold update for dv/dt = (-(v-v_rest)+J)/tau."""

    target = p.v_rest + current
    return target + (v - target) * np.exp(-dt / p.tau)


def simulate_lif(
    current: np.ndarray,
    dt: float,
    params: LIFParams | None = None,
) -> dict[str, np.ndarray]:
    """Simulate a single hard-reset LIF neuron.

    Spikes/events are returned in Nengo's conventional units: ``amplitude / dt``
    at the event sample and zero otherwise.
    """

    p = params or LIFParams()
    current = np.asarray(current, dtype=float)
    n_steps = current.size

    voltage = np.zeros(n_steps, dtype=float)
    events = np.zeros(n_steps, dtype=float)
    refractory_time = np.zeros(n_steps, dtype=float)

    v = p.v_rest
    refr = 0.0

    for k, j in enumerate(current):
        if refr > 0.0:
            refr = max(0.0, refr - dt)
            v = p.v_reset
        else:
            v_prev = v
            v = _lif_voltage_update(v, j, dt, p)
            v = max(v, p.min_voltage)

            if v_prev < p.v_thresh and v >= p.v_thresh:
                events[k] = p.amplitude / dt
                v = p.v_reset
                refr = p.tau_ref

        voltage[k] = v
        refractory_time[k] = refr

    return {
        "input_current": current,
        "voltage": voltage,
        "events": events,
        "refractory_time": refractory_time,
    }
