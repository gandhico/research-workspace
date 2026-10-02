"""Fixed-point and depolarization-block analysis for HyperLIF.

All results are derived from the continuous-time dynamics implemented in
``src/neurons/hyperlif.py`` and ``src/neurons/adaptive_hyperlif.py``:

    tau dv/dt = -(v - v_rest) + I - tau * G(r, I) * (v - v_reset)
    tau_r dr/dt = sigmoid(alpha (v - (v_thresh - gamma r))) - r

with baseline conductance ``G = reset_gain * r**2`` and adaptive conductance
``G = (base_gain + gain_scaling |I|) * r**2``.

The membrane equation has the equilibrium (for a frozen gate value ``r`` and
frozen conductance scale ``G_scale``)

    v* = (v_rest + I + tau * G_scale * r**2 * v_reset) / (1 + tau * G_scale * r**2),

i.e. a current divided by an input-dependent total conductance. When the gate
saturates open (r -> 1) at a depolarized voltage, repetitive spiking ceases and
the neuron is in a depolarization block (DB).
"""

from __future__ import annotations

import numpy as np


def _sigmoid(x: float) -> float:
    x = float(np.clip(x, -700.0, 700.0))
    return 1.0 / (1.0 + np.exp(-x))


def gate_knee_voltage(p) -> float:
    """Effective threshold when the gate is fully open (r = 1): v_thresh - gamma."""

    return float(p.v_thresh - p.gamma)


def latched_voltage(current: float, p, gain_scale: float, r: float = 1.0) -> float:
    """Depolarized membrane equilibrium for a frozen gate ``r`` and conductance.

    ``gain_scale`` is the conductance pre-factor multiplying ``r**2`` (i.e.
    ``reset_gain`` for HyperLIF or ``base_gain + gain_scaling*|I|`` for the
    adaptive model).
    """

    g = gain_scale * r * r
    num = p.v_rest + current + p.tau * g * p.v_reset
    den = 1.0 + p.tau * g
    return float(num / den)


def _adaptive_gain_scale(current: float, p) -> float:
    """Conductance pre-factor for the model described by ``p``.

    Works for both HyperLIFParams (uses ``reset_gain``) and
    AdaptiveHyperLIFParams (uses ``base_gain + gain_scaling*|I|``).
    """

    if hasattr(p, "gain_scaling") and hasattr(p, "base_gain"):
        return float(p.base_gain + p.gain_scaling * abs(current))
    return float(p.reset_gain)


def coupled_equilibria(current: float, p, n_scan: int = 4000) -> list[dict[str, float]]:
    """Return self-consistent equilibria (v*, r*) of the coupled (v, r) system.

    A frozen-gate voltage equilibrium ``v*(r)`` is substituted into the gate
    steady state ``r = sigmoid(alpha (v*(r) - (v_thresh - gamma r)))`` and the
    residual ``g(r) = sigmoid(...) - r`` is scanned for sign changes over
    r in [0, 1], then refined by bisection. Each returned equilibrium reports
    voltage, gate, the conductance scale, and a simple stability flag for the
    fast gate map.
    """

    gain_scale = _adaptive_gain_scale(current, p)

    def residual(r: float) -> float:
        v = latched_voltage(current, p, gain_scale, r)
        eff_thresh = p.v_thresh - p.gamma * r
        return _sigmoid(p.alpha * (v - eff_thresh)) - r

    rs = np.linspace(0.0, 1.0, n_scan)
    vals = np.array([residual(r) for r in rs])

    roots: list[float] = []
    for i in range(n_scan - 1):
        a, b = vals[i], vals[i + 1]
        if a == 0.0:
            roots.append(rs[i])
        elif a * b < 0.0:
            lo, hi = rs[i], rs[i + 1]
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if residual(lo) * residual(mid) <= 0.0:
                    hi = mid
                else:
                    lo = mid
            roots.append(0.5 * (lo + hi))

    out: list[dict[str, float]] = []
    eps = 1e-5
    for r_star in roots:
        v_star = latched_voltage(current, p, gain_scale, r_star)
        # Stability of the fast gate fixed point: d(sigmoid)/dr - 1 < 0.
        dgate = (residual(min(1.0, r_star + eps)) - residual(max(0.0, r_star - eps))) / (2 * eps)
        out.append(
            {
                "current": float(current),
                "v_star": float(v_star),
                "r_star": float(r_star),
                "gain_scale": float(gain_scale),
                "gate_stable": bool(dgate < 0.0),
            }
        )
    return out


def db_onset_current(p) -> float:
    """Closed-form DB-onset current for the baseline (fixed-gain) HyperLIF.

    The neuron latches when the depolarized equilibrium with the gate open
    (r = 1) reaches the gate knee v_thresh - gamma:

        (v_rest + I + tau*G*v_reset)/(1 + tau*G) = v_thresh - gamma

    Solving for I gives

        I_DB = (v_thresh - gamma)(1 + tau*G) - v_rest - tau*G*v_reset.

    Uses ``reset_gain`` if present (HyperLIF), else ``base_gain`` as the
    fixed baseline capacity.
    """

    g = float(getattr(p, "reset_gain", getattr(p, "base_gain", 0.0)))
    knee = p.v_thresh - p.gamma
    return float(knee * (1.0 + p.tau * g) - p.v_rest - p.tau * g * p.v_reset)


def adaptive_asymptotic_voltage(p) -> float:
    """Limit of the open-gate depolarized voltage as |I| -> infinity (adaptive).

    With G = base_gain + gain_scaling|I| and r = 1,

        v*(I) = (v_rest + I + tau*G*v_reset)/(1 + tau*G).

    As |I| -> infinity this tends to (1 + tau*gain_scaling*v_reset)/(tau*gain_scaling).
    """

    s = float(getattr(p, "gain_scaling", 0.0))
    if s <= 0.0:
        return float("inf")
    return float((1.0 + p.tau * s * p.v_reset) / (p.tau * s))


def adaptive_is_db_free(p) -> dict[str, float | bool]:
    """Whether the adaptive law keeps the high-drive equilibrium below the knee.

    If the asymptotic open-gate voltage stays below the gate knee
    (v_thresh - gamma), the gate never fully commits at arbitrarily large drive,
    so the adaptive model cannot latch into the saturated DB equilibrium that
    traps the fixed-gain model. The threshold on gain_scaling (normalized case
    v_rest = v_reset = 0) is gain_scaling > 1 / (tau (v_thresh - gamma)).
    """

    v_inf = adaptive_asymptotic_voltage(p)
    knee = gate_knee_voltage(p)
    crit = float("inf")
    denom = p.tau * (p.v_thresh - p.gamma)
    if denom > 0.0:
        crit = 1.0 / denom
    return {
        "asymptotic_voltage": float(v_inf),
        "gate_knee": float(knee),
        "gain_scaling": float(getattr(p, "gain_scaling", 0.0)),
        "gain_scaling_critical": float(crit),
        "db_free": bool(v_inf < knee),
    }
