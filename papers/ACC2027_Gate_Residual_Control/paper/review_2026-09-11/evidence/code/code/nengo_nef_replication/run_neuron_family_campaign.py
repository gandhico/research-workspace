"""Run the matched fixed/PES neuron-family campaign with resumable outputs."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_CONTROLLERS = (
    "classical",
    "nengo-cmg-fixed",
    "nengo-nef-pes",
    "nengo-lif-fixed", "nengo-lif-pes",
    "nengo-alif-fixed", "nengo-alif-pes",
    "nengo-izhikevich-fixed", "nengo-izhikevich-pes",
    "nengo-lifrate-fixed", "nengo-lifrate-pes",
)
DEFAULT_MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
PLATFORM_SCALE = {"x2": 1.0, "cf2-rotor": 1.5}


def csv_tuple(value: str):
    return tuple(item.strip() for item in value.split(",") if item.strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=HERE / "results" / "neuron_family_matched_45s")
    parser.add_argument("--platforms", type=csv_tuple, default=tuple(PLATFORM_SCALE))
    parser.add_argument("--missions", type=csv_tuple, default=DEFAULT_MISSIONS)
    parser.add_argument("--controllers", type=csv_tuple, default=DEFAULT_CONTROLLERS)
    parser.add_argument("--duration", type=float, default=45.0)
    parser.add_argument("--log-every", type=int, default=10)
    parser.add_argument("--no-neural-archive", action="store_true")
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    plan = []
    for platform in args.platforms:
        for mission in args.missions:
            for controller in args.controllers:
                output = args.output_root / platform / mission / controller
                summary = output / "summary.json"
                if summary.exists():
                    plan.append({"platform": platform, "mission": mission, "controller": controller, "status": "existing"})
                    continue
                command = [
                    sys.executable, str(HERE / "run_mujoco_nef.py"),
                    "--platform", platform, "--controller", controller,
                    "--mission", mission, "--duration", str(args.duration),
                    "--dt", "0.0005", "--beta", "0.5",
                    "--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0",
                    "--actuator-scale", str(PLATFORM_SCALE[platform]),
                    "--log-every", str(args.log_every), "--output", str(output),
                ]
                if args.no_neural_archive:
                    command.append("--no-neural-archive")
                print(f"RUN {platform}/{mission}/{controller}", flush=True)
                started = time.perf_counter()
                subprocess.run(command, check=True)
                plan.append({
                    "platform": platform, "mission": mission, "controller": controller,
                    "status": "completed", "wall_seconds": time.perf_counter() - started,
                })
    payload = {
        "schema": 1,
        "duration_s": args.duration,
        "dt_s": 0.0005,
        "beta": 0.5,
        "learning_rate": 0.0008,
        "k_error": 8.0,
        "k_rate": 0.0,
        "platform_actuator_scale": PLATFORM_SCALE,
        "missions": list(args.missions),
        "controllers": list(args.controllers),
        "full_neural_archive": not args.no_neural_archive,
        "runs": plan,
    }
    (args.output_root / "campaign_manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Campaign complete: {len(plan)} run cells")


if __name__ == "__main__":
    main()

