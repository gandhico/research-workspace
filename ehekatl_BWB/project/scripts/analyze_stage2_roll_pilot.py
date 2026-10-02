#!/usr/bin/env python3
"""Evaluate a Stage-2 roll pilot against the three frozen Stage-1 baselines."""

import argparse
import csv
from pathlib import Path

import numpy as np


FREQUENCIES_HZ = (0.10, 0.20, 0.35, 0.55, 0.80)


def load(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def array(rows, name):
    def number(text):
        if text.lower() == "true":
            return 1.0
        if text.lower() == "false":
            return 0.0
        return float(text)

    return np.asarray([number(row[name]) for row in rows], dtype=float)


def correlation(a, b):
    return float(np.corrcoef(a, b)[0, 1]) if np.std(a) and np.std(b) else float("nan")


def spectral_amplitudes(rows, field):
    t = array(rows, "t_s")
    y = array(rows, field)
    mask = (t >= 10.0) & (t <= 50.0)
    t = t[mask]
    y = y[mask]
    y = y - np.polyval(np.polyfit(t, y, 1), t)
    return np.asarray([
        2.0 * abs(np.sum(y * np.exp(-2j * np.pi * frequency * t))) / len(t)
        for frequency in FREQUENCIES_HZ
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path)
    parser.add_argument("baselines", type=Path, nargs=3)
    args = parser.parse_args()

    pilot = load(args.pilot)
    baselines = [load(path) for path in args.baselines]
    t = array(pilot, "t_s")
    excitation = array(pilot, "identification_excitation")
    active = np.abs(excitation) > 0.0
    total_roll = array(pilot, "total_roll_ratio")
    sent_roll = array(pilot, "sent_ctrl_1")

    print(f"file={args.pilot}")
    print(f"rows={len(pilot)} elapsed_s={t[-1] - t[0]:.9f} max_gap_s={np.max(np.diff(t)):.9f}")
    print(
        "engaged_fraction={:.6f} start_allowed_fraction={:.6f}".format(
            np.mean(array(pilot, "engaged")), np.mean(array(pilot, "start_allowed"))
        )
    )
    print(
        "paused_samples={} replay_samples={} zero_speed_samples={}".format(
            int(np.count_nonzero(array(pilot, "sim_paused"))),
            int(np.count_nonzero(array(pilot, "replay_mode"))),
            int(np.count_nonzero(array(pilot, "sim_speed") <= 0.0)),
        )
    )
    print(
        f"excitation_samples={np.count_nonzero(active)} range="
        f"{np.min(excitation):+.7f}..{np.max(excitation):+.7f}"
    )
    print(
        "corr_excitation_sent={:.6f} corr_sent_total={:.6f} corr_excitation_total={:.6f}".format(
            correlation(excitation[active], sent_roll[active]),
            correlation(sent_roll[active], total_roll[active]),
            correlation(excitation[active], total_roll[active]),
        )
    )
    for lag in range(1, 4):
        lag_mask = active[:-lag] & active[lag:]
        print(
            f"lag_{lag}_corr_sent_total="
            f"{correlation(sent_roll[:-lag][lag_mask], total_roll[lag:][lag_mask]):.6f} "
            f"corr_excitation_total="
            f"{correlation(excitation[:-lag][lag_mask], total_roll[lag:][lag_mask]):.6f}"
        )
    for field in ("total_roll_ratio", "roll_deg", "p_deg_s", "pitch_deg", "q_deg_s"):
        values = array(pilot, field)
        print(f"{field}_range={np.min(values):+.7f}..{np.max(values):+.7f}")
    print(
        "abort_samples={} saturation_samples={}".format(
            sum(row["identification_latched_off"].lower() == "true" for row in pilot),
            sum(
                row["ctrl_0_saturated"].lower() == "true"
                or row["ctrl_1_saturated"].lower() == "true"
                for row in pilot
            ),
        )
    )

    for field in ("roll_deg", "p_deg_s"):
        pilot_spectrum = spectral_amplitudes(pilot, field)
        baseline_spectra = np.vstack([spectral_amplitudes(rows, field) for rows in baselines])
        baseline_max = np.max(baseline_spectra, axis=0)
        ratios = np.divide(
            pilot_spectrum, baseline_max,
            out=np.full_like(pilot_spectrum, np.inf), where=baseline_max > 0,
        )
        print(f"{field}_spectral_amplitude=" + ",".join(f"{value:.8g}" for value in pilot_spectrum))
        print(f"{field}_vs_baseline_max_ratio=" + ",".join(f"{value:.3f}" for value in ratios))


if __name__ == "__main__":
    main()
