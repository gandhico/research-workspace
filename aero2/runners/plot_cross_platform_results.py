from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLATFORM_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "_shared"))

from quanser_residual_campaign.plot_latest import plot_latest


def main() -> None:
    figure_path = plot_latest(PLATFORM_ROOT / "results" / "cross_platform_offline")
    print(f"Saved figure: {figure_path}")


if __name__ == "__main__":
    main()

