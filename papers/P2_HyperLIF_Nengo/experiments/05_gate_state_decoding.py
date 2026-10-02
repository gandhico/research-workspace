"""Experiment 05: decoding from voltage, filtered events, and the reset gate.

A smooth multi-frequency current drives an Adaptive HyperLIF neuron. We fit
scalar linear decoders (least squares, 70/30 train/test split) from three
internal signals:

  * membrane voltage  -> input current,
  * exponentially filtered events -> input current,
  * reset gate r(t)   -> a readiness-to-fire target derived from the current.

Generates the trace CSV, the decoder-metrics CSV, and the summary log used by
Figure ``fig_decode`` and Table ``tab_decoding``.
"""

from __future__ import annotations

import numpy as np

from _common import CSV_DIR, ensure_results, write_log
from neurons import AdaptiveHyperLIFParams
from neurons.adaptive_hyperlif import simulate_adaptive_hyperlif
from simulation.current_protocols import decoding_protocol, time_axis
from simulation.metrics import exp_filter_events, linear_decode, write_csv, write_rows


def main() -> None:
    ensure_results()

    dt = 1e-4
    duration = 1.0
    t = time_axis(duration, dt)
    current = decoding_protocol(t)
    adaptive = simulate_adaptive_hyperlif(current, dt, AdaptiveHyperLIFParams(), method="julia")

    filtered_events = exp_filter_events(adaptive["events"], dt, tau=0.025)
    # Readiness target: a saturating ramp of input current into [0, 1].
    readiness = np.clip((current - 0.7) / 0.9, 0.0, 1.0)

    pred_voltage, train_v, test_v = linear_decode(adaptive["voltage"], current)
    pred_events, train_e, test_e = linear_decode(filtered_events, current)
    pred_gate, train_g, test_g = linear_decode(adaptive["reset_gate"], readiness)

    write_csv(
        CSV_DIR / "05_gate_state_decoding.csv",
        {
            "t": t,
            "input_current": current,
            "readiness_target": readiness,
            "voltage": adaptive["voltage"],
            "reset_gate": adaptive["reset_gate"],
            "events": adaptive["events"],
            "filtered_events": filtered_events,
            "decoded_current_from_voltage": pred_voltage,
            "decoded_current_from_events": pred_events,
            "decoded_readiness_from_gate": pred_gate,
        },
    )

    rows = [
        {"decoder": "voltage_to_current", "train_rmse": train_v, "test_rmse": test_v},
        {"decoder": "filtered_events_to_current", "train_rmse": train_e, "test_rmse": test_e},
        {"decoder": "gate_to_readiness", "train_rmse": train_g, "test_rmse": test_g},
    ]
    write_rows(CSV_DIR / "05_decoding_metrics.csv", rows)
    write_log("05_gate_state_decoding.txt", "\n".join(str(row) for row in rows) + "\n")


if __name__ == "__main__":
    main()
