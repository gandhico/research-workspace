from __future__ import annotations

import argparse
import sys
from pathlib import Path


PLATFORM = "qcar"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLATFORM_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "_shared"))

from quanser_residual_campaign.runner import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run QCar/QCar2 offline baseline vs HyperLIF residual benchmark.")
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    payload = run_benchmark(
        platform=PLATFORM,
        output_dir=PLATFORM_ROOT / "results" / "offline",
        duration=args.duration,
        make_plots=not args.no_plots,
    )
    print(f"Summary: {payload['artifacts']['summary_json']}")
    print(f"Figure: {payload['artifacts']['figure']}")


if __name__ == "__main__":
    main()

