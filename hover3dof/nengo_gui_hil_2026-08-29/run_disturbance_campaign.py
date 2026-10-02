"""Run all nontrivial Hover missions with matched PD/CMG hard pulses."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
MISSION_PROFILE = {
    "roll": {"pulse_factor": 1.0, "reference_scale": 1.0, "transition": 0.0, "allocator": "fixed-bias"},
    "full3": {"pulse_factor": 1.0, "reference_scale": 1.0, "transition": 0.0, "allocator": "fixed-bias"},
    "hard45": {"pulse_factor": 0.05, "reference_scale": 1.0, "transition": 0.0, "allocator": "fixed-bias"},
    "hardstep": {"pulse_factor": 0.10, "reference_scale": 0.7, "transition": 0.5, "allocator": "stability-priority"},
    "yaw360": {"pulse_factor": 0.05, "reference_scale": 0.8, "transition": 0.0, "allocator": "stability-priority"},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=HERE / "results" / "disturbance_campaign_2026-08-31")
    parser.add_argument("--duration", type=float, default=25.0)
    parser.add_argument("--disturbance-scale", type=float, default=1.0)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    for mission in MISSIONS:
        profile = MISSION_PROFILE[mission]
        applied_scale = args.disturbance_scale * profile["pulse_factor"]
        for controller in ("pd", "nengo-pes"):
            command = [
                sys.executable, str(HERE / "run_hover_headless.py"),
                "--controller", controller, "--mission", mission,
                "--duration", str(args.duration), "--disturbance", "hard-pulses",
                "--disturbance-scale", str(applied_scale),
                "--output-root", str(args.output_root),
                "--reference-scale", str(profile["reference_scale"]),
                "--hardstep-transition-s", str(profile["transition"]),
                "--allocation-policy", profile["allocator"],
            ]
            print(f"RUN Hover {mission}/{controller}", flush=True)
            result = subprocess.run(command, check=False)
            if result.returncode:
                print(f"PRESERVED ABORT {mission}/{controller}: exit={result.returncode}", flush=True)


if __name__ == "__main__":
    main()
