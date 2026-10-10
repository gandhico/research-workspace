"""Run or resume the matched 45 s CF2-rotor and Skydio-X2 NEF campaign."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_mujoco_nef.py"
PLATFORMS = {"cf2-rotor": 1.5, "x2": 1.0}
MISSIONS = ("hover", "roll", "full3", "hard45", "hardstep", "yaw360")
CONTROLLERS = ("classical", "nengo-nef-pes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=HERE / "results" / "matched_45s")
    parser.add_argument("--duration", type=float, default=45.0)
    parser.add_argument("--log-every", type=int, default=10)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    completed = []
    for platform, actuator_scale in PLATFORMS.items():
        for mission in MISSIONS:
            for controller in CONTROLLERS:
                label = f"{platform}_{mission}_{controller}".replace("-", "_")
                output = args.output_root / label
                summary_path = output / "summary.json"
                if summary_path.exists() and not args.force:
                    summary = json.loads(summary_path.read_text(encoding="utf-8"))
                    if summary.get("duration") == args.duration and summary.get("n_steps", 0) > 0:
                        print(f"SKIP complete {label}", flush=True)
                        completed.append(summary)
                        continue
                command = [
                    sys.executable,
                    str(RUNNER),
                    "--platform", platform,
                    "--controller", controller,
                    "--mission", mission,
                    "--duration", str(args.duration),
                    "--dt", "0.0005",
                    "--beta", "0.5",
                    "--learning-rate", "0.0008",
                    "--k-error", "8",
                    "--k-rate", "0",
                    "--actuator-scale", str(actuator_scale),
                    "--log-every", str(args.log_every),
                    "--output", str(output),
                ]
                print(f"RUN {label}", flush=True)
                subprocess.run(command, check=True)
                completed.append(json.loads(summary_path.read_text(encoding="utf-8")))
    print(f"COMPLETE {len(completed)} runs", flush=True)


if __name__ == "__main__":
    main()

