"""Characterize activity and *actual* event rates before RL training.

This is an operating-point study on prescribed currents, not evidence of
racing-control improvement. The same current is supplied to each mode.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import numpy as np

from cmg_cells import CMGPopulation, CMGParams, policy_preset

HERE = Path(__file__).resolve().parent


def run(mode: str, current: float, duration: float, dt: float, params: CMGParams):
    cell = CMGPopulation(1, mode, params)
    trace = []
    for k in range(round(duration / dt)):
        cell.step(np.array([current]), dt)
        if k % max(1, round(0.002 / dt)) == 0:
            trace.append((cell.time_s, current, cell.v[0], cell.r[0],
                          cell.features()[0], cell.last_events[0], cell.filtered_rate_hz[0]))
    x = np.asarray(trace)
    # Count after the first 0.5 s so a single startup crossing cannot be
    # misreported as sustained spiking.
    warm_steps = round(min(0.5, duration / 4) / dt)
    cell2 = CMGPopulation(1, mode, params)
    count_warm = 0
    for k in range(round(duration / dt)):
        cell2.step(np.array([current]), dt)
        if k == warm_steps - 1:
            count_warm = int(cell2.event_total[0])
    steady_hz = (int(cell2.event_total[0]) - count_warm) / (duration - warm_steps * dt)
    return dict(mode=mode, current=current, event_count=int(cell.event_total[0]),
                event_hz_steady=steady_hz, gate_mean_steady=float(np.mean(x[x[:, 0] >= 0.5, 3])),
                feature_mean_steady=float(np.mean(x[x[:, 0] >= 0.5, 4])),
                voltage_mean_steady=float(np.mean(x[x[:, 0] >= 0.5, 2]))), x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=2.0)
    ap.add_argument("--dt", type=float, default=0.0005)
    ap.add_argument("--currents", type=float, nargs="+", default=[0.4, 0.8, 1.2, 1.6, 2.0, 2.8])
    ap.add_argument("--out", type=Path, default=HERE / "results" / "cell_calibration")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for mode in CMGPopulation.MODES:
        p = policy_preset(mode)
        for current in a.currents:
            row, trace = run(mode, current, a.duration, a.dt, p)
            rows.append(row)
            np.savez_compressed(a.out / f"{mode}_current_{current:g}.npz",
                                t=trace[:, 0], current=trace[:, 1], voltage=trace[:, 2],
                                gate=trace[:, 3], feature=trace[:, 4], event=trace[:, 5],
                                filtered_rate_hz=trace[:, 6])
    with (a.out / "summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    (a.out / "manifest.json").write_text(json.dumps({"duration_s": a.duration, "neural_dt_s": a.dt,
        "currents": a.currents, "parameters": policy_preset("graded").asdict(),
        "note": "crossing mode is upward crossings without reset; reset_spike changes the cell dynamics"}, indent=2))
    for row in rows:
        print(f"{row['mode']:12s} J={row['current']:4.1f}  spikes={row['event_hz_steady']:6.1f} Hz  "
              f"mean gate={row['gate_mean_steady']:.3f}  mean feature={row['feature_mean_steady']:.3f}")
    print(a.out)


if __name__ == "__main__":
    main()
