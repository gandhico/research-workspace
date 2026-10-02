"""Experiment 01: hard-reset LIF vs continuous-reset HyperLIF under a step.

Generates the trace CSV and summary log used by Figure ``fig_step`` and the
qualitative discussion of the continuous reset gate.
"""

from __future__ import annotations

from _common import CSV_DIR, ensure_results, write_log
from neurons import HyperLIFParams, LIFParams, simulate_hyperlif, simulate_lif
from simulation.current_protocols import step_protocol, time_axis
from simulation.metrics import trace_summary, write_csv


def main() -> None:
    ensure_results()

    dt = 1e-4
    duration = 0.25
    t = time_axis(duration, dt)
    current = step_protocol(t, high=1.4)

    lif = simulate_lif(current, dt, LIFParams())
    hyper = simulate_hyperlif(current, dt, HyperLIFParams(), method="julia")

    write_csv(
        CSV_DIR / "01_lif_vs_hyperlif.csv",
        {
            "t": t,
            "input_current": current,
            "lif_voltage": lif["voltage"],
            "lif_events": lif["events"],
            "hyperlif_voltage": hyper["voltage"],
            "hyperlif_reset_gate": hyper["reset_gate"],
            "hyperlif_conductance": hyper["conductance"],
            "hyperlif_events": hyper["events"],
        },
    )

    rows = [
        trace_summary("LIF", lif, duration),
        trace_summary("HyperLIF", hyper, duration),
    ]
    write_log("01_lif_vs_hyperlif.txt", "\n".join(str(row) for row in rows) + "\n")


if __name__ == "__main__":
    main()
