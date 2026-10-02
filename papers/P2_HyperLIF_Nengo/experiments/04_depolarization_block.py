"""Experiment 04: depolarization-block latch under sustained high drive.

At a constant current above the analytical DB-onset of the fixed-gain model,
the baseline HyperLIF latches at a depolarized equilibrium (gate saturates open,
repetitive spiking ceases), while Adaptive HyperLIF raises its discharge
capacity with |I| and keeps producing a stable limit cycle. Generates the trace
CSV for Figure ``fig_db``.
"""

from __future__ import annotations

import numpy as np

from _common import CSV_DIR, ensure_results, write_log
from analysis import db_onset_current, latched_voltage
from neurons import AdaptiveHyperLIFParams, HyperLIFParams
from neurons.adaptive_hyperlif import simulate_adaptive_hyperlif
from neurons.hyperlif import simulate_hyperlif
from simulation.current_protocols import time_axis
from simulation.metrics import event_count, write_csv


def main() -> None:
    ensure_results()

    dt = 1e-4
    duration = 0.3
    drive = 3.3  # above the fixed-gain DB onset (~2.4), within the adaptive firing range
    t = time_axis(duration, dt)
    current = np.full_like(t, drive)

    hyper_p = HyperLIFParams()
    adapt_p = AdaptiveHyperLIFParams()

    hyper = simulate_hyperlif(current, dt, hyper_p, method="julia")
    adaptive = simulate_adaptive_hyperlif(current, dt, adapt_p, method="julia")

    write_csv(
        CSV_DIR / "04_depolarization_block.csv",
        {
            "t": t,
            "input_current": current,
            "hyperlif_voltage": hyper["voltage"],
            "hyperlif_reset_gate": hyper["reset_gate"],
            "hyperlif_conductance": hyper["conductance"],
            "hyperlif_events": hyper["events"],
            "adaptive_voltage": adaptive["voltage"],
            "adaptive_reset_gate": adaptive["reset_gate"],
            "adaptive_conductance": adaptive["conductance"],
            "adaptive_dynamic_gain": adaptive["dynamic_gain"],
            "adaptive_events": adaptive["events"],
        },
    )

    settle = t >= 0.1
    pred_latched = latched_voltage(drive, hyper_p, hyper_p.reset_gain, r=1.0)
    log = [
        f"Drive current: {drive}",
        f"Fixed-gain DB onset (analytical): {db_onset_current(hyper_p):.4f}",
        f"HyperLIF: events={event_count(hyper['events'])}, "
        f"settled mean V={np.mean(hyper['voltage'][settle]):.4f}, "
        f"settled mean gate={np.mean(hyper['reset_gate'][settle]):.4f} "
        f"(predicted latched V={pred_latched:.4f})",
        f"Adaptive: events={event_count(adaptive['events'])}, "
        f"settled mean V={np.mean(adaptive['voltage'][settle]):.4f}, "
        f"settled mean gate={np.mean(adaptive['reset_gate'][settle]):.4f}, "
        f"settled mean conductance={np.mean(adaptive['conductance'][settle]):.4f}",
    ]
    write_log("04_depolarization_block.txt", "\n".join(log) + "\n")


if __name__ == "__main__":
    main()
