#!/usr/bin/env python3
"""Replay the exact frozen inner-rate runtime controller over saved logs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lqr.delay_aware_lqr import DelayAwareRateLQR


def replay(path: Path, axis: str):
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    rate_column = "p_deg_s" if axis == "roll" else "q_deg_s"
    trim_column = "ctrl_before_1" if axis == "roll" else "ctrl_before_0"
    controller = DelayAwareRateLQR(axis, float(rows[0][trim_column]))
    perturbations = [controller.step(float(row[rate_column]))[1] for row in rows]
    return {
        "file": path.name,
        "axis": axis,
        "samples": len(rows),
        "peak_perturbation": float(np.max(np.abs(perturbations))),
        "rms_perturbation": float(np.sqrt(np.mean(np.square(perturbations)))),
        "saturation_fraction": float(np.mean(np.abs(perturbations) >= controller.command_limit - 1e-12)),
        "max_slew": float(np.max(np.abs(np.diff([0.0] + perturbations)))),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    definitions = {
        "roll": ("stage2_roll_training_01_20260710_142240.csv", "stage2_roll_training_02_20260710_142615.csv",
                 "stage2_roll_validation_01_20260710_143047.csv", "stage2_roll_validation_02_20260712_135450.csv"),
        "pitch": ("stage2_pitch_training_01_20260712_140739.csv", "stage2_pitch_training_02_20260712_141515.csv",
                  "stage2_pitch_validation_01_20260712_142028.csv", "stage2_pitch_validation_02_20260712_142348.csv"),
    }
    result = [replay(ROOT / "logs" / name, axis) for axis, names in definitions.items() for name in names]
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
