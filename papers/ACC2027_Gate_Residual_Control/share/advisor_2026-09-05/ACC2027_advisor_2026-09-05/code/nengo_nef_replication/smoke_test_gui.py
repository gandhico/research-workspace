"""Headless build-and-run checks for both Nengo MuJoCo GUI platforms."""
from __future__ import annotations

import argparse
import json
import os
import runpy
from pathlib import Path

import nengo
import numpy as np


HERE = Path(__file__).resolve().parent


def run_case(platform: str, mission: str, duration: float) -> dict:
    os.environ["GRA_GUI_PLATFORM"] = platform
    os.environ["GRA_GUI_MISSION"] = mission
    os.environ["GRA_GUI_DURATION"] = "45"
    os.environ["GRA_GUI_ACTUATOR_SCALE"] = "1.5" if platform == "cf2-rotor" else "1.0"
    os.environ["GRA_GUI_MUJOCO_VIEWER"] = "none"
    os.environ["GRA_GUI_REALTIME"] = "0"
    os.environ["GRA_GUI_VIEWER_FPS"] = "30"
    namespace = runpy.run_path(str(HERE / "gui_cmg_pes_mujoco.py"))
    with nengo.Simulator(namespace["model"], dt=namespace["DT"], progress_bar=False) as sim:
        namespace["on_start"](sim)
        sim.run(duration)
        errors = np.asarray(sim.data[namespace["p_errors"]])
        attitude = np.asarray(sim.data[namespace["p_attitude"]])
        residual = np.asarray(sim.data[namespace["p_residual"]])
        activity = np.asarray(sim.data[namespace["p_activity"]])
        weights = np.asarray(namespace["LIVE"].weights)
        namespace["on_close"](sim)

    arrays = (errors, attitude, residual, activity, weights)
    if not all(np.all(np.isfinite(array)) for array in arrays):
        raise RuntimeError(f"Non-finite GUI state for {platform}/{mission}")
    if errors.shape[1] != 2 or activity.shape[1] != 6 or weights.shape != (3, 6):
        raise RuntimeError(f"Unexpected signal schema for {platform}/{mission}")

    return {
        "platform": platform,
        "mission": mission,
        "simulated_seconds": duration,
        "steps": int(errors.shape[0]),
        "last_pd_qerror_rad": float(errors[-1, 0]),
        "last_cmg_pes_qerror_rad": float(errors[-1, 1]),
        "max_abs_residual_Nm": float(np.max(np.abs(residual))),
        "max_activity": float(np.max(activity)),
        "decoder_frobenius_norm": float(np.linalg.norm(weights)),
        "finite": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=0.20)
    parser.add_argument(
        "--output", type=Path, default=HERE / "results" / "gui_smoke_test.json"
    )
    args = parser.parse_args()
    if args.duration <= 0:
        raise ValueError("--duration must be positive")

    cases = [
        run_case("x2", "hard45", args.duration),
        run_case("cf2-rotor", "yaw360", args.duration),
    ]
    payload = {"status": "passed", "dt_seconds": 5e-4, "cases": cases}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
