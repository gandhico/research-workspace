"""Experiment 03: f-I curves and the depolarization block.

Sweeps a constant input current and records steady-state firing rate, peak and
mean voltage, gate occupancy, and mean reset conductance for LIF, HyperLIF, and
Adaptive HyperLIF. Firing rate is measured over a settling window so the single
onset crossing does not inflate low rates.

Also records the analytical depolarization-block (DB) analysis from
``src/analysis`` and cross-checks the predicted latched voltage against the
simulated mean voltage in the latched regime. Feeds Figure ``fig_fi`` and the
DB discussion.
"""

from __future__ import annotations

import numpy as np

from _common import CSV_DIR, ensure_results, write_log
from analysis import (
    adaptive_is_db_free,
    coupled_equilibria,
    db_onset_current,
    gate_knee_voltage,
    latched_voltage,
)
from neurons import AdaptiveHyperLIFParams, HyperLIFParams, LIFParams
from neurons.adaptive_hyperlif import simulate_adaptive_hyperlif
from neurons.hyperlif import simulate_hyperlif
from neurons.lif import simulate_lif
from simulation.current_protocols import time_axis
from simulation.metrics import write_rows


def _steady_rate(events: np.ndarray, t: np.ndarray, settle: float) -> float:
    """Event rate measured only after a settling time ``settle`` (Hz)."""

    mask = t >= settle
    window = float(t[-1] - settle) if t[-1] > settle else 0.0
    count = int(np.count_nonzero(np.asarray(events)[mask] > 0.0))
    return count / window if window > 0.0 else 0.0


def _summarize(name: str, current_level: float, trace: dict, t: np.ndarray, settle: float) -> dict:
    row = {
        "model": name,
        "input_current": float(current_level),
        "event_rate_hz": _steady_rate(trace["events"], t, settle),
        "voltage_max": float(np.max(trace["voltage"])),
        "voltage_mean": float(np.mean(trace["voltage"][t >= settle])),
        "gate_mean": float(np.mean(trace["reset_gate"][t >= settle])) if "reset_gate" in trace else 0.0,
        "gate_max": float(np.max(trace["reset_gate"])) if "reset_gate" in trace else 0.0,
        "conductance_mean": float(np.mean(trace["conductance"][t >= settle])) if "conductance" in trace else 0.0,
    }
    return row


def main() -> None:
    ensure_results()

    dt = 1e-4
    duration = 0.6
    settle = 0.15
    t = time_axis(duration, dt)
    currents = np.round(np.arange(0.0, 6.0001, 0.1), 4)

    hyper_p = HyperLIFParams()
    adapt_p = AdaptiveHyperLIFParams()
    lif_p = LIFParams()

    rows: list[dict] = []
    for level in currents:
        current = np.full_like(t, float(level))
        lif = simulate_lif(current, dt, lif_p)
        hyper = simulate_hyperlif(current, dt, hyper_p, method="julia")
        adaptive = simulate_adaptive_hyperlif(current, dt, adapt_p, method="julia")
        rows.append(_summarize("LIF", level, lif, t, settle))
        rows.append(_summarize("HyperLIF", level, hyper, t, settle))
        rows.append(_summarize("Adaptive HyperLIF", level, adaptive, t, settle))

    write_rows(CSV_DIR / "03_current_sweep.csv", rows)

    # --- Analytical DB analysis, cross-checked against the sweep ---------------
    i_db = db_onset_current(hyper_p)
    knee = gate_knee_voltage(hyper_p)
    adapt_info = adaptive_is_db_free(adapt_p)

    # Cross-check: predicted vs simulated latched voltage for fixed HyperLIF at
    # a current well above the DB onset.
    check_I = 4.0
    pred_latched = latched_voltage(check_I, hyper_p, hyper_p.reset_gain, r=1.0)
    sim_row = next(r for r in rows if r["model"] == "HyperLIF" and abs(r["input_current"] - check_I) < 1e-6)
    sim_latched = sim_row["voltage_mean"]

    eq_rows = []
    for level in [1.0, 2.0, 2.4, 3.0, 4.0, 5.0]:
        for name, p in [("HyperLIF", hyper_p), ("Adaptive HyperLIF", adapt_p)]:
            for eq in coupled_equilibria(level, p):
                eq_rows.append({"model": name, **eq})
    write_rows(CSV_DIR / "03_equilibria.csv", eq_rows)

    db_rows = [
        {
            "quantity": "hyperlif_db_onset_current",
            "value": i_db,
            "note": "(v_thresh-gamma)(1+tau*reset_gain); fixed-gain DB latch onset",
        },
        {"quantity": "gate_knee_voltage", "value": knee, "note": "v_thresh - gamma"},
        {
            "quantity": "hyperlif_latched_voltage_pred_at_I4",
            "value": pred_latched,
            "note": "analytical v* with r=1",
        },
        {
            "quantity": "hyperlif_latched_voltage_sim_at_I4",
            "value": sim_latched,
            "note": "simulated mean voltage in latched regime",
        },
        {
            "quantity": "adaptive_asymptotic_voltage",
            "value": adapt_info["asymptotic_voltage"],
            "note": "open-gate voltage as |I|->inf",
        },
        {
            "quantity": "adaptive_gain_scaling",
            "value": adapt_info["gain_scaling"],
            "note": "configured gain_scaling (beta)",
        },
        {
            "quantity": "adaptive_gain_scaling_critical",
            "value": adapt_info["gain_scaling_critical"],
            "note": "1/(tau(v_thresh-gamma)); above this the open-gate eq stays below the knee",
        },
        {
            "quantity": "adaptive_db_free",
            "value": float(bool(adapt_info["db_free"])),
            "note": "1 if asymptotic voltage < gate knee",
        },
    ]
    write_rows(CSV_DIR / "03_db_analysis.csv", db_rows)

    # Empirical operating-range summary from the sweep.
    def rate_of(model: str, lo: float, hi: float) -> float:
        vals = [r["event_rate_hz"] for r in rows if r["model"] == model and lo <= r["input_current"] <= hi]
        return float(np.max(vals)) if vals else 0.0

    log = [
        f"Sweep rows: {len(rows)} (currents {currents[0]}..{currents[-1]}, step 0.1)",
        f"HyperLIF DB-onset current (analytical): {i_db:.4f}",
        f"Gate knee voltage (v_thresh - gamma): {knee:.4f}",
        f"Fixed-HyperLIF latched voltage at I={check_I}: predicted {pred_latched:.4f}, simulated {sim_latched:.4f}",
        f"Adaptive asymptotic open-gate voltage: {adapt_info['asymptotic_voltage']:.4f} "
        f"(knee {knee:.4f}); db_free={adapt_info['db_free']}",
        f"Adaptive gain_scaling {adapt_info['gain_scaling']:.1f} vs critical "
        f"{adapt_info['gain_scaling_critical']:.4f}",
        f"Peak HyperLIF rate: {rate_of('HyperLIF', 0, 6):.1f} Hz; "
        f"peak Adaptive rate: {rate_of('Adaptive HyperLIF', 0, 6):.1f} Hz; "
        f"peak LIF rate: {rate_of('LIF', 0, 6):.1f} Hz",
    ]
    write_log("03_current_sweep.txt", "\n".join(log) + "\n")


if __name__ == "__main__":
    main()
