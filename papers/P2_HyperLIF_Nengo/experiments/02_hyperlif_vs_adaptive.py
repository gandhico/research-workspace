"""Experiment 02: fixed-gain HyperLIF vs Adaptive HyperLIF under a stress current.

A piecewise-constant current ramps to high amplitude to expose the difference
between the fixed reset conductance ``reset_gain*r^2`` and the input-dependent
adaptive conductance ``(base_gain + gain_scaling|I|)*r^2``. Generates the trace
CSV and summary log used by Figure ``fig_stress``.
"""

from __future__ import annotations

from _common import CSV_DIR, ensure_results, write_log
from neurons import AdaptiveHyperLIFParams, HyperLIFParams
from neurons.adaptive_hyperlif import simulate_adaptive_hyperlif
from neurons.hyperlif import simulate_hyperlif
from simulation.current_protocols import stress_protocol, time_axis
from simulation.metrics import trace_summary, write_csv


def main() -> None:
    ensure_results()

    dt = 1e-4
    duration = 0.34
    t = time_axis(duration, dt)
    current = stress_protocol(t)

    hyper = simulate_hyperlif(current, dt, HyperLIFParams(), method="julia")
    adaptive = simulate_adaptive_hyperlif(current, dt, AdaptiveHyperLIFParams(), method="julia")

    write_csv(
        CSV_DIR / "02_hyperlif_vs_adaptive.csv",
        {
            "t": t,
            "input_current": current,
            "hyperlif_voltage": hyper["voltage"],
            "hyperlif_reset_gate": hyper["reset_gate"],
            "hyperlif_conductance": hyper["conductance"],
            "hyperlif_events": hyper["events"],
            "adaptive_voltage": adaptive["voltage"],
            "adaptive_reset_gate": adaptive["reset_gate"],
            "adaptive_dynamic_gain": adaptive["dynamic_gain"],
            "adaptive_conductance": adaptive["conductance"],
            "adaptive_events": adaptive["events"],
        },
    )

    rows = [
        trace_summary("HyperLIF", hyper, duration),
        trace_summary("Adaptive HyperLIF", adaptive, duration),
    ]
    write_log("02_hyperlif_vs_adaptive.txt", "\n".join(str(row) for row in rows) + "\n")


if __name__ == "__main__":
    main()
