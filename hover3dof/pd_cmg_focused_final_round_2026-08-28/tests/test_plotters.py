"""Render smoke tests for both offline PD figure generators."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


class PlotterTests(unittest.TestCase):
    def _write_run(self, folder: Path, controller: str) -> None:
        folder.mkdir(parents=True)
        rows = []
        for index, t in enumerate(np.linspace(0.0, 0.095, 20)):
            row = {"t": t}
            for axis, phase in zip(("yaw", "pitch", "roll"), (0.0, .5, 1.0)):
                row[f"{axis}_ref_deg"] = 5.0 * np.sin(t + phase)
                row[f"{axis}_deg"] = 4.8 * np.sin(t + phase)
                row[f"requested_delta_tau_{axis}"] = .001 * np.sin(t + phase)
                row[f"realized_delta_tau_{axis}"] = .0008 * np.sin(t + phase)
            for channel, offset in zip(("Vf", "Vb", "Vl", "Vr"), (0.0, .2, .4, .6)):
                row[channel] = 2.0 + offset + .1 * np.sin(t)
            row["requested_residual_torque_norm"] = .003
            row["realized_residual_torque_norm"] = .002
            if controller == "pd-cmg":
                for unit in range(6):
                    row[f"neuron_v_{unit}"] = .1 * unit + t
                    row[f"neuron_r_{unit}"] = min(1.0, index / 19 + .01 * unit)
                    row[f"neuron_activity_{unit}"] = min(1.0, index / 19 + .02 * unit)
                for weight in range(18):
                    row[f"decoder_w_{weight}"] = .1 + .001 * index + .01 * weight
            rows.append(row)
        with (folder / "trace.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        (folder / "summary.json").write_text(json.dumps({
            "controller": controller,
            "mission": "hover",
            "duration": .1,
            "angle_err_mean_deg": .25 if controller == "pd" else .2,
            "angle_err_max_deg": .5,
        }), encoding="utf-8")

    def test_both_plotters_render(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            pd = base / "pd"
            cmg = base / "cmg"
            self._write_run(pd, "pd")
            self._write_run(cmg, "pd-cmg")
            tracking = base / "tracking.png"
            neurons = base / "neurons.png"
            subprocess.run([
                sys.executable, str(ROOT / "plotters" / "plot_pd_tracking.py"),
                "--pd", str(pd), "--pd-cmg", str(cmg), "--out", str(tracking),
            ], check=True)
            subprocess.run([
                sys.executable, str(ROOT / "plotters" / "plot_pd_neurons.py"),
                "--run-dir", str(cmg), "--out", str(neurons),
            ], check=True)
            self.assertGreater(tracking.stat().st_size, 10_000)
            self.assertGreater(neurons.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
